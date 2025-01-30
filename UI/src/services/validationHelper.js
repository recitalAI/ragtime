// validationHelper.js

function validateLLMAnswer(llmAnswer) {
  if (!llmAnswer) {
    return {
      cost: 0,
      duration: 0,
      name: "Unknown",
      timestamp: new Date().toUTCString()
    };
  }

  return {
    ...llmAnswer,
    cost: llmAnswer.cost ?? 0,
    duration: llmAnswer.duration ?? 0,
    name: llmAnswer.name || "Unknown",
    timestamp: llmAnswer.timestamp || new Date().toUTCString()
  };
}

function validateItems(items) {
  if (!Array.isArray(items)) return [];
  
  return items.map(item => {
    // Validate answers
    if (item.answers?.items) {
      item.answers.items = item.answers.items.map(answer => ({
        ...answer,
        llm_answer: validateLLMAnswer(answer.llm_answer)
      }));
    }

    // Validate facts
    if (item.facts?.llm_answer) {
      item.facts.llm_answer = validateLLMAnswer(item.facts.llm_answer);
    }

    return item;
  });
}

export function validateData(data) {
  if (!data) return { meta: {}, items: [] };

  const validatedData = {
    meta: data.meta || {},
    items: validateItems(data.items)
  };

  return validatedData;
}