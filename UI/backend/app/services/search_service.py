"""Search (reciTAL) retriever service.

Answers AND chunks come from the external Search platform, not from RAGtime's
own generation. For each question we:

    POST {BASE}/search/api/v1/search/   (query[, folder_id])  -> chunks + query_id
    POST {BASE}/search/api/v1/search/rag?query=&query_id=&prompt_id=
         (body = the chunks)                                  -> answer (streamed)

The answer stream is a sequence of {"msg": "..."} pieces we concatenate; the
model appends a citation marker like `[6578:1]` (file_id:split_id) which we
strip from the displayed/evaluated answer (the chunk provenance is kept on the
chunks themselves, so nothing is lost for a future "expected documents" metric).

Design notes:
  * BASE_URL and PROMPT_ID are fixed here (not user-configurable).
  * The bearer token and the optional folder_id come from the caller (they live
    in Profile settings, like the LLM API keys) — never logged, never written
    into results.
  * The HTTP layer (`_http_search` / `_http_rag`) is deliberately separated from
    the parsing/cleaning/Expe-building logic so the latter is unit-testable
    without network access.
  * This module is retriever-specific, but `build_expe_from_retrieval` returns a
    plain Expe usable by the generic review/evaluation flow — so a future
    retriever can reuse the same checkpoint machinery.
"""
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests

from ragtime.expe import QA, Answer, Answers, Chunk, Chunks, Expe, LLMAnswer, Question


# ── Fixed configuration (not user-configurable) ─────────────────────────────
SEARCH_BASE_URL = "https://rag.api.recital.ai"
SEARCH_PROMPT_ID = 13
SEARCH_API = "/search/api/v1"
_TIMEOUT = 60

# Concurrency + resilience knobs.
SEARCH_MAX_WORKERS = 6          # parallel questions (bounded to spare the server)
SEARCH_RETRIES = 3             # attempts per request on transient failures
SEARCH_BACKOFF = 2.0          # seconds, exponential base between retries
# If the parallel phase sees this many transient failures, fall back to a slow
# sequential pass for the remaining questions (let the server recover).
SEARCH_OVERLOAD_THRESHOLD = 3

# HTTP status codes worth retrying (transient: rate limit / server / gateway).
_TRANSIENT_STATUS = {429, 500, 502, 503, 504}

# Name under which the Search bearer token / folder id are stored (Profile
# settings, in the APIKey table like the LLM keys).
SEARCH_TOKEN_KEY = "SEARCH_TOKEN"
SEARCH_FOLDER_KEY = "SEARCH_FOLDER_ID"

# Citation marker the rag/ answer appends, e.g. "[6578:1]" or "[6578:1, 6578:2]".
_CITATION_RE = re.compile(r"\s*\[\s*\d+\s*:\s*\d+\s*(?:[,-]\s*\d+\s*(?::\s*\d+)?\s*)*\]")


class SearchError(RuntimeError):
    """Raised when a Search call fails in a way that should stop the phase."""


class SearchTransientError(SearchError):
    """A failure that is worth retrying (timeout, rate limit, 5xx) and that
    signals possible server overload."""


