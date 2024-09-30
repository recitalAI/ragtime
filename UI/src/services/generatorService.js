import { http } from '@/plugins/axios';


export const answerGeneratorService = {
  generateAnswers(questions, model, useRetriever = false, retrieverType = null) {
    const payload = {
      items: questions.map(q => ({ 
        question: { 
          text: q.question.text || q.question 
        } 
      })),
      model: model,
      useRetriever: useRetriever,
      retrieverType: retrieverType
    };
    return http.post('generate-answers', payload)
    .then(response => {
      if (response.data && response.data.items) {
        return response.data.items;
      } else {
        throw new Error('Unexpected response format from server');
      }
    })
    .catch(error => {
      console.error('Error generating answers:', error);
      throw error;
    });
  },

  
  generateAnswerForQuestion(questionData, model, useRetriever = false, retrieverType = null) {
    return this.generateAnswers([questionData], model, useRetriever, retrieverType)
      .then(items => items[0]);
  }
};

export const factGeneratorService = {
  generateFacts(questions, model) {
    const payload = {
      items: questions.map(q => ({
        question: { text: q.question.text || q.question },
        answers: { items: q.answers.items }
      })),
      model: model
    };
    return http.post('generate-facts', payload)
    .then(response => {
      if (response.data && response.data.items) {
        return response.data.items;
      } else {
        throw new Error('Unexpected response format from server');
      }
    })
    .catch(error => {
      console.error('Error generating facts:', error);
      throw error;
    });
  },

  generateFactsForQuestion(questionData, model) {
    return this.generateFacts([questionData], model)
      .then(items => items[0]);
  }
};

export const modelService = {
  async getAvailableModels() {
    try {
      const response = await http.get('available-models');
      return response.data;
    } catch (error) {
      console.error('Error fetching available models:', error);
      throw error;
    }
  },

  async getAvailableRetrievers() {
    try {
      const response = await http.get('available-retrievers');
      return response.data;
    } catch (error) {
      console.error('Error fetching available retrievers:', error);
      throw error;
    }
  }
};

