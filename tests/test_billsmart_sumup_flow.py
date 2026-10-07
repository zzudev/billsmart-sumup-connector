from unittest.mock import patch

from connector.billsmart_transaction import build_payment_request
from connector.sumup_payment_adapter import build_sumup_checkout_payload
from connector.sumup_reader_client import send_checkout_to_physical_solo


def test_billsmart_transaction_reaches_solo_with_expected_amount():
    transaction = {
        "schema_version": "0.1",
        "transaction_type": "sale",
        "sale_id": "BLB-FLOW-0001",
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

    payment_request = build_payment_request(transaction)
    payload = build_sumup_checkout_payload(payment_request)

    with patch(
        "connector.sumup_reader_client.send_checkout_to_reader",
        return_value={"status": "PENDING"},
    ) as send_checkout, patch(
        "connector.sumup_reader_client.get_merchant_code",
        return_value="MERCHANT-TEST",
    ), patch(
        "connector.sumup_reader_client.get_readers",
        return_value=[
            {
                "id": "physical-reader",
                "name": "BillSmart Solo",
                "device": {"model": "solo"},
            }
        ],
    ):
        result = send_checkout_to_physical_solo(
            api_key="test-api-key",
            payload=payload,
        )

    assert payload == {
        "total_amount": {
            "currency": "EUR",
            "minor_unit": 2,
            "value": 620,
        }
    }

    send_checkout.assert_called_once_with(
        api_key="test-api-key",
        merchant_code="MERCHANT-TEST",
        reader_id="physical-reader",
        payload=payload,
    )

    assert result == {"status": "PENDING"}
