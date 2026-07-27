// Pure transforms behind the experiment-results page (sub-step 5.2).
// Everything here is dependency-free and side-effect-free so it can be
// unit-tested in isolation with a saved results JSON as fixture.
// Logic is moved verbatim from components/ExperimentResults.vue.

export const calculatePercentage = (value, total) => {
  if (total === 0) return '0.0';
  return ((value / total) * 100).toFixed(1);
};

export const formatCost = (cost) => {
  return `${(cost * 100).toFixed(2)}c$`;
};

// Total-cost format in US dollars, up to 3 decimals, trailing zeros trimmed
// (e.g. $2.157, $0.03, $0). Used for the "total price" figures on the Home
// tables and the experiment summary, where the user wants dollars rather than
// the per-call cents format above.
export const formatCostUSD = (cost) => {
  const n = Number(cost) || 0;
  // toFixed(3) then strip trailing zeros and any dangling decimal point.
  const s = n.toFixed(3).replace(/\.?0+$/, '');
  return `$${s}`;
};

export const getFactStatusClass = (status) => {
  switch (status) {
    case 'ok':
      return 'status-ok';
    case 'hallu':
      return 'status-error';
    case 'missing':
      return 'status-warning';
    default:
      return '';
  }
};

// Split the per-model summary rows into main models vs chunk-eval pseudo
// models ("Missings Eval" / "Hallucination(s) Eval").
export const splitSummaryResults = (results) => ({
  main: results.filter(result => !result.isChunkEval),
  chunks: results.filter(result => result.isChunkEval),
});

export const extractFactEvaluation = (evalText, factNumber) => {
  if (!evalText) return { result: '', evalShow: '' };
  // Remove HTML tags and normalize newlines
  const cleanText = evalText.replace(/<\/?[^>]+(>|$)/g, "\n").replace(/\n+/g, "\n").trim();

  // Remove [EXTRA] and everything after it
  const textWithoutExtra = cleanText.split(/\[extra\]|\[EXTRA\]|<p>\s*\[?extra\]?/i)[0];

  // Pattern for numbered or unnumbered list items
  const itemPattern = new RegExp(
    `(?:^|\\n)\\s*(?:${factNumber}\\.|\\[?${factNumber}\\]?)?\\s*` +
    `\\[(OK|NOT FOUND|HALLU)\\]` +
    `(?:(?!(?:\\n\\s*(?:${factNumber}\\.|\\[?${factNumber}\\]?)?\\s*\\[(OK|NOT FOUND|HALLU)\\])).)*`,
    'gms'
  );
  const paragraphPattern = new RegExp(`(?:Part(?:ie)? (?:in|dans) (?:the|le) paragraphe?|Citation pertinente du paragraphe|Part in the paragraph)\\s*(?::|:?\\s*)(.*)|(No part in the paragraph supports this fact\\.)`, 'i');
  let matches;
  // Initialize to a string so the `result.match(...)` calls below never
  // receive `undefined`. This happens when the evaluation LLM returns an
  // unstructured / free-text answer (e.g. it declines to classify because
  // the paragraph is too short) so no [OK]/[NOT FOUND]/[HALLU] block is
  // parsed: `matches` ends up empty and `result` would otherwise stay unset.
  let result = '';
  try {
    matches = [...(textWithoutExtra.matchAll(itemPattern) || [])];
    // Only read the block for THIS fact number when it actually exists.
    // Guarding here means an out-of-range factNumber (fewer parsed blocks
    // than facts) degrades to "unknown" rather than throwing and falling
    // through to the fallback, which used to show another fact's status.
    if (matches.length > 0 && matches[factNumber - 1]) {
      result = matches[factNumber - 1][0].trim();

      // Check for multiple occurrences of the pattern
      const patternToCheck = /(?:\n\s*(?:\d+\.|\[?\d+\]?)?\s*\[(OK|NOT FOUND|HALLU)\])/g;
      const occurrences = (result.match(patternToCheck) || []).length;

      if (occurrences > 1) {
        console.warn('Multiple fact patterns found in the result. Resetting matches.');
        matches = [];
        result = '';
      }
    }
  } catch (error) {
    console.warn('Error with initial pattern matching:', error);
    matches = [];
    result = '';
  }

  if (matches.length === 0) {
    console.log('No matches found with itemPattern, trying itemPattern2');
    const itemPattern2 = new RegExp(
      `(?:^|\\n)\\s*(?:${factNumber}\\.|\\[?${factNumber}\\]?)?\\s*` +
      `\\[(OK|NOT FOUND|HALLU)\\]` +
      `(?:(?!(?:\\n\\s*(?:\\d+\\.|\\[?\\d+\\]?)?\\s*\\[(OK|NOT FOUND|HALLU)\\])).)*` +
      `(?=\\s*\\d+\\s*$|$)`,
      'gms'
    );
    try {
      matches = textWithoutExtra.match(itemPattern2);
      // Pick the block for THIS fact number (not always the first one) so a
      // fact whose status block is absent degrades to "unknown" instead of
      // silently inheriting another fact's status.
      result = matches[factNumber - 1] ? matches[factNumber - 1].trim() : '';
    } catch (error) {
      console.warn('Error with fallback pattern matching:', error);
      matches = [];
    }
  }
  if (!matches) return { result: '', evalShow: '' };

  const stateMatch = result.match(/^\s*(?:\d+\.|\[\d+\])?\s*\[(OK|NOT FOUND|HALLU)\]/i);
  const state = stateMatch ? stateMatch[1] : '';

  let uniqueResult = result.replace(/^\s*(?:\d+\.|\[\d+\])?\s*\[(OK|NOT FOUND|HALLU)\]\s*-?\s*/i, '');
  const partMatch = result.match(paragraphPattern);
  let processedPartMatch = '';

  if (partMatch) {
    processedPartMatch = (partMatch[1] || partMatch[2] || '').trim();
    uniqueResult = uniqueResult.replace(partMatch[0], '').trim();
  }
  processedPartMatch = processedPartMatch.replace(/N\/A|None/gi, "").trim();
  const evalShow = `<p><em>${processedPartMatch || ' '}</em></p><p>${uniqueResult}</p>`;

  return { result: `[${state}] ${uniqueResult}`, evalShow };
};

