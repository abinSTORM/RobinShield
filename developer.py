from analyzer import analyze_contract
from scanner import get_token_info
from metadata import get_token_metadata


def analyze_developer(address):

    contract = analyze_contract(address)

    token = get_token_info(address)

    metadata = get_token_metadata(address)

    if contract is None or token is None or metadata is None:
        return None

    return {
        "proxy": contract["proxy"],
        "proxy_type": contract["proxy_type"],
        "implementation": contract["implementation"],

        "holders": metadata["holders"],
        "reputation": metadata["reputation"],
        "type": metadata["type"],

        "name": token["name"],
        "symbol": token["symbol"],
        "supply": token["supply"],
    }