export const experimentService = {
  startExperiment(config) {
    return http.post('start-experiment', config)
    .then(response => {
      if (response.data && response.data.results_path) {
        return response.data;
      } else {
        throw new Error('Unexpected response format from server');
      }
    })
    .catch(error => {
      console.error('Error starting experiment:', error);
      if (error.response) {
        console.error('Error response from server:', error.response.data);
        console.error('Error status:', error.response.status);
        console.error('Error headers:', error.response.headers);
      } else if (error.request) {
        console.error('No response received:', error.request);
      } else {
        console.error('Error setting up request:', error.message);
      }
      throw error;
    });
  },


  async deleteValidationSet(name) {
    try {
      // Find the full filename based on the displayed name
      const response = await http.get('validation-sets');
      const validationSet = response.data.find(set => set.name === name);
      if (!validationSet) {
        throw new Error('Validation set not found');
      }
      const fullFileName = `${name}_Validation_set_Q${validationSet.questions}_F${validationSet.facts}.json`;
      
      await http.delete(`delete-validation-set/${encodeURIComponent(fullFileName)}`);
      return { message: 'Validation set deleted successfully' };
    } catch (error) {
      console.error('Error deleting validation set:', error);
      throw error;
    }
  },

  async deleteExperiment(name) {
    try {
      await http.delete(`delete-experiment/${encodeURIComponent(name)}`);
      return { message: 'Experiment deleted successfully' };
    } catch (error) {
      console.error('Error deleting experiment:', error);
      throw error;
    }
  },

  async getValidationSet(name) {
    try {
      const response = await http.get(`validation-set/${encodeURIComponent(name)}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching validation set:', error);
      throw error;
    }
  },
  async getAllExperiments() {
    try {
      const response = await http.get('experiments');
      return response.data.map(experiment => ({
        ...experiment,
        chunks: experiment.chunks || 0,
        retriever: experiment.retriever || 'Not specified'
      }));
    } catch (error) {
      console.error('Error fetching all experiments:', error);
      throw error;
    }
  },
  
  async getExperimentResults(resultsPath) {
    try {
      const response = await http.get(`experiment-results?path=${encodeURIComponent(resultsPath)}`);
      const expe = response.data;

      // Process summary results
      const summary = this.processExperimentSummary(expe);

      // Process detailed results
      const detailed = this.processDetailedResults(expe);

      // Process full evaluation
      const full = this.processFullEvaluation(expe);

      return { summary, detailed, full };
    } catch (error) {
      console.error('Error fetching experiment results:', error);
      throw error;
    }
  },

  processExperimentSummary(expe) {
    const modelResults = {};
    const items = expe.items || [expe];  // Handle both structures

    items.forEach(qa => {
      const answers = qa.answers?.items || [qa];  // Handle both structures
      const mainAnswer = answers[0];

      answers.forEach(answer => {
        const modelName = answer.llm_answer?.name || answer.model;
        if (!modelResults[modelName]) {
          modelResults[modelName] = {
            name: modelName,
            count: 0,
            totalScore: 0,
            totalFacts: 0,
            totalOk: 0,
            totalHallu: 0,
            totalMissing: 0,
            totalExtra: 0,
            isChunkEval: modelName === "Missings Eval" || modelName === "Hallucinations Eval" || modelName === "Hallucination Eval"
          };
        }

        const result = modelResults[modelName];
        result.count++;

        if (modelName === "Hallucinations Eval" || modelName === "Hallucination Eval") {
          result.totalFacts += mainAnswer.eval?.meta?.nb_hallu || 0;
        } else if (modelName === "Missings Eval") {
          result.totalFacts += mainAnswer.eval?.meta?.nb_missing || 0;
        } else {
          result.totalScore += answer.eval?.auto || 0;
          result.totalFacts += qa.facts?.items?.length || 0;
        }

        result.totalOk += answer.eval?.meta?.nb_ok || 0;
        result.totalHallu += answer.eval?.meta?.nb_hallu || 0;
        result.totalMissing += answer.eval?.meta?.nb_missing || 0;
        result.totalExtra += answer.eval?.meta?.nb_extra || 0;
      });
    });

    return Object.values(modelResults).map(result => ({
      name: result.name,
      date: items[0].answers?.items?.find(a => a.llm_answer?.name === result.name)?.llm_answer?.timestamp || 
            items[0].answers?.items?.find(a => a.model === result.name)?.timestamp || 'N/A',
      score: result.isChunkEval ? '-' : (result.count > 0 ? (result.totalScore / result.count) * 100 : 0),
      facts: result.totalFacts,
      ok: result.totalOk,
      hallu: result.totalHallu,
      missing: result.totalMissing,
      extra: result.totalExtra,
      isChunkEval: result.isChunkEval
    }));
  },

  processDetailedResults(expe) {
    const items = expe.items || [expe];

    return items.flatMap(qa => {
      const answers = qa.answers?.items || [qa]; 
      const factsCount = qa.facts?.items?.length || 0; 
      return answers.map(answer => ({
        text: qa.question?.text || qa.question,
        model: answer.llm_answer?.name || answer.model,
        score: answer.eval?.auto || 0,
        ok: answer.eval?.meta?.nb_ok || 0,
        hallu: answer.eval?.meta?.nb_hallu || 0,
        missing: answer.eval?.meta?.nb_missing || 0,
        extra: answer.eval?.meta?.nb_extra || 0,
        factsCount: factsCount 
      }));
    });
  },

  processFullEvaluation(expe) {
    const items = expe.items || [expe];  // Handle both structures
    return items.map(qa => {
      const answers = qa.answers?.items || [qa];  // Handle both structures
      const mainAnswers = answers.filter(item => 
        (item.llm_answer?.name || item.model) !== "Missings Eval" && 
        (item.llm_answer?.name || item.model) !== "Hallucinations Eval" && 
        (item.llm_answer?.name || item.model) !== "Hallucination Eval"
      );
      const chunkEvaluations = answers.filter(item => 
        (item.llm_answer?.name || item.model) === "Missings Eval" || 
        (item.llm_answer?.name || item.model) === "Hallucinations Eval" || 
        (item.llm_answer?.name || item.model) === "Hallucination Eval"
      ); 


      return {
        question: qa.question?.text || qa.question,
        facts: qa.facts?.items || [],
        chunks: qa.chunks?.items || [],
        answers: mainAnswers.map(answer => ({
          text: typeof answer.text === 'object' ? JSON.stringify(answer.text) : answer.text,
          model: answer.llm_answer?.name || answer.model,
          cost: answer.llm_answer?.cost || answer.cost,
          duration: answer.llm_answer?.duration || answer.duration,
          time: answer.llm_answer?.timestamp || answer.timestamp,
          evaluation: answer.eval ? {
            text: answer.eval.text,
            model: answer.eval.llm_answer?.name || answer.eval.model || 'Unknown',
            cost: answer.eval.llm_answer?.cost || answer.eval.cost || 0,
            duration: answer.eval.llm_answer?.duration || answer.eval.duration || 0,
            time: answer.eval.llm_answer?.timestamp || answer.eval.timestamp || '',
            auto: answer.eval.auto || 0,
            ok: answer.eval.meta?.ok || [],
            missing: answer.eval.meta?.missing || [],
            hallu: answer.eval.meta?.hallu || [],
            extra: answer.eval.meta?.nb_extra || 0,
            human: answer.eval.human
          } : null
        })),
        chunkEvaluations: chunkEvaluations.map(item => ({
          type: item.llm_answer?.name || item.model,
          text: item.eval?.text || '',
          model: item.eval?.llm_answer?.name || item.eval?.model || 'Unknown',
          cost: item.eval?.llm_answer?.cost || item.eval?.cost || 0,
          duration: item.eval?.llm_answer?.duration || item.eval?.duration || 0,
          time: item.eval?.llm_answer?.timestamp || item.eval?.timestamp || '',
          evaluation: item.eval ? {
            text: item.eval.text,
            meta: item.eval.meta,
            model: item.llm_answer?.name || item.model,
            ok: item.eval.meta?.ok || [],
            missing: item.eval.meta?.missing || [],
            hallu: item.eval.meta?.hallu || [],
            extra: item.eval.meta?.nb_extra || 0,
            auto: item.eval.auto || 0,
            nb_ok: item.eval.meta?.nb_ok || 0,
            nb_missing: item.eval.meta?.nb_missing || 0,
            nb_hallu: item.eval.meta?.nb_hallu || 0
          } : null
        }))
      };
    });
  }
};