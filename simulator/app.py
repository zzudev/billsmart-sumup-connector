"""Local web interface for the BillSmart Transaction Simulator."""

import json
from pathlib import Path
from uuid import uuid4

from flask import Flask, render_template_string, request

from connector.billsmart_simulated_payment import confirm_simulated_payment
from connector.billsmart_payment_link import create_payment_for_sale
from connector.billsmart_sale_registry import save_sale
from connector.billsmart_transaction import (
    calculate_gross_total,
    validate_transaction,
)

app = Flask(__name__)

SALES_PATH = Path("runtime/state/simulator_sales.json")
PAYMENTS_PATH = Path("runtime/state/simulator_payments.json")

EXAMPLE_SALE = {
    "schema_version": "0.1",
    "transaction_type": "sale",
    "sale_id": "BLB-SIM-001",
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

PAGE = """
<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>BillSmart Transaction Simulator</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 850px;
           margin: 40px auto; padding: 0 20px; }
    textarea { width: 100%; height: 370px; box-sizing: border-box;
               font-family: monospace; font-size: 14px; }
    button { padding: 12px 24px; margin-top: 15px;
             margin-right: 10px; cursor: pointer; }
    .result { margin-top: 20px; padding: 15px; background: #eef5ff;
              white-space: pre-wrap; }
    .error { background: #ffeaea; }
  </style>
</head>
<body>
  <h1>BillSmart Transaction Simulator</h1>
  <p>Mode développement — aucun paiement réel.</p>

  <form method="post">
    <label for="sale_json">Vente BillSmart (JSON)</label>
    <textarea id="sale_json" name="sale_json">{{ sale_json }}</textarea>

    <button type="submit" name="action" value="validate">
      VALIDER LA VENTE
    </button>

    <button type="submit" name="action" value="pay">
      PAYER — SIMULATION
    </button>
  </form>

  {% if message %}
    <div class="result {% if error %}error{% endif %}">
      {{ message }}
    </div>
  {% endif %}

  {% if payment_id and not error %}
    <form method="post">
      <input type="hidden" name="action" value="confirm">
      <input type="hidden" name="payment_id" value="{{ payment_id }}">
      <button type="submit">CONFIRMER — SIMULATION</button>
    </form>
  {% endif %}

  {% if receipt %}
    <h2>Ticket BillSmart — SIMULATION</h2>
    <pre>{{ receipt }}</pre>
  {% endif %}
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    sale_json = json.dumps(EXAMPLE_SALE, indent=2, ensure_ascii=False)
    message = None
    error = False
    payment_id = None
    receipt = None

    if request.method == "POST":
        sale_json = request.form.get("sale_json", "")

        try:
            action = request.form.get("action", "validate")

            if action == "confirm":
                payment_id = request.form.get("payment_id", "")
                ticket = confirm_simulated_payment(
                    payment_id=payment_id,
                    sales_path=SALES_PATH,
                    payments_path=PAYMENTS_PATH,
                )
                receipt = json.dumps(
                    ticket, indent=2, ensure_ascii=False
                )
                message = (
                    "Paiement confirmé — SIMULATION UNIQUEMENT.\n"
                    f"Paiement : {payment_id}\n"
                    "Aucune transaction bancaire effectuée."
                )
            else:
                sale = json.loads(sale_json)
                validate_transaction(sale)
                total = calculate_gross_total(sale)

            if action == "validate":
                message = f"Vente valide — Total : {total} {sale['currency']}"

            elif action == "pay":
                save_sale(sale, state_path=SALES_PATH)

                payment_id = f"BLB-PAY-{uuid4().hex[:12]}"

                payment = create_payment_for_sale(
                    sale_id=sale["sale_id"],
                    payment_id=payment_id,
                    provider="simulator",
                    sales_path=SALES_PATH,
                    payments_path=PAYMENTS_PATH,
                )

                payment_id = payment["payment_id"]
                message = (
                    "Vente enregistrée.\n"
                    f"Vente : {sale['sale_id']}\n"
                    f"Paiement : {payment['payment_id']}\n"
                    f"Montant : {payment['amount']} {payment['currency']}\n"
                    f"État : {payment['status']}\n"
                    "Aucun paiement réel effectué."
                )

            elif action != "confirm":
                raise ValueError("Action inconnue.")

        except (ValueError, TypeError, AttributeError) as exc:
            message = f"Opération refusée : {exc}"
            error = True

    return render_template_string(
        PAGE,
        sale_json=sale_json,
        message=message,
        error=error,
        payment_id=payment_id,
        receipt=receipt,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=False)
