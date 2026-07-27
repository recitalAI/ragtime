/**
 * Spreadsheet (.xlsx) formats for the two import points, in one place:
 *   - validation sets  (question / answer / facts)
 *   - experiment setup (question / answer / model_name / chunk_*)
 *
 * Holds the column specs, the human-readable help shown in the UI, the
 * .xlsx template generators, and the parsers. Keeping the spec, the help
 * text, the template and the parser together means they cannot drift apart.
 *
 * xlsx (SheetJS) is already a project dependency.
 */
import * as XLSX from 'xlsx';

export class SpreadsheetFormatError extends Error {
  constructor(message, details = []) {
    super(message);
    this.name = 'SpreadsheetFormatError';
    this.details = details;
  }
}

/* ------------------------------------------------------------------ *
 * Validation set format
 * ------------------------------------------------------------------ */

export const VALIDATION_SET_FORMAT = {
  title: 'Validation set file formats',
  required: ['question'],
  optional: ['answer', 'facts'],
  columns: [
    { name: 'question', required: true, help: 'The question text. Required.' },
    { name: 'answer', required: false, help: 'The reference answer. Optional — you can also generate answers later.' },
    {
      name: 'facts',
      required: false,
      help: 'The expected facts. Separate them with a semicolon (;), with a line break '
        + '(Alt+Enter in Excel), or write them as a list between brackets. Optional. '
        + 'Numbering is added automatically. Separate fact_1, fact_2, … columns also work.',
    },
  ],
  factsExample: 'Paris is the capital of France; France is a country in Europe\n'
    + '[Paris is the capital of France; France is a country in Europe]\n'
    + '(or one fact per line inside the cell)',
  jsonNote:
    'JSON is also accepted: either the full Ragtime format '
    + '{"items": [{"question": {"text": "..."}, "answers": {"items": [{"text": "..."}]}, "facts": {"items": [{"text": "..."}]}}]} '
    + 'or the simple format [{"question": "a question", "answer": "an answer"}].',
  example: {
    question: 'What is the capital of France?',
    answer: 'The capital of France is Paris.',
    facts: 'Paris is the capital of France; France is a country in Europe',
  },
};

/* ------------------------------------------------------------------ *
 * Experiment setup format (answers imported from a spreadsheet)
 * ------------------------------------------------------------------ */

export const EXPERIMENT_DATA_FORMAT = {
  title: 'Answer data file format',
  required: ['question'],
  optional: ['answer', 'model_name', 'chunk_1 … chunk_N'],
  columns: [
    { name: 'question', required: true, help: 'Must match a question of the selected validation set. Required.' },
    { name: 'answer', required: false, help: 'The answer produced by the system you want to evaluate.' },
    { name: 'model_name', required: false, help: 'Name of the system/model that produced the answer (shown in the results).' },
    {
      name: 'chunk_1, chunk_2, …',
      required: false,
      help: 'Retrieved passages, one per column. ANY column whose name starts with "chunk_" is picked up, '
        + 'so add chunk_6, chunk_7 … as needed — there is no fixed limit. The template ships with 5.',
    },
  ],
  jsonNote: null,
  example: {
    question: 'What is the capital of France?',
    answer: 'Paris.',
    model_name: 'my-rag-system',
    chunks: ['France is a country in Europe. Its capital is Paris.', 'Paris has 2.1M inhabitants.'],
  },
};

/* ------------------------------------------------------------------ *
 * Template generation
 * ------------------------------------------------------------------ */

function downloadWorkbook(rows, sheetName, fileName, colWidths) {
  const ws = XLSX.utils.aoa_to_sheet(rows);
  if (colWidths) ws['!cols'] = colWidths.map((w) => ({ wch: w }));
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, sheetName);
  XLSX.writeFile(wb, fileName);
}

/** Empty validation-set template with headers + one example row. */
export function downloadValidationSetTemplate() {
  const ex = VALIDATION_SET_FORMAT.example;
  downloadWorkbook(
    [
      ['question', 'answer', 'facts'],
      [ex.question, ex.answer, ex.facts],
    ],
    'validation_set',
    'ragtime_validation_set_template.xlsx',
    [60, 60, 60]
  );
}

/** Empty experiment data template with 5 chunk columns + one example row. */
export function downloadExperimentDataTemplate(chunkColumns = 5) {
  const ex = EXPERIMENT_DATA_FORMAT.example;
  const headers = ['question', 'answer', 'model_name'];
  for (let i = 1; i <= chunkColumns; i += 1) headers.push(`chunk_${i}`);
  const row = [ex.question, ex.answer, ex.model_name];
  for (let i = 0; i < chunkColumns; i += 1) row.push(ex.chunks[i] || '');
  downloadWorkbook(
    [headers, row],
    'answers',
    'ragtime_answers_template.xlsx',
    [60, 60, 20, ...Array(chunkColumns).fill(40)]
  );
}

