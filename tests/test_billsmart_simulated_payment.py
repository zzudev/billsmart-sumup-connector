"""Tests for the isolated BillSmart simulated payment flow."""

from copy import deepcopy

import pytest

from connector.billsmart_payment_link import create_payment_for_sale
from connector.billsmart_payment_registry import (
    load_payment,
    update_payment_status,
)
from connector.billsmart_sale_registry import save_sale
from connector.billsmart_simulated_payment import confirm_simulated_payment
from simulator.app import EXAMPLE_SALE


def prepare_payment(tmp_path, provider="simulator"):
    sales_path = tmp_path / "sales.json"
    payments_path = tmp_path / "payments.json"

    save_sale(deepcopy(EXAMPLE_SALE), state_path=sales_path)

    payment = create_payment_for_sale(
        sale_id="BLB-SIM-001",
        payment_id="BLB-PAY-TEST-001",
        provider=provider,
        sales_path=sales_path,
        payments_path=payments_path,
    )

    return sales_path, payments_path, payment


def test_simulated_payment_builds_detailed_receipt(tmp_path):
    sales_path, payments_path, payment = prepare_payment(tmp_path)

    receipt = confirm_simulated_payment(
        payment_id=payment["payment_id"],
        sales_path=sales_path,
        payments_path=payments_path,
    )

    assert receipt["sale_id"] == "BLB-SIM-001"
    assert receipt["totals"]["gross"] == "6.20"
    assert len(receipt["items"]) == 2
    assert receipt["items"][0]["name"] == "Café"
    assert receipt["items"][0]["quantity"] == 2
    assert receipt["items"][1]["name"] == "Croissant"
    assert receipt["payment"]["provider"] == "simulator"
    assert receipt["payment"]["status"] == "succeeded"

    saved_payment = load_payment(
        payment["payment_id"], state_path=payments_path
    )
    assert saved_payment["status"] == "succeeded"


def test_simulation_refuses_sumup_payment(tmp_path):
    sales_path, payments_path, payment = prepare_payment(
        tmp_path, provider="sumup"
    )

    with pytest.raises(ValueError, match="Only simulator"):
        confirm_simulated_payment(
            payment_id=payment["payment_id"],
            sales_path=sales_path,
            payments_path=payments_path,
        )

    assert load_payment(
        payment["payment_id"], state_path=payments_path
    )["status"] == "created"


def test_simulation_refuses_failed_payment(tmp_path):
    sales_path, payments_path, payment = prepare_payment(tmp_path)

    update_payment_status(
        payment["payment_id"], "pending", state_path=payments_path
    )
    update_payment_status(
        payment["payment_id"], "failed", state_path=payments_path
    )

    with pytest.raises(ValueError, match="cannot be simulated"):
        confirm_simulated_payment(
            payment_id=payment["payment_id"],
            sales_path=sales_path,
            payments_path=payments_path,
        )

    assert load_payment(
        payment["payment_id"], state_path=payments_path
    )["status"] == "failed"


def test_simulation_refuses_amount_mismatch(tmp_path):
    sales_path, payments_path, payment = prepare_payment(tmp_path)

    import json

    payments = json.loads(payments_path.read_text(encoding="utf-8"))
    payments[payment["payment_id"]]["amount"] = "6.30"
    payments_path.write_text(
        json.dumps(payments), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="does not match"):
        confirm_simulated_payment(
            payment_id=payment["payment_id"],
            sales_path=sales_path,
            payments_path=payments_path,
        )

    assert load_payment(
        payment["payment_id"], state_path=payments_path
    )["status"] == "created"