def _headers(token: str) -> Dict[str, str]:
    return {
        "accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _is_transient(exc: Exception) -> bool:
    if isinstance(exc, (requests.Timeout, requests.ConnectionError)):
        return True
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return exc.response.status_code in _TRANSIENT_STATUS
    return False


# ── HTTP layer (network) — kept thin so the rest is testable offline ────────
def _http_search(query: str, token: str, folder_id: Optional[str]) -> Dict[str, Any]:
    params: Dict[str, Any] = {"query": query}
    if folder_id:
        params["folder_id"] = folder_id
    url = f"{SEARCH_BASE_URL}{SEARCH_API}/search/"
    resp = requests.post(url, headers=_headers(token), params=params, json={}, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def _http_rag(query: str, query_id: int, chunks_body: List[Dict[str, Any]],
              token: str) -> List[str]:
    """Call rag/ and return the raw list of streamed message pieces."""
    params = {"query": query, "query_id": query_id, "prompt_id": SEARCH_PROMPT_ID}
    url = f"{SEARCH_BASE_URL}{SEARCH_API}/search/rag"
    resp = requests.post(url, headers=_headers(token), params=params,
                         json=chunks_body, timeout=_TIMEOUT, stream=True)
    resp.raise_for_status()
    pieces: List[str] = []
    for raw in resp.iter_lines(decode_unicode=True):
        if not raw:
            continue
        pieces.append(raw)
    return pieces


# ── Pure logic (no network) — unit-tested ───────────────────────────────────
def parse_rag_stream(raw_lines: List[str]) -> str:
    """Reconstruct the answer text from rag/'s streamed lines.

    Each line is normally a JSON object {"msg": "..."}; tolerate an SSE-style
    'data:' prefix and non-JSON lines (kept as-is)."""
    out: List[str] = []
    for raw in raw_lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("data:"):
            line = line[len("data:"):].strip()
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            out.append(line)
            continue
        if isinstance(obj, dict) and "msg" in obj:
            out.append(obj["msg"])
        else:
            out.append(json.dumps(obj, ensure_ascii=False))
    return "".join(out)


def strip_citations(answer: str) -> str:
    """Remove trailing/inline citation markers like [6578:1] from the answer."""
    if not answer:
        return ""
    cleaned = _CITATION_RE.sub("", answer)
    # Collapse any doubled spaces left behind, tidy space-before-period.
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([.,;:!?])", r"\1", cleaned)
    return cleaned.strip()


def chunk_content(chunk: Dict[str, Any]) -> str:
    """The text of a search/ chunk."""
    return str(chunk.get("content") or "").strip()


def build_qa(question_text: str, answer_text: str, chunks: List[Dict[str, Any]],
             facts_items: Optional[List[Dict[str, Any]]] = None,
             model_name: str = "Search") -> QA:
    """Build one QA (question + Search answer + chunks [+ carried facts]).

    Mirrors the structure the rest of RAGtime expects: the answer sits in
    answers.items[0] with an llm_answer stamp, chunks in chunks.items, facts (if
    the validation set carried them) preserved so evaluation can score them."""
    qa = QA()
    qa.question = Question(text=question_text)

    ans = Answer(text=answer_text)
    ans.llm_answer = LLMAnswer(
        name=model_name,
        text=answer_text,
        timestamp=datetime.now(),
        duration=None,
        cost=None,
    )
    qa.answers = Answers(items=[ans])

    qa.chunks = Chunks(items=[Chunk(text=chunk_content(c)) for c in chunks if chunk_content(c)])

    # Preserve facts from the validation set (needed by answer evaluation).
    if facts_items:
        from ragtime.expe import Fact, Facts
        qa.facts = Facts(items=[Fact(text=f.get("text", "") if isinstance(f, dict) else str(f))
                                for f in facts_items])
    return qa


# ── Orchestration (network) ─────────────────────────────────────────────────
def retrieve_and_generate(question_text: str, token: str,
                          folder_id: Optional[str] = None) -> Tuple[str, List[Dict[str, Any]]]:
    """One question -> (clean answer, chunks).

    Raises SearchTransientError on timeouts / rate-limit / 5xx (worth retrying
    and a sign of possible overload), SearchError on other failures."""
    try:
        sr = _http_search(question_text, token, folder_id)
    except Exception as e:
        if _is_transient(e):
            raise SearchTransientError(f"search/ transient failure: {e}") from e
        if isinstance(e, requests.HTTPError):
            code = e.response.status_code if e.response is not None else '?'
            raise SearchError(f"search/ failed ({code}) — token or folder access?") from e
        raise SearchError(f"search/ request error: {e}") from e

    chunks = sr.get("chunks", []) or []
    query_id = sr.get("query_id")
    if query_id is None:
        raise SearchError("search/ returned no query_id; cannot call rag/.")

    try:
        # Passthrough mapping confirmed sufficient during probing.
        pieces = _http_rag(question_text, query_id, chunks, token)
    except Exception as e:
        if _is_transient(e):
            raise SearchTransientError(f"rag/ transient failure: {e}") from e
        if isinstance(e, requests.HTTPError):
            code = e.response.status_code if e.response is not None else '?'
            raise SearchError(f"rag/ failed ({code}).") from e
        raise SearchError(f"rag/ request error: {e}") from e

    answer = strip_citations(parse_rag_stream(pieces))
    return answer, chunks


def retrieve_and_generate_with_retry(question_text: str, token: str,
                                     folder_id: Optional[str] = None,
                                     retries: int = SEARCH_RETRIES,
                                     backoff: float = SEARCH_BACKOFF
                                     ) -> Tuple[str, List[Dict[str, Any]]]:
    """retrieve_and_generate with exponential backoff on transient failures.
    Non-transient errors are raised immediately (retrying won't help)."""
    attempt = 0
    while True:
        try:
            return retrieve_and_generate(question_text, token, folder_id)
        except SearchTransientError:
            attempt += 1
            if attempt >= retries:
                raise
            time.sleep(backoff * (2 ** (attempt - 1)))


def _process_one(item: Dict[str, Any], token: str, folder_id: Optional[str]):
    """Retrieve one question. Returns (qa, error_str_or_None). A failure yields
    a QA with an empty answer and no chunks, plus the error string, so the batch
    can continue and the user sees it at the checkpoint."""
    q = item.get("question", "")
    facts = item.get("facts")
    try:
        answer, chunks = retrieve_and_generate_with_retry(q, token, folder_id)
        return build_qa(q, answer, chunks, facts_items=facts), None
    except SearchTransientError as e:
        return build_qa(q, "", [], facts_items=facts), f"overloaded/timeout: {e}"
    except SearchError as e:
        return build_qa(q, "", [], facts_items=facts), str(e)


def run_search_retrieval(expe_questions: List[Dict[str, Any]], token: str,
                         folder_id: Optional[str] = None,
                         log: Optional[Callable[[str], None]] = None,
                         max_workers: int = SEARCH_MAX_WORKERS) -> Expe:
    """Retrieve answers+chunks for every question and build an Expe.

    Runs questions in a bounded thread pool for speed. Each request retries with
    backoff on transient failures (timeout / rate-limit / 5xx). If the parallel
    phase hits too many transient failures (server overload), it stops launching
    new parallel work and processes the remaining questions sequentially to let
    the server recover. A question that still fails gets an empty answer + an
    error note (the batch never aborts); the checkpoint surfaces it.

    `expe_questions` is a list of {question, facts:[{text}]}; facts are carried
    from the validation set for the later evaluation. `log` gets progress lines
    (never the token). Results keep the input order.
    """
    def _log(msg: str):
        if log:
            log(msg)
        # Use the package logger ("ragtime_logger"), the SAME channel as answer
        # generation and evaluation. The root logger is set to WARNING by the
        # package, so logging.info here would be filtered out of the Docker
        # output and wouldn't be captured by the job log handler. Routing
        # through ragtime_logger unifies Search logs with the rest.
        logging.getLogger('ragtime_logger').info(msg)

    if not token:
        raise SearchError("No Search token configured. Add it in Profile settings.")

    total = len(expe_questions)
    results: List[Optional[QA]] = [None] * total
    _log(f"[Search] Retrieving answers and chunks for {total} question(s) "
         f"(up to {max_workers} in parallel)")

    transient_failures = 0
    overloaded = False
    done = 0

    # ── Parallel phase ──────────────────────────────────────────────────────
    if total > 1 and max_workers > 1:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_idx = {}
            # Submit only while not overloaded; keep a cursor for the rest.
            next_idx = 0
            # Prime the pool.
            while next_idx < total and len(future_to_idx) < max_workers:
                fut = pool.submit(_process_one, expe_questions[next_idx], token, folder_id)
                future_to_idx[fut] = next_idx
                next_idx += 1

            while future_to_idx:
                for fut in as_completed(list(future_to_idx)):
                    idx = future_to_idx.pop(fut)
                    qa, err = fut.result()
                    results[idx] = qa
                    done += 1
                    q = expe_questions[idx].get("question", "")[:70]
                    if err:
                        transient = err.startswith("overloaded/timeout")
                        transient_failures += 1 if transient else 0
                        _log(f"[Search][{done}/{total}] FAILED — {err} | {q}")
                    else:
                        n = len(qa.chunks.items) if qa.chunks else 0
                        _log(f"[Search][{done}/{total}] ok, {n} chunk(s) | {q}")

                    # Overload guard: stop feeding the pool; finish the rest slow.
                    if transient_failures >= SEARCH_OVERLOAD_THRESHOLD and not overloaded:
                        overloaded = True
                        _log(f"[Search] Too many transient failures "
                             f"({transient_failures}) — slowing down: remaining "
                             f"questions will run sequentially.")

                    # Feed one more into the pool if we still have work and are
                    # not in overload mode.
                    if next_idx < total and not overloaded:
                        f2 = pool.submit(_process_one, expe_questions[next_idx], token, folder_id)
                        future_to_idx[f2] = next_idx
                        next_idx += 1
                    break  # re-enter as_completed with the updated dict

            # Any leftover (overload kicked in) -> sequential below.
            remaining = list(range(next_idx, total))
    else:
        remaining = list(range(total))

    # ── Sequential phase (overload fallback, or single question) ────────────
    for idx in remaining:
        qa, err = _process_one(expe_questions[idx], token, folder_id)
        results[idx] = qa
        done += 1
        q = expe_questions[idx].get("question", "")[:70]
        if err:
            _log(f"[Search][{done}/{total}] FAILED — {err} | {q}")
        else:
            n = len(qa.chunks.items) if qa.chunks else 0
            _log(f"[Search][{done}/{total}] ok, {n} chunk(s) | {q}")
        if overloaded:
            time.sleep(SEARCH_BACKOFF)  # gentle pacing while recovering

    expe = Expe()
    for qa in results:
        expe.append(qa if qa is not None else build_qa("", "", []))
    n_failed = sum(1 for qa in results if qa is not None and (not qa.answers.items or not qa.answers.items[0].text))
    if n_failed:
        _log(f"[Search] Retrieval complete with {n_failed} empty/failed answer(s) — review before evaluating.")
    else:
        _log("[Search] Retrieval complete — awaiting review")
    return expe
