from .verifier import get_contract_info


def analyze_contract(address):

    contract = get_contract_info(address)

    if contract is None:
        return None

    result = {
        "proxy": False,
        "proxy_type": None,
        "implementation": None,
    }

    # Check if contract is a proxy
    if contract.get("proxy_type"):
        result["proxy"] = True
        result["proxy_type"] = contract.get("proxy_type")

    implementations = contract.get("implementations")

    if implementations:
        result["implementation"] = implementations[0].get("name")

    return result