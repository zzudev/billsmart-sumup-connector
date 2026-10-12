import tempfile
from pathlib import Path

from connector.billsmart_sale_registry import (
    load_sale,
    save_sale,
)


def test_sale_is_persisted_and_reloaded():
    sale = {
        "schema_version": "0.1",
        "transaction_type": "sale",
        "sale_id": "BLB-TEST-0001",
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
            }
        ],
        "totals": {"gross": "5.00"},
        "payment": {
            "status": "pending",
            "amount": "5.00",
            "method": None,
            "provider": None,
            "provider_transaction_id": None,
        },
        "metadata": {},
    }

    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "sales.json"

        save_sale(sale, state_path=state_path)

        restored = load_sale(
            "BLB-TEST-0001",
            state_path=state_path,
        )

        assert restored == sale


def test_duplicate_sale_is_rejected():
    from copy import deepcopy

    from connector.billsmart_sale_registry import save_sale

    sale = {
        "schema_version": "0.1",
        "transaction_type": "sale",
        "sale_id": "BLB-DUPLICATE-0001",
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
                "quantity": 1,
                "unit_price": "2.50",
            }
        ],
        "totals": {"gross": "2.50"},
        "payment": {
            "status": "pending",
            "amount": "2.50",
            "method": None,
            "provider": None,
            "provider_transaction_id": None,
        },
        "metadata": {},
    }

    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "sales.json"

        save_sale(sale, state_path=state_path)

        duplicate = deepcopy(sale)

        import pytest

        with pytest.raises(
            ValueError,
            match="Vente BillSmart déjà enregistrée",
        ):
            save_sale(duplicate, state_path=state_path)

        assert load_sale(
            "BLB-DUPLICATE-0001",
            state_path=state_path,
        ) == sale


def test_invalid_sale_is_not_persisted():
    import pytest

    from connector.billsmart_transaction import (
        BillSmartTransactionError,
    )

    sale = {
        "schema_version": "0.1",
        "transaction_type": "sale",
        "sale_id": "BLB-INVALID-0001",
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
            }
        ],
        "totals": {"gross": "6.00"},
        "payment": {
            "status": "pending",
            "amount": "6.00",
            "method": None,
            "provider": None,
            "provider_transaction_id": None,
        },
        "metadata": {},
    }

    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "sales.json"

        with pytest.raises(
            BillSmartTransactionError,
            match="Gross total mismatch",
        ):
            save_sale(sale, state_path=state_path)

        assert load_sale(
            "BLB-INVALID-0001",
            state_path=state_path,
        ) is None

        assert not state_path.exists()
