"""Provider-neutral verification of normalized payment confirmations."""

from decimal import Decimal, InvalidOperation


def verify_payment_confirmation(payment, confirmation):
    """Compare a registered payment with a normalized confirmation."""
    if not isinstance(payment, dict) or not isinstance(confirmation, dict):
        raise ValueError("Invalid payment verification data")

    for field in ("payment_id", "sale_id", "provider"):
        value = payment.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Invalid payment field: {field}")

    for field in (
        "provider_checkout_id",
        "provider_client_transaction_id",
    ):
        expected = payment.get(field)
        actual = confirmation.get(field)

        if not isinstance(expected, str) or not expected.strip():
            raise ValueError(f"Missing registered reference: {field}")

        if not isinstance(actual, str) or not actual.strip():
            raise ValueError(f"Missing confirmation reference: {field}")

        if expected != actual:
            raise ValueError(f"Payment reference mismatch: {field}")

    if (
        not isinstance(payment.get("currency"), str)
        or not payment["currency"].strip()
        or confirmation.get("currency") != payment["currency"]
    ):
        raise ValueError("Payment currency mismatch")

    try:
        expected_amount = Decimal(str(payment["amount"]))
        actual_amount = Decimal(str(confirmation["amount"]))
    except (KeyError, InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Invalid payment amount") from exc

    if (
        not expected_amount.is_finite()
        or not actual_amount.is_finite()
        or expected_amount <= 0
        or actual_amount <= 0
        or expected_amount != expected_amount.quantize(Decimal("0.01"))
        or actual_amount != actual_amount.quantize(Decimal("0.01"))
        or expected_amount != actual_amount
    ):
        raise ValueError("Payment amount mismatch")

    status = confirmation.get("status")
    if status not in ("pending", "succeeded", "failed", "cancelled"):
        raise ValueError("Invalid confirmation status")

    return {
        "payment_id": payment["payment_id"],
        "sale_id": payment["sale_id"],
        "status": status,
    }
