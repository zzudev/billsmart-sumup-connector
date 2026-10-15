import csv
from copy import deepcopy

import pytest

from connector.billsmart_enriched_csv import build_enriched_csv


def sample_receipt():
    return {
        "schema_version": "0.1",
        "transaction_type": "sale",
        "sale_id": "BLB-TEST-CSV-001",
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
            "provider": "simulator",
            "status": "succeeded",
            "amount": "6.20",
            "currency": "EUR",
        },
    }


def test_csv_preserves_items(tmp_path):
    output = tmp_path / "ticket.csv"
    result = build_enriched_csv(sample_receipt(), output_path=output)

    assert result == output

    with output.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows == [
        {
            "reference": "BLB001",
            "designation": "Café",
            "quantite": "2",
            "prix_unitaire": "2.10",
        },
        {
            "reference": "BLB002",
            "designation": "Croissant",
            "quantite": "1",
            "prix_unitaire": "2.00",
        },
    ]


def test_csv_rejects_unconfirmed_payment(tmp_path):
    receipt = sample_receipt()
    receipt["payment"]["status"] = "pending"

    with pytest.raises(ValueError):
        build_enriched_csv(receipt, output_path=tmp_path / "ticket.csv")


def test_csv_rejects_missing_designation(tmp_path):
    receipt = sample_receipt()
    receipt["items"][0]["name"] = ""

    with pytest.raises(ValueError):
        build_enriched_csv(receipt, output_path=tmp_path / "ticket.csv")


def test_csv_rejects_excessive_price_precision(tmp_path):
    receipt = sample_receipt()
    receipt["items"][0]["unit_price"] = "2.105"
    receipt["totals"]["gross"] = "6.21"
    receipt["payment"]["amount"] = "6.21"

    with pytest.raises(ValueError):
        build_enriched_csv(receipt, output_path=tmp_path / "ticket.csv")
