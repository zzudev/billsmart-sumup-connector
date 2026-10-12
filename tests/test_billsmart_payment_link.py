import tempfile
from pathlib import Path

from connector.billsmart_sale_registry import save_sale
from connector.billsmart_payment_link import create_payment_for_sale


def test_payment_is_linked_to_existing_sale():
    sale = {
        "schema_version": "0.1",
        "transaction_type": "sale",
        "sale_id": "BLB-SALE-001",
        "currency": "EUR",
        "source": {"type": "billsmart_simulator"},
        "merchant": {"merchant_id": "BLB-DEMO"},
        "items": [
            {
                "reference": "CAFE",
                "label": "Café",
                "quantity": 2,
                "unit_price": "2.50",
            }
        ],
        "totals": {"gross": "5.00"},
        "payment": {"status": "pending", "amount": "5.00"},
    }

    with tempfile.TemporaryDirectory() as tmp:
        sales_path = Path(tmp) / "sales.json"
        payments_path = Path(tmp) / "payments.json"

        save_sale(sale, state_path=sales_path)

        payment = create_payment_for_sale(
            sale_id="BLB-SALE-001",
            payment_id="BLB-PAY-001",
            provider="sumup",
            sales_path=sales_path,
            payments_path=payments_path,
        )

        assert payment["sale_id"] == sale["sale_id"]
        assert payment["amount"] == "5.00"
        assert payment["currency"] == "EUR"
        assert payment["status"] == "created"


def test_payment_rejected_when_sale_does_not_exist():
    import pytest

    with tempfile.TemporaryDirectory() as tmp:
        sales_path = Path(tmp) / "sales.json"
        payments_path = Path(tmp) / "payments.json"

        with pytest.raises(
            ValueError,
            match="BillSmart sale not found",
        ):
            create_payment_for_sale(
                sale_id="BLB-UNKNOWN-001",
                payment_id="BLB-PAY-UNKNOWN-001",
                provider="sumup",
                sales_path=sales_path,
                payments_path=payments_path,
            )

        assert not payments_path.exists()


def test_payment_rejected_when_stored_sale_is_inconsistent():
    import json
    import pytest

    with tempfile.TemporaryDirectory() as tmp:
        sales_path = Path(tmp) / "sales.json"
        payments_path = Path(tmp) / "payments.json"

        sale = {
            "schema_version": "0.1",
            "transaction_type": "sale",
            "sale_id": "BLB-SALE-INVALID",
            "currency": "EUR",
            "source": {"type": "billsmart_simulator"},
            "merchant": {"merchant_id": "BLB-DEMO"},
            "items": [
                {
                    "label": "Café",
                    "quantity": 2,
                    "unit_price": "2.50",
                }
            ],
            "totals": {"gross": "6.00"},
            "payment": {"amount": "6.00"},
        }

        sales_path.write_text(
            json.dumps({sale["sale_id"]: sale}),
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="Gross total mismatch"):
            create_payment_for_sale(
                sale_id="BLB-SALE-INVALID",
                payment_id="BLB-PAY-INVALID",
                provider="sumup",
                sales_path=sales_path,
                payments_path=payments_path,
            )

        assert not payments_path.exists()
