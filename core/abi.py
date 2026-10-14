from core.cache import save_cache
from core.cache import load_cache

import requests
import json
import time
import os
from config import BLOCKSCOUT_API, BLOCKSCOUT_SMART_CONTRACT


_BLOCKSCOUT_ROOT = BLOCKSCOUT_API.removesuffix("/api/v2").rstrip("/")
BASE_URL = os.getenv(
    "BLOCKSCOUT_LEGACY_API",
    _BLOCKSCOUT_ROOT + "/api",
)


def get_abi(address):
    """
    Fetch contract ABI from Blockscout.

    Cache is checked first to avoid unnecessary API requests.

    Returns:
        list: ABI when available
        None: when ABI is unavailable or contract is unverified

    Important:
    This function does not print "Contract source code not verified".
    The caller decides how an unavailable ABI should be displayed.
    """

    # ==================================================
    # CACHE
    # ==================================================

    cached = load_cache(
        address
    )

    if cached is not None:

        print(
            "✅ ABI loaded from cache"
        )

        return cached

    # ==================================================
    # API URL
    # ==================================================

    params = {
        "module": "contract",
        "action": "getabi",
        "address": address,
    }

    retries = 3

    # ==================================================
    # FETCH
    # ==================================================

    for attempt in range(retries):

        try:

            response = requests.get(
                BASE_URL,
                params=params,
                timeout=10,
            )

            # ------------------------------------------
            # RATE LIMIT
            # ------------------------------------------

            if response.status_code == 429:

                if attempt < retries - 1:

                    print(
                        "Rate limit reached. Retrying..."
                    )

                    time.sleep(2)

                    continue

                return None

            # ------------------------------------------
            # HTTP ERROR
            # ------------------------------------------

            if response.status_code in (401, 402, 403, 404):
                print(
                    "Robinhood Chain explorer API returned "
                    f"HTTP {response.status_code}; trying supported fallbacks."
                )
                break

            if response.status_code != 200:

                print(
                    f"HTTP Error: {response.status_code}"
                )

                return None

            # ------------------------------------------
            # JSON
            # ------------------------------------------

            try:

                data = response.json()

            except ValueError:

                print(
                    "Invalid JSON response from ABI API."
                )

                return None

            # ------------------------------------------
            # API RESULT
            # ------------------------------------------

            message = str(data.get("message", "")).lower()

            if message != "ok":
                return _get_abi_v2(address)

            # ------------------------------------------
            # ABI
            # ------------------------------------------

            raw_abi = data.get("result")

            if not raw_abi:

                return None

            try:

                abi = json.loads(
                    raw_abi
                )

            except (
                TypeError,
                ValueError,
            ):

                print(
                    "Invalid ABI returned by API."
                )

                return None

            # ------------------------------------------
            # VALIDATE
            # ------------------------------------------

            if not isinstance(
                abi,
                list,
            ):

                print(
                    "Unexpected ABI format returned by API."
                )

                return None

            # ------------------------------------------
            # CACHE
            # ------------------------------------------

            save_cache(
                address,
                abi,
            )

            print(
                "✅ ABI downloaded and cached"
            )

            return abi

        except requests.exceptions.RequestException:

            if attempt < retries - 1:

                print(
                    "Network error while fetching ABI. "
                    "Retrying..."
                )

                time.sleep(2)

                continue

            return None

    return _get_abi_v2(address)


def _get_abi_v2(address):
    """Fallback to Blockscout's native per-chain REST contract endpoint."""
    try:
        response = requests.get(
            f"{BLOCKSCOUT_SMART_CONTRACT}/{address}",
            timeout=10,
        )
        if response.status_code != 200:
            print(
                "Blockscout contract API unavailable: "
                f"HTTP {response.status_code}."
            )
            return _get_abi_pro(address)

        data = response.json()
        raw_abi = data.get("abi")
        if isinstance(raw_abi, str):
            raw_abi = json.loads(raw_abi)
        if not isinstance(raw_abi, list) or not raw_abi:
            return None

        save_cache(address, raw_abi)
        print("✅ ABI downloaded from Blockscout and cached")
        return raw_abi
    except (requests.exceptions.RequestException, ValueError, TypeError) as error:
        print(f"Blockscout contract API lookup failed: {error}")
        return _get_abi_pro(address)


def _get_abi_pro(address):
    """Use Blockscout's keyed multichain API when the local explorer is blocked."""
    api_key = os.environ.get("BLOCKSCOUT_API_KEY")
    if not api_key:
        print(
            "No BLOCKSCOUT_API_KEY is configured; verified source/ABI "
            "could not be fetched from the available explorer endpoints."
        )
        return None

    try:
        response = requests.get(
            "https://api.blockscout.com/v2/api",
            params={
                "chainid": "4663",
                "module": "contract",
                "action": "getabi",
                "address": address,
                "apikey": api_key,
            },
            timeout=10,
        )
        if response.status_code != 200:
            print(
                "Blockscout keyed API unavailable: "
                f"HTTP {response.status_code}."
            )
            return None

        data = response.json()
        raw_abi = data.get("result")
        if str(data.get("message", "")).lower() != "ok" or not raw_abi:
            return None
        abi = json.loads(raw_abi) if isinstance(raw_abi, str) else raw_abi
        if not isinstance(abi, list) or not abi:
            return None

        save_cache(address, abi)
        print("✅ ABI downloaded from Blockscout Pro API and cached")
        return abi
    except (requests.exceptions.RequestException, ValueError, TypeError) as error:
        print(f"Blockscout keyed API lookup failed: {error}")
        return None
