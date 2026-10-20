"""FIXED: model registry, prices, cost accounting and spend ledger for the GitHub Copilot SDK study.

Every model is Copilot-hosted and runs through the Copilot SDK runtime on the account's Copilot credits. Prices are $ per
1M tokens, as returned by CopilotClient.list_models() on 2026-10-19. Ledger: studies/ledger.json; work is refused once
the total reaches the cap (RSI_COPILOT_CAP_USD).
"""
import fcntl
import json
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STUDIES = ROOT / "studies"
LEDGER = STUDIES / "ledger.json"

# id -> route, prices (in, out, cache_read) per 1M tokens
MODELS = {
    "claude-haiku-5.5": dict(route="copilot", price=(0.10, 0.50, 0.01), lab="Anthropic"),
    "gpt-6-luna": dict(route="copilot", price=(0.10, 0.50, 0.01), lab="OpenAI"),
    "gpt-5.6-luna": dict(route="copilot", price=(0.20, 1.20, 0.02), lab="OpenAI"),
    "mai-code-1.1-flash": dict(route="copilot", price=(0.20, 1.20, 0.02), lab="Microsoft"),
    "grok-4.7": dict(route="copilot", price=(2.0, 6.0, 0.5), lab="xAI"),
    "claude-sonnet-5.5": dict(route="copilot", price=(2.0, 10.0, 0.1), lab="Anthropic"),
    "gpt-6.1-sol": dict(route="copilot", price=(2.0, 10.0, 0.1), lab="OpenAI"),
    "gpt-6-sol": dict(route="copilot", price=(2.0, 10.0, 0.2), lab="OpenAI"),
    "gpt-5.3-codex": dict(route="copilot", price=(1.75, 14.0, 0.175), lab="OpenAI"),
    "claude-opus-5.5": dict(route="copilot", price=(4.0, 20.0, 0.2), lab="Anthropic"),
    "gpt-5.6-sol": dict(route="copilot", price=(4.0, 20.0, 0.4), lab="OpenAI"),
    "gpt-6-astra": dict(route="copilot", price=(10.0, 50.0, 1.0), lab="OpenAI"),
}
PROVIDER = {"copilot": "copilot"}


def load_env() -> None:
    for p in (ROOT / ".env",):  # COPILOT_GITHUB_TOKEN=... (never commit .env)
        if p.exists():
            for line in p.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()
CAPS = {"copilot": float(os.environ.get("RSI_COPILOT_CAP_USD", "1200"))}


def provider_of(model: str) -> str:
    return PROVIDER[MODELS[model]["route"]]


def cost_of(model: str, tin: int, tout: int, cached: int = 0) -> float:
    pi, po, pc = MODELS[model]["price"]
    cached = min(cached or 0, tin or 0)
    return ((tin - cached) * pi + cached * pc + tout * po) / 1e6


class SpendCapExceeded(RuntimeError):
    pass


def _read() -> dict:
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else {"total": {}, "by_tag": {}}


def ledger_add(cost: float, tag: str, provider: str) -> float:
    """Adds spend under a file lock (several processes may run). Returns the provider's new total."""
    STUDIES.mkdir(exist_ok=True)
    with open(STUDIES / ".ledger.lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        d = _read()
        d["total"][provider] = round(d["total"].get(provider, 0.0) + cost, 6)
        key = f"{provider}:{tag}"
        d["by_tag"][key] = round(d["by_tag"].get(key, 0.0) + cost, 6)
        d["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        LEDGER.write_text(json.dumps(d, indent=1))
        return d["total"][provider]


def ledger_total(provider: str) -> float:
    return _read()["total"].get(provider, 0.0)


def check_cap(provider: str) -> None:
    if ledger_total(provider) >= CAPS[provider]:
        raise SpendCapExceeded(f"{provider} spend ${ledger_total(provider):.2f} >= cap ${CAPS[provider]:.2f}")
