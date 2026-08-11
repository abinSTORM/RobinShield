from web3 import Web3

ERC20_DECIMALS_ABI = [
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [
            {
                "internalType": "uint8",
                "name": "",
                "type": "uint8",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


def get_token_decimals(w3, token_address):

    token = w3.eth.contract(
        address=Web3.to_checksum_address(token_address),
        abi=ERC20_DECIMALS_ABI,
    )

    return token.functions.decimals().call()