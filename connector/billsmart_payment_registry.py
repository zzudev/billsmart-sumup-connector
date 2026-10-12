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


def set_provider_checkout_reference(
    payment_id,
    checkout_id,
    *,
    state_path=DEFAULT_PAYMENTS_PATH,
):
    """Associate a provider checkout reference with a payment attempt."""
    if not isinstance(checkout_id, str) or not checkout_id.strip():
        raise ValueError("Invalid provider checkout reference")

    path = Path(state_path)

    if not path.exists():
        raise ValueError(f"Payment not found: {payment_id}")

    with path.open("r", encoding="utf-8") as f:
        payments = json.load(f)

    if not isinstance(payments, dict):
        raise ValueError("Invalid BillSmart payment registry")

    if payment_id not in payments:
        raise ValueError(f"Payment not found: {payment_id}")

    payment = payments[payment_id]
    existing = payment.get("provider_checkout_id")

    if existing is not None:
        if existing == checkout_id:
            return payment
        raise ValueError("Conflicting provider checkout reference")

    for other_id, other_payment in payments.items():
        if (
            other_id != payment_id
            and other_payment.get("provider") == payment.get("provider")
            and other_payment.get("provider_checkout_id") == checkout_id
        ):
            raise ValueError("Provider checkout reference already assigned")

    payment["provider_checkout_id"] = checkout_id

    temporary_path = path.with_suffix(".tmp")

    with temporary_path.open("w", encoding="utf-8") as f:
        json.dump(payments, f, indent=2, ensure_ascii=False, sort_keys=True)

    temporary_path.replace(path)

    return payment


def update_payment_status(
    payment_id,
    new_status,
    *,
    state_path=DEFAULT_PAYMENTS_PATH,
):
    """Update a payment status using controlled state transitions."""
    allowed_transitions = {
        "created": {"pending"},
        "pending": {"succeeded", "failed", "cancelled"},
        "succeeded": set(),
        "failed": set(),
        "cancelled": set(),
    }

    path = Path(state_path)

    if not path.exists():
        raise ValueError(f"Payment not found: {payment_id}")

    with path.open("r", encoding="utf-8") as f:
        payments = json.load(f)

    if not isinstance(payments, dict):
        raise ValueError("Invalid BillSmart payment registry")

    if payment_id not in payments:
        raise ValueError(f"Payment not found: {payment_id}")

    payment = payments[payment_id]
    current_status = payment.get("status")

    if current_status not in allowed_transitions:
        raise ValueError(f"Unknown payment status: {current_status}")

    if new_status == current_status:
        return payment

    if new_status not in allowed_transitions[current_status]:
        raise ValueError(
            f"Invalid payment status transition: "
            f"{current_status} -> {new_status}"
        )

    payment["status"] = new_status

    temporary_path = path.with_suffix(".tmp")

    with temporary_path.open("w", encoding="utf-8") as f:
        json.dump(payments, f, indent=2, ensure_ascii=False, sort_keys=True)

    temporary_path.replace(path)

    return payment


def set_provider_client_transaction_reference(
    payment_id,
    client_transaction_id,
    *,
    state_path=DEFAULT_PAYMENTS_PATH,
):
    """Associate a provider client transaction reference with a payment."""
    if (
        not isinstance(client_transaction_id, str)
        or not client_transaction_id.strip()
    ):
        raise ValueError("Invalid provider client transaction reference")

    path = Path(state_path)

    if not path.exists():
        raise ValueError(f"Payment not found: {payment_id}")

    with path.open("r", encoding="utf-8") as f:
        payments = json.load(f)

    if not isinstance(payments, dict):
        raise ValueError("Invalid BillSmart payment registry")

    if payment_id not in payments:
        raise ValueError(f"Payment not found: {payment_id}")

    payment = payments[payment_id]
    field = "provider_client_transaction_id"
    existing = payment.get(field)

    if existing is not None:
        if existing == client_transaction_id:
            return payment
        raise ValueError("Conflicting provider client transaction reference")

    for other_id, other_payment in payments.items():
        if (
            other_id != payment_id
            and other_payment.get("provider") == payment.get("provider")
            and other_payment.get(field) == client_transaction_id
        ):
            raise ValueError(
                "Provider client transaction reference already assigned"
            )

    payment[field] = client_transaction_id

    temporary_path = path.with_suffix(".tmp")

    with temporary_path.open("w", encoding="utf-8") as f:
        json.dump(payments, f, indent=2, ensure_ascii=False, sort_keys=True)

    temporary_path.replace(path)

    return payment
