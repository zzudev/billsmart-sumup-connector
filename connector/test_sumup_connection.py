import os
from pathlib import Path

import requests
from dotenv import load_dotenv


# Charger le fichier .env situé à la racine du projet.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Récupérer la clé API sans l'afficher.
api_key = os.getenv("SUMUP_API_KEY")

if not api_key:
    raise RuntimeError("SUMUP_API_KEY is missing from .env")

# Effectuer une requête en lecture seule.
url = "https://api.sumup.com/v0.1/me"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json",
}

try:
    response = requests.get(
        url,
        headers=headers,
        timeout=15,
    )

    print(f"HTTP status: {response.status_code}")

    if response.ok:
        print("SumUp API authentication successful.")

        data = response.json()
        
        merchant_profile = data.get("merchant_profile") or {}
        merchant_code = merchant_profile.get("merchant_code")

        if merchant_code:
            print("Merchant code récupéré avec succès.")
        else:
            print("Merchant code introuvable.")

    else:
        print("SumUp API request failed.")
        print("Check the API key and its permissions.")

except requests.RequestException as exc:
    print(f"Connection error: {type(exc).__name__}")
