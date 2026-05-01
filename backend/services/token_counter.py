"""
In-memory token usage tracker. Resets on server restart.
Tracks per-provider, per-model usage and estimates cost in USD.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock

# USD per 1M tokens (input / output)
_MODEL_PRICES: dict[str, tuple[float, float]] = {
    "claude-sonnet-4-20250514":  (3.00, 15.00),
    "claude-opus-4-20250514":    (15.00, 75.00),
    "claude-haiku-4-5-20251001": (0.80, 4.00),
    "gpt-4o-mini":               (0.15, 0.60),
    "gpt-4o":                    (2.50, 10.00),
    "grok-3-mini":               (0.30, 0.50),
    "grok-3":                    (3.00, 15.00),
}

_PROVIDER_OF: dict[str, str] = {
    "claude-sonnet-4-20250514":  "anthropic",
    "claude-opus-4-20250514":    "anthropic",
    "claude-haiku-4-5-20251001": "anthropic",
    "gpt-4o-mini":               "openai",
    "gpt-4o":                    "openai",
    "grok-3-mini":               "xai",
    "grok-3":                    "xai",
}


@dataclass
class ModelStats:
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    requests: int = 0
    cost_usd: float = 0.0


@dataclass
class ProviderStats:
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    requests: int = 0
    errors: int = 0
    cost_usd: float = 0.0
    models: dict[str, ModelStats] = field(default_factory=dict)


class TokenCounter:
    def __init__(self) -> None:
        self._lock = Lock()
        self._stats: dict[str, ProviderStats] = {}
        self._started_at = datetime.now(timezone.utc)

    def record(self, model: str, input_tokens: int, output_tokens: int) -> None:
        provider = _PROVIDER_OF.get(model, "unknown")
        price_in, price_out = _MODEL_PRICES.get(model, (0.0, 0.0))
        cost = (input_tokens * price_in + output_tokens * price_out) / 1_000_000

        with self._lock:
            if provider not in self._stats:
                self._stats[provider] = ProviderStats(provider=provider)
            ps = self._stats[provider]
            ps.input_tokens += input_tokens
            ps.output_tokens += output_tokens
            ps.requests += 1
            ps.cost_usd += cost

            if model not in ps.models:
                ps.models[model] = ModelStats(model=model)
            ms = ps.models[model]
            ms.input_tokens += input_tokens
            ms.output_tokens += output_tokens
            ms.requests += 1
            ms.cost_usd += cost

    def record_error(self, provider: str) -> None:
        with self._lock:
            if provider not in self._stats:
                self._stats[provider] = ProviderStats(provider=provider)
            self._stats[provider].errors += 1

    def snapshot(self) -> dict:
        with self._lock:
            providers = {}
            total_cost = 0.0
            for p, ps in self._stats.items():
                total_cost += ps.cost_usd
                providers[p] = {
                    "input_tokens": ps.input_tokens,
                    "output_tokens": ps.output_tokens,
                    "total_tokens": ps.input_tokens + ps.output_tokens,
                    "requests": ps.requests,
                    "errors": ps.errors,
                    "cost_usd": round(ps.cost_usd, 6),
                    "models": {
                        m: {
                            "input_tokens": ms.input_tokens,
                            "output_tokens": ms.output_tokens,
                            "requests": ms.requests,
                            "cost_usd": round(ms.cost_usd, 6),
                        }
                        for m, ms in ps.models.items()
                    },
                }
            return {
                "providers": providers,
                "total_cost_usd": round(total_cost, 6),
                "session_started": self._started_at.isoformat(),
            }

    def reset(self) -> None:
        with self._lock:
            self._stats.clear()
            self._started_at = datetime.now(timezone.utc)


# Module-level singleton
counter = TokenCounter()
