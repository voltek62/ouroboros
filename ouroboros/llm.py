"""
Ouroboros — LLM client.

The only module that communicates with the LLM API (Edgee).
Contract: chat(), default_model(), available_models(), add_usage().
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

DEFAULT_LIGHT_MODEL = "google/gemini-3-pro-preview"


def normalize_reasoning_effort(value: str, default: str = "medium") -> str:
    allowed = {"none", "minimal", "low", "medium", "high", "xhigh"}
    v = str(value or "").strip().lower()
    return v if v in allowed else default


def reasoning_rank(value: str) -> int:
    order = {"none": 0, "minimal": 1, "low": 2, "medium": 3, "high": 4, "xhigh": 5}
    return int(order.get(str(value or "").strip().lower(), 3))


def add_usage(total: Dict[str, Any], usage: Dict[str, Any]) -> None:
    """Accumulate usage from one LLM call into a running total."""
    for k in ("prompt_tokens", "completion_tokens", "total_tokens", "cached_tokens", "cache_write_tokens"):
        total[k] = int(total.get(k) or 0) + int(usage.get(k) or 0)
    if usage.get("cost"):
        total["cost"] = float(total.get("cost") or 0) + float(usage["cost"])


def fetch_provider_pricing() -> Dict[str, Tuple[float, float, float]]:
    """
    Fetch current pricing from Edgee Models API.

    Returns dict of {model_id: (input_per_1m, cached_per_1m, output_per_1m)}.
    Returns empty dict on failure.
    """
    try:
        import requests
    except ImportError:
        log.warning("requests not installed, cannot fetch pricing")
        return {}

    try:
        api_key = os.environ.get("EDGEE_API_KEY", "").strip() or os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            return {}
        url = "https://api.edgee.ai/v1/models"
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=15,
        )
        resp.raise_for_status()

        models = resp.json().get("data", [])

        pricing_dict = {}
        for model in models:
            model_id = model.get("id", "")
            if not model_id:
                continue

            pricing = model.get("pricing") or {}
            if not pricing:
                continue

            raw_prompt = pricing.get("prompt") or pricing.get("input") or pricing.get("input_price")
            raw_completion = pricing.get("completion") or pricing.get("output") or pricing.get("output_price")
            if raw_prompt is None or raw_completion is None:
                continue

            prompt_price = round(float(raw_prompt) * 1_000_000, 4)
            completion_price = round(float(raw_completion) * 1_000_000, 4)
            raw_cached = pricing.get("input_cache_read")
            if raw_cached is not None:
                cached_price = round(float(raw_cached) * 1_000_000, 4)
            else:
                cached_price = round(prompt_price * 0.1, 4)

            pricing_dict[model_id] = (prompt_price, cached_price, completion_price)
            # Also index "bare" ids (without provider prefix) so e.g. "gpt-5.4"
            # resolves the same as "openai/gpt-5.4". First entry wins.
            if "/" in model_id:
                bare = model_id.split("/", 1)[1]
                pricing_dict.setdefault(bare, (prompt_price, cached_price, completion_price))

        log.info("Fetched pricing for %d models from Edgee", len(pricing_dict))
        return pricing_dict

    except (requests.RequestException, ValueError, KeyError, TypeError) as e:
        log.warning("Failed to fetch Edgee pricing: %s", e)
        return {}


class LLMClient:
    """Edgee API wrapper. All LLM calls go through this class."""

    def __init__(
        self,
        api_key: Optional[str] = None,
    ):
        self._api_key = (
            api_key
            or os.environ.get("EDGEE_API_KEY", "")
            or os.environ.get("OPENROUTER_API_KEY", "")
        )
        self._client = None

    def _get_client(self):
        if self._client is None:
            from edgee import Edgee

            self._client = Edgee(self._api_key)
        return self._client

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        tools: Optional[List[Dict[str, Any]]] = None,
        reasoning_effort: str = "medium",
        max_tokens: int = 16384,
        tool_choice: str = "auto",
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Single LLM call. Returns: (response_message_dict, usage_dict with cost)."""
        client = self._get_client()

        request_input: Dict[str, Any] = {
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if tools:
            request_input["tools"] = tools
            request_input["tool_choice"] = tool_choice

        resp = client.send(model=model, input=request_input)
        msg = resp.message or {"role": "assistant", "content": resp.text or ""}
        usage: Dict[str, Any] = {}
        if resp.usage is not None:
            usage = {
                "prompt_tokens": int(getattr(resp.usage, "prompt_tokens", 0) or 0),
                "completion_tokens": int(getattr(resp.usage, "completion_tokens", 0) or 0),
                "total_tokens": int(getattr(resp.usage, "total_tokens", 0) or 0),
            }
        # Edgee SDK does not expose per-request cost directly in send() response.
        # Cost is estimated upstream when usage["cost"] is missing.

        # Extract cached_tokens from prompt_tokens_details if available
        if not usage.get("cached_tokens"):
            prompt_details = usage.get("prompt_tokens_details") or {}
            if isinstance(prompt_details, dict) and prompt_details.get("cached_tokens"):
                usage["cached_tokens"] = int(prompt_details["cached_tokens"])

        # Extract cache_write_tokens from prompt_tokens_details if available
        # Provider-specific cache-write fields
        # Native Anthropic: "cache_creation_tokens" or "cache_creation_input_tokens"
        if not usage.get("cache_write_tokens"):
            prompt_details_for_write = usage.get("prompt_tokens_details") or {}
            if isinstance(prompt_details_for_write, dict):
                cache_write = (prompt_details_for_write.get("cache_write_tokens")
                              or prompt_details_for_write.get("cache_creation_tokens")
                              or prompt_details_for_write.get("cache_creation_input_tokens"))
                if cache_write:
                    usage["cache_write_tokens"] = int(cache_write)

        return msg, usage

    def vision_query(
        self,
        prompt: str,
        images: List[Dict[str, Any]],
        model: str = "anthropic/claude-sonnet-4.6",
        max_tokens: int = 1024,
        reasoning_effort: str = "low",
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Send a vision query to an LLM. Lightweight — no tools, no loop.

        Args:
            prompt: Text instruction for the model
            images: List of image dicts. Each dict must have either:
                - {"url": "https://..."} — for URL images
                - {"base64": "<b64>", "mime": "image/png"} — for base64 images
            model: VLM-capable model ID
            max_tokens: Max response tokens
            reasoning_effort: Effort level

        Returns:
            (text_response, usage_dict)
        """
        # Build multipart content
        content: List[Dict[str, Any]] = [{"type": "text", "text": prompt}]
        for img in images:
            if "url" in img:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": img["url"]},
                })
            elif "base64" in img:
                mime = img.get("mime", "image/png")
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{img['base64']}"},
                })
            else:
                log.warning("vision_query: skipping image with unknown format: %s", list(img.keys()))

        messages = [{"role": "user", "content": content}]
        response_msg, usage = self.chat(
            messages=messages,
            model=model,
            tools=None,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
        )
        text = response_msg.get("content") or ""
        return text, usage

    def default_model(self) -> str:
        """Return the single default model from env. LLM switches via tool if needed."""
        return os.environ.get("OUROBOROS_MODEL", "gpt-5.2")

    def available_models(self) -> List[str]:
        """Return list of available models from env (for switch_model tool schema)."""
        main = os.environ.get("OUROBOROS_MODEL", "gpt-5.2")
        code = os.environ.get("OUROBOROS_MODEL_CODE", "")
        light = os.environ.get("OUROBOROS_MODEL_LIGHT", "")
        models = [main]
        if code and code != main:
            models.append(code)
        if light and light != main and light != code:
            models.append(light)
        return models


# Backward compatibility for existing imports.
def fetch_edgee_pricing() -> Dict[str, Tuple[float, float, float]]:
    return fetch_provider_pricing()


# Backward compatibility for existing imports.
def fetch_openrouter_pricing() -> Dict[str, Tuple[float, float, float]]:
    return fetch_provider_pricing()
