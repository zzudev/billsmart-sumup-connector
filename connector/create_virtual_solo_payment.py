import os

import requests
from dotenv import load_dotenv


load_dotenv()

SUMUP_API_KEY = os.getenv("SUMUP_API_KEY")
SUMUP_READER_ID = os.getenv("SUMUP_READER_ID")

if not SUMUP_API_KEY:
    raise RuntimeError("SUMUP_API_KEY absente du fichier .env")

if not SUMUP_READER_ID:
    raise RuntimeError("SUMUP_READER_ID absent du fichier .env")

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

merchant_code = me_response.json()["merchant_profile"]["merchant_code"]

print("Merchant code récupéré avec succès.")

checkout_url = (
    f"https://api.sumup.com/v0.1/merchants/"
    f"{merchant_code}/readers/{SUMUP_READER_ID}/checkout"
)

payload = {
    "total_amount": {
        "currency": "EUR",
        "minor_unit": 2,
        "value": 1200,
    }
}

print("Checkout Virtual Solo préparé.")

checkout_response = requests.post(
    checkout_url,
    headers=headers,
    json=payload,
)

print("HTTP status :", checkout_response.status_code)
print("Réponse :", checkout_response.text)