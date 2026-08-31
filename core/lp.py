from web3 import Web3

from config import RPC_URL


V2_FACTORY_ABI = [
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "tokenA",
                "type": "address",
            },
            {
                "internalType": "address",
                "name": "tokenB",
                "type": "address",
            },
        ],
        "name": "getPair",
        "outputs": [
            {
                "internalType": "address",
                "name": "pair",
                "type": "address",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


PAIR_ABI = [
    {
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {
                "internalType": "uint112",
                "name": "_reserve0",
                "type": "uint112",
            },
            {
                "internalType": "uint112",
                "name": "_reserve1",
                "type": "uint112",
            },
            {
                "internalType": "uint32",
                "name": "_blockTimestampLast",
                "type": "uint32",
            },
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token0",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "token1",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "account",
                "type": "address",
            }
        ],
        "name": "balanceOf",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


# Common Uniswap V2 factory.
# Keep this configurable through config.py if the project
# already defines another factory.
DEFAULT_FACTORY_ADDRESS = (
    "0x8bcEaA40B9AcdfAedF85AdF4FF01F5Ad6517937f"
)


def get_web3():
    """
    Return a connected Web3 instance.
    """

    w3 = Web3(
        Web3.HTTPProvider(RPC_URL)
    )

    if not w3.is_connected():
        raise ConnectionError(
            "Unable to connect to Robinhood Chain RPC."
        )

    return w3


def get_factory_address():
    """
    Get the configured V2 factory address.

    If FACTORY_ADDRESS exists in config.py, use it.
    Otherwise return the default placeholder.
    """

    try:
        from config import FACTORY_ADDRESS

        if FACTORY_ADDRESS:
            return Web3.to_checksum_address(
                FACTORY_ADDRESS
            )

    except ImportError:
        pass

    return Web3.to_checksum_address(
        DEFAULT_FACTORY_ADDRESS
    )


def get_pair(
    token_address,
    factory_address=None,
    weth_address=None,
):
    """
    Return the Uniswap V2 pair for a token.

    This function is retained for compatibility with the
    original liquidity tests and older engine code.

    Parameters
    ----------
    token_address:
        ERC-20 token address.

    factory_address:
        Optional V2 factory address.

    weth_address:
        Optional WETH/native wrapped asset address.
        If omitted, tries to load WETH_ADDRESS from config.py.
    """

    w3 = get_web3()

    token_address = Web3.to_checksum_address(
        token_address
    )

    if factory_address is None:
        factory_address = get_factory_address()

    if weth_address is None:

        try:
            from config import WETH_ADDRESS

            weth_address = WETH_ADDRESS

        except ImportError:
            weth_address = None

    if not weth_address:
        raise ValueError(
            "WETH_ADDRESS is not configured."
        )

    weth_address = Web3.to_checksum_address(
        weth_address
    )

    factory = w3.eth.contract(
        address=Web3.to_checksum_address(
            factory_address
        ),
        abi=V2_FACTORY_ABI,
    )

    try:

        pair = factory.functions.getPair(
            token_address,
            weth_address,
        ).call()

    except Exception:
        return None

    if not pair:
        return None

    zero_address = (
        "0x0000000000000000000000000000000000000000"
    )

    if pair.lower() == zero_address.lower():
        return None

    return Web3.to_checksum_address(
        pair
    )


def get_pair_contract(pair_address):
    """
    Return a Web3 contract object for a V2 pair.
    """

    w3 = get_web3()

    return w3.eth.contract(
        address=Web3.to_checksum_address(
            pair_address
        ),
        abi=PAIR_ABI,
    )


def get_pair_reserves(pair_address):
    """
    Read raw V2 pair reserves.
    """

    pair = get_pair_contract(
        pair_address
    )

    return pair.functions.getReserves().call()


def get_pair_tokens(pair_address):
    """
    Return token0 and token1 addresses.
    """

    pair = get_pair_contract(
        pair_address
    )

    token0 = pair.functions.token0().call()
    token1 = pair.functions.token1().call()

    return (
        Web3.to_checksum_address(token0),
        Web3.to_checksum_address(token1),
    )


def get_lp_total_supply(pair_address):
    """
    Return total LP token supply.
    """

    pair = get_pair_contract(
        pair_address
    )

    return pair.functions.totalSupply().call()


def get_lp_balance(
    pair_address,
    account,
):
    """
    Return LP token balance for an address.
    """

    pair = get_pair_contract(
        pair_address
    )

    return pair.functions.balanceOf(
        Web3.to_checksum_address(account)
    ).call()
