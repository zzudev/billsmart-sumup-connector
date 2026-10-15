import pytest


def test_verify_matching_payment_confirmation():
    from connector.billsmart_payment_verification import (
        verify_payment_confirmation,
    )

    payment = {
        "payment_id": "BLB-PAY-001",
        "sale_id": "BLB-SALE-001",
        "amount": "6.20",
        "currency": "EUR",
        "provider": "sumup",
        "status": "pending",
        "provider_checkout_id": "CHECKOUT-001",
        "provider_client_transaction_id": "CLIENT-TX-001",
    }

    confirmation = {
        "provider_checkout_id": "CHECKOUT-001",
        "provider_client_transaction_id": "CLIENT-TX-001",
        "amount": "6.20",
        "currency": "EUR",
        "status": "succeeded",
    }

    result = verify_payment_confirmation(payment, confirmation)

    assert result == {
        "payment_id": "BLB-PAY-001",
        "sale_id": "BLB-SALE-001",
        "status": "succeeded",
    }


@pytest.mark.parametrize(
    "field,invalid_value",
    [
        ("provider_checkout_id", "WRONG-CHECKOUT"),
        ("provider_client_transaction_id", "WRONG-TRANSACTION"),
        ("amount", "6.21"),
        ("currency", "USD"),
        ("provider_checkout_id", None),
        ("provider_client_transaction_id", None),
        ("status", "unknown"),
    ],
)
def test_reject_mismatched_payment_confirmation(field, invalid_value):
    from connector.billsmart_payment_verification import (
        verify_payment_confirmation,
    )

    payment = {
        "payment_id": "BLB-PAY-001",
        "sale_id": "BLB-SALE-001",
        "amount": "6.20",
        "currency": "EUR",
        "provider": "sumup",
        "status": "pending",
        "provider_checkout_id": "CHECKOUT-001",
        "provider_client_transaction_id": "CLIENT-TX-001",
    }

    confirmation = {
        "provider_checkout_id": "CHECKOUT-001",
        "provider_client_transaction_id": "CLIENT-TX-001",
        "amount": "6.20",
        "currency": "EUR",
        "status": "succeeded",
    }

    confirmation[field] = invalid_value

    with pytest.raises(ValueError):
        verify_payment_confirmation(payment, confirmation)
