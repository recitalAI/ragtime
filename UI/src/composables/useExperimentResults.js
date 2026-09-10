// State + actions behind the experiment-results page (sub-step 5.2).
// All computation lives in experimentResultsTransforms.js (pure,
// unit-testable); this composable owns the refs and the interactions the
// children emit back to.
import { ref, computed } from 'vue';
import { marked } from 'marked';
import { experimentService } from '@/services/generatorService';
import {
  buildDetailedGroups,
  computeChunksSummary,
  computeQuestionBadge,
  splitSummaryResults,
} from '@/composables/experimentResultsTransforms';

// marked-based formatters, shared with the presentational children.
export const markdownToHtml = (text) => {
  return marked(text);
};

export const formatAnswer = (text) => {
  if (!text) return '';
  let t = String(text);
  // Some pipelines flattened real newlines into literal 'n'/'nn' right after a
  // sentence-ending char (:.)]) — restore them (only when followed by something
  // that plausibly starts a new line, to avoid touching real words).
  t = t.replace(/([:.)\]])(nn?)(?=[A-ZÀ-Ý0-9•-])/g, (m, p1, p2) => p1 + (p2 === 'nn' ? '\n\n' : '\n'));
  // Unwrap block HTML the model sometimes emits, so marked can re-render it
  // cleanly instead of leaving raw <p>…</p> with un-parsed markdown inside.
  t = t.replace(/<\/p>\s*<p>/gi, '\n\n').replace(/<\/?p>/gi, '\n\n');
  t = t.replace(/<br\s*\/?>/gi, '\n');
  // Normalize bullet characters (• ·) at line start into markdown list markers,
  // and ensure a dash marker has a space after it. Flat list — every bullet or
  // dash becomes a top-level item (robust across the model's irregular nesting).
  t = t.replace(/^[\u2022\u00b7]\s*/gm, '- ');
  t = t.replace(/^-(?=\S)/gm, '- ');
  t = t.replace(/\n{3,}/g, '\n\n').trim();
  return marked(t, { breaks: true });
};

// I4: highlight, inside the rendered answer, the passages that a fact refers to
// — green for an OK fact, red for a Hallu fact — with the fact shown on hover.
// The extract text comes from the eval (fact.evalExtract). Matching order:
// exact substring -> whitespace-tolerant -> fragments split around [...] / (...)
// / ... truncations. If nothing matches, the passage is left untouched (no
// false highlight) so the answer simply renders as before.
const _escapeAttr = (s) => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

