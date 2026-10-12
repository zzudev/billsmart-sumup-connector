"""Persistence of BillSmart sales before payment."""

import json
from pathlib import Path

from connector.billsmart_transaction import validate_transaction


DEFAULT_SALES_PATH = Path("runtime/state/billsmart_sales.json")


def load_sale(sale_id, *, state_path=DEFAULT_SALES_PATH):
    """Retrieve a previously saved BillSmart sale."""
    path = Path(state_path)

    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as f:
        sales = json.load(f)

    if not isinstance(sales, dict):
        raise ValueError("Registre des ventes BillSmart invalide.")

    return sales.get(sale_id)


def save_sale(sale, *, state_path=DEFAULT_SALES_PATH):
    """Validate and persist a BillSmart sale."""
    validate_transaction(sale)

    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            sales = json.load(f)

        if not isinstance(sales, dict):
            raise ValueError("Registre des ventes BillSmart invalide.")
    else:
        sales = {}

    sale_id = sale["sale_id"]

    if sale_id in sales:
        raise ValueError(
            f"Vente BillSmart déjà enregistrée : {sale_id}"
        )

    sales[sale_id] = sale

    temporary_path = path.with_suffix(".tmp")

    with temporary_path.open("w", encoding="utf-8") as f:
        json.dump(
            sales,
            f,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )

    temporary_path.replace(path)
