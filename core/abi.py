from core.cache import save_cache
from core.cache import load_cache

import requests
import json
import time


BASE_URL = "https://robinhoodchain.blockscout.com/api"


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

    url = (
        f"{BASE_URL}"
        f"?module=contract"
        f"&action=getabi"
        f"&address={address}"
    )

    retries = 3

    # ==================================================
    # FETCH
    # ==================================================

    for attempt in range(
        retries
    ):

        try:

            response = requests.get(
                url,
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

            if str(
                data.get("status")
            ) != "1":

                # Do NOT print the API message here.
                #
                # Blockscout commonly returns messages
                # such as "Contract source code not verified".
                #
                # The scanner handles ABI-unavailable
                # status itself.

                return None

            # ------------------------------------------
            # ABI
            # ------------------------------------------

            raw_abi = data.get(
                "result"
            )

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

    # ==================================================
    # FAILED
    # ==================================================

    return None