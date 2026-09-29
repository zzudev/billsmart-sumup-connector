import os
import uuid
from pathlib import Path

import requests
from dotenv import load_dotenv

# Charger la configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

api_key = os.getenv("SUMUP_API_KEY")

if not api_key:
    raise RuntimeError("SUMUP_API_KEY manquante.")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json"
}

# Récupérer le code commerçant
response = requests.get(
    "https://api.sumup.com/v0.1/me",
    headers=headers,
    timeout=15
)

response.raise_for_status()

merchant_code = response.json()["merchant_profile"]["merchant_code"]

# Préparer notre checkout
checkout = {
    "checkout_reference": str(uuid.uuid4()),
    "amount": 12.00,
    "currency": "EUR",
    "merchant_code": merchant_code,
    "description": "Test BillSmart Sandbox",
    "hosted_checkout": {
        "enabled": True
    }
}

# Créer le checkout
response = requests.post(
    "https://api.sumup.com/v0.1/checkouts",
    headers=headers,
    json=checkout,
    timeout=15
)

print("HTTP status:", response.status_code)

if response.ok:
    data = response.json()

    print("Checkout créé avec succès.")
    print("Statut du checkout :", data.get("status"))
    print("Environnement sandbox :", data.get("merchant_sandbox"))
    print("Champs disponibles :", list(data.keys()))
    print("Identifiant du checkout :", data.get("id"))
    print("Hosted Checkout disponible :", bool(data.get("hosted_checkout_url")))
    print("URL Hosted Checkout :", data.get("hosted_checkout_url"))
else:
    print("Échec de la création du checkout.")
    print("Code HTTP :", response.status_code)
