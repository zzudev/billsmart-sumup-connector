import os
from pathlib import Path

import requests
from dotenv import load_dotenv

from connector.billsmart_csv import build_billsmart_csv
from connector.idempotency import is_transaction_processed
from connector.receipt_delivery import deliver_receipt


STATE_PATH = Path("runtime/state/processed_transactions.json")

load_dotenv()

SUMUP_API_KEY = os.getenv("SUMUP_API_KEY")

if not SUMUP_API_KEY:
    raise RuntimeError("SUMUP_API_KEY absente du fichier .env")

headers = {
    "Authorization": f"Bearer {SUMUP_API_KEY}",
    "Content-Type": "application/json",
}

print("Configuration SumUp chargée avec succès.")

# Récupération du profil marchand SumUp
me_response = requests.get(
    "https://api.sumup.com/v0.1/me",
    headers=headers,
)

me_response.raise_for_status()

merchant_profile = me_response.json()["merchant_profile"]
merchant_code = merchant_profile["merchant_code"]

print("Profil marchand récupéré avec succès.")

# Récupération de l'historique des transactions
transactions_url = (
    f"https://api.sumup.com/v2.1/merchants/"
    f"{merchant_code}/transactions/history"
)

history_response = requests.get(
    transactions_url,
    headers=headers,
    params={"limit": 20},
)

history_response.raise_for_status()

transactions = history_response.json().get("items", [])

print("Historique récupéré avec succès.")
print("Nombre de transactions :", len(transactions))

# Sélection des transactions POS
pos_transactions = [
    transaction
    for transaction in transactions
    if transaction.get("payment_type") == "POS"
]

if not pos_transactions:
    raise RuntimeError("Aucune transaction POS trouvée.")

# Sélection de la transaction POS la plus récente
latest_pos_transaction = max(
    pos_transactions,
    key=lambda transaction: transaction.get("timestamp", ""),
)

print("Transaction POS la plus récente sélectionnée.")
print("Montant :", latest_pos_transaction.get("amount"))
print("Type de paiement :", latest_pos_transaction.get("payment_type"))
print("Mode d'entrée :", latest_pos_transaction.get("entry_mode"))

transaction_id = latest_pos_transaction.get("id")

if not transaction_id:
    raise RuntimeError("Identifiant de transaction absent.")

if is_transaction_processed(
    transaction_id,
    state_path=STATE_PATH,
):
    print("Transaction SumUp déjà traitée. Aucun nouveau ticket créé.")
    raise SystemExit(0)

transaction_details_url = (
    f"https://api.sumup.com/v2.1/merchants/"
    f"{merchant_code}/transactions"
)

details_response = requests.get(
    transaction_details_url,
    headers=headers,
    params={"id": transaction_id},
)

details_response.raise_for_status()

transaction_details = details_response.json()

products = transaction_details.get("products", [])

print("Détails de la transaction récupérés avec succès.")
print("Nombre de produits :", len(products))


ticket_items = []

for product in products:
    ticket_item = {
        "price": product.get("price", 0.0),
        "quantity": product.get("quantity", 0),
        "total_price": product.get("total_price", 0.0),
        "total_with_vat": product.get("total_with_vat", 0.0),
        "vat_amount": product.get("vat_amount", 0.0),
    }

    ticket_items.append(ticket_item)

print("Lignes du ticket BillSmart créées :", len(ticket_items))

merchant_data = {
    "company_name": merchant_profile.get("company_name"),
    "doing_business_as": merchant_profile.get("doing_business_as"),
    "address": {
        "address_line1": merchant_profile.get("address", {}).get("address_line1"),
        "post_code": merchant_profile.get("address", {}).get("post_code"),
        "city": merchant_profile.get("address", {}).get("city"),
        "country": merchant_profile.get("address", {}).get("country"),
    },
    "country": merchant_profile.get("country"),
    "currency": merchant_profile.get("default_currency"),
}

print("Données marchand préparées pour le ticket BillSmart.")


billsmart_ticket = {
    "merchant": merchant_data,
    "transaction": {
        "timestamp": transaction_details.get("timestamp"),
        "currency": transaction_details.get("currency"),
        "payment_type": transaction_details.get("payment_type"),
        "entry_mode": transaction_details.get("entry_mode"),
        "status": transaction_details.get("status"),
    },
    "items": ticket_items,
    "totals": {
        "amount": transaction_details.get("amount", 0.0),
        "vat_amount": transaction_details.get("vat_amount", 0.0),
        "tip_amount": transaction_details.get("tip_amount", 0.0),
    },
}

print("Objet ticket BillSmart construit avec succès.")


merchant = billsmart_ticket["merchant"]
transaction = billsmart_ticket["transaction"]
items = billsmart_ticket["items"]
totals = billsmart_ticket["totals"]

print("\n" + "=" * 40)
print("TICKET BILLSMART")
print("=" * 40)

# En-tête marchand
print(merchant.get("doing_business_as") or merchant.get("company_name") or "Commerçant")

if (
    merchant.get("doing_business_as")
    and merchant.get("company_name")
    and merchant["doing_business_as"] != merchant["company_name"]
):
    print(merchant["company_name"])

address = merchant.get("address", {})

address_line1 = address.get("address_line1")
post_code = address.get("post_code")
city = address.get("city")
country = address.get("country")

if address_line1:
    print(address_line1)

city_line = " ".join(
    str(value)
    for value in [post_code, city]
    if value
)

if city_line:
    print(city_line)

if country:
    print(country)

print("-" * 40)

# Lignes du ticket
for index, item in enumerate(items, start=1):
    print(f"Article {index}")
    print(f"  Quantité : {item['quantity']}")
    print(f"  Prix      : {item['price']:.2f} €")
    print(f"  Total     : {item['total_with_vat']:.2f} €")
    print(f"  TVA       : {item['vat_amount']:.2f} €")

print("-" * 40)

# Totaux
print(f"TOTAL : {totals['amount']:.2f} €")
print(f"TVA   : {totals['vat_amount']:.2f} €")

print("-" * 40)

print(f"Paiement : {transaction['payment_type']}")
print(f"Entrée   : {transaction['entry_mode']}")
print(f"Statut   : {transaction['status']}")

print("=" * 40)

# Génération du CSV compatible avec BSM1
output_csv_path = build_billsmart_csv(ticket_items)

print(f"CSV BSM1 généré avec succès : {output_csv_path}")

delivery_result = deliver_receipt(
    transaction_id,
    output_csv_path,
    state_path=STATE_PATH,
)

receipt = delivery_result.get("receipt")
edge = delivery_result.get("edge", {})

if not receipt:
    raise RuntimeError(
        "BSM1 n'a pas confirmé la création du ticket."
    )

print(
    "Ticket BillSmart créé avec succès."
    f" ID : {receipt['receipt_id']}"
)

if edge.get("ok"):
    print("Affichage BSM5 demandé avec succès.")
else:
    print(
        "Ticket créé, mais l'affichage BSM5 a échoué."
        " Le ticket ne sera pas recréé."
    )
