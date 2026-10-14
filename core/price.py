import requests


DEXSCREENER_TOKEN_URL = (
    "https://api.dexscreener.com/latest/dex/tokens/"
)


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

    except (
        requests.RequestException,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:

        raise RuntimeError(
            "Unable to retrieve ETH/USD price."
        ) from exc


def get_token_price_usd(
    token_address,
):
    """
    Get a token's USD price from DexScreener.

    Returns:
        float | None

    The result is based on the best available pair
    returned by DexScreener. This is a valuation helper,
    not a guarantee that the token is liquid or safely
    tradable.
    """

    if not token_address:

        return None

    url = (
        DEXSCREENER_TOKEN_URL
        + str(
            token_address
        )
    )

    try:

        response = requests.get(
            url,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

    except (
        requests.RequestException,
        ValueError,
    ):

        return None

    if not isinstance(
        data,
        dict,
    ):

        return None

    pairs = data.get(
        "pairs"
    )

    if not isinstance(
        pairs,
        list,
    ):

        return None

    candidates = []

    for pair in pairs:

        if not isinstance(
            pair,
            dict,
        ):

            continue

        price_usd = pair.get(
            "priceUsd"
        )

        try:

            price_usd = float(
                price_usd
            )

        except (
            TypeError,
            ValueError,
        ):

            continue

        if price_usd <= 0:

            continue

        liquidity = (
            pair.get(
                "liquidity"
            )
            or {}
        )

        try:

            liquidity_usd = float(
                liquidity.get(
                    "usd",
                    0,
                )
                or 0
            )

        except (
            TypeError,
            ValueError,
        ):

            liquidity_usd = 0.0

        candidates.append(
            (
                liquidity_usd,
                price_usd,
            )
        )

    if not candidates:

        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )

    return candidates[0][1]