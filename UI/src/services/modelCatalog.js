import { apiKeyService } from '@/services/apiKeyService';
import { modelService } from '@/services/generatorService';

// Sub-step 5.3: the model list lives server-side (/api/available-models
// returns built-ins + custom classes with provider / required_key). This
// module splits the unified catalog into the shapes the pages consume and
// derives availability-based disabling generically: a model is disabled
// when its required_key is not configured.

export async function fetchModelCatalog() {
  const models = await modelService.getAvailableModels();
  const builtins = models.filter(m => !m.custom);
  const customs = models.filter(m => m.custom);
  const grouped = {};
  builtins.forEach(m => {
    (grouped[m.provider] = grouped[m.provider] || []).push(m.name);
  });
  return { models, builtins, customs, grouped };
}

// Refresh key state server-side, then return {openai: bool, mistral: bool, ...}.
export async function refreshAvailability() {
  await apiKeyService.refreshApiKeyAvailability();
  return apiKeyService.checkApiKeyAvailability();
}

// v-select options for evaluation / answer / fact model dropdowns —
// same shape as the former apiKeyService.availableLLMs constant.
/**
 * Build the option list for a model <v-select>.
 *
 * @param {object}   opts
 * @param {boolean}  opts.hideUnavailable  drop models whose provider key is
 *                                         not configured (keeps the plain
 *                                         selects short).
 * @param {string[]} opts.excludeProviders  providers to leave out entirely,
 *                                          e.g. ['OVH'] on the validation-set
 *                                          screen where they are not wanted.
 * @param {boolean}  opts.excludeAnswerGenOnly  drop models flagged
 *                                          answer_gen_only (new GPT-5.x /
 *                                          Anthropic models are offered only in
 *                                          the experiment-setup answer-gen grid,
 *                                          not on validation-set fact/eval
 *                                          selects).
 */
export function buildModelOptions(
  builtins,
  availability,
  { hideUnavailable = false, excludeProviders = [], excludeAnswerGenOnly = false } = {}
) {
  const excluded = new Set(excludeProviders.map(p => String(p).toLowerCase()));
  const rows = builtins.filter(m =>
    (!hideUnavailable || !m.required_key || availability[m.required_key])
    && !excluded.has(String(m.provider || '').toLowerCase())
    && !(excludeAnswerGenOnly && m.answer_gen_only)
  );
  return [
    { title: 'Select a model', value: '', disabled: true },
    ...rows.map(m => ({
      title: m.title || m.name,
      value: m.name,
      required_key: m.required_key,
      pricing: m.pricing || null,
      disabled: m.required_key ? !availability[m.required_key] : false,
    })),
  ];
}

// Compact price tag for a model, e.g. "$3 / $15 per 1M" (input / output).
// Returns '' when no price is known, so callers can v-if it away.
export function formatModelPrice(pricing) {
  if (!pricing) return '';
  const fmt = (v) => {
    if (v === null || v === undefined) return '?';
    // Trim trailing zeros: 0.10 -> $0.1, 3.0 -> $3
    return `$${Number(v).toString()}`;
  };
  return `${fmt(pricing.input)} / ${fmt(pricing.output)} per 1M`;
}

export function isModelDisabled(builtins, availability, modelName) {
  const meta = builtins.find(m => m.name === modelName);
  return !!(meta && meta.required_key && !availability[meta.required_key]);
}
