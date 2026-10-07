import requests


SUMUP_API_BASE_URL = "https://api.sumup.com"


def build_headers(api_key):
    """Build HTTP headers for the SumUp API."""
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def get_merchant_code(api_key):
    """Retrieve the SumUp merchant code associated with the API key."""
    response = requests.get(
        f"{SUMUP_API_BASE_URL}/v0.1/me",
        headers=build_headers(api_key),
        timeout=15,
    )

    response.raise_for_status()

    return response.json()["merchant_profile"]["merchant_code"]


def select_physical_solo(readers):
    """Return the unique physical SumUp Solo reader."""
    physical_solos = [
        reader
        for reader in readers
        if (reader.get("device") or {}).get("model") == "solo"
    ]

    if len(physical_solos) != 1:
        raise RuntimeError(
            "Impossible d'identifier un unique Solo physique."
        )

    return physical_solos[0]


def get_readers(api_key, merchant_code):
    """Retrieve the SumUp readers associated with a merchant."""
    response = requests.get(
        (
            f"{SUMUP_API_BASE_URL}/v0.1/merchants/"
            f"{merchant_code}/readers"
        ),
        headers=build_headers(api_key),
        timeout=15,
    )

    response.raise_for_status()

    return response.json().get("items", [])


def send_checkout_to_reader(
    api_key,
    merchant_code,
    reader_id,
    payload,
):
    """Send a prepared checkout payload to a SumUp reader."""
    checkout_url = (
        f"{SUMUP_API_BASE_URL}/v0.1/merchants/"
        f"{merchant_code}/readers/{reader_id}/checkout"
    )

    response = requests.post(
        checkout_url,
        headers=build_headers(api_key),
        json=payload,
        timeout=15,
    )

    response.raise_for_status()

    return response.json()


def send_checkout_to_physical_solo(api_key, payload):
    """Send a prepared checkout payload to the unique physical Solo."""
    merchant_code = get_merchant_code(api_key)

    readers = get_readers(
        api_key,
        merchant_code,
    )

    reader = select_physical_solo(readers)

    return send_checkout_to_reader(
        api_key=api_key,
        merchant_code=merchant_code,
        reader_id=reader["id"],
        payload=payload,
    )
