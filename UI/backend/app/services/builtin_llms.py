"""First-class built-in LLM models shipped WITH the product.

Distinct from the user's classes.py (volume-mounted extension point for
arbitrary/open-source models a user wants to evaluate): this module is
committed, always present, and its models get proper provider + key gating in
the catalog — the same treatment as the OpenAI/Mistral/Anthropic entries in
BUILTIN_MODELS.

Currently holds the OVH AI Endpoints models. OVH is OpenAI-compatible and
reached through LiteLLM with `api_base` pointing at OVH's endpoint and the
`OVH_API_KEY` credential. OVH serves everything through vLLM with per-model
reasoning parsers, so gpt-oss (Harmony analysis channel) and Qwen3 return
their thinking in `reasoning_content` — not in `content` — which is exactly
what ReasoningLLM expects (no <think> stripping needed).

Discovery: class_detector collects LLM subclasses whose module starts with
'app.services', so importing this module (done in api/models_info.py and
api/experiments.py) registers these automatically. Each class carries
`provider` and `required_key` class attributes that the catalog reads to gate
availability on the OVH key and label the provider correctly.
"""
import os

from pydantic import Field
from typing import ClassVar

from ragtime.llms import LiteLLM, ReasoningLLM
from ragtime.prompters import Prompter

# OpenAI-compatible base URL for OVH AI Endpoints.
OVH_API_URL = "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1"

# Register OVH per-token prices with LiteLLM so cost is computed rather than
# falling back to 0 (LiteLLM has no price entry for openai/<ovh-model>).
try:
    from app.services.ovh_pricing import register_ovh_prices
    register_ovh_prices()
except Exception:  # pricing must never block model registration
    pass


def _ovh_params():
    """Common completion kwargs so LiteLLM routes to OVH's endpoint with the
    OVH credential. Uses the openai/ provider prefix + api_base."""
    return {
        "api_base": OVH_API_URL,
        "api_key": os.getenv("OVH_API_KEY"),
    }


# --- OVH mixin: shared provider identity + OVH routing ----------------------
# `provider` / `required_key` are read by the catalog (models_info.py) to label
# the model and disable it when OVH_API_KEY is absent. `supports_reasoning_toggle`
# and `reasoning_note` drive the UI's per-model reasoning control.

class _OVHBase:
    provider: ClassVar[str] = "OVH"
    required_key: ClassVar[str] = "ovh"
    built_in_retriever: ClassVar[bool] = False


# ---------------------------------------------------------------------------
# Classic (non-reasoning) OVH models — plain LiteLLM
# ---------------------------------------------------------------------------

class OVH_Mistral7B(_OVHBase, LiteLLM):
    """OVH · Mistral-7B-Instruct-v0.3 (7B, 127K ctx)."""
    title: ClassVar[str] = "OVH · Mistral 7B Instruct"
    supports_reasoning_toggle: ClassVar[bool] = False
    name: str = "openai/Mistral-7B-Instruct-v0.3"
    prompter: Prompter = Field(..., description="Prompter instance")
    extra_params: dict = Field(default_factory=_ovh_params)


class OVH_MistralNemo(_OVHBase, LiteLLM):
    """OVH · Mistral-Nemo-Instruct-2407 (12B, 118K ctx)."""
    title: ClassVar[str] = "OVH · Mistral Nemo Instruct"
    supports_reasoning_toggle: ClassVar[bool] = False
    name: str = "openai/Mistral-Nemo-Instruct-2407"
    prompter: Prompter = Field(..., description="Prompter instance")
    extra_params: dict = Field(default_factory=_ovh_params)


class OVH_Llama33_70B(_OVHBase, LiteLLM):
    """OVH · Meta-Llama-3.3-70B-Instruct (70B, 131K ctx)."""
    title: ClassVar[str] = "OVH · Llama 3.3 70B Instruct"
    supports_reasoning_toggle: ClassVar[bool] = False
    name: str = "openai/Meta-Llama-3_3-70B-Instruct"
    prompter: Prompter = Field(..., description="Prompter instance")
    extra_params: dict = Field(default_factory=_ovh_params)


# ---------------------------------------------------------------------------
# Reasoning OVH models — ReasoningLLM (thinking arrives in reasoning_content)
# ---------------------------------------------------------------------------

class OVH_Qwen3_32B(_OVHBase, ReasoningLLM):
    """OVH · Qwen3-32B (32B, 32K ctx). Hybrid reasoning model, but OVH's
    endpoint does not yet accept the enable_thinking toggle
    (chat_template_kwargs is rejected with a 400), so reasoning is left on and
    NOT user-toggmeable until OVH supports it. Served through vLLM's qwen3
    parser, so the final answer stays in content."""
    title: ClassVar[str] = "OVH · Qwen3 32B"
    supports_reasoning_toggle: ClassVar[bool] = False
    reasoning_note: ClassVar[str] = "Reasoning always on (OVH toggle not yet supported)"
    name: str = "openai/Qwen3-32B"
    prompter: Prompter = Field(..., description="Prompter instance")
    extra_params: dict = Field(default_factory=_ovh_params)


class OVH_GptOss20B(_OVHBase, ReasoningLLM):
    """OVH · gpt-oss-20b (21B, 131K ctx). Harmony format; reasoning effort
    configurable but always on — analysis channel goes to reasoning_content."""
    title: ClassVar[str] = "OVH · GPT-OSS 20B"
    supports_reasoning_toggle: ClassVar[bool] = False
    reasoning_note: ClassVar[str] = "Reasoning always on (effort configurable)"
    name: str = "openai/gpt-oss-20b"
    prompter: Prompter = Field(..., description="Prompter instance")
    extra_params: dict = Field(default_factory=_ovh_params)


class OVH_GptOss120B(_OVHBase, ReasoningLLM):
    """OVH · gpt-oss-120b (117B, 131K ctx). Harmony format; reasoning effort
    configurable but always on — analysis channel goes to reasoning_content."""
    title: ClassVar[str] = "OVH · GPT-OSS 120B"
    supports_reasoning_toggle: ClassVar[bool] = False
    reasoning_note: ClassVar[str] = "Reasoning always on (effort configurable)"
    name: str = "openai/gpt-oss-120b"
    prompter: Prompter = Field(..., description="Prompter instance")
    extra_params: dict = Field(default_factory=_ovh_params)
