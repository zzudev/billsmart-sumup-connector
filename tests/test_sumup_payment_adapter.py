from connector.sumup_payment_adapter import build_sumup_checkout_payload


def test_build_sumup_checkout_payload():
    payment_request = {
        "sale_id": "BLB-TEST-0001",
        "amount": "6.20",
        "currency": "EUR",
    }

    payload = build_sumup_checkout_payload(payment_request)

    assert payload == {
        "total_amount": {
            "currency": "EUR",
            "minor_unit": 2,
            "value": 620,
        }
    }


def test_reject_amount_with_more_than_two_decimal_places():
    import pytest

    payment_request = {
        "sale_id": "BLB-TEST-0001",
        "amount": "6.205",
        "currency": "EUR",
    }

    with pytest.raises(
        ValueError,
        match="Amount has more than two decimal places",
    ):
        build_sumup_checkout_payload(payment_request)
