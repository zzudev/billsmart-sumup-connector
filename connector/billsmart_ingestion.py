from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


DEFAULT_BSM1_ROOT = Path("/home/billsmart1/boulxblb_receipts")


def ingest_csv_with_bsm1(
    csv_path: str | Path,
    *,
    bsm1_root: str | Path = DEFAULT_BSM1_ROOT,
) -> dict[str, Any]:
    csv_path = Path(csv_path)
    bsm1_root = Path(bsm1_root)

    command = [
        str(bsm1_root / "venv/bin/python"),
        "-m",
        "backend.app.receipt_ingestion_cli",
        str(csv_path.resolve()),
    ]

    completed = subprocess.run(
        command,
        cwd=bsm1_root,
        capture_output=True,
        text=True,
        check=False,
    )

    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Réponse JSON invalide de BSM1."
        ) from exc

    if not isinstance(result, dict):
        raise RuntimeError("Réponse BSM1 invalide.")

    return result
