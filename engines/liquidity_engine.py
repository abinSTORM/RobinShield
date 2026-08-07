from web3 import Web3

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def analyze_liquidity(pair_address):

    if pair_address is None:
        return {
            "found": False,
            "dex": None,
            "risk": "HIGH",
            "reason": "No liquidity pool found."
        }

    if pair_address == ZERO_ADDRESS:
        return {
            "found": False,
            "dex": None,
            "risk": "HIGH",
            "reason": "No liquidity pool found."
        }

    return {
        "found": True,
        "dex": "Uniswap V2",
        "risk": "UNKNOWN",
        "reason": "Liquidity pool detected."
    }