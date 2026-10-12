"""Link BillSmart sales to provider-neutral payment attempts."""

from connector.billsmart_sale_registry import load_sale
from connector.billsmart_payment_registry import save_payment
from connector.billsmart_transaction import build_payment_request


def create_payment_for_sale(
    *,
    sale_id,
    payment_id,
    provider,
    sales_path,
    payments_path,
):
    """Create a payment attempt for an existing BillSmart sale."""
    sale = load_sale(sale_id, state_path=sales_path)

    if sale is None:
        raise ValueError(f"BillSmart sale not found: {sale_id}")

    payment_request = build_payment_request(sale)

    payment = {
        "payment_id": payment_id,
        "sale_id": sale_id,
        "amount": payment_request["amount"],
        "currency": payment_request["currency"],
        "provider": provider,
        "status": "created",
        "provider_checkout_id": None,
    }

    save_payment(payment, state_path=payments_path)

    return payment
