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


def test_extract_reader_checkout_identifiers():
    from connector.sumup_payment_adapter import (
        extract_reader_checkout_identifiers,
    )

    response = {
        "data": {
            "checkout_id": "CHECKOUT-001",
            "client_transaction_id": "CLIENT-TX-001",
        }
    }

    assert extract_reader_checkout_identifiers(response) == {
        "checkout_id": "CHECKOUT-001",
        "client_transaction_id": "CLIENT-TX-001",
    }


def test_invalid_reader_checkout_responses_are_rejected():
    import pytest

    from connector.sumup_payment_adapter import (
        extract_reader_checkout_identifiers,
    )

    invalid_responses = [
        None,
        {},
        {"status": "PENDING"},
        {"data": None},
        {"data": {}},
        {"data": {"checkout_id": ""}},
        {"data": {"checkout_id": 123}},
        {"data": {"client_transaction_id": "   "}},
    ]

    for response in invalid_responses:
        with pytest.raises(ValueError):
            extract_reader_checkout_identifiers(response)


def test_reader_checkout_accepts_partial_identifiers():
    from connector.sumup_payment_adapter import (
        extract_reader_checkout_identifiers,
    )

    response_with_checkout_id = {
        "data": {
            "checkout_id": "CHECKOUT-001",
        }
    }

    assert extract_reader_checkout_identifiers(
        response_with_checkout_id
    ) == {
        "checkout_id": "CHECKOUT-001",
    }

    response_with_client_transaction_id = {
        "data": {
            "client_transaction_id": "CLIENT-TX-001",
        }
    }

    assert extract_reader_checkout_identifiers(
        response_with_client_transaction_id
    ) == {
        "client_transaction_id": "CLIENT-TX-001",
    }


def test_normalize_reader_checkout_pending():
    from connector.sumup_payment_adapter import (
        normalize_reader_checkout,
    )

    response = {
        "data": {
            "checkout_id": "CHECKOUT-001",
            "client_transaction_id": "CLIENT-TX-001",
            "status": "pending",
            "payment_status": "pending",
            "total_amount": {
                "currency": "EUR",
                "minor_unit": 2,
                "value": 620,
            },
        }
    }

    assert normalize_reader_checkout(response) == {
        "provider_checkout_id": "CHECKOUT-001",
        "provider_client_transaction_id": "CLIENT-TX-001",
        "status": "pending",
        "amount": "6.20",
        "currency": "EUR",
    }


def test_normalize_reader_checkout_rejects_inconsistent_data():
    import pytest

    from connector.sumup_payment_adapter import (
        normalize_reader_checkout,
    )

    valid_data = {
        "checkout_id": "CHECKOUT-001",
        "client_transaction_id": "CLIENT-TX-001",
        "status": "pending",
        "payment_status": "pending",
        "total_amount": {
            "currency": "EUR",
            "minor_unit": 2,
            "value": 620,
        },
    }

    invalid_cases = [
        {"status": "unknown"},
        {"payment_status": "failed"},
        {"checkout_id": ""},
        {"client_transaction_id": ""},
        {"total_amount": {"currency": "EUR", "minor_unit": 2, "value": 0}},
        {"total_amount": {"currency": "EUR", "minor_unit": 2, "value": 620.5}},
        {"total_amount": {"currency": "EUR", "minor_unit": 3, "value": 620}},
    ]

    for changes in invalid_cases:
        data = {**valid_data, **changes}

        with pytest.raises(ValueError):
            normalize_reader_checkout({"data": data})


def test_normalize_reader_checkout_terminal_statuses():
    from connector.sumup_payment_adapter import (
        normalize_reader_checkout,
    )

    status_mapping = {
        "successful": "succeeded",
        "failed": "failed",
        "cancelled": "cancelled",
    }

    for provider_status, expected_status in status_mapping.items():
        response = {
            "data": {
                "checkout_id": "CHECKOUT-TERMINAL-001",
                "client_transaction_id": "CLIENT-TX-TERMINAL-001",
                "status": provider_status,
                "payment_status": provider_status,
                "total_amount": {
                    "currency": "EUR",
                    "minor_unit": 2,
                    "value": 620,
                },
            }
        }

        normalized = normalize_reader_checkout(response)

        assert normalized == {
            "provider_checkout_id": "CHECKOUT-TERMINAL-001",
            "provider_client_transaction_id": "CLIENT-TX-TERMINAL-001",
            "status": expected_status,
            "amount": "6.20",
            "currency": "EUR",
        }
