from decimal import Decimal


def build_sumup_checkout_payload(payment_request):
    """Translate a BillSmart payment request into a SumUp checkout payload."""
    amount = Decimal(payment_request["amount"])

    if amount != amount.quantize(Decimal("0.01")):
        raise ValueError(
            "Amount has more than two decimal places"
        )

    value = int(amount * 100)

    return {
        "total_amount": {
            "currency": payment_request["currency"],
            "minor_unit": 2,
            "value": value,
        }
    }


def extract_reader_checkout_identifiers(response):
    """Extract identifiers from a SumUp Reader Checkout response."""
    if not isinstance(response, dict):
        raise ValueError("Invalid SumUp checkout response")

    data = response.get("data")

    if not isinstance(data, dict):
        raise ValueError("Missing SumUp checkout data")

    identifiers = {}

    for field in ("checkout_id", "client_transaction_id"):
        value = data.get(field)

        if value is not None:
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Invalid SumUp identifier: {field}")

            identifiers[field] = value

    if not identifiers:
        raise ValueError("Missing SumUp checkout identifiers")

    return identifiers


def normalize_reader_checkout(response):
    """Normalize a SumUp Reader Checkout response for BillSmart."""
    if not isinstance(response, dict):
        raise ValueError("Invalid SumUp checkout response")

    data = response.get("data")
    if not isinstance(data, dict):
        raise ValueError("Missing SumUp checkout data")

    checkout_id = data.get("checkout_id")
    client_transaction_id = data.get("client_transaction_id")

    for name, value in (
        ("checkout_id", checkout_id),
        ("client_transaction_id", client_transaction_id),
    ):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Invalid SumUp identifier: {name}")

    status_mapping = {
        "pending": "pending",
        "successful": "succeeded",
        "failed": "failed",
        "cancelled": "cancelled",
    }

    provider_status = data.get("status")
    if provider_status not in status_mapping:
        raise ValueError("Unknown SumUp checkout status")

    payment_status = data.get("payment_status")
    if payment_status is not None and payment_status != provider_status:
        raise ValueError("Inconsistent SumUp payment status")

    total_amount = data.get("total_amount")
    if not isinstance(total_amount, dict):
        raise ValueError("Missing SumUp total amount")

    currency = total_amount.get("currency")
    minor_unit = total_amount.get("minor_unit")
    value = total_amount.get("value")

    if not isinstance(currency, str) or not currency.strip():
        raise ValueError("Invalid SumUp currency")

    if type(minor_unit) is not int or minor_unit != 2:
        raise ValueError("Unsupported SumUp minor unit")

    if type(value) is not int or value <= 0:
        raise ValueError("Invalid SumUp amount")

    amount = Decimal(value) / Decimal(100)

    return {
        "provider_checkout_id": checkout_id,
        "provider_client_transaction_id": client_transaction_id,
        "status": status_mapping[provider_status],
        "amount": f"{amount:.2f}",
        "currency": currency,
    }