export const highlightAnswer = (answerText, facts) => {
  const html = formatAnswer(answerText);
  if (!Array.isArray(facts) || facts.length === 0) return html;

  const STATUS_LABEL = { ok: 'OK', hallu: 'Hallu', missing: 'Missing' };

  // Collect passages to highlight, each tagged with its fact (status, text,
  // comment). A fact's extract may hold several "…" quotes and/or [...]
  // truncations — every real fragment becomes a needle.
  const needles = [];
  facts.forEach((f, fi) => {
    const st = f.status;
    if (st !== 'ok' && st !== 'hallu' && st !== 'missing') return;
    const raw = (f.evalExtract || '').trim();
    if (!raw) return;
    let passages = (raw.match(/"([^"]+)"/g) || []).map((q) => q.slice(1, -1));
    if (passages.length === 0) passages = [raw];
    for (let p of passages) {
      p = p.replace(/^["'\s]+|["'\s]+$/g, '');
      if (/^\[.*\]$/.test(p)) continue;
      const frags = p
        .split(/\s*(?:\[\.\.\.\]|\(\.\.\.\)|\.\.\.)\s*/)
        .map((x) => x.replace(/^[\s\-\u2013\u2014:]+|\s+$/g, '').trim())
        .filter((x) => x.length >= 12);
      for (const fr of frags) {
        needles.push({ text: fr, fi, status: st, fact: f.text || '', comment: f.evalComment || '' });
      }
    }
  });
  if (needles.length === 0) return html;
  needles.sort((a, b) => b.text.length - a.text.length);

  // Visible text + offset map (skips tags, inserts a space at block-tag edges
  // so passages spanning <li>/<p> still match, decodes common entities).
  const entity = { '&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#39;': "'", '&rsquo;': '\u2019', '&nbsp;': ' ' };
  const blockTag = /^<\/?(?:li|p|ul|ol|div|br|tr|td|h[1-6]|blockquote)\b/i;
  let vtext = '';
  const map = [];
  for (let i = 0; i < html.length; ) {
    if (html[i] === '<') {
      const e = html.indexOf('>', i);
      const tag = html.slice(i, e < 0 ? html.length : e + 1);
      const next = e < 0 ? html.length : e + 1;
      if (blockTag.test(tag) && vtext.length && !/\s$/.test(vtext)) { vtext += ' '; map.push(next); }
      i = next; continue;
    }
    if (html[i] === '&') {
      const sc = html.indexOf(';', i);
      if (sc >= 0 && sc - i <= 9) { vtext += (entity[html.slice(i, sc + 1)] || ' '); map.push(i); i = sc + 1; continue; }
    }
    vtext += html[i]; map.push(i); i++;
  }

  const escapeRe = (str) => str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

  // Find every needle's visible range (whitespace-tolerant). Unlike before we
  // DO keep overlaps — a passage shared by several facts must show them all.
  const hits = []; // { vs, ve, needle }
  for (const n of needles) {
    let re;
    try { re = new RegExp(escapeRe(n.text.replace(/\s+/g, ' ').trim()).replace(/ /g, '\\s+'), 'g'); }
    catch (e) { continue; }
    let m;
    while ((m = re.exec(vtext)) !== null) {
      let vs = m.index, ve = m.index + m[0].length;
      while (vs < ve && /\s/.test(vtext[vs])) vs++;
      while (ve > vs && /\s/.test(vtext[ve - 1])) ve--;
      if (ve > vs) hits.push({ vs, ve, needle: n });
      if (m.index === re.lastIndex) re.lastIndex++;
    }
  }
  if (hits.length === 0) return html;

  // Build boundary points, then walk segments; each segment carries the set of
  // facts covering it. A segment with >1 distinct fact is a shared ("multi")
  // zone. Emit <mark> per non-empty segment, back to front.
  const points = new Set();
  hits.forEach((h) => { points.add(h.vs); points.add(h.ve); });
  const bounds = [...points].sort((a, b) => a - b);

  const _attr = (s) => _escapeAttr(s);
  const segments = [];
  for (let b = 0; b < bounds.length - 1; b++) {
    const s = bounds[b], e = bounds[b + 1];
    if (e <= s) continue;
    const covering = hits.filter((h) => h.vs <= s && h.ve >= e).map((h) => h.needle);
    if (covering.length === 0) continue;
    // distinct facts covering this segment
    const byFact = {};
    covering.forEach((n) => { byFact[n.fi] = n; });
    const uniq = Object.values(byFact);
    const cls = uniq.length > 1 ? 'hl-multi' : ('hl-' + uniq[0].status);
    const title = uniq
      .map((n) => `[${STATUS_LABEL[n.status] || '?'}] ${n.fact}${n.comment ? ' — ' + n.comment : ''}`)
      .join('\n');
    segments.push({ hStart: map[s], hEnd: map[e - 1] + 1, cls, title });
  }
  // Insert marks back to front. A segment may span HTML tags (e.g. a passage
  // across two <li>, or through a <strong>). A single <mark> can't enclose tags
  // without producing invalid, browser-truncated markup — so within each
  // segment we wrap only the TEXT runs, closing before every tag and reopening
  // after it. Result: one visible highlight, valid HTML.
  segments.sort((a, b) => b.hStart - a.hStart);
  let out = html;
  for (const sg of segments) {
    const open = `<mark class="${sg.cls}" title="${_attr(sg.title)}">`;
    const slice = out.slice(sg.hStart, sg.hEnd);
    // Split the slice into tags (kept as-is) and text runs (wrapped).
    const wrapped = slice.replace(/([^<]+)|(<[^>]*>)/g, (m, textRun, tag) => {
      if (tag) return tag;                      // leave tags untouched
      if (!textRun || !textRun.trim()) return textRun; // don't wrap pure ws
      return open + textRun + '</mark>';
    });
    out = out.slice(0, sg.hStart) + wrapped + out.slice(sg.hEnd);
  }
  return out;
};

export function useExperimentResults() {
  const mainResults = ref([]);
  const chunkResults = ref([]);
  const fullEvaluation = ref([]);
  const experimentMeta = ref({});
  const loading = ref(true);
  const error = ref(null);
  const experimentName = ref('');
  const showChunksSummary = ref(false);
  const selectedModel = ref('');
  const chunksSummary = ref({
    llm: { hallucinations: 0, missings: 0, combined: 0, wholeTest: 0 },
    chunks: { hallucinations: 0, missings: 0, combined: 0, wholeTest: 0 }
  });

  const filters = ref({
    ok: true,
    hallu: true,
    missing: true,
    extra: true
  });

  const hasChunkEvaluations = computed(() => chunkResults.value.length > 0);
  // Chunk eval was requested but produced nothing to show — because there were
  // no hallucinations/missing facts to attribute (all answers correct). Lets
  // the UI explain the empty state instead of showing nothing.
  const chunkEvalRequestedButEmpty = computed(() =>
    !!experimentMeta.value.evaluate_chunks && !hasChunkEvaluations.value
  );
  // Facts whose evaluation silently failed (empty eval). Surfaced so totals
  // stay coherent (ok+hallu+missing+unevaluated = facts).
  const totalUnevaluated = computed(() =>
    (mainResults.value || []).reduce((s, r) => s + (r.unevaluated || 0), 0)
  );
  const groupedDetailedResults = ref([]);

  // Errors attributed to the retriever vs the LLM across all questions — the
  // key signal when evaluating a retriever. Shown by default when there are
  // errors (the per-model breakdown stays available on click).

  const filteredDetailedResults = computed(() => {
    return groupedDetailedResults.value
      .map((group, idx) => ({
        ...group,
        originalIndex: idx + 1,
        badge: computeQuestionBadge(group),
        show: (filters.value.ok && group.mainResult.ok > 0) ||
              (filters.value.hallu && group.mainResult.hallu > 0) ||
              (filters.value.missing && group.mainResult.missing > 0) ||
              (filters.value.extra && group.mainResult.extra > 0)
      }))
      .filter(group => group.show);
  });

  // `resultsSource` is the results name (post-experiment redirect) or a
  // legacy full path (old bookmarks); the backend accepts both.
  const fetchResults = async (resultsSource) => {
    if (resultsSource) {
      try {
        loading.value = true;
        error.value = null;
        const data = await experimentService.getExperimentResults(resultsSource);
        const summary = splitSummaryResults(data.summary);
        mainResults.value = summary.main;
        chunkResults.value = summary.chunks;
        groupedDetailedResults.value = buildDetailedGroups(data.detailed, data.full);
        fullEvaluation.value = data.full;
        experimentMeta.value = data.meta || {};
        experimentName.value = resultsSource.split('/').pop().replace('.json', '');
      } catch (err) {
        console.error('Error fetching experiment results:', err);
        error.value = 'Error fetching experiment results: ' + err.message;
      } finally {
        loading.value = false;
      }
    } else {
      error.value = 'No results name provided';
      loading.value = false;
    }
  };

  const toggleExpandedDetails = (group) => {
    const originalGroup = groupedDetailedResults.value.find(g => g.question === group.question);
    if (originalGroup) {
      originalGroup.showExpanded = !originalGroup.showExpanded;
    }
  };

  const showChunkContent = (group, chunkIndex) => {
    group.chunks[chunkIndex].isVisible = !group.chunks[chunkIndex].isVisible;
  };

  const showChunk = (group, factIndex, chunkNumber) => {
    const fact = group.facts[factIndex];
    if (fact) {
      const button = fact.chunkButtons.find(b => b.number === chunkNumber);
      if (button) {
        button.isVisible = !button.isVisible;
      }
    }
  };

  const toggleChunksSummary = (modelName) => {
    if (selectedModel.value === modelName && showChunksSummary.value) {
      showChunksSummary.value = false;
    } else {
      selectedModel.value = modelName;
      chunksSummary.value = computeChunksSummary(fullEvaluation.value, modelName);
      showChunksSummary.value = true;
    }
  };

  const closeChunksSummary = () => {
    showChunksSummary.value = false;
    setTimeout(() => {
      selectedModel.value = '';
    }, 150);
  };

  return {
    mainResults,
    chunkResults,
    fullEvaluation,
    loading,
    error,
    experimentName,
    showChunksSummary,
    selectedModel,
    chunksSummary,
    hasChunkEvaluations,
    chunkEvalRequestedButEmpty,
    totalUnevaluated,
    experimentMeta,
    groupedDetailedResults,
    filteredDetailedResults,
    filters,
    fetchResults,
    toggleExpandedDetails,
    showChunk,
    showChunkContent,
    toggleChunksSummary,
    closeChunksSummary,
  };
}
