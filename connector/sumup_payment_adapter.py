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
