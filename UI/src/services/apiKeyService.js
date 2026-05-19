import { http } from '@/plugins/axios';

export const apiKeyService = {
  async checkApiKeyAvailability() {
    try {
      const response = await http.get('user/api-keys/availability');
      return response.data;
    } catch (error) {
      console.error('Error checking API key availability:', error);
      throw error;
    }
  },

  async refreshApiKeyAvailability() {
    try {
      const response = await http.post('user/api-keys/refresh');
      return response.data;
    } catch (error) {
      console.error('Error refreshing API key availability:', error);
      throw error;
    }
  }
};

export const openAIModels = ['gpt-5', 'gpt-5-mini', 'gpt-5-nano'];
export const mistralAIModels = ['mistral/mistral-small-latest', 'mistral/mistral-medium-latest', 'mistral/mistral-large-latest'];


export const availableLLMs = [
      { title: 'Select a model', value: '', disabled: true },
      { title: 'GPT-5', value: 'gpt-5', disabled: false},
      { title: 'GPT-5-mini', value: 'gpt-5-mini', disabled: false},
      { title: 'GPT-5-nano', value: 'gpt-5-nano', disabled: false},
      { title: 'Mistral Large', value: 'mistral/mistral-large-latest', disabled: false},
      { title: 'Mistral Medium', value: 'mistral/mistral-medium-latest', disabled: false},
      { title: 'Mistral Small', value: 'mistral/mistral-small-latest', disabled: false},
];

export const groupedLLMs = {
      'OpenAI': openAIModels,
      // 'Anthropic': [
      //   'claude-3-haiku-20240307', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-5-sonnet-20240620'
      // ],
      // 'Google': [
      //   'gemini/gemini-pro', 'gemini/gemini-1.5-pro'
      // ],
      'Mistral AI': mistralAIModels,
      // 'Cohere': [
      //   'command', 'command-light', 'command-nightly', 'command-r', 'command-r-plus'
      // ],
      // 'Together AI': [
      //   'together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1', 'together_ai/togethercomputer/CodeLlama-34b-Instruct'
      // ],
      // 'Ollama': [
      //   'ollama/llama2', 'ollama/mistral', 'ollama/codellama', 'ollama/vicuna'
      // ],
      // 'HuggingFace': [
      //   'huggingface/BigScience/bloom', 'huggingface/google/flan-t5-xxl'
      // ],
      // 'Deepseek': [
      //   'deepseek/deepseek-chat', 'deepseek/deepseek-coder'
      // ],
      // 'Openrouter': [
      //   'openrouter/deepseek/deepseek-r1', 'openrouter/deepseek/deepseek-chat', 'openrouter/deepseek/deepseek-coder'
      // ]
    };