import os

from dotenv import load_dotenv

from connector.billsmart_transaction import build_payment_request
from connector.sumup_payment_adapter import build_sumup_checkout_payload
from connector.sumup_reader_client import send_checkout_to_physical_solo


TRANSACTION = {
    "schema_version": "0.1",
    "transaction_type": "sale",
    "sale_id": "BLB-REAL-0001",
    "currency": "EUR",
    "source": {
        "type": "billsmart_simulator",
        "provider": None,
        "external_reference": None,
    },
    "merchant": {
        "merchant_id": "BLB-DEMO",
        "name": "Commerce de démonstration",
    },
    "items": [
        {
            "reference": "CAFE",
            "label": "Café",
            "quantity": 2,
            "unit_price": "2.50",
        },
        {
            "reference": "CROISSANT",
            "label": "Croissant",
            "quantity": 1,
            "unit_price": "1.20",
        },
    ],
    "totals": {
        "gross": "6.20",
    },
    "payment": {
        "status": "pending",
        "amount": "6.20",
        "method": None,
        "provider": None,
        "provider_transaction_id": None,
    },
    "metadata": {},
}


def main():
    load_dotenv()

    api_key = os.getenv("SUMUP_API_KEY")
    if not api_key:
        raise RuntimeError("SUMUP_API_KEY is missing")

    payment_request = build_payment_request(TRANSACTION)
    payload = build_sumup_checkout_payload(payment_request)

    print(
        "BillSmart sale prepared:",
        payment_request["sale_id"],
        payment_request["amount"],
        payment_request["currency"],
    )

    response = send_checkout_to_physical_solo(
        api_key=api_key,
        payload=payload,
    )

    print("SumUp checkout created:", response)


if __name__ == "__main__":
    main()
