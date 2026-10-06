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

me_response = requests.get(
    "https://api.sumup.com/v0.1/me",
    headers=headers,
)
me_response.raise_for_status()

merchant_code = me_response.json()["merchant_profile"]["merchant_code"]

readers_url = (
    f"https://api.sumup.com/v0.1/merchants/"
    f"{merchant_code}/readers"
)

readers_response = requests.get(
    readers_url,
    headers=headers,
)
readers_response.raise_for_status()

physical_solos = [
    reader
    for reader in readers_response.json().get("items", [])
    if (reader.get("device") or {}).get("model") == "solo"
]

if len(physical_solos) != 1:
    raise RuntimeError(
        "Impossible d'identifier un unique Solo physique."
    )

reader = physical_solos[0]
reader_id = reader["id"]

print("Solo physique identifié :", reader.get("name"))
print("État :", reader.get("status"))

checkout_url = (
    f"https://api.sumup.com/v0.1/merchants/"
    f"{merchant_code}/readers/{reader_id}/checkout"
)

payload = {
    "total_amount": {
        "currency": "EUR",
        "minor_unit": 2,
        "value": 100,
    }
}

print("Checkout physique préparé : 1.00 EUR.")

checkout_response = requests.post(
    checkout_url,
    headers=headers,
    json=payload,
)

print("HTTP status :", checkout_response.status_code)

if checkout_response.ok:
    print("Checkout envoyé au Solo physique.")
else:
    print("Échec de création du checkout.")
    print(checkout_response.text)
