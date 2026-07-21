import json
from datetime import datetime, timezone
from pathlib import Path

from .parsers.base import ParseResult


def load_history(path: str | Path) -> dict:
    """Load price history from JSON file."""
    p = Path(path)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_history(path: str | Path, history: dict) -> None:
    """Save price history to JSON file."""
    Path(path).write_text(
        json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def update_history(
    history: dict,
    product_id: str,
    product_name: str,
    results: dict[str, ParseResult],
) -> None:
    """Append a new price snapshot to the history for a product."""
    if product_id not in history:
        history[product_id] = {"name": product_name, "history": []}

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prices": {},
    }

    for store, result in results.items():
        entry["prices"][store] = {
            "price": result.price,
            "available": result.available,
        }

    # Only append if we have at least some store results
    if entry["prices"]:
        history[product_id]["history"].append(entry)

        # Cap at 2000 entries to prevent file bloat
        if len(history[product_id]["history"]) > 2000:
            history[product_id]["history"] = history[product_id]["history"][-2000:]