export const extractChunkEvaluation = (chunkEvals, factNumber, qaChunks) => {

  if (!chunkEvals) {
    return { status: '', evaluation: '', chunkButtons: [] };
  }

  const relevantEval = chunkEvals.find(evalItem =>
    evalItem.evaluation && evalItem.evaluation.text && evalItem.evaluation.text.includes(`[Fait ${factNumber}]`)
  );

  if (relevantEval) {

    const regex = new RegExp(`\\[Fait ${factNumber}\\].*?(?=\\[Fait|$)`, 's');
    const match = relevantEval.evaluation.text.match(regex);
    const result = match ? match[0].trim() : '';

    const statusRegex = /(?:statut|status)\s*(?::)?\s*\[?(OK|HALLU|MISSING)\]?/i;
    const statusMatch = result.match(statusRegex);
    const status = statusMatch ? statusMatch[1].toLowerCase() : '';

    const explanationRegex = /Explication : (.*?)(?=\nLes chunks|\nSource|$)/s;
    const explanationMatch = result.match(explanationRegex);
    const explanation = explanationMatch ? explanationMatch[1].trim() : '';

    const sourceRegex = /Source(?:\s*\(si applicable\))?\s*(?::)?\s*"([^"]*)"/;
    const sourceMatch = result.match(sourceRegex);
    const source = sourceMatch ? `<em>${sourceMatch[1]}</em>` : '';

    // Extract chunks and create buttons
    const chunksRegex = /Les chunks(?:\s*\(si applicable\))?\s*(?::)?\s*"([^"]*)"/;
    const chunksMatch = result.match(chunksRegex);
    const chunks = chunksMatch ? chunksMatch[1] : '';

    const chunkNumbers = chunks.match(/\d+/g) || [];

    const chunkButtons = chunkNumbers.map(num => ({
      number: parseInt(num),
      text: qaChunks[parseInt(num) - 1]?.text || 'Chunk not found',
      isVisible: false
    }));

    const formattedEval = `
      ${source ? `<p>Source : ${source}</p>` : ''}
      <p>${explanation}</p>
    `;

    return { status, evaluation: formattedEval, chunkButtons };
  }

  return { status: '', evaluation: '', chunkButtons: [] };
};

