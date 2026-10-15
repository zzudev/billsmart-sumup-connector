"""Explicit simulated payment confirmation for local BillSmart tests."""

from connector.billsmart_enriched_receipt import build_enriched_receipt
from connector.billsmart_payment_registry import (
    load_payment,
    update_payment_status,
)


def confirm_simulated_payment(
    *,
    payment_id,
    sales_path,
    payments_path,
):
    """Simulate success and build a detailed receipt; never call a provider."""
    payment = load_payment(payment_id, state_path=payments_path)

    if payment is None:
        raise ValueError(f"Payment not found: {payment_id}")

    if payment.get("provider") != "simulator":
        raise ValueError("Only simulator payments can be simulated")

    if payment.get("status") not in ("created", "pending", "succeeded"):
        raise ValueError("Payment cannot be simulated from this status")

    sale_id = payment.get("sale_id")

    if not isinstance(sale_id, str) or not sale_id.strip():
        raise ValueError("Invalid payment sale identifier")

    # Check the sale and amount before modifying payment state.
    # The receipt builder requires succeeded, so perform an independent
    # preflight validation using the existing transaction functions.
    from decimal import Decimal, InvalidOperation
    from connector.billsmart_sale_registry import load_sale
    from connector.billsmart_transaction import (
        build_payment_request,
        validate_transaction,
    )

    sale = load_sale(sale_id, state_path=sales_path)

    if sale is None:
        raise ValueError(f"Sale not found: {sale_id}")

    validate_transaction(sale)
    expected = build_payment_request(sale)

    try:
        amount = Decimal(str(payment["amount"]))
    except (KeyError, InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Invalid payment amount") from exc

    if (
        payment.get("currency") != expected["currency"]
        or not amount.is_finite()
        or amount != Decimal(expected["amount"])
    ):
        raise ValueError("Payment does not match the sale")

    if payment["status"] == "created":
        update_payment_status(
            payment_id,
            "pending",
            state_path=payments_path,
        )

    if payment["status"] in ("created", "pending"):
        update_payment_status(
            payment_id,
            "succeeded",
            state_path=payments_path,
        )

    return build_enriched_receipt(
        sale_id=sale_id,
        payment_id=payment_id,
        sales_path=sales_path,
        payments_path=payments_path,
    )
