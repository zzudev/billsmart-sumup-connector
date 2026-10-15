"""Tests for the BillSmart Transaction Simulator web interface."""

import json

from simulator.app import EXAMPLE_SALE, app


def test_simulator_homepage():
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.get("/")

    assert response.status_code == 200
    assert b"BillSmart Transaction Simulator" in response.data
    assert b"VALIDER LA VENTE" in response.data
    assert b"BLB-SIM-001" in response.data


def test_simulator_validates_example_sale():
    app.config["TESTING"] = True

    with app.test_client() as client:
        response = client.post(
            "/",
            data={
                "sale_json": json.dumps(
                    EXAMPLE_SALE,
                    ensure_ascii=False,
                )
            },
        )

    assert response.status_code == 200
    assert b"6.20 EUR" in response.data


def test_simulator_pay_creates_sale_and_payment(tmp_path, monkeypatch):
    from connector.billsmart_sale_registry import load_sale
    from connector.billsmart_payment_registry import load_payment
    import simulator.app as simulator_module

    sales_path = tmp_path / "sales.json"
    payments_path = tmp_path / "payments.json"

    monkeypatch.setattr(simulator_module, "SALES_PATH", sales_path)
    monkeypatch.setattr(simulator_module, "PAYMENTS_PATH", payments_path)

    with app.test_client() as client:
        response = client.post(
            "/",
            data={
                "sale_json": json.dumps(EXAMPLE_SALE),
                "action": "pay",
            },
        )

    assert response.status_code == 200
    assert b"Vente enregistr" in response.data
    assert b"BLB-SIM-001" in response.data

    sale = load_sale("BLB-SIM-001", state_path=sales_path)
    assert sale is not None
    assert len(sale["items"]) == 2

    payments = json.loads(payments_path.read_text(encoding="utf-8"))
    assert len(payments) == 1

    payment_id = next(iter(payments))
    payment = load_payment(payment_id, state_path=payments_path)

    assert payment["sale_id"] == "BLB-SIM-001"
    assert payment["amount"] == "6.20"
    assert payment["currency"] == "EUR"
    assert payment["provider"] == "simulator"
    assert payment["status"] == "created"


def test_simulator_rejects_invalid_sale_without_persistence(
    tmp_path, monkeypatch
):
    import simulator.app as simulator_module

    sales_path = tmp_path / "sales.json"
    payments_path = tmp_path / "payments.json"

    monkeypatch.setattr(simulator_module, "SALES_PATH", sales_path)
    monkeypatch.setattr(simulator_module, "PAYMENTS_PATH", payments_path)

    invalid_sale = json.loads(json.dumps(EXAMPLE_SALE))
    invalid_sale["totals"]["gross"] = "99.00"

    with app.test_client() as client:
        response = client.post(
            "/",
            data={
                "sale_json": json.dumps(invalid_sale),
                "action": "pay",
            },
        )

    assert response.status_code == 200
    assert b"Op" in response.data
    assert not sales_path.exists()
    assert not payments_path.exists()


def test_simulator_web_confirmation_builds_receipt(tmp_path, monkeypatch):
    """The web flow confirms a simulated payment and displays its receipt."""
    import re
    import simulator.app as simulator_module
    from connector.billsmart_payment_registry import load_payment

    sales_path = tmp_path / "sales.json"
    payments_path = tmp_path / "payments.json"

    monkeypatch.setattr(simulator_module, "SALES_PATH", sales_path)
    monkeypatch.setattr(simulator_module, "PAYMENTS_PATH", payments_path)

    with app.test_client() as client:
        created = client.post(
            "/",
            data={
                "sale_json": json.dumps(EXAMPLE_SALE),
                "action": "pay",
            },
        )

        assert created.status_code == 200
        assert b"CONFIRMER" in created.data

        match = re.search(rb"BLB-PAY-[0-9a-f]{12}", created.data)
        assert match is not None
        payment_id = match.group().decode()

        confirmed = client.post(
            "/",
            data={
                "action": "confirm",
                "payment_id": payment_id,
            },
        )

    assert confirmed.status_code == 200
    assert b"Ticket BillSmart" in confirmed.data
    assert "Café".encode() in confirmed.data
    assert b"Croissant" in confirmed.data
    assert b"6.20" in confirmed.data
    assert b"succeeded" in confirmed.data

    payment = load_payment(payment_id, state_path=payments_path)
    assert payment["status"] == "succeeded"
    assert payment["provider"] == "simulator"
