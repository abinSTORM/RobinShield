import requests


def get_eth_price_usd():
    """
    Get the current ETH/USD price.
    """

    url = "https://api.coingecko.com/api/v3/simple/price"

    params = {
        "ids": "ethereum",
        "vs_currencies": "usd",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        price = data["ethereum"]["usd"]

        return float(price)

    except (requests.RequestException, KeyError, TypeError, ValueError) as exc:
        raise RuntimeError(
            "Unable to retrieve ETH/USD price."
        ) from exc