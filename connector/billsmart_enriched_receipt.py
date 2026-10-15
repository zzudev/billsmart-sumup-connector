"""Build provider-neutral BillSmart receipts from saved sales and payments."""

from copy import deepcopy
from decimal import Decimal

from connector.billsmart_sale_registry import load_sale
from connector.billsmart_payment_registry import load_payment
from connector.billsmart_transaction import (
    build_payment_request,
    validate_transaction,
)


def build_enriched_receipt(
    *,
    sale_id,
    payment_id,
    sales_path,
    payments_path,
):
    """Build a receipt for a matching, successfully recorded payment."""
    sale = load_sale(sale_id, state_path=sales_path)

    if sale is None:
        raise ValueError(f"BillSmart sale not found: {sale_id}")

    payment = load_payment(payment_id, state_path=payments_path)

    if payment is None:
        raise ValueError(f"BillSmart payment not found: {payment_id}")

    validate_transaction(sale)

    if sale["sale_id"] != sale_id:
        raise ValueError("Sale identifier mismatch")

    if payment.get("payment_id") != payment_id:
        raise ValueError("Payment identifier mismatch")

    if payment.get("sale_id") != sale_id:
        raise ValueError("Payment does not belong to this sale")

    if payment.get("status") != "succeeded":
        raise ValueError("Payment is not successful")

    expected = build_payment_request(sale)

    if payment.get("currency") != expected["currency"]:
        raise ValueError("Payment currency mismatch")

    try:
        payment_amount = Decimal(str(payment["amount"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid payment amount") from exc

    if (
        not payment_amount.is_finite()
        or payment_amount != Decimal(expected["amount"])
    ):
        raise ValueError("Payment amount mismatch")

    receipt = deepcopy(sale)

    receipt["payment"] = {
        "payment_id": payment["payment_id"],
        "amount": expected["amount"],
        "currency": expected["currency"],
        "provider": payment["provider"],
        "status": payment["status"],
    }

    return receipt
