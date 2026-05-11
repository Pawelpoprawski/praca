"""AI token usage tracker — append-only JSONL log.

Each AI call (translation, extraction, CV extraction) appends one JSON line to
`ai_usage.jsonl` in backend/. The file persists across Python process restarts
and gives a full audit trail for cost calculation.

Usage in a service:
    from app.services.ai_usage import track_usage
    response = await client.chat.completions.create(...)
    if response.usage:
        track_usage(
            service="translation",
            model=response.model,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            job_id=str(job.id),
        )

To get a summary:
    python -m app.services.ai_usage  # prints summary
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Log lives in backend/ai_usage.jsonl
LOG_FILE = Path(__file__).resolve().parent.parent.parent / "ai_usage.jsonl"

# Pricing in USD per 1M tokens (as of 2026-05).
# Update here when models or prices change.
PRICING_PER_M = {
    "gpt-5.4-nano":     {"input": 0.200,  "output": 1.250},
    "gpt-5.4-mini":     {"input": 0.750,  "output": 4.500},
    "gpt-4o-mini":      {"input": 0.150,  "output": 0.600},
    "gpt-4o":           {"input": 2.500,  "output": 10.000},
    "gpt-4-turbo":      {"input": 10.000, "output": 30.000},
    "gpt-4":            {"input": 30.000, "output": 60.000},
    "gpt-3.5-turbo":    {"input": 0.500,  "output": 1.500},
    "claude-haiku-4-5": {"input": 1.000,  "output": 5.000},
    "claude-sonnet-4-6": {"input": 3.000, "output": 15.000},
    "claude-opus-4-7":  {"input": 15.000, "output": 75.000},
}


def _resolve_model_pricing(model_id: str) -> dict | None:
    """Match any model variant to its base pricing key.

    Examples:
        gpt-4o-mini-2024-07-18 -> gpt-4o-mini
        gpt-4o-2024-08-06       -> gpt-4o
    """
    if model_id in PRICING_PER_M:
        return PRICING_PER_M[model_id]
    # Try prefix match (longest first)
    for key in sorted(PRICING_PER_M.keys(), key=len, reverse=True):
        if model_id.startswith(key):
            return PRICING_PER_M[key]
    return None


def calc_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate cost in USD for a single call. Returns 0 if pricing unknown."""
    p = _resolve_model_pricing(model)
    if not p:
        return 0.0
    return (prompt_tokens * p["input"] + completion_tokens * p["output"]) / 1_000_000


def track_usage(
    service: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    job_id: str | None = None,
    extra: dict | None = None,
) -> None:
    """Append one usage record to the JSONL log."""
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "service": service,
        "model": model,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "cost_usd": round(calc_cost(model, prompt_tokens, completion_tokens), 6),
        "job_id": job_id,
    }
    if extra:
        record.update(extra)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Failed to write ai_usage.jsonl: {e}")


def read_records(limit: int | None = None) -> list[dict]:
    """Read all records from the JSONL log. limit=None reads everything."""
    if not LOG_FILE.exists():
        return []
    records = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if limit and i >= limit:
                break
    return records


def summarize(records: list[dict] | None = None) -> dict:
    """Aggregate usage by service + model. Returns totals + cost."""
    if records is None:
        records = read_records()
    by_service: dict = {}
    by_model: dict = {}
    total_calls = 0
    total_in = 0
    total_out = 0
    total_cost = 0.0

    for r in records:
        svc = r.get("service", "?")
        mdl = r.get("model", "?")
        ptok = r.get("prompt_tokens", 0)
        ctok = r.get("completion_tokens", 0)
        cost = r.get("cost_usd", 0.0)

        for bucket, key in [(by_service, svc), (by_model, mdl)]:
            b = bucket.setdefault(key, {"calls": 0, "input": 0, "output": 0, "cost": 0.0})
            b["calls"] += 1
            b["input"] += ptok
            b["output"] += ctok
            b["cost"] += cost

        total_calls += 1
        total_in += ptok
        total_out += ctok
        total_cost += cost

    return {
        "total_calls": total_calls,
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "total_tokens": total_in + total_out,
        "total_cost_usd": round(total_cost, 6),
        "by_service": by_service,
        "by_model": by_model,
    }


def print_summary() -> None:
    """Pretty-print summary to stdout."""
    s = summarize()
    print(f"=== AI USAGE SUMMARY ({LOG_FILE}) ===")
    print(f"Total calls:         {s['total_calls']}")
    print(f"Total input tokens:  {s['total_input_tokens']:,}")
    print(f"Total output tokens: {s['total_output_tokens']:,}")
    print(f"Total tokens:        {s['total_tokens']:,}")
    print(f"Total cost USD:      ${s['total_cost_usd']:.4f}")
    print()
    print("BY SERVICE:")
    for svc, b in s["by_service"].items():
        print(f"  {svc:20s} calls={b['calls']:4d}  in={b['input']:>8,}  out={b['output']:>8,}  cost=${b['cost']:.4f}")
    print()
    print("BY MODEL:")
    for mdl, b in s["by_model"].items():
        print(f"  {mdl:25s} calls={b['calls']:4d}  in={b['input']:>8,}  out={b['output']:>8,}  cost=${b['cost']:.4f}")


if __name__ == "__main__":
    print_summary()
