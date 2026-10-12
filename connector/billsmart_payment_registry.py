"""Provider-neutral persistence of BillSmart payment attempts."""

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


DEFAULT_PAYMENTS_PATH = Path("runtime/state/billsmart_payments.json")


def load_payment(payment_id, *, state_path=DEFAULT_PAYMENTS_PATH):
    """Retrieve a payment attempt by its BillSmart identifier."""
    path = Path(state_path)

    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as f:
        payments = json.load(f)

    if not isinstance(payments, dict):
        raise ValueError("Invalid BillSmart payment registry")

    return payments.get(payment_id)


def save_payment(payment, *, state_path=DEFAULT_PAYMENTS_PATH):
    """Validate and persist a new payment attempt."""
    if not isinstance(payment, dict):
        raise ValueError("Payment must be a dictionary")

    for field in ("payment_id", "sale_id", "currency", "provider"):
        value = payment.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Invalid payment field: {field}")

    try:
        amount = Decimal(str(payment["amount"]))
    except (KeyError, InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("Invalid payment amount") from exc

    if (
        not amount.is_finite()
        or amount <= 0
        or amount != amount.quantize(Decimal("0.01"))
    ):
        raise ValueError("Invalid payment amount")

    if payment.get("status") != "created":
        raise ValueError("Initial payment status must be created")

    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            payments = json.load(f)
        if not isinstance(payments, dict):
            raise ValueError("Invalid BillSmart payment registry")
    else:
        payments = {}

    payment_id = payment["payment_id"]

    if payment_id in payments:
        raise ValueError(f"Payment already registered: {payment_id}")

    payments[payment_id] = payment

    temporary_path = path.with_suffix(".tmp")

    with temporary_path.open("w", encoding="utf-8") as f:
        json.dump(payments, f, indent=2, ensure_ascii=False, sort_keys=True)

    temporary_path.replace(path)
