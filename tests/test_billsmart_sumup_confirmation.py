"""Tests for the SumUp-to-BillSmart confirmation workflow."""

from unittest.mock import patch

from connector.billsmart_payment_registry import (
    load_payment,
    save_payment,
    set_provider_checkout_reference,
    set_provider_client_transaction_reference,
    update_payment_status,
)


def test_confirm_registered_sumup_payment(tmp_path):
    from connector.billsmart_sumup_confirmation import (
        confirm_sumup_payment,
    )

    state_path = tmp_path / "payments.json"

    save_payment(
        {
            "payment_id": "BLB-PAY-001",
            "sale_id": "BLB-SALE-001",
            "amount": "6.20",
            "currency": "EUR",
            "provider": "sumup",
            "status": "created",
            "provider_checkout_id": None,
        },
        state_path=state_path,
    )

    set_provider_checkout_reference(
        "BLB-PAY-001",
        "CHECKOUT-001",
        state_path=state_path,
    )

    set_provider_client_transaction_reference(
        "BLB-PAY-001",
        "CLIENT-TX-001",
        state_path=state_path,
    )

    update_payment_status(
        "BLB-PAY-001",
        "pending",
        state_path=state_path,
    )

    sumup_response = {
        "data": {
            "checkout_id": "CHECKOUT-001",
            "client_transaction_id": "CLIENT-TX-001",
            "status": "successful",
            "total_amount": {
                "currency": "EUR",
                "minor_unit": 2,
                "value": 620,
            },
        }
    }

    with patch(
        "connector.sumup_reader_client.get_reader_checkout",
        return_value=sumup_response,
    ) as mocked_get:
        result = confirm_sumup_payment(
            payment_id="BLB-PAY-001",
            api_key="TEST-KEY",
            merchant_code="TEST-MERCHANT",
            reader_id="TEST-READER",
            payments_path=state_path,
        )

    mocked_get.assert_called_once_with(
        "TEST-KEY",
        "TEST-MERCHANT",
        "TEST-READER",
        "CHECKOUT-001",
    )

    assert result["payment_id"] == "BLB-PAY-001"
    assert result["sale_id"] == "BLB-SALE-001"
    assert result["status"] == "succeeded"

    stored = load_payment(
        "BLB-PAY-001",
        state_path=state_path,
    )
    assert stored["status"] == "succeeded"


def test_reject_mismatched_checkout_without_updating_payment(tmp_path):
    import pytest

    from connector.billsmart_sumup_confirmation import (
        confirm_sumup_payment,
    )

    state_path = tmp_path / "payments.json"

    save_payment(
        {
            "payment_id": "BLB-PAY-002",
            "sale_id": "BLB-SALE-002",
            "amount": "6.20",
            "currency": "EUR",
            "provider": "sumup",
            "status": "created",
            "provider_checkout_id": None,
        },
        state_path=state_path,
    )

    set_provider_checkout_reference(
        "BLB-PAY-002",
        "CHECKOUT-002",
        state_path=state_path,
    )

    set_provider_client_transaction_reference(
        "BLB-PAY-002",
        "CLIENT-TX-002",
        state_path=state_path,
    )

    update_payment_status(
        "BLB-PAY-002",
        "pending",
        state_path=state_path,
    )

    invalid_response = {
        "data": {
            "checkout_id": "WRONG-CHECKOUT",
            "client_transaction_id": "CLIENT-TX-002",
            "status": "successful",
            "total_amount": {
                "currency": "EUR",
                "minor_unit": 2,
                "value": 620,
            },
        }
    }

    with patch(
        "connector.sumup_reader_client.get_reader_checkout",
        return_value=invalid_response,
    ) as mocked_get:
        with pytest.raises(ValueError, match="Payment reference mismatch"):
            confirm_sumup_payment(
                payment_id="BLB-PAY-002",
                api_key="TEST-KEY",
                merchant_code="TEST-MERCHANT",
                reader_id="TEST-READER",
                payments_path=state_path,
            )

    mocked_get.assert_called_once()

    stored = load_payment(
        "BLB-PAY-002",
        state_path=state_path,
    )

    assert stored["status"] == "pending"
    assert stored["provider_checkout_id"] == "CHECKOUT-002"


def test_reject_wrong_amount_without_updating_payment(tmp_path):
    import pytest

    from connector.billsmart_sumup_confirmation import (
        confirm_sumup_payment,
    )

    state_path = tmp_path / "payments.json"

    save_payment(
        {
            "payment_id": "BLB-PAY-003",
            "sale_id": "BLB-SALE-003",
            "amount": "6.20",
            "currency": "EUR",
            "provider": "sumup",
            "status": "created",
            "provider_checkout_id": None,
        },
        state_path=state_path,
    )

    set_provider_checkout_reference(
        "BLB-PAY-003",
        "CHECKOUT-003",
        state_path=state_path,
    )

    set_provider_client_transaction_reference(
        "BLB-PAY-003",
        "CLIENT-TX-003",
        state_path=state_path,
    )

    update_payment_status(
        "BLB-PAY-003",
        "pending",
        state_path=state_path,
    )

    wrong_amount_response = {
        "data": {
            "checkout_id": "CHECKOUT-003",
            "client_transaction_id": "CLIENT-TX-003",
            "status": "successful",
            "total_amount": {
                "currency": "EUR",
                "minor_unit": 2,
                "value": 630,
            },
        }
    }

    with patch(
        "connector.sumup_reader_client.get_reader_checkout",
        return_value=wrong_amount_response,
    ) as mocked_get:
        with pytest.raises(ValueError, match="Payment amount mismatch"):
            confirm_sumup_payment(
                payment_id="BLB-PAY-003",
                api_key="TEST-KEY",
                merchant_code="TEST-MERCHANT",
                reader_id="TEST-READER",
                payments_path=state_path,
            )

    mocked_get.assert_called_once()

    stored = load_payment(
        "BLB-PAY-003",
        state_path=state_path,
    )

    assert stored["status"] == "pending"
    assert stored["amount"] == "6.20"


def test_sumup_network_error_preserves_payment_status(tmp_path):
    import pytest

    from connector.billsmart_sumup_confirmation import (
        confirm_sumup_payment,
    )

    state_path = tmp_path / "payments.json"

    save_payment(
        {
            "payment_id": "BLB-PAY-004",
            "sale_id": "BLB-SALE-004",
            "amount": "6.20",
            "currency": "EUR",
            "provider": "sumup",
            "status": "created",
            "provider_checkout_id": None,
        },
        state_path=state_path,
    )

    set_provider_checkout_reference(
        "BLB-PAY-004",
        "CHECKOUT-004",
        state_path=state_path,
    )

    set_provider_client_transaction_reference(
        "BLB-PAY-004",
        "CLIENT-TX-004",
        state_path=state_path,
    )

    update_payment_status(
        "BLB-PAY-004",
        "pending",
        state_path=state_path,
    )

    with patch(
        "connector.sumup_reader_client.get_reader_checkout",
        side_effect=ConnectionError("Simulated SumUp outage"),
    ) as mocked_get:
        with pytest.raises(
            ConnectionError,
            match="Simulated SumUp outage",
        ):
            confirm_sumup_payment(
                payment_id="BLB-PAY-004",
                api_key="TEST-KEY",
                merchant_code="TEST-MERCHANT",
                reader_id="TEST-READER",
                payments_path=state_path,
            )

    mocked_get.assert_called_once()

    stored = load_payment(
        "BLB-PAY-004",
        state_path=state_path,
    )

    assert stored["status"] == "pending"
    assert stored["provider_checkout_id"] == "CHECKOUT-004"
