import os

from pathlib import Path

import requests
from dotenv import load_dotenv

# Charger notre configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

api_key = os.getenv("SUMUP_API_KEY")

if not api_key:
    raise RuntimeError("SUMUP_API_KEY est manquante.")

# Préparer l'authentification
headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json"
}

# Récupérer le profil du commerçant
response = requests.get(
    "https://api.sumup.com/v0.1/me",
    headers=headers,
    timeout=15
)

response.raise_for_status()

merchant_code = response.json()["merchant_profile"]["merchant_code"]

# Construire l'URL de l'API Transactions
url = (
    f"https://api.sumup.com/v2.1/merchants/"
    f"{merchant_code}/transactions/history"
)

print("URL de l'API Transactions construite avec succès.")

# Interroger l'API Transactions
params = {
    "limit": 10
}


#Appel de l'API SUMUP

response = requests.get(
    url,
    headers=headers,
    params=params,
    timeout=15
)

print("HTTP status:", response.status_code)

if response.ok:
    data = response.json()
    print("Type de réponse :", type(data).__name__)

    if isinstance(data, dict):
        print("Champs disponibles :", list(data.keys()))

        transactions = data.get("items", [])

        print("Nombre de transactions :", len(transactions))

        for index, transaction in enumerate(transactions):
            print(
                f"Transaction {index} :",
                "amount =", transaction.get("amount"),
                "| payment_type =", transaction.get("payment_type"),
                "| entry_mode =", transaction.get("entry_mode"),
                "| timestamp =", transaction.get("timestamp"),
            )

        if transactions:
            print(
                "Champs de la première transaction :",
                list(transactions[0].keys())
            )
            transaction = next(
                (
                    transaction
                    for transaction in transactions
                    if transaction.get("payment_type") == "POS"
                ),
                None,
            )

            if transaction is None:
                raise RuntimeError("Aucune transaction POS trouvée.")

            print("Transaction POS sélectionnée.")

            transaction_id = transaction.get("id")

            if transaction_id:
                print("Identifiant de transaction récupéré avec succès.")
                # Récupérer les détails de la transaction
                details_url = (
                    f"https://api.sumup.com/v2.1/merchants/"
                    f"{merchant_code}/transactions"
                )

                details_response = requests.get(
                    details_url,
                    headers=headers,
                    params={"id": transaction_id},
                    timeout=15
                )

                print("HTTP détails :", details_response.status_code)

                if details_response.ok:
                    details = details_response.json()
                    print("Champs détaillés :", list(details.keys()))
                    print("Type de paiement :", details.get("payment_type"))
                    products = details.get("products") or []

                    print("Type du champ products :", type(products).__name__)
                    print("Nombre de produits :", len(products))

                    if products:
                        print("Champs du premier produit :", list(products[0].keys()))
                        print("Premier produit :", products[0])
                    else:
                        print("Aucun produit détaillé disponible.")

                    # Récupérer le reçu associé à la transaction
                    receipt_url = (
                        f"https://api.sumup.com/v1.1/receipts/{transaction_id}"
                    )

                    receipt_response = requests.get(
                        receipt_url,
                        headers=headers,
                        params={"mid": merchant_code},
                        timeout=15
                    )

                    print("HTTP reçu :", receipt_response.status_code)

                    if receipt_response.ok:
                        receipt = receipt_response.json()

                        print("Champs du reçu :", list(receipt.keys()))

                        transaction_data = receipt.get("transaction_data") or {}
                        products = transaction_data.get("products") or []

                        print("Nombre de produits dans le reçu :", len(products))
                    else:
                        print("Échec de récupération du reçu.")

                else:
                    print("Échec de récupération des détails.")

            else:
                print("Identifiant de transaction introuvable.")

        else:
            print("Aucune transaction disponible.")

    elif isinstance(data, list):
        print("Nombre de transactions :", len(data))

else:
    print("Échec de la récupération des transactions.")
