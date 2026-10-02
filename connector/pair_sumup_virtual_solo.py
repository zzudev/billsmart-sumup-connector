import os

import requests
from dotenv import load_dotenv


load_dotenv()

SUMUP_API_KEY = os.getenv("SUMUP_API_KEY")

if not SUMUP_API_KEY:
    raise RuntimeError("SUMUP_API_KEY absente du fichier .env")

headers = {
    "Authorization": f"Bearer {SUMUP_API_KEY}",
    "Content-Type": "application/json",
}

# Récupération du profil marchand SumUp
me_response = requests.get(
    "https://api.sumup.com/v0.1/me",
    headers=headers,
)

me_response.raise_for_status()

merchant_code = me_response.json()["merchant_profile"]["merchant_code"]

print("Merchant code récupéré avec succès.")

pairing_code = input("Saisis le pairing code affiché par Virtual Solo : ").strip()

if not pairing_code:
    raise RuntimeError("Pairing code manquant")

create_reader_url = (
    f"https://api.sumup.com/v0.1/merchants/{merchant_code}/readers"
)

payload = {
    "name": "BillSmart Virtual Solo",
    "pairing_code": pairing_code,
}

reader_response = requests.post(
    create_reader_url,
    headers=headers,
    json=payload,
)

print("HTTP status :", reader_response.status_code)
print("Réponse :", reader_response.text)