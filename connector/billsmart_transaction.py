from decimal import Decimal, InvalidOperation


class BillSmartTransactionError(ValueError):
    """Raised when a BillSmart transaction is invalid."""


def _money(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise BillSmartTransactionError(
            f"Invalid monetary value: {value!r}"
        ) from exc


def calculate_gross_total(transaction):
    """Calculate the gross sale total from the transaction items."""
    items = transaction.get("items")

    if not isinstance(items, list) or not items:
        raise BillSmartTransactionError(
            "Transaction must contain at least one item"
        )

    total = Decimal("0.00")

    for item in items:
        quantity = _money(item.get("quantity"))
        unit_price = _money(item.get("unit_price"))

        if quantity <= 0:
            raise BillSmartTransactionError(
                f"Item quantity must be greater than zero: {quantity}"
            )

        if unit_price < 0:
            raise BillSmartTransactionError(
                f"Item unit price cannot be negative: {unit_price}"
            )

        total += quantity * unit_price

    return total.quantize(Decimal("0.01"))


def validate_transaction(transaction):
    """Validate the financial consistency of a BillSmart transaction."""
    required_fields = (
        "schema_version",
        "transaction_type",
        "sale_id",
        "currency",
        "source",
        "merchant",
        "items",
        "totals",
        "payment",
    )

    for field in required_fields:
        if field not in transaction:
            raise BillSmartTransactionError(
                f"Missing required field: {field}"
            )

    if transaction["schema_version"] != "0.1":
        raise BillSmartTransactionError(
            f"Unsupported schema version: "
            f"{transaction['schema_version']}"
        )

    if transaction["transaction_type"] != "sale":
        raise BillSmartTransactionError(
            f"Unsupported transaction type: "
            f"{transaction['transaction_type']}"
        )

    sale_id = transaction["sale_id"]
    if not isinstance(sale_id, str) or not sale_id.strip():
        raise BillSmartTransactionError(
            "sale_id must be a non-empty string"
        )

    currency = transaction["currency"]
    if (
        not isinstance(currency, str)
        or len(currency) != 3
        or not currency.isalpha()
        or currency != currency.upper()
    ):
        raise BillSmartTransactionError(
            f"Invalid currency code: {currency!r}"
        )

    calculated_total = calculate_gross_total(transaction)

    totals = transaction.get("totals")
    if not isinstance(totals, dict):
        raise BillSmartTransactionError(
            "Transaction must contain totals"
        )

    declared_total = _money(totals.get("gross"))

    if calculated_total != declared_total:
        raise BillSmartTransactionError(
            f"Gross total mismatch: "
            f"calculated={calculated_total} declared={declared_total}"
        )

    payment = transaction.get("payment")
    if not isinstance(payment, dict):
        raise BillSmartTransactionError(
            "Transaction must contain payment"
        )

    payment_amount = _money(payment.get("amount"))

    if payment_amount != declared_total:
        raise BillSmartTransactionError(
            f"Payment amount mismatch: "
            f"payment={payment_amount} gross={declared_total}"
        )

    return True
