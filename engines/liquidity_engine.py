from core.token import get_token_decimals
from web3 import Web3

from config import RPC_URL
from core.lp import V2_FACTORY_ABI, PAIR_ABI


V2_FACTORY = "0x8bcEaA40B9AcdfAedF85AdF4FF01F5Ad6517937f"

WETH = "0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73"

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"


def find_v2_pair(token_address):

    w3 = Web3(Web3.HTTPProvider(RPC_URL))

    if not w3.is_connected():
        raise ConnectionError("Unable to connect to Robinhood Chain RPC.")

    token_address = Web3.to_checksum_address(token_address)

    factory = w3.eth.contract(
        address=Web3.to_checksum_address(V2_FACTORY),
        abi=V2_FACTORY_ABI,
    )

    pair = factory.functions.getPair(
        token_address,
        Web3.to_checksum_address(WETH),
    ).call()

    if pair.lower() == ZERO_ADDRESS.lower():
        return None

    return pair


def analyze_liquidity(token_address):

    pair_address = find_v2_pair(token_address)

    if pair_address is None:
        return {
            "found": False,
            "dex": None,
            "pair": None,
            "liquidity_eth": 0,
            "risk": "HIGH",
            "reason": "No Uniswap V2 WETH liquidity pool found.",
        }

    w3 = Web3(Web3.HTTPProvider(RPC_URL))

    pair = w3.eth.contract(
        address=Web3.to_checksum_address(pair_address),
        abi=PAIR_ABI,
    )

    token0 = pair.functions.token0().call()
    token1 = pair.functions.token1().call()

    reserve0, reserve1, _ = pair.functions.getReserves().call()
    token_decimals = get_token_decimals(w3, token_address)

    if token0.lower() == WETH.lower():
        weth_reserve = reserve0
        token_reserve = reserve1
    else:
        weth_reserve = reserve1
        token_reserve = reserve0

    weth_amount = w3.from_wei(weth_reserve, "ether")

    liquidity_eth = float(weth_amount) * 2

    if liquidity_eth < 1:
        risk = "HIGH"
    elif liquidity_eth < 10:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return {
        "found": True,
        "dex": "Uniswap V2",
        "pair": pair_address,
        "weth_reserve": float(weth_amount),
        "token_reserve": f"{token_reserve / (10 ** token_decimals):.18f}",
        "token_decimals": token_decimals,
        "liquidity_eth": round(liquidity_eth, 4),
        "risk": risk,
        "reason": "Uniswap V2 WETH liquidity pool detected.",
    }