/* ------------------------------------------------------------------ *
 * Parsing
 * ------------------------------------------------------------------ */

function sheetToRows(arrayBuffer) {
  const wb = XLSX.read(arrayBuffer, { type: 'array' });
  const first = wb.SheetNames[0];
  if (!first) throw new SpreadsheetFormatError('The workbook has no sheet.');
  return XLSX.utils.sheet_to_json(wb.Sheets[first], { header: 1, blankrows: false });
}

/**
 * Split a facts cell into individual facts. Accepts, in any combination:
 *   "fact one; fact two"            (semicolons — the documented default)
 *   "[fact one; fact two]"          (bracketed list)
 *   "fact one\nfact two"            (one per line, Alt+Enter in Excel)
 * A trailing separator is ignored, and a lone semicolon inside a sentence
 * is only a separator when it actually splits non-empty parts.
 */
export function splitFacts(raw) {
  let text = String(raw ?? '').trim();
  if (!text) return [];
  // Strip a single wrapping [...] if present.
  if (text.startsWith('[') && text.endsWith(']')) {
    text = text.slice(1, -1);
  }
  return text
    .split(/[;\n\r]+/)
    .map((f) => f.trim())
    .filter(Boolean);
}

function headerIndex(headers, name) {
  return headers.indexOf(name);
}

/**
 * Parse a validation-set .xlsx into normalized items
 * ({question:{text}, answers:{items:[…]}, facts:{items:[…]}}).
 * Throws SpreadsheetFormatError with actionable details.
 */
export function parseValidationSetSheet(arrayBuffer) {
  const rows = sheetToRows(arrayBuffer);
  if (!rows.length) throw new SpreadsheetFormatError('The sheet is empty.');

  const headers = (rows[0] || []).map((h) => String(h ?? '').trim().toLowerCase());
  const qi = headerIndex(headers, 'question');
  if (qi === -1) {
    throw new SpreadsheetFormatError(
      'The sheet must contain a "question" column.',
      [`Columns found: ${headers.filter(Boolean).join(', ') || '(none)'}`]
    );
  }
  const ai = headerIndex(headers, 'answer');
  const fi = headerIndex(headers, 'facts');
  const factColumns = headers
    .map((h, i) => ({ h, i }))
    .filter(({ h }) => /^fact_\d+$/.test(h))
    .map(({ i }) => i);

  const items = [];
  let skipped = 0;
  rows.slice(1).forEach((row) => {
    const question = String(row[qi] ?? '').trim();
    if (!question) { skipped += 1; return; }

    const answerText = ai !== -1 ? String(row[ai] ?? '').trim() : '';
    const answers = answerText
      ? [{ meta: {}, text: answerText, eval: { human: 1 }, llm_answer: { name: 'Human', timestamp: null, cost: null, duration: null } }]
      : [];

    let factTexts = [];
    if (fi !== -1) {
      factTexts = splitFacts(String(row[fi] ?? ''));
    }
    factColumns.forEach((ci) => {
      const t = String(row[ci] ?? '').trim();
      if (t) factTexts.push(t);
    });

    items.push({
      question: { text: question },
      answers: { items: answers },
      facts: {
        items: factTexts.map((t, idx) => ({
          meta: {},
          // Keep the package's numbered format so generated and imported
          // facts look identical everywhere.
          text: /^\s*\d+[.)]\s*/.test(t) ? t : `${idx + 1}. ${t}`,
        })),
      },
    });
  });

  if (!items.length) {
    throw new SpreadsheetFormatError(
      'No usable row found: every row is missing a question.',
      ['Fill the "question" column, one question per row.']
    );
  }
  return { items, skipped };
}

/** Validate an experiment-setup data sheet, returning its rows unchanged. */
export function validateExperimentSheet(rows) {
  if (!rows || !rows.length) throw new SpreadsheetFormatError('The sheet is empty.');
  const headers = (rows[0] || []).map((h) => String(h ?? '').trim().toLowerCase());
  if (headerIndex(headers, 'question') === -1) {
    throw new SpreadsheetFormatError(
      'The file must contain a "question" column.',
      [`Columns found: ${headers.filter(Boolean).join(', ') || '(none)'}`]
    );
  }
  return rows;
}
