from cache import save_cache
from cache import load_cache

import requests
import json
import time

BASE_URL = "https://robinhoodchain.blockscout.com/api"


def get_abi(address):

    # Check cache first
    cached = load_cache(address)

    if cached is not None:
        print("✅ ABI loaded from cache")
        return cached

    url = (
        f"{BASE_URL}"
        f"?module=contract"
        f"&action=getabi"
        f"&address={address}"
    )

    retries = 3

    for attempt in range(retries):

        try:

            response = requests.get(url, timeout=10)

            if response.status_code == 429:

                print("Rate limit reached. Retrying...")

                time.sleep(2)

                continue

            if response.status_code != 200:

                print(f"HTTP Error: {response.status_code}")

                return None

            data = response.json()

            if str(data.get("status")) != "1":

                print(data.get("message"))

                return None

            abi = json.loads(data["result"])

            # Save ABI to cache
            save_cache(address, abi)

            print("✅ ABI downloaded and cached")

            return abi

        except requests.exceptions.RequestException as e:

            print("Network Error:", e)

            time.sleep(2)

    print("Failed to fetch ABI after multiple attempts.")

    return None