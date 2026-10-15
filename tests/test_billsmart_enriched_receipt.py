"""Tests for provider-neutral BillSmart enriched receipts."""

from connector.billsmart_sale_registry import save_sale
from connector.billsmart_payment_registry import (
    save_payment,
    update_payment_status,
)


def test_build_enriched_receipt_preserves_sale_items(tmp_path):
    from connector.billsmart_enriched_receipt import (
        build_enriched_receipt,
    )

    sales_path = tmp_path / "sales.json"
    payments_path = tmp_path / "payments.json"

    sale = {
        "schema_version": "0.1",
        "transaction_type": "sale",
        "sale_id": "BLB-SALE-101",
        "currency": "EUR",
        "source": {"type": "simulator"},
        "merchant": {"name": "Café Démonstration"},
        "items": [
            {
                "name": "Café",
                "quantity": 2,
                "unit_price": "2.10",
            },
            {
                "name": "Croissant",
                "quantity": 1,
                "unit_price": "2.00",
            },
        ],
        "totals": {"gross": "6.20"},
        "payment": {"amount": "6.20"},
    }

    save_sale(sale, state_path=sales_path)

    save_payment(
        {
            "payment_id": "BLB-PAY-101",
            "sale_id": "BLB-SALE-101",
            "amount": "6.20",
            "currency": "EUR",
            "provider": "sumup",
            "status": "created",
            "provider_checkout_id": None,
        },
        state_path=payments_path,
    )

    update_payment_status(
        "BLB-PAY-101",
        "pending",
        state_path=payments_path,
    )
    update_payment_status(
        "BLB-PAY-101",
        "succeeded",
        state_path=payments_path,
    )

    receipt = build_enriched_receipt(
        sale_id="BLB-SALE-101",
        payment_id="BLB-PAY-101",
        sales_path=sales_path,
        payments_path=payments_path,
    )

    assert receipt["sale_id"] == "BLB-SALE-101"
    assert receipt["items"] == sale["items"]
    assert receipt["totals"]["gross"] == "6.20"
    assert receipt["currency"] == "EUR"
    assert receipt["payment"]["payment_id"] == "BLB-PAY-101"
    assert receipt["payment"]["status"] == "succeeded"


def test_reject_pending_payment_receipt(tmp_path):
    import pytest

    from connector.billsmart_enriched_receipt import (
        build_enriched_receipt,
    )

    sales_path = tmp_path / "sales.json"
    payments_path = tmp_path / "payments.json"

    sale = {
        "schema_version": "0.1",
        "transaction_type": "sale",
        "sale_id": "BLB-SALE-102",
        "currency": "EUR",
        "source": {"type": "simulator"},
        "merchant": {"name": "Café Démonstration"},
        "items": [
            {"name": "Café", "quantity": 2, "unit_price": "2.10"},
            {"name": "Croissant", "quantity": 1, "unit_price": "2.00"},
        ],
        "totals": {"gross": "6.20"},
        "payment": {"amount": "6.20"},
    }

    save_sale(sale, state_path=sales_path)

    save_payment(
        {
            "payment_id": "BLB-PAY-102",
            "sale_id": "BLB-SALE-102",
            "amount": "6.20",
            "currency": "EUR",
            "provider": "sumup",
            "status": "created",
            "provider_checkout_id": None,
        },
        state_path=payments_path,
    )

    update_payment_status(
        "BLB-PAY-102",
        "pending",
        state_path=payments_path,
    )

    with pytest.raises(ValueError, match="Payment is not successful"):
        build_enriched_receipt(
            sale_id="BLB-SALE-102",
            payment_id="BLB-PAY-102",
            sales_path=sales_path,
            payments_path=payments_path,
        )

    assert (
        __import__(
            "connector.billsmart_payment_registry",
            fromlist=["load_payment"],
        ).load_payment(
            "BLB-PAY-102",
            state_path=payments_path,
        )["status"]
        == "pending"
    )


def test_reject_payment_belonging_to_another_sale(tmp_path):
    import pytest

    from connector.billsmart_enriched_receipt import (
        build_enriched_receipt,
    )
    from connector.billsmart_payment_registry import load_payment

    sales_path = tmp_path / "sales.json"
    payments_path = tmp_path / "payments.json"

    sale = {
        "schema_version": "0.1",
        "transaction_type": "sale",
        "sale_id": "BLB-SALE-103",
        "currency": "EUR",
        "source": {"type": "simulator"},
        "merchant": {"name": "Café Démonstration"},
        "items": [
            {"name": "Café", "quantity": 2, "unit_price": "2.10"},
            {"name": "Croissant", "quantity": 1, "unit_price": "2.00"},
        ],
        "totals": {"gross": "6.20"},
        "payment": {"amount": "6.20"},
    }

    save_sale(sale, state_path=sales_path)

    save_payment(
        {
            "payment_id": "BLB-PAY-103",
            "sale_id": "BLB-SALE-OTHER",
            "amount": "6.20",
            "currency": "EUR",
            "provider": "sumup",
            "status": "created",
            "provider_checkout_id": None,
        },
        state_path=payments_path,
    )

    update_payment_status(
        "BLB-PAY-103", "pending", state_path=payments_path
    )
    update_payment_status(
        "BLB-PAY-103", "succeeded", state_path=payments_path
    )

    with pytest.raises(
        ValueError,
        match="Payment does not belong to this sale",
    ):
        build_enriched_receipt(
            sale_id="BLB-SALE-103",
            payment_id="BLB-PAY-103",
            sales_path=sales_path,
            payments_path=payments_path,
        )

    assert load_payment(
        "BLB-PAY-103", state_path=payments_path
    )["status"] == "succeeded"


def test_reject_payment_amount_mismatch(tmp_path):
    import pytest

    from connector.billsmart_enriched_receipt import (
        build_enriched_receipt,
    )
    from connector.billsmart_payment_registry import load_payment

    sales_path = tmp_path / "sales.json"
    payments_path = tmp_path / "payments.json"

    sale = {
        "schema_version": "0.1",
        "transaction_type": "sale",
        "sale_id": "BLB-SALE-104",
        "currency": "EUR",
        "source": {"type": "simulator"},
        "merchant": {"name": "Café Démonstration"},
        "items": [
            {"name": "Café", "quantity": 2, "unit_price": "2.10"},
            {"name": "Croissant", "quantity": 1, "unit_price": "2.00"},
        ],
        "totals": {"gross": "6.20"},
        "payment": {"amount": "6.20"},
    }

    save_sale(sale, state_path=sales_path)

    save_payment(
        {
            "payment_id": "BLB-PAY-104",
            "sale_id": "BLB-SALE-104",
            "amount": "6.30",
            "currency": "EUR",
            "provider": "sumup",
            "status": "created",
            "provider_checkout_id": None,
        },
        state_path=payments_path,
    )

    update_payment_status(
        "BLB-PAY-104",
        "pending",
        state_path=payments_path,
    )
    update_payment_status(
        "BLB-PAY-104",
        "succeeded",
        state_path=payments_path,
    )

    with pytest.raises(ValueError, match="Payment amount mismatch"):
        build_enriched_receipt(
            sale_id="BLB-SALE-104",
            payment_id="BLB-PAY-104",
            sales_path=sales_path,
            payments_path=payments_path,
        )

    assert load_payment(
        "BLB-PAY-104",
        state_path=payments_path,
    )["status"] == "succeeded"
