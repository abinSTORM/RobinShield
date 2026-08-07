import requests

BASE_URL = "https://robinhoodchain.blockscout.com/api/v2"


def get_token_metadata(address):

    url = f"{BASE_URL}/tokens/{address}"

    response = requests.get(url)

    if response.status_code != 200:
        return None

    data = response.json()

    return {
        "holders": int(data.get("holders_count", 0)),
        "reputation": data.get("reputation"),
        "type": data.get("type"),
        "market_cap": data.get("circulating_market_cap"),
        "volume_24h": data.get("volume_24h"),
    }