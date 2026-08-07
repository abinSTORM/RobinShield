import requests
from config import BLOCKSCOUT_SMART_CONTRACT


def get_contract_info(address):
    url = f"{BLOCKSCOUT_SMART_CONTRACT}/{address}"

    try:
        response = requests.get(url)

        if response.status_code != 200:
            return None

        return response.json()

    except Exception as e:
        print(e)
        return None


def get_source_code(address):
    contract = get_contract_info(address)

    if contract is None:
        return None

    return contract.get("source_code")