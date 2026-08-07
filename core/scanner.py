from web3 import Web3

from config import RPC_URL

w3 = Web3(Web3.HTTPProvider(RPC_URL))

ERC20_ABI = [
    {
        "name": "name",
        "outputs": [{"type": "string"}],
        "inputs": [],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "name": "symbol",
        "outputs": [{"type": "string"}],
        "inputs": [],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "name": "decimals",
        "outputs": [{"type": "uint8"}],
        "inputs": [],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "name": "totalSupply",
        "outputs": [{"type": "uint256"}],
        "inputs": [],
        "stateMutability": "view",
        "type": "function",
    },
]


def get_token_info(address):     # Web3

    if not w3.is_connected():
        return None

    try:
        address = Web3.to_checksum_address(address)

        token = w3.eth.contract(
            address=address,
            abi=ERC20_ABI
        )

        name = token.functions.name().call()

        symbol = token.functions.symbol().call()

        decimals = token.functions.decimals().call()

        supply = token.functions.totalSupply().call()

        supply = supply / (10 ** decimals)

        return {
            "name": name,
            "symbol": symbol,
            "decimals": decimals,
            "supply": supply,
        }

    except Exception as e:
        print(e)
        return None