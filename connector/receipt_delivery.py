from __future__ import annotations

from pathlib import Path
from typing import Any

from connector.billsmart_ingestion import ingest_csv_with_bsm1
from connector.idempotency import (
    is_transaction_processed,
    mark_transaction_processed,
)


def deliver_receipt(
    transaction_id: str,
    csv_path: str | Path,
    *,
    state_path: str | Path,
) -> dict[str, Any]:
    if is_transaction_processed(
        transaction_id,
        state_path=state_path,
    ):
        return {
            "ok": True,
            "already_processed": True,
        }

    result = ingest_csv_with_bsm1(csv_path)

    receipt = result.get("receipt")
    if receipt:
        mark_transaction_processed(
            transaction_id,
            receipt,
            state_path=state_path,
        )

    return {
        **result,
        "already_processed": False,
    }
