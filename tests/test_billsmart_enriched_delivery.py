from pathlib import Path
from unittest.mock import patch

import pytest

from connector.billsmart_enriched_delivery import prepare_enriched_delivery


def sample_receipt(provider="simulator"):
    return {
        "schema_version": "0.1",
        "transaction_type": "sale",
        "sale_id": "BLB-TEST-001",
        "currency": "EUR",
        "source": {"type": "simulator"},
        "merchant": {"name": "Café Démonstration"},
        "items": [
            {"name": "Café", "quantity": 2, "unit_price": "2.10"},
            {"name": "Croissant", "quantity": 1, "unit_price": "2.00"},
        ],
        "totals": {"gross": "6.20"},
        "payment": {
            "payment_id": "BLB-PAY-TEST",
            "provider": provider,
            "status": "succeeded",
            "amount": "6.20",
            "currency": "EUR",
        },
    }


@patch("connector.billsmart_enriched_delivery.build_enriched_receipt")
def test_prepare_generates_csv_without_delivery(build_receipt, tmp_path):
    build_receipt.return_value = sample_receipt()

    result = prepare_enriched_delivery(
        sale_id="BLB-TEST-001",
        payment_id="BLB-PAY-TEST",
        sales_path=tmp_path / "sales.json",
        payments_path=tmp_path / "payments.json",
        output_dir=tmp_path,
    )

    assert result["transaction_id"] == "BLB-SIM:BLB-PAY-TEST"
    assert result["csv_path"].is_file()

    content = result["csv_path"].read_text(encoding="utf-8")
    assert "Café" in content
    assert "Croissant" in content


@patch("connector.billsmart_enriched_delivery.build_enriched_receipt")
def test_prepare_rejects_non_simulator_provider(build_receipt, tmp_path):
    build_receipt.return_value = sample_receipt(provider="sumup")

    with pytest.raises(ValueError, match="simulator"):
        prepare_enriched_delivery(
            sale_id="BLB-TEST-001",
            payment_id="BLB-PAY-TEST",
            sales_path=tmp_path / "sales.json",
            payments_path=tmp_path / "payments.json",
            output_dir=tmp_path,
        )

    assert list(tmp_path.glob("*.csv")) == []


@patch("connector.billsmart_enriched_delivery.build_enriched_receipt")
def test_prepare_rejects_unsafe_payment_id(build_receipt, tmp_path):
    build_receipt.return_value = sample_receipt()

    with pytest.raises(ValueError, match="Invalid payment identifier"):
        prepare_enriched_delivery(
            sale_id="BLB-TEST-001",
            payment_id="../unsafe",
            sales_path=tmp_path / "sales.json",
            payments_path=tmp_path / "payments.json",
            output_dir=tmp_path,
        )

    assert list(tmp_path.glob("*.csv")) == []


@patch("connector.billsmart_enriched_delivery.build_enriched_receipt")
def test_simulated_delivery_calls_fake_only(build_receipt, tmp_path):
    from unittest.mock import Mock

    from connector.billsmart_enriched_delivery import (
        simulate_enriched_delivery,
    )

    build_receipt.return_value = sample_receipt()

    fake_delivery = Mock(return_value={
        "ok": True,
        "already_processed": False,
        "receipt": {"receipt_id": 42},
        "edge": {"ok": True},
    })

    state_path = tmp_path / "simulator_deliveries.json"

    result = simulate_enriched_delivery(
        sale_id="BLB-TEST-001",
        payment_id="BLB-PAY-TEST",
        sales_path=tmp_path / "sales.json",
        payments_path=tmp_path / "payments.json",
        delivery_func=fake_delivery,
        output_dir=tmp_path,
        state_path=state_path,
    )

    fake_delivery.assert_called_once_with(
        "BLB-SIM:BLB-PAY-TEST",
        tmp_path / "billsmart_BLB-PAY-TEST.csv",
        state_path=state_path,
    )

    assert result["csv_path"].is_file()
    assert result["delivery_result"]["receipt"]["receipt_id"] == 42
    assert not state_path.exists()
