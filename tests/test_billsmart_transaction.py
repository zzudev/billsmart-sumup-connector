import copy
from decimal import Decimal

import pytest

from connector.billsmart_transaction import (
    BillSmartTransactionError,
    calculate_gross_total,
    validate_transaction,
)


SAMPLE_TRANSACTION = {
    "schema_version": "0.1",
    "transaction_type": "sale",
    "sale_id": "BLB-TEST-0001",
    "issued_at": "2026-10-07T10:00:00+02:00",
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
            "tax_rate": "10.00",
            "total": "5.00",
        },
        {
            "reference": "CROISSANT",
            "label": "Croissant",
            "quantity": 1,
            "unit_price": "1.20",
            "tax_rate": "10.00",
            "total": "1.20",
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


def test_sample_transaction_total():
    assert SAMPLE_TRANSACTION["totals"]["gross"] == "6.20"
    assert SAMPLE_TRANSACTION["payment"]["amount"] == "6.20"


def test_calculate_gross_total():
    total = calculate_gross_total(SAMPLE_TRANSACTION)

    assert total == Decimal("6.20")


def test_validate_consistent_transaction():
    assert validate_transaction(SAMPLE_TRANSACTION) is True


def test_reject_inconsistent_gross_total():
    transaction = copy.deepcopy(SAMPLE_TRANSACTION)
    transaction["totals"]["gross"] = "6.50"
    transaction["payment"]["amount"] = "6.50"

    with pytest.raises(
        BillSmartTransactionError,
        match="Gross total mismatch",
    ):
        validate_transaction(transaction)


def test_reject_inconsistent_payment_amount():
    transaction = copy.deepcopy(SAMPLE_TRANSACTION)
    transaction["payment"]["amount"] = "6.50"

    with pytest.raises(
        BillSmartTransactionError,
        match="Payment amount mismatch",
    ):
        validate_transaction(transaction)


def test_reject_missing_sale_id():
    transaction = copy.deepcopy(SAMPLE_TRANSACTION)
    del transaction["sale_id"]

    with pytest.raises(
        BillSmartTransactionError,
        match="Missing required field: sale_id",
    ):
        validate_transaction(transaction)


def test_reject_unsupported_schema_version():
    transaction = copy.deepcopy(SAMPLE_TRANSACTION)
    transaction["schema_version"] = "99.0"

    with pytest.raises(
        BillSmartTransactionError,
        match="Unsupported schema version",
    ):
        validate_transaction(transaction)


def test_reject_empty_sale_id():
    transaction = copy.deepcopy(SAMPLE_TRANSACTION)
    transaction["sale_id"] = ""

    with pytest.raises(
        BillSmartTransactionError,
        match="sale_id must be a non-empty string",
    ):
        validate_transaction(transaction)


def test_reject_invalid_currency():
    transaction = copy.deepcopy(SAMPLE_TRANSACTION)
    transaction["currency"] = "eur"

    with pytest.raises(
        BillSmartTransactionError,
        match="Invalid currency code",
    ):
        validate_transaction(transaction)


def test_reject_zero_quantity():
    transaction = copy.deepcopy(SAMPLE_TRANSACTION)
    transaction["items"][0]["quantity"] = 0

    with pytest.raises(
        BillSmartTransactionError,
        match="Item quantity must be greater than zero",
    ):
        validate_transaction(transaction)


def test_reject_negative_unit_price():
    transaction = copy.deepcopy(SAMPLE_TRANSACTION)
    transaction["items"][0]["unit_price"] = "-2.50"

    with pytest.raises(
        BillSmartTransactionError,
        match="Item unit price cannot be negative",
    ):
        validate_transaction(transaction)


def test_build_payment_request():
    from connector.billsmart_transaction import build_payment_request

    payment_request = build_payment_request(SAMPLE_TRANSACTION)

    assert payment_request == {
        "sale_id": "BLB-TEST-0001",
        "amount": "6.20",
        "currency": "EUR",
    }


def test_payment_request_rejects_invalid_transaction():
    from connector.billsmart_transaction import build_payment_request

    transaction = copy.deepcopy(SAMPLE_TRANSACTION)
    transaction["payment"]["amount"] = "6.50"

    with pytest.raises(
        BillSmartTransactionError,
        match="Payment amount mismatch",
    ):
        build_payment_request(transaction)
