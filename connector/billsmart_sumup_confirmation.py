"""Confirm a registered BillSmart payment using a SumUp Reader checkout."""

from connector.billsmart_payment_registry import (
    load_payment,
    update_payment_status,
)
from connector.billsmart_payment_verification import (
    verify_payment_confirmation,
)
from connector.sumup_payment_adapter import normalize_reader_checkout
from connector import sumup_reader_client


def confirm_sumup_payment(
    *,
    payment_id,
    api_key,
    merchant_code,
    reader_id,
    payments_path,
):
    """Retrieve, verify and apply a SumUp payment confirmation."""
    payment = load_payment(payment_id, state_path=payments_path)

    if payment is None:
        raise ValueError(f"BillSmart payment not found: {payment_id}")

    if payment.get("provider") != "sumup":
        raise ValueError("Payment provider is not SumUp")

    checkout_id = payment.get("provider_checkout_id")

    if not isinstance(checkout_id, str) or not checkout_id.strip():
        raise ValueError("Missing registered SumUp checkout reference")

    response = sumup_reader_client.get_reader_checkout(
        api_key,
        merchant_code,
        reader_id,
        checkout_id,
    )

    confirmation = normalize_reader_checkout(response)

    verified = verify_payment_confirmation(
        payment,
        confirmation,
    )

    return update_payment_status(
        verified["payment_id"],
        verified["status"],
        state_path=payments_path,
    )
