from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any


def build_billsmart_csv(
    ticket_items: list[dict[str, Any]],
    *,
    output_dir: str | Path = "runtime/tmp",
    timestamp: str | None = None,
) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"ticket_sumup_{timestamp}.csv"

    with output_path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow([
            "reference",
            "designation",
            "quantite",
            "prix_unitaire",
        ])

        for index, item in enumerate(ticket_items, start=1):
            writer.writerow([
                f"SUMUP{index:03d}",
                "Paiement SumUp",
                item["quantity"],
                f"{float(item['price']):.2f}",
            ])

    return output_path
