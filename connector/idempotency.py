from __future__ import annotations

import json
from pathlib import Path
from typing import Any


DEFAULT_STATE_PATH = Path(
    "runtime/state/processed_transactions.json"
)


def load_registry(
    state_path: str | Path = DEFAULT_STATE_PATH,
) -> dict[str, Any]:
    path = Path(state_path)

    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        raise ValueError("Registre d'idempotence invalide.")

    return data


def is_transaction_processed(
    transaction_id: str,
    *,
    state_path: str | Path = DEFAULT_STATE_PATH,
) -> bool:
    registry = load_registry(state_path)
    return transaction_id in registry


def mark_transaction_processed(
    transaction_id: str,
    receipt_data: dict[str, Any],
    *,
    state_path: str | Path = DEFAULT_STATE_PATH,
) -> None:
    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    registry = load_registry(path)
    registry[transaction_id] = receipt_data

    temporary_path = path.with_suffix(".tmp")

    with temporary_path.open("w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, sort_keys=True)

    temporary_path.replace(path)
