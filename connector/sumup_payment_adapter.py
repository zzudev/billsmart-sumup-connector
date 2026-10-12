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
