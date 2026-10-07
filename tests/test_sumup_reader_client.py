import pytest

from connector.sumup_reader_client import select_physical_solo


def test_select_physical_solo():
    readers = [
        {
            "id": "virtual-reader",
            "name": "Virtual Solo",
            "device": {"model": "virtual"},
        },
        {
            "id": "physical-reader",
            "name": "BillSmart Solo",
            "status": "paired",
            "device": {"model": "solo"},
        },
    ]

    reader = select_physical_solo(readers)

    assert reader["id"] == "physical-reader"
    assert reader["name"] == "BillSmart Solo"


def test_select_physical_solo_rejects_no_solo():
    readers = [
        {
            "id": "virtual-reader",
            "device": {"model": "virtual"},
        }
    ]

    with pytest.raises(
        RuntimeError,
        match="Impossible d'identifier un unique Solo physique",
    ):
        select_physical_solo(readers)


def test_select_physical_solo_rejects_multiple_solos():
    readers = [
        {
            "id": "physical-reader-1",
            "device": {"model": "solo"},
        },
        {
            "id": "physical-reader-2",
            "device": {"model": "solo"},
        },
    ]

    with pytest.raises(
        RuntimeError,
        match="Impossible d'identifier un unique Solo physique",
    ):
        select_physical_solo(readers)


def test_get_merchant_code():
    from unittest.mock import patch

    from connector.sumup_reader_client import get_merchant_code

    with patch("connector.sumup_reader_client.requests.get") as get:
        get.return_value.json.return_value = {
            "merchant_profile": {
                "merchant_code": "MERCHANT-TEST",
            }
        }

        merchant_code = get_merchant_code("test-api-key")

    assert merchant_code == "MERCHANT-TEST"

    get.assert_called_once_with(
        "https://api.sumup.com/v0.1/me",
        headers={
            "Authorization": "Bearer test-api-key",
            "Content-Type": "application/json",
        },
        timeout=15,
    )

    get.return_value.raise_for_status.assert_called_once_with()


def test_get_readers():
    from unittest.mock import patch

    from connector.sumup_reader_client import get_readers

    with patch("connector.sumup_reader_client.requests.get") as get:
        get.return_value.json.return_value = {
            "items": [
                {
                    "id": "physical-reader",
                    "name": "BillSmart Solo",
                    "device": {"model": "solo"},
                }
            ]
        }

        readers = get_readers(
            "test-api-key",
            "MERCHANT-TEST",
        )

    assert readers == [
        {
            "id": "physical-reader",
            "name": "BillSmart Solo",
            "device": {"model": "solo"},
        }
    ]

    get.assert_called_once_with(
        "https://api.sumup.com/v0.1/merchants/MERCHANT-TEST/readers",
        headers={
            "Authorization": "Bearer test-api-key",
            "Content-Type": "application/json",
        },
        timeout=15,
    )

    get.return_value.raise_for_status.assert_called_once_with()


def test_send_checkout_to_reader():
    from unittest.mock import patch

    from connector.sumup_reader_client import send_checkout_to_reader

    payload = {
        "total_amount": {
            "currency": "EUR",
            "minor_unit": 2,
            "value": 620,
        }
    }

    with patch("connector.sumup_reader_client.requests.post") as post:
        post.return_value.json.return_value = {
            "status": "PENDING",
        }

        result = send_checkout_to_reader(
            api_key="test-api-key",
            merchant_code="MERCHANT-TEST",
            reader_id="physical-reader",
            payload=payload,
        )

    post.assert_called_once_with(
        (
            "https://api.sumup.com/v0.1/merchants/"
            "MERCHANT-TEST/readers/physical-reader/checkout"
        ),
        headers={
            "Authorization": "Bearer test-api-key",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=15,
    )

    post.return_value.raise_for_status.assert_called_once_with()
    assert result == {"status": "PENDING"}


def test_send_checkout_to_physical_solo():
    from unittest.mock import patch

    from connector.sumup_reader_client import send_checkout_to_physical_solo

    payload = {
        "total_amount": {
            "currency": "EUR",
            "minor_unit": 2,
            "value": 620,
        }
    }

    with (
        patch(
            "connector.sumup_reader_client.get_merchant_code",
            return_value="MERCHANT-TEST",
        ) as get_merchant_code,
        patch(
            "connector.sumup_reader_client.get_readers",
            return_value=[
                {
                    "id": "physical-reader",
                    "name": "BillSmart Solo",
                    "device": {"model": "solo"},
                }
            ],
        ) as get_readers,
        patch(
            "connector.sumup_reader_client.send_checkout_to_reader",
            return_value={"status": "PENDING"},
        ) as send_checkout,
    ):
        result = send_checkout_to_physical_solo(
            api_key="test-api-key",
            payload=payload,
        )

    get_merchant_code.assert_called_once_with("test-api-key")
    get_readers.assert_called_once_with(
        "test-api-key",
        "MERCHANT-TEST",
    )
    send_checkout.assert_called_once_with(
        api_key="test-api-key",
        merchant_code="MERCHANT-TEST",
        reader_id="physical-reader",
        payload=payload,
    )

    assert result == {"status": "PENDING"}
