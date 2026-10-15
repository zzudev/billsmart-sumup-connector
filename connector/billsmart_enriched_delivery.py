"""Prepare enriched BillSmart receipts for the existing BSM1 delivery flow."""

from pathlib import Path

from connector.billsmart_enriched_csv import build_enriched_csv
from connector.billsmart_enriched_receipt import build_enriched_receipt


def prepare_enriched_delivery(
    *,
    sale_id,
    payment_id,
    sales_path,
    payments_path,
    output_dir="runtime/tmp",
):
    """Prepare a confirmed receipt without ingesting or displaying it."""
    receipt = build_enriched_receipt(
        sale_id=sale_id,
        payment_id=payment_id,
        sales_path=sales_path,
        payments_path=payments_path,
    )

    if receipt["payment"]["provider"] != "simulator":
        raise ValueError(
            "This POC delivery preparation supports simulator payments only"
        )

    if (
        not isinstance(payment_id, str)
        or not payment_id.strip()
        or any(char not in "abcdefghijklmnopqrstuvwxyz"
               "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for char in payment_id)
    ):
        raise ValueError("Invalid payment identifier for CSV filename")

    output_path = Path(output_dir) / f"billsmart_{payment_id}.csv"

    csv_path = build_enriched_csv(
        receipt,
        output_path=output_path,
    )

    return {
        "sale_id": sale_id,
        "payment_id": payment_id,
        "transaction_id": f"BLB-SIM:{payment_id}",
        "csv_path": csv_path,
    }


def simulate_enriched_delivery(
    *,
    sale_id,
    payment_id,
    sales_path,
    payments_path,
    delivery_func,
    output_dir="runtime/tmp",
    state_path="runtime/state/simulator_deliveries.json",
):
    """Exercise delivery orchestration with an injected fake delivery function."""
    if not callable(delivery_func):
        raise ValueError("A callable fake delivery function is required")

    prepared = prepare_enriched_delivery(
        sale_id=sale_id,
        payment_id=payment_id,
        sales_path=sales_path,
        payments_path=payments_path,
        output_dir=output_dir,
    )

    result = delivery_func(
        prepared["transaction_id"],
        prepared["csv_path"],
        state_path=state_path,
    )

    return {
        **prepared,
        "delivery_result": result,
    }
