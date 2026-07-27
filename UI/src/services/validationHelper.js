// validationHelper.js
//
// Single source of truth for normalizing validation-set data, whatever the
// entry point (file import, backend fetch, localStorage restore).
//
// Accepted input shapes:
//   { "meta": {...}, "items": [ ... ] }        (full Ragtime format)
//   [ ... ]                                    (bare array of items)
// where each item can be:
//   { "question": {"text": "..."} | "...",
//     "answers": {"items": [...]} | [...],     (optional)
//     "facts":   {"items": [...]} | [...] }    (optional)
//   { "question": "...", "answer": "..." }     (simple format)
// and each answer can be a string, or an object with "text" and optionally
// "llm_answer" and "eval".
//
// Output invariants (guaranteed for every item):
//   item.question.text      -> non-empty string
//   item.answers.items[]    -> { text: string, llm_answer: object, eval: { human: number }, isEditing: false }
//   item.facts.items[]      -> { meta: object, text: string }

export class FormatError extends Error {
  constructor(message) {
    super(message);
    this.name = 'FormatError';
  }
}

export const EXPECTED_FORMAT_HINT =
  'Expected format: {"items": [{"question": {"text": "..."}, ' +
  '"answers": {"items": [{"text": "..."}]}, "facts": {"items": [{"text": "..."}]}}]} ' +
  '— or the simple format [{"question": "...", "answer": "..."}]. ' +
  '"answers" and "facts" are optional.';

function toText(value) {
  if (typeof value === 'string') return value;
  if (value && typeof value === 'object' && typeof value.text === 'string') return value.text;
  return '';
}

function normalizeLLMAnswer(llmAnswer) {
  const base = llmAnswer && typeof llmAnswer === 'object' ? llmAnswer : {};
  return {
    ...base,
    cost: typeof base.cost === 'number' ? base.cost : null,
    duration: typeof base.duration === 'number' ? base.duration : null,
    name: base.name || 'Unknown',
    timestamp: base.timestamp || null,
  };
}

function normalizeAnswer(answer) {
  if (typeof answer === 'string') answer = { text: answer };
  if (!answer || typeof answer !== 'object') answer = {};
  const llm = normalizeLLMAnswer(answer.llm_answer);
  const humanRaw = answer.eval && answer.eval.human;
  return {
    meta: {},
    ...answer,
    text: toText(answer.text) || toText(llm.text) || '',
    llm_answer: llm,
    eval: {
      ...(answer.eval && typeof answer.eval === 'object' ? answer.eval : {}),
      human: Number.isFinite(Number(humanRaw)) ? Number(humanRaw) : 0,
    },
    isEditing: false,
  };
}

function normalizeFacts(facts) {
  let items = [];
  if (Array.isArray(facts)) items = facts;
  else if (facts && Array.isArray(facts.items)) items = facts.items;
  const normalizedItems = items
    .map((f) =>
      typeof f === 'string'
        ? { meta: {}, text: f }
        : { meta: {}, ...(f && typeof f === 'object' ? f : {}), text: toText(f && f.text) }
    )
    .filter((f) => f.text);
  const container = facts && !Array.isArray(facts) && typeof facts === 'object' ? { ...facts } : {};
  container.items = normalizedItems;
  if (container.llm_answer) container.llm_answer = normalizeLLMAnswer(container.llm_answer);
  return container;
}

function normalizeItem(item, index) {
  if (!item || typeof item !== 'object' || Array.isArray(item)) {
    throw new FormatError(`Item ${index + 1} is not an object. ${EXPECTED_FORMAT_HINT}`);
  }
  const questionText = toText(item.question).trim();
  if (!questionText) return null; // skipped by caller, counted in result

  let answers = item.answers;
  if (!answers && item.answer !== undefined) {
    // Simple format: {"question": "...", "answer": "..."} -> validated by definition
    answers = { items: [{ text: toText(item.answer), eval: { human: 1 } }] };
  }
  let answerItems = [];
  if (Array.isArray(answers)) answerItems = answers;
  else if (answers && Array.isArray(answers.items)) answerItems = answers.items;

  return {
    ...item,
    question:
      item.question && typeof item.question === 'object'
        ? { ...item.question, text: questionText }
        : { text: questionText },
    answers: { items: answerItems.map(normalizeAnswer) },
    facts: normalizeFacts(item.facts),
  };
}

/**
 * Normalize any supported input into { meta, items }.
 * Throws FormatError (with the expected-format hint) when the structure
 * cannot be interpreted, so callers can show a helpful message instead
 * of crashing later.
 */
export function validateData(data) {
  if (data == null) return { meta: {}, items: [] };
  if (Array.isArray(data)) data = { items: data };
  if (typeof data !== 'object') {
    throw new FormatError(`The file root must be an object or an array. ${EXPECTED_FORMAT_HINT}`);
  }
  if (!Array.isArray(data.items)) {
    throw new FormatError(`No "items" array found in the file. ${EXPECTED_FORMAT_HINT}`);
  }
  const items = [];
  let skipped = 0;
  data.items.forEach((item, i) => {
    const normalized = normalizeItem(item, i);
    if (normalized) items.push(normalized);
    else skipped += 1;
  });
  const result = { meta: data.meta && typeof data.meta === 'object' ? data.meta : {}, items };
  // Non-enumerable so it never leaks into saved JSON.
  Object.defineProperty(result, 'skippedCount', { value: skipped, enumerable: false });
  return result;
}

/**
 * The reference answer of a question, following the rule:
 * first human-validated answer (eval.human === 1) if any, otherwise the
 * first answer with non-empty text. Returns null when the question has
 * no usable answer.
 */
export function selectReferenceAnswer(question) {
  const items = (question && question.answers && question.answers.items) || [];
  const hasText = (a) => a && typeof a.text === 'string' && a.text.trim() !== '';
  return items.find((a) => hasText(a) && a.eval && Number(a.eval.human) === 1) || items.find(hasText) || null;
}

/**
 * Build the answer payload sent to /api/generate-facts for one question.
 * The Ragtime package only generates facts for answers with eval.human == 1,
 * so the selected reference answer is explicitly marked as validated here.
 * Handles answers with partial or missing llm_answer without crashing.
 */
export function buildFactAnswerPayload(answer) {
  const payload = {
    meta: (answer && answer.meta) || {},
    text: (answer && answer.text) || '',
    eval: { ...((answer && answer.eval) || {}), human: 1 },
  };
  const llm = answer && answer.llm_answer;
  if (llm && (llm.text || llm.timestamp || (llm.name && llm.name !== 'Unknown'))) {
    payload.llm_answer = { ...llm, timestamp: llm.timestamp || null };
  }
  return payload;
}
