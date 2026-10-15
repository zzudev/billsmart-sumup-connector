"""Convert a confirmed BillSmart enriched receipt to BSM1 CSV."""

import csv
from decimal import Decimal, InvalidOperation
from pathlib import Path

from connector.billsmart_transaction import validate_transaction


CSV_COLUMNS = (
    "reference",
    "designation",
    "quantite",
    "prix_unitaire",
)


def _decimal(value, field):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid {field}") from exc

    if not result.is_finite():
        raise ValueError(f"Non-finite {field}")

    return result


def build_enriched_csv(receipt, *, output_path):
    """Write a BSM1-compatible CSV without triggering ingestion."""
    validate_transaction(receipt)

    payment = receipt["payment"]

    if payment.get("status") != "succeeded":
        raise ValueError("Payment must be succeeded")

    if receipt["currency"] != "EUR":
        raise ValueError("Only EUR is supported by this CSV adapter")

    if payment.get("currency") != receipt["currency"]:
        raise ValueError("Payment currency mismatch")

    declared_total = _decimal(receipt["totals"]["gross"], "total")
    payment_total = _decimal(payment.get("amount"), "payment amount")

    if declared_total != payment_total:
        raise ValueError("Payment total mismatch")

    rows = []
    calculated_total = Decimal("0.00")

    for index, item in enumerate(receipt["items"], start=1):
        designation = item.get("name")

        if not isinstance(designation, str) or not designation.strip():
            raise ValueError(f"Missing item name at position {index}")

        quantity = _decimal(item.get("quantity"), "quantity")
        unit_price = _decimal(item.get("unit_price"), "unit price")

        if quantity <= 0 or quantity != quantity.to_integral_value():
            raise ValueError("Quantity must be a positive integer")

        if unit_price < 0 or unit_price != unit_price.quantize(
            Decimal("0.01")
        ):
            raise ValueError("Unit price must have at most two decimals")

        calculated_total += quantity * unit_price

        rows.append({
            "reference": f"BLB{index:03d}",
            "designation": designation.strip(),
            "quantite": str(int(quantity)),
            "prix_unitaire": f"{unit_price:.2f}",
        })

    if calculated_total != declared_total:
        raise ValueError("CSV line total mismatch")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    return output_path