export const analyzeFactAndChunkStatus = (factStatus, chunkStatus) => {
  let problemType = '';
  let explanation = '';

  switch (`${factStatus}${chunkStatus}`) {
    case 'missingok':
      problemType = 'LLM issue';
      explanation = `Correct chunks retrieved but the LLM failed to generate the correct answer.`;
      break;
    case 'missingmissing':
      problemType = 'Retriever or source issue';
      explanation = 'Chunks do not provide the correct context.';
      break;
    case 'missinghallu':
      problemType = 'Retriever or source issue';
      explanation = `Chunks provide inconsistent context, LLM detected that and didn't answer.`;
      break;
    case 'halluok':
      problemType = 'Contradiction';
      explanation = 'The LLM generates information that contradicts the information contained in the provided chunks.';
      break;
    case 'hallumissing':
      problemType = 'Invention';
      explanation = `The chunks provided do not contain the information, but the LLM adds it. It does not contradict what is stated in a chunk; it "invents" the information.`;
      break;
    case 'halluhallu':
      problemType = 'Corpus';
      explanation = 'A contradiction with one of the facts is present in the documentary corpus. The information is contained in the chunks, and the LLM reproduces it correctly, but this information contradicts one of the facts. This error could stem from a mistake in the validation dataset (incorrect fact), an issue with the retriever failing to retrieve the correct chunk, or an inconsistency in the documentation.';
      break;
    default:
      problemType = '';
      explanation = '';
  }

  return { problemType, explanation };
};

// Group the per-answer detailed rows by question, enriching each group with
// the answer/evaluation metadata and per-fact statuses used by the expanded
// row. Pure version of the former processDetailedResults (the caller assigns
// the returned array to its ref).
export const buildDetailedGroups = (results, fullEval) => {
  const groups = {};
  results.forEach((result, idx) => {
    if (!groups[result.text]) {
      const fullEvalItem = fullEval.find(item => item.question === result.text);

      if (!fullEvalItem) {
        console.error(`No matching full evaluation item found for question: ${result.text}`);
        return;
      }

      const mainAnswer = fullEvalItem.answers && fullEvalItem.answers[0];

      if (!mainAnswer) {
        console.error(`No main answer found for question: ${result.text}`);
        return;
      }

      const evaluation = mainAnswer.evaluation;
      groups[result.text] = {
        originalIndex: idx,
        question: result.text,
        mainResult: null,
        factsCount: result.factsCount,
        chunkEvals: [],
        hasChunkEvals: false,
        showChunkEvals: false,
        showDetails: false,
        showExpanded: false,
        chunks: (fullEvalItem.chunks || []).map((chunk) => ({
          ...chunk,
          isVisible: false
        })),
        facts: (fullEvalItem.facts || []).map((fact, index) => {
          const factNumber = index + 1;
          let status = 'unknown';
          let factEvaluation = '';

          if (evaluation && evaluation.text) {
            factEvaluation = extractFactEvaluation(evaluation.text, factNumber);
            if (factEvaluation.result.includes('[OK]')) status = 'ok';
            else if (factEvaluation.result.includes('[NOT FOUND]')) status = 'missing';
            else if (factEvaluation.result.includes('[HALLU]')) status = 'hallu';
          }

          const { status: chunkStatus, evaluation: chunkEvaluation, chunkButtons } =
            extractChunkEvaluation(fullEvalItem.chunkEvaluations, factNumber, fullEvalItem.chunks || []);

          const { problemType, explanation } = analyzeFactAndChunkStatus(status, chunkStatus);

          return {
            ...fact,
            status,
            evaluation: factEvaluation.evalShow,
            chunkEval: chunkEvaluation,
            chunkButtons: chunkButtons.map(button => ({ ...button, isVisible: false })),
            problemType,
            problemExplanation: explanation
          };
        }),
        answer: mainAnswer.text || '',
        answerModel: mainAnswer.model || 'Unknown',
        answerDate: mainAnswer.time || '',
        answerDuration: mainAnswer.duration || 0,
        answerCost: mainAnswer.cost || 0,
        evalModel: evaluation?.model || 'Unknown',
        evalDate: evaluation?.time || '',
        evalDuration: evaluation?.duration || 0,
        evalCost: evaluation?.cost || 0,
      };
    }

    if (result.model !== "Missings Eval" && result.model !== "Hallucinations Eval" && result.model !== "Hallucination Eval") {
      groups[result.text].mainResult = result;
      groups[result.text].mainModel = result.model;
    } else {
      groups[result.text].chunkEvals.push(result);
      groups[result.text].hasChunkEvals = true;
    }
  });

  return Object.values(groups);
};

// Attribution of hallucination/missing errors to the LLM vs the retriever
// for one model, from the full evaluation. Pure version of the former
// calculateChunksSummary.
export const computeChunksSummary = (fullEvaluationItems, modelName) => {
  let totalFacts = 0;
  let totalHallu = 0, totalMissing = 0;
  let llmHallu = 0, llmMissing = 0, chunksHallu = 0, chunksMissing = 0;

  fullEvaluationItems.forEach((item) => {
    totalFacts += item.facts.length;

    const mainAnswer = item.answers.find(a => a.model === modelName);
    if (mainAnswer && mainAnswer.evaluation) {
      totalHallu += mainAnswer.evaluation.hallu?.length || 0;
      totalMissing += mainAnswer.evaluation.missing?.length || 0;
    }

    const chunksHalluEval = item.chunkEvaluations.find(e => e.type === "Hallucinations Eval" || e.type === "Hallucination Eval")?.evaluation;
    const chunksMissingEval = item.chunkEvaluations.find(e => e.type === "Missings Eval")?.evaluation;

    if (chunksHalluEval && chunksHalluEval.meta) {
      llmHallu += (chunksHalluEval.meta.nb_ok || 0) + (chunksHalluEval.meta.nb_missing || 0);
      chunksHallu += (chunksHalluEval.meta.nb_hallu || 0) + (chunksHalluEval.meta.nb_missing || 0);
    }

    if (chunksMissingEval && chunksMissingEval.meta) {
      llmMissing += chunksMissingEval.meta.nb_ok || 0;
      chunksMissing += (chunksMissingEval.meta.nb_missing || 0) + (chunksMissingEval.meta.nb_hallu || 0);
    }
  });

  const llmCombined = llmHallu + llmMissing;
  const chunksCombined = chunksHallu + chunksMissing;
  const totalErrors = totalHallu + totalMissing;

  const calculatePercentage = (value, total) => {
    return total !== 0 ? Number((value / total * 100).toFixed(2)) : 0;
  };

  return {
    llm: {
      hallucinations: `${llmHallu} / ${totalHallu}`,
      hallucinationsPr: calculatePercentage(llmHallu, totalHallu),
      missings: `${llmMissing} / ${totalMissing}`,
      missingsPr: calculatePercentage(llmMissing, totalMissing),
      combined: `${llmCombined} / ${totalErrors}`,
      combinedPr: calculatePercentage(llmCombined, totalErrors),
      wholeTest: `${llmCombined} / ${totalFacts}`,
      wholeTestPr: calculatePercentage(llmCombined, totalFacts)
    },
    chunks: {
      hallucinationsPr: calculatePercentage(chunksHallu, totalHallu),
      hallucinations: `${chunksHallu} / ${totalHallu}`,
      missingsPr: calculatePercentage(chunksMissing, totalMissing),
      missings: `${chunksMissing} / ${totalMissing}`,
      combinedPr: calculatePercentage(chunksCombined, totalErrors),
      combined: `${chunksCombined} / ${totalErrors}`,
      wholeTestPr: calculatePercentage(chunksCombined, totalFacts),
      wholeTest: `${chunksCombined} / ${totalFacts}`
    }
  };
};