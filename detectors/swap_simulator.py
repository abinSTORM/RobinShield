import os

import socket

import subprocess

import time

from web3 import Web3

from config import RPC_URL

from core.lp import PAIR_ABI

# ============================================================

# ALCHEMY FORK RPC

# ============================================================

def _read_env_value(

    name,

):

    value = os.getenv(

        name

    )

    if value:

        return value.strip()

    project_root = os.path.abspath(

        os.path.join(

            os.path.dirname(

                os.path.abspath(__file__)

            ),

            "..",

        )

    )

    env_path = os.path.join(

        project_root,

        ".env",

    )

    try:

        with open(

            env_path,

            "r",

            encoding="utf-8",

        ) as file:

            for raw_line in file:

                line = raw_line.strip()

                if not line:

                    continue

                if line.startswith(

                    "#"

                ):

                    continue

                if not line.startswith(

                    name + "="

                ):

                    continue

                value = line.split(

                    "=",

                    1,

                )[1].strip()

                if (

                    len(value) >= 2

                    and value[0] == '"'

                    and value[-1] == '"'

                ):

                    value = value[1:-1]

                elif (

                    len(value) >= 2

                    and value[0] == "'"

                    and value[-1] == "'"

                ):

                    value = value[1:-1]

                return value.strip()

    except Exception:

        pass

    return None

ALCHEMY_API_KEY = _read_env_value(

    "ALCHEMY_API_KEY"

)

if ALCHEMY_API_KEY:

    FORK_RPC_URL = (

        "https://robinhood-mainnet.g.alchemy.com/v2/"

        + ALCHEMY_API_KEY

    )

else:

    FORK_RPC_URL = RPC_URL

# ============================================================

# ROBINHOOD CHAIN / UNISWAP V2

# ============================================================

UNISWAP_V2_ROUTER = Web3.to_checksum_address(

    "0x89e5DB8B5aA49aA85AC63f691524311AEB649eba"

)

# Official Uniswap SwapRouter02 deployment on Robinhood Chain.
UNISWAP_V3_ROUTER = Web3.to_checksum_address(
    "0xCaf681a66D020601342297493863E78C959E5cb2"
)
V3_FEE_TIERS = (100, 500, 3000, 10000)

V3_ROUTER_ABI = [
    {
        "inputs": [{
            "components": [
                {"internalType": "address", "name": "tokenIn", "type": "address"},
                {"internalType": "address", "name": "tokenOut", "type": "address"},
                {"internalType": "uint24", "name": "fee", "type": "uint24"},
                {"internalType": "address", "name": "recipient", "type": "address"},
                {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"},
            ],
            "internalType": "struct IV3SwapRouter.ExactInputSingleParams",
            "name": "params",
            "type": "tuple",
        }],
        "name": "exactInputSingle",
        "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function",
    }
]

# ============================================================

# ANVIL

# ============================================================

ANVIL_HOST = "127.0.0.1"

# Use a different port so an accidentally running manual Anvil

# instance is less likely to conflict with RobinShield.

ANVIL_PORT = 18545

ANVIL_RPC_URL = (

    f"http://{ANVIL_HOST}:{ANVIL_PORT}"

)

ANVIL_START_TIMEOUT = 20

ANVIL_READY_INTERVAL = 0.25

# Temporary native balance exists ONLY inside the local fork.

TEST_GAS_BALANCE_WEI = 10**20

# ============================================================

# ABIS

# ============================================================

ERC20_ABI = [

    {

        "inputs": [

            {

                "internalType": "address",

                "name": "owner",

                "type": "address",

            },

            {

                "internalType": "address",

                "name": "spender",

                "type": "address",

            },

        ],

        "name": "allowance",

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

    {

        "inputs": [

            {

                "internalType": "address",

                "name": "spender",

                "type": "address",

            },

            {

                "internalType": "uint256",

                "name": "amount",

                "type": "uint256",

            },

        ],

        "name": "approve",

        "outputs": [

            {

                "internalType": "bool",

                "name": "",

                "type": "bool",

            }

        ],

        "stateMutability": "nonpayable",

        "type": "function",

    },

    {

        "inputs": [

            {

                "internalType": "address",

                "name": "to",

                "type": "address",

            },

            {

                "internalType": "uint256",

                "name": "amount",

                "type": "uint256",

            },

        ],

        "name": "transfer",

        "outputs": [

            {

                "internalType": "bool",

                "name": "",

                "type": "bool",

            }

        ],

        "stateMutability": "nonpayable",

        "type": "function",

    },

]

ROUTER_ABI = [

    {

        "inputs": [

            {

                "internalType": "uint256",

                "name": "amountIn",

                "type": "uint256",

            },

            {

                "internalType": "uint256",

                "name": "amountOutMin",

                "type": "uint256",

            },

            {

                "internalType": "address[]",

                "name": "path",

                "type": "address[]",

            },

            {

                "internalType": "address",

                "name": "to",

                "type": "address",

            },

            {

                "internalType": "uint256",

                "name": "deadline",

                "type": "uint256",

            },

        ],

        "name": "swapExactTokensForTokensSupportingFeeOnTransferTokens",

        "outputs": [],

        "stateMutability": "nonpayable",

        "type": "function",

    }

]

# ============================================================

# WEB3

# ============================================================

def get_web3(

    rpc_url=RPC_URL,

):

    w3 = Web3(

        Web3.HTTPProvider(

            rpc_url

        )

    )

    if not w3.is_connected():

        raise ConnectionError(

            f"Unable to connect to RPC: {rpc_url}"

        )

    return w3

# ============================================================

# SAFE HELPERS

# ============================================================

def safe_checksum(

    address,

):

    if not address:

        return None

    try:

        return Web3.to_checksum_address(

            address

        )

    except Exception:

        return None

def rpc_request(

    w3,

    method,

    params,

):

    response = w3.provider.make_request(

        method,

        params,

    )

    if not isinstance(

        response,

        dict,

    ):

        raise RuntimeError(

            f"Invalid RPC response for {method}."

        )

    if response.get(

        "error"

    ):

        raise RuntimeError(

            str(

                response["error"]

            )

        )

    return response.get(

        "result"

    )

def wait_for_port(

    host,

    port,

    timeout=ANVIL_START_TIMEOUT,

):

    deadline = time.time() + timeout

    while time.time() < deadline:

        sock = socket.socket(

            socket.AF_INET,

            socket.SOCK_STREAM,

        )

        sock.settimeout(

            0.5

        )

        try:

            if sock.connect_ex(

                (

                    host,

                    port,

                )

            ) == 0:

                return True

        finally:

            sock.close()

        time.sleep(

            ANVIL_READY_INTERVAL

        )

    return False

# ============================================================

# CONTRACT HELPERS

# ============================================================

def _normalize_hex(value):
    if isinstance(value, bytes):
        return "0x" + value.hex()
    value = str(value)
    return value if value.startswith("0x") else "0x" + value

def _decode_transfer_address(topic):
    topic_hex = _normalize_hex(topic)[2:]
    if len(topic_hex) < 40:
        raise ValueError(f"Invalid indexed address topic: {topic}")
    return Web3.to_checksum_address("0x" + topic_hex[-40:])

def _decode_transfer_value(data):
    if isinstance(data, bytes):
        return int.from_bytes(data, byteorder="big")
    return int(_normalize_hex(data), 16)

def get_token_contract(

    w3,

    token_address,

):

    return w3.eth.contract(

        address=Web3.to_checksum_address(

            token_address

        ),

        abi=ERC20_ABI,

    )

def get_router(

    w3,

):

    return w3.eth.contract(

        address=UNISWAP_V2_ROUTER,

        abi=ROUTER_ABI,

    )


def get_v3_router(w3):
    return w3.eth.contract(
        address=UNISWAP_V3_ROUTER,
        abi=V3_ROUTER_ABI,
    )


def execute_v3_swap(w3, router, sender, token_in, token_out, fee, amount):
    """Execute one exact-input V3 swap in the temporary fork."""
    sender = Web3.to_checksum_address(sender)
    token_in = Web3.to_checksum_address(token_in)
    token_out = Web3.to_checksum_address(token_out)
    token_in_contract = get_token_contract(w3, token_in)
    token_out_contract = get_token_contract(w3, token_out)
    before_in = get_balance(token_in_contract, sender)
    before_out = get_balance(token_out_contract, sender)

    params = (
        token_in,
        token_out,
        int(fee),
        sender,
        int(amount),
        0,
        0,
    )
    swap_function = router.functions.exactInputSingle(params)
    try:
        swap_function.call({
            "from": sender,
            "gas": 1_500_000,
            "gasPrice": w3.eth.gas_price,
        })
    except Exception as exc:
        detail = str(exc).replace("\n", " ")[:600]
        raise RuntimeError(
            f"V3 exactInputSingle preflight reverted: {type(exc).__name__}: {detail}"
        ) from exc

    tx = swap_function.build_transaction({
        "from": sender,
        "gas": 1_500_000,
        "gasPrice": w3.eth.gas_price,
        "nonce": w3.eth.get_transaction_count(sender),
    })
    tx_hash = w3.eth.send_transaction(tx)
    receipt = wait_for_receipt(w3, tx_hash)
    after_in = get_balance(token_in_contract, sender)
    after_out = get_balance(token_out_contract, sender)
    spent = max(before_in - after_in, 0)
    received = max(after_out - before_out, 0)
    receipt_status = int(receipt.get("status", 0))
    error = None
    if receipt_status != 1:
        try:
            swap_function.call({
                "from": sender,
                "gas": 1_500_000,
                "gasPrice": w3.eth.gas_price,
            })
        except Exception as exc:
            detail = str(exc).replace("\n", " ")[:600]
            error = (
                f"V3 exactInputSingle reverted in the temporary fork: "
                f"{type(exc).__name__}: {detail}"
            )
        if error is None:
            error = "V3 exactInputSingle transaction reverted after a successful preflight simulation."
    return {
        "success": receipt_status == 1 and spent > 0 and received > 0,
        "tx_hash": tx_hash.hex(),
        "gas_used": int(receipt.get("gasUsed", 0)),
        "receipt_status": receipt_status,
        "error": error,
        "input_spent": int(spent),
        "output_received": int(received),
        "before_input_balance": int(before_in),
        "after_input_balance": int(after_in),
        "before_output_balance": int(before_out),
        "after_output_balance": int(after_out),
    }

# ============================================================

# TOKEN READS

# ============================================================

def get_balance(

    token,

    address,

):

    try:

        return int(

            token.functions.balanceOf(

                Web3.to_checksum_address(

                    address

                )

            ).call()

        )

    except Exception:

        return 0

def get_allowance(

    token,

    owner,

    spender,

):

    try:

        return int(

            token.functions.allowance(

                Web3.to_checksum_address(

                    owner

                ),

                Web3.to_checksum_address(

                    spender

                ),

            ).call()

        )

    except Exception:

        return 0

# ============================================================

# HOLDER SELECTION

# ============================================================

def get_candidate_holders(

    holders,

    excluded_addresses=None,

):

    """

    Build a clean list of possible test holders.

    Excludes:

        - zero address

        - dead address

        - explicitly excluded addresses

        - obvious LP / pool / locker / staking addresses

        - the token contract itself

    """

    candidates = []

    if not isinstance(

        holders,

        dict,

    ):

        return candidates

    items = holders.get(

        "items",

        [],

    )

    if not isinstance(

        items,

        list,

    ):

        return candidates

    ignored_keywords = [

        "uniswap",

        "pair",

        "pool",

        "lp",

        "liquidity",

        "dead",

        "burn",

        "locker",

        "staking",

    ]

    excluded = set()

    if excluded_addresses:

        for address in excluded_addresses:

            checksum = safe_checksum(

                address

            )

            if checksum:

                excluded.add(

                    checksum.lower()

                )

    # Always exclude burn addresses.

    excluded.add(

        "0x0000000000000000000000000000000000000000"

    )

    excluded.add(

        "0x000000000000000000000000000000000000dead"

    )

    for holder in items:

        if not isinstance(

            holder,

            dict,

        ):

            continue

        address_info = holder.get(

            "address",

            {}

        )

        if not isinstance(

            address_info,

            dict,

        ):

            continue

        address = safe_checksum(

            address_info.get(

                "hash"

            )

        )

        if not address:

            continue

        normalized_address = address.lower()

        if normalized_address in excluded:

            continue

        name = address_info.get(

            "name"

        )

        if name:

            lowered_name = str(

                name

            ).lower()

            if any(

                keyword in lowered_name

                for keyword in ignored_keywords

            ):

                continue

        balance = holder.get(

            "value",

            0,

        )

        try:

            balance = int(

                balance

            )

        except (

            TypeError,

            ValueError,

        ):

            balance = 0

        if balance <= 0:

            continue

        candidates.append(

            {

                "address": address,

                "reported_balance": balance,

            }

        )

    # Largest reported holder first.

    candidates.sort(

        key=lambda item: item.get(

            "reported_balance",

            0,

        ),

        reverse=True,

    )

    return candidates

def find_test_holder(

    token,

    holders,

    excluded_addresses=None,

):

    """

    Select the largest valid current holder that can be

    verified directly with balanceOf().

    The balance reported by the holder index is only used

    for ordering. The live balanceOf() result is authoritative.

    """

    token_address = safe_checksum(

        getattr(

            token,

            "address",

            None,

        )

    )

    exclusions = []

    if excluded_addresses:

        exclusions.extend(

            excluded_addresses

        )

    # Never use the token contract itself as the test holder.

    if token_address:

        exclusions.append(

            token_address

        )

    candidates = get_candidate_holders(

        holders,

        excluded_addresses=exclusions,

    )

    for candidate in candidates:

        address = candidate.get(

            "address"

        )

        if not address:

            continue

        try:

            balance = get_balance(

                token,

                address,

            )

        except Exception:

            balance = 0

        if balance <= 0:

            continue

        return {

            "address": address,

            "balance": int(

                balance

            ),

        }

    return None

# ============================================================

# ANVIL PROCESS

# ============================================================

def start_anvil():

    env = os.environ.copy()

    command = [

        "anvil",

        "--fork-url",

        FORK_RPC_URL,

        "--port",

        str(

            ANVIL_PORT

        ),

        "--host",

        ANVIL_HOST,

        "--silent",

    ]

    process = subprocess.Popen(

        command,

        stdout=subprocess.DEVNULL,

        stderr=subprocess.DEVNULL,

        env=env,

    )

    if not wait_for_port(

        ANVIL_HOST,

        ANVIL_PORT,

    ):

        try:

            process.terminate()

            process.wait(

                timeout=3

            )

        except Exception:

            pass

        raise RuntimeError(

            "Anvil did not become ready within "

            f"{ANVIL_START_TIMEOUT} seconds."

        )

    return process

def stop_anvil(

    process,

):

    if process is None:

        return

    try:

        if process.poll() is None:

            process.terminate()

            process.wait(

                timeout=5

            )

    except Exception:

        try:

            process.kill()

        except Exception:

            pass

# ============================================================

# ANVIL ACCOUNT CONTROL

# ============================================================

def impersonate_account(

    w3,

    address,

):

    rpc_request(

        w3,

        "anvil_impersonateAccount",

        [

            Web3.to_checksum_address(

                address

            )

        ],

    )

def stop_impersonating(

    w3,

    address,

):

    try:

        rpc_request(

            w3,

            "anvil_stopImpersonatingAccount",

            [

                Web3.to_checksum_address(

                    address

                )

            ],

        )

    except Exception:

        pass

def set_account_balance(

    w3,

    address,

    balance_wei=TEST_GAS_BALANCE_WEI,

):

    rpc_request(

        w3,

        "anvil_setBalance",

        [

            Web3.to_checksum_address(

                address

            ),

            hex(

                int(

                    balance_wei

                )

            ),

        ],

    )

# ============================================================

# RECEIPT

# ============================================================

def wait_for_receipt(

    w3,

    tx_hash,

    timeout=30,

):

    return w3.eth.wait_for_transaction_receipt(

        tx_hash,

        timeout=timeout,

    )

# ============================================================

# APPROVAL

# ============================================================

def approve_router(

    w3,

    token,

    holder,

    amount,

    router_address=UNISWAP_V2_ROUTER,

):

    holder = Web3.to_checksum_address(

        holder

    )

    tx = token.functions.approve(

        Web3.to_checksum_address(router_address),

        int(amount),

    ).build_transaction(

        {

            "from": holder,

            "gas": 300000,

            "gasPrice": w3.eth.gas_price,

            "nonce": w3.eth.get_transaction_count(

                holder

            ),

        }

    )

    tx_hash = w3.eth.send_transaction(

        tx

    )

    receipt = wait_for_receipt(

        w3,

        tx_hash,

    )

    if int(

        receipt.get(

            "status",

            0,

        )

    ) != 1:

        raise RuntimeError(

            "Temporary router approval transaction reverted."

        )

    allowance = get_allowance(

        token,

        holder,

        router_address,

    )

    if allowance < int(

        amount

    ):

        raise RuntimeError(

            "Router allowance was not updated after "

            "the temporary approval."

        )

    return {

        "tx_hash": tx_hash.hex(),

        "allowance": allowance,

    }

# ============================================================

# ROUTER SELL

# ============================================================

def execute_sell(
    w3,
    router,
    holder,
    token_address,
    quote_token,
    pair_address,
    amount,
):

    holder = Web3.to_checksum_address(

        holder

    )

    token_address = Web3.to_checksum_address(

        token_address

    )

    quote_token = Web3.to_checksum_address(
        quote_token
    )

    pair_address = Web3.to_checksum_address(
        pair_address
    )

    token_contract = get_token_contract(

        w3,

        token_address,

    )

    quote_contract = get_token_contract(

        w3,

        quote_token,

    )

    # --------------------------------------------------------

    # BEFORE BALANCES

    # --------------------------------------------------------

    before_token_balance = get_balance(

        token_contract,

        holder,

    )

    before_quote_balance = get_balance(

        quote_contract,

        holder,

    )

    block = w3.eth.get_block(

        "latest"

    )

    deadline = (

        int(

            block[

                "timestamp"

            ]

        )

        + 600

    )

    tx = (

        router.functions

        .swapExactTokensForTokensSupportingFeeOnTransferTokens(

            int(amount),

            0,

            [

                token_address,

                quote_token,

            ],

            holder,

            deadline,

        )

        .build_transaction(

            {

                "from": holder,

                "gas": 1500000,

                "gasPrice": w3.eth.gas_price,

                "nonce": w3.eth.get_transaction_count(

                    holder

                ),

            }

        )

    )

    tx_hash = w3.eth.send_transaction(

        tx

    )

    receipt = wait_for_receipt(

        w3,

        tx_hash,

    )

    receipt_status = int(

        receipt.get(

            "status",

            0,

        )

    )

    # --------------------------------------------------------

    # AFTER BALANCES

    # --------------------------------------------------------

    after_token_balance = get_balance(

        token_contract,

        holder,

    )

    after_quote_balance = get_balance(

        quote_contract,

        holder,

    )

    token_spent = max(

        before_token_balance

        - after_token_balance,

        0,

    )

    quote_received = max(

        after_quote_balance

        - before_quote_balance,

        0,

    )

    # --------------------------------------------------------

    # --------------------------------------------------------
    # TRANSFER EVENT INSPECTION
    # --------------------------------------------------------

    transfer_topic = _normalize_hex(
        Web3.keccak(text="Transfer(address,address,uint256)")
    ).lower()

    token_transfer_events = []
    quote_transfer_events = []

    token_address_checksum = Web3.to_checksum_address(token_address)
    quote_token_checksum = Web3.to_checksum_address(quote_token)
    pair_address_checksum = Web3.to_checksum_address(pair_address)
    holder_checksum = Web3.to_checksum_address(holder)

    for log in receipt.get("logs", []):
        try:
            log_address = Web3.to_checksum_address(
                _normalize_hex(log.get("address"))
            )

            topics = log.get("topics", [])
            if not isinstance(topics, (list, tuple)):
                topics = list(topics)

            if len(topics) < 3:
                continue

            if _normalize_hex(topics[0]).lower() != transfer_topic:
                continue

            event = {
                "from": _decode_transfer_address(topics[1]),
                "to": _decode_transfer_address(topics[2]),
                "value": _decode_transfer_value(
                    log.get("data", "0x0")
                ),
            }

            if log_address.lower() == token_address_checksum.lower():
                token_transfer_events.append(event)
            elif log_address.lower() == quote_token_checksum.lower():
                quote_transfer_events.append(event)

        except Exception:
            continue

    # --------------------------------------------------------
    # TOKEN TRANSFER FROM HOLDER
    # --------------------------------------------------------

    event_spent = sum(
        int(event["value"])
        for event in token_transfer_events
        if event["from"].lower() == holder_checksum.lower()
    )

    # Amount of token that actually arrived at the pair.
    # This is useful later for distinguishing transfer tax from
    # normal AMM price impact.
    event_pair_token_received = sum(
        int(event["value"])
        for event in token_transfer_events
        if (
            event["from"].lower() == holder_checksum.lower()
            and event["to"].lower() == pair_address_checksum.lower()
        )
    )

    # --------------------------------------------------------
    # QUOTE TRANSFER TO HOLDER
    # --------------------------------------------------------

    event_received = sum(
        int(event["value"])
        for event in quote_transfer_events
        if event["to"].lower() == holder_checksum.lower()
    )

    # SUCCESS

    # --------------------------------------------------------

    success = (

        receipt_status == 1

        and token_spent > 0

        and quote_received > 0

    )

    return {

        "success": success,

        "tx_hash": tx_hash.hex(),

        "gas_used": int(

            receipt.get(

                "gasUsed",

                0,

            )

        ),

        "receipt_status": receipt_status,

        "before_token_balance": int(

            before_token_balance

        ),

        "after_token_balance": int(

            after_token_balance

        ),

        "token_spent": int(

            token_spent

        ),

        "before_quote_balance": int(

            before_quote_balance

        ),

        "after_quote_balance": int(

            after_quote_balance

        ),

        "quote_received": int(

            quote_received

        ),

        "token_transfer_events": (

            token_transfer_events

        ),

        "quote_transfer_events": (

            quote_transfer_events

        ),

        "event_spent": int(
            event_spent
        ),

        "event_received": int(
            event_received
        ),

        "event_token_spent": int(
            event_spent
        ),

        "event_quote_received": int(
            event_received
        ),

        "event_pair_token_received": int(
            event_pair_token_received
        ),

    }

# ============================================================

# ROUTER BUY

# ============================================================

def execute_buy(

    w3,

    router,

    buyer,

    token_address,

    quote_token,

    amount,

):

    buyer = Web3.to_checksum_address(

        buyer

    )

    token_address = Web3.to_checksum_address(

        token_address

    )

    quote_token = Web3.to_checksum_address(

        quote_token

    )

    token_contract = get_token_contract(

        w3,

        token_address,

    )

    quote_contract = get_token_contract(

        w3,

        quote_token,

    )

    block = w3.eth.get_block(

        "latest"

    )

    deadline = (

        int(

            block[

                "timestamp"

            ]

        )

        + 600

    )

    # --------------------------------------------------------

    # BEFORE BALANCES

    # --------------------------------------------------------

    before_token_balance = get_balance(

        token_contract,

        buyer,

    )

    before_quote_balance = get_balance(

        quote_contract,

        buyer,

    )

    # --------------------------------------------------------

    # BUILD BUY TRANSACTION

    # --------------------------------------------------------

    tx = (

        router.functions

        .swapExactTokensForTokensSupportingFeeOnTransferTokens(

            int(amount),

            0,

            [

                quote_token,

                token_address,

            ],

            buyer,

            deadline,

        )

        .build_transaction(

            {

                "from": buyer,

                "gas": 1500000,

                "gasPrice": w3.eth.gas_price,

                "nonce": w3.eth.get_transaction_count(

                    buyer

                ),

            }

        )

    )

    tx_hash = w3.eth.send_transaction(

        tx

    )

    receipt = wait_for_receipt(

        w3,

        tx_hash,

    )

    receipt_status = int(

        receipt.get(

            "status",

            0,

        )

    )

    # --------------------------------------------------------

    # AFTER BALANCES

    # --------------------------------------------------------

    after_token_balance = get_balance(

        token_contract,

        buyer,

    )

    after_quote_balance = get_balance(

        quote_contract,

        buyer,

    )

    token_received = max(

        after_token_balance

        - before_token_balance,

        0,

    )

    quote_spent = max(

        before_quote_balance

        - after_quote_balance,

        0,

    )

    # --------------------------------------------------------

    # --------------------------------------------------------
    # TRANSFER EVENT INSPECTION
    # --------------------------------------------------------

    transfer_topic = _normalize_hex(
        Web3.keccak(text="Transfer(address,address,uint256)")
    ).lower()

    token_transfer_events = []
    token_address_checksum = Web3.to_checksum_address(token_address)
    buyer_checksum = Web3.to_checksum_address(buyer)

    for log in receipt.get("logs", []):
        try:
            log_address = Web3.to_checksum_address(
                _normalize_hex(log.get("address"))
            )

            if log_address.lower() != token_address_checksum.lower():
                continue

            topics = log.get("topics", [])
            if not isinstance(topics, (list, tuple)):
                topics = list(topics)

            if len(topics) < 3:
                continue

            if _normalize_hex(topics[0]).lower() != transfer_topic:
                continue

            token_transfer_events.append(
                {
                    "from": _decode_transfer_address(topics[1]),
                    "to": _decode_transfer_address(topics[2]),
                    "value": _decode_transfer_value(
                        log.get("data", "0x0")
                    ),
                }
            )

        except Exception:
            continue

    # Determine whether a token transfer to BUYER occurred.

    # --------------------------------------------------------

    event_received = 0

    for event in token_transfer_events:

        if (

            event[

                "to"

            ].lower()

            == buyer.lower()

        ):

            event_received += int(

                event[

                    "value"

                ]

            )

    # --------------------------------------------------------

    # Success determination

    #

    # Balance increase is primary evidence.

    # Transfer event is secondary diagnostic evidence.

    # --------------------------------------------------------

    success = (

        receipt_status == 1

        and token_received > 0

    )

    return {

        "success": success,

        "tx_hash": tx_hash.hex(),

        "gas_used": int(

            receipt.get(

                "gasUsed",

                0,

            )

        ),

        "receipt_status": receipt_status,

        "before_token_balance": int(

            before_token_balance

        ),

        "after_token_balance": int(

            after_token_balance

        ),

        "token_received": int(

            token_received

        ),

        "before_quote_balance": int(

            before_quote_balance

        ),

        "after_quote_balance": int(

            after_quote_balance

        ),

        "quote_spent": int(

            quote_spent

        ),

        "token_transfer_events": (

            token_transfer_events

        ),

        "event_received": int(

            event_received

        ),

    }

# ============================================================

# TEMPORARY BUY QUOTE-TOKEN FUNDING

# ============================================================

def fund_buyer_with_quote_token(

    w3,

    quote_token,

    pair_address,

    buyer_address,

    amount,

):

    """

    Fund the simulated buyer with quote tokens from a real

    quote-token holder.

    The transfer happens ONLY inside the temporary Anvil fork.

    The LP pair itself is never modified for funding.

    """

    quote_token = Web3.to_checksum_address(

        quote_token

    )

    pair_address = Web3.to_checksum_address(

        pair_address

    )

    buyer_address = Web3.to_checksum_address(

        buyer_address

    )

    quote_contract = get_token_contract(

        w3,

        quote_token,

    )

    # --------------------------------------------------------

    # Known quote-token holders discovered from Alchemy.

    #

    # These are candidate addresses with positive live

    # quote-token balances. The first usable holder is used.

    # --------------------------------------------------------

    quote_funding_candidates = [

        "0x8366a39CC670B4001A1121B8F6A443A643e40951",

        "0xE9713f453aDB9245B19559790c96F470a18F2fDF",

        "0xfac1d7dC76bE90C5Cadd5B022af7838dd8190F16",

        "0x1A18a8b96eac3F980133A18402d04194f1FAA4E7",

        "0xA9877C8A990CA2EEBa4dD3eE9ab4D2395c9F8b23",

        "0x2782B5b3fD9B7c5FB3cfB11a730A7b7e480A0e33",

    ]

    # --------------------------------------------------------

    # Amount required.

    # --------------------------------------------------------

    requested_amount = int(

        amount

    )

    if requested_amount <= 0:

        raise RuntimeError(

            "Temporary BUY funding amount is zero."

        )

    # --------------------------------------------------------

    # Try real quote-token holders in order.

    # --------------------------------------------------------

    for source_address in quote_funding_candidates:

        source_address = Web3.to_checksum_address(

            source_address

        )

        if (

            source_address.lower()

            == pair_address.lower()

        ):

            continue

        if (

            source_address.lower()

            == buyer_address.lower()

        ):

            continue

        source_balance = get_balance(

            quote_contract,

            source_address,

        )

        if source_balance < requested_amount:

            continue

        # ----------------------------------------------------

        # Impersonate source holder only inside Anvil.

        # ----------------------------------------------------

        impersonate_account(

            w3,

            source_address,

        )

        try:

            # Give the impersonated holder temporary gas.

            set_account_balance(

                w3,

                source_address,

            )

            buyer_balance_before = get_balance(

                quote_contract,

                buyer_address,

            )

            tx = quote_contract.functions.transfer(

                buyer_address,

                requested_amount,

            ).build_transaction(

                {

                    "from": source_address,

                    "gas": 300000,

                    "gasPrice": w3.eth.gas_price,

                    "nonce": w3.eth.get_transaction_count(

                        source_address

                    ),

                }

            )

            tx_hash = w3.eth.send_transaction(

                tx

            )

            receipt = wait_for_receipt(

                w3,

                tx_hash,

            )

            if int(

                receipt.get(

                    "status",

                    0,

                )

            ) != 1:

                continue

            buyer_balance_after = get_balance(

                quote_contract,

                buyer_address,

            )

            received = max(

                buyer_balance_after

                - buyer_balance_before,

                0,

            )

            if received <= 0:

                continue

            return {

                "requested": requested_amount,

                "received": int(

                    received

                ),

                "source": source_address,

                "tx_hash": tx_hash.hex(),

                "gas_used": int(

                    receipt.get(

                        "gasUsed",

                        0,

                    )

                ),

            }

        finally:

            stop_impersonating(

                w3,

                source_address,

            )

    raise RuntimeError(

        "No suitable real quote-token holder had enough "

        "balance to fund the temporary BUY."

    )

# ============================================================

# SINGLE FORKED BUY TEST

# ============================================================

def calculate_v2_expected_output(
    amount_in,
    reserve_in,
    reserve_out,
):
    try:
        amount_in = int(amount_in)
        reserve_in = int(reserve_in)
        reserve_out = int(reserve_out)
    except Exception:
        return None

    if (
        amount_in <= 0
        or reserve_in <= 0
        or reserve_out <= 0
    ):
        return None

    amount_in_with_fee = (
        amount_in * 997
    )

    numerator = (
        amount_in_with_fee
        * reserve_out
    )

    denominator = (
        reserve_in * 1000
        + amount_in_with_fee
    )

    if denominator <= 0:
        return None

    return (
        numerator
        // denominator
    )

def run_isolated_buy_test(
    token_address,
    quote_token,
    pair_address,
    buyer_address,
    label,
    amount,
    version="V2",
    fee=3000,
):
    test = {
        "side": "BUY",
        "label": label,
        "amount_in": int(amount),
        "success": False,
        "fork_used": False,
        "funding": False,
        "approval": False,
        "quote_balance_verified": False,
        "token_received": 0,
        "quote_spent": 0,
        "event_received": 0,
        "tx_hash": None,
        "gas_used": None,
        "receipt_status": None,
        "before_token_balance": 0,
        "after_token_balance": 0,
        "before_quote_balance": 0,
        "after_quote_balance": 0,
        "error": None,
        "protocol": "Uniswap V3" if str(version).upper() == "V3" else "Uniswap V2",
        "fee_tier": int(fee) if str(version).upper() == "V3" else None,
    }

    process = None
    fork_w3 = None
    buyer_address = Web3.to_checksum_address(buyer_address)
    pair_address = Web3.to_checksum_address(pair_address)

    try:
        process = start_anvil()

        fork_w3 = get_web3(
            ANVIL_RPC_URL
        )

        test["fork_used"] = True

        impersonate_account(
            fork_w3,
            buyer_address,
        )

        set_account_balance(
            fork_w3,
            buyer_address,
        )

        funding = fund_buyer_with_quote_token(
            fork_w3,
            quote_token,
            pair_address,
            buyer_address,
            amount,
        )

        received_quote = int(
            funding["received"]
        )

        test["funding"] = True

        if received_quote <= 0:
            raise RuntimeError(
                "Temporary BUY quote-token funding produced zero balance."
            )

        test["quote_balance_verified"] = True

        quote_contract = get_token_contract(
            fork_w3,
            quote_token,
        )

        approval = approve_router(
            fork_w3,
            quote_contract,
            buyer_address,
            received_quote,
            router_address=(
                UNISWAP_V3_ROUTER
                if str(version).upper() == "V3"
                else UNISWAP_V2_ROUTER
            ),
        )

        test["approval"] = True

        is_v3 = str(version).upper() == "V3"
        router = get_v3_router(fork_w3) if is_v3 else get_router(fork_w3)

        # --------------------------------------------------------
        # V2 EXPECTED BUY OUTPUT
        # --------------------------------------------------------

        if is_v3:
            expected_token_received = None
            v3_buy = execute_v3_swap(
                fork_w3, router, buyer_address, quote_token,
                token_address, fee, received_quote,
            )
            buy = {
                **v3_buy,
                "token_received": v3_buy.get("output_received", 0),
                "quote_spent": v3_buy.get("input_spent", 0),
            }
        else:
            pair_contract = fork_w3.eth.contract(
                address=pair_address,
                abi=PAIR_ABI,
            )
            reserve0, reserve1, _ = pair_contract.functions.getReserves().call()
            token0 = Web3.to_checksum_address(pair_contract.functions.token0().call())
            quote_checksum = Web3.to_checksum_address(quote_token)
            token_checksum = Web3.to_checksum_address(token_address)
            if token0.lower() == quote_checksum.lower():
                quote_reserve, token_reserve = int(reserve0), int(reserve1)
            elif token0.lower() == token_checksum.lower():
                quote_reserve, token_reserve = int(reserve1), int(reserve0)
            else:
                raise RuntimeError("BUY pair tokens do not match quote/token addresses.")
            expected_token_received = calculate_v2_expected_output(
                received_quote, quote_reserve, token_reserve
            )
            buy = execute_buy(
                fork_w3, router, buyer_address, token_address,
                quote_token, received_quote,
            )

        actual_token_received = int(
            buy.get(
                "token_received",
                0,
            )
            or 0
        )

        runtime_buy_tax = None

        if (
            expected_token_received is not None
            and expected_token_received > 0
            and actual_token_received >= 0
            and actual_token_received <= expected_token_received
        ):
            runtime_buy_tax = (
                (
                    expected_token_received
                    - actual_token_received
                )
                / expected_token_received
                * 100
            )

        test[
            "expected_token_received"
        ] = int(
            expected_token_received or 0
        )

        test[
            "runtime_buy_tax"
        ] = runtime_buy_tax

        test["success"] = bool(
            buy.get("success")
        )

        test["token_received"] = int(
            buy.get(
                "token_received",
                0,
            )
        )

        test["receipt_status"] = buy.get(
            "receipt_status"
        )

        test["quote_spent"] = int(
            buy.get(
                "quote_spent",
                0,
            )
        )

        test["event_received"] = int(
            buy.get(
                "event_received",
                0,
            )
        )

        test["tx_hash"] = buy.get(
            "tx_hash"
        )

        test["gas_used"] = buy.get(
            "gas_used"
        )

        test["before_token_balance"] = int(
            buy.get(
                "before_token_balance",
                0,
            )
        )

        test["after_token_balance"] = int(
            buy.get(
                "after_token_balance",
                0,
            )
        )

        test["before_quote_balance"] = int(
            buy.get(
                "before_quote_balance",
                0,
            )
        )

        test["after_quote_balance"] = int(
            buy.get(
                "after_quote_balance",
                0,
            )
        )

        if not test["success"]:
            test["error"] = (
                "BUY execution did not produce a positive "
                "token balance increase."
            )

    except Exception as e:
        test["error"] = str(e)

    finally:
        try:
            if fork_w3:
                stop_impersonating(
                    fork_w3,
                    buyer_address,
                )
        except Exception:
            pass

        stop_anvil(
            process
        )

    return test

# ============================================================

# TEST SIZE BUILDER

# ============================================================

def build_test_amounts(

    balance,

):

    try:

        balance = int(

            balance

        )

    except Exception:

        return []

    if balance <= 0:

        return []

    # Independent tests:

    #

    # 0.01%

    # 0.10%

    # 1%

    # 10%

    #

    # Every percentage is tested on a NEW Anvil fork.

    percentages = [

        (

            "0.01%",

            10000,

        ),

        (

            "0.10%",

            1000,

        ),

        (

            "1.00%",

            100,

        ),

        (

            "10.00%",

            10,

        ),

    ]

    tests = []

    for label, divisor in percentages:

        amount = max(

            1,

            balance // divisor,

        )

        if amount > balance:

            continue

        tests.append(

            {

                "label": label,

                "amount": int(

                    amount

                ),

            }

        )

    return tests

# ============================================================

# SINGLE FORKED SELL TEST

# ============================================================

def run_isolated_sell_test(
    token_address,
    quote_token,
    pair_address,
    holder_address,
    expected_balance,
    label,
    amount,
    version="V2",
    fee=3000,
):
    test = {
        "side": "SELL",
        "label": label,
        "amount_in": int(amount),
        "success": False,
        "fork_used": False,
        "approval": False,
        "token_balance_verified": False,
        "tx_hash": None,
        "gas_used": None,
        "receipt_status": None,
        "token_spent": 0,
        "quote_received": 0,
        "event_spent": 0,
        "event_received": 0,
        "event_pair_token_received": 0,
        "before_token_balance": 0,
        "after_token_balance": 0,
        "before_quote_balance": 0,
        "after_quote_balance": 0,
        "error": None,
        "protocol": "Uniswap V3" if str(version).upper() == "V3" else "Uniswap V2",
        "fee_tier": int(fee) if str(version).upper() == "V3" else None,
    }

    process = None
    fork_w3 = None

    holder_address = Web3.to_checksum_address(
        holder_address
    )

    pair_address = Web3.to_checksum_address(
        pair_address
    )

    try:
        process = start_anvil()

        fork_w3 = get_web3(
            ANVIL_RPC_URL
        )

        test["fork_used"] = True

        # ----------------------------------------------------
        # Impersonate real holder.
        # ----------------------------------------------------

        impersonate_account(
            fork_w3,
            holder_address,
        )

        # ----------------------------------------------------
        # Give only simulated native balance.
        # ----------------------------------------------------

        set_account_balance(
            fork_w3,
            holder_address,
        )

        # ----------------------------------------------------
        # Verify token balance exists in fork.
        # ----------------------------------------------------

        token = get_token_contract(
            fork_w3,
            token_address,
        )

        fork_balance = get_balance(
            token,
            holder_address,
        )

        if fork_balance <= 0:
            raise RuntimeError(
                "Holder token balance was not available "
                "inside the temporary fork."
            )

        test["token_balance_verified"] = True

        # Never sell more than actually exists.
        amount = min(
            int(amount),
            fork_balance,
        )

        if amount <= 0:
            raise RuntimeError(
                "Deep SELL amount became zero after "
                "fork balance validation."
            )

        # ----------------------------------------------------
        # Temporary approval.
        # ----------------------------------------------------

        approval = approve_router(
            fork_w3,
            token,
            holder_address,
            amount,
            router_address=(
                UNISWAP_V3_ROUTER
                if str(version).upper() == "V3"
                else UNISWAP_V2_ROUTER
            ),
        )

        test["approval"] = True

        # ----------------------------------------------------
        # SELL.
        # ----------------------------------------------------

        if str(version).upper() == "V3":
            router = get_v3_router(fork_w3)
            v3_sell = execute_v3_swap(
                fork_w3, router, holder_address, token_address,
                quote_token, fee, amount,
            )
            sell = {
                **v3_sell,
                "token_spent": v3_sell.get("input_spent", 0),
                "quote_received": v3_sell.get("output_received", 0),
                "before_token_balance": v3_sell.get("before_input_balance", 0),
                "after_token_balance": v3_sell.get("after_input_balance", 0),
                "before_quote_balance": v3_sell.get("before_output_balance", 0),
                "after_quote_balance": v3_sell.get("after_output_balance", 0),
                "event_spent": 0,
                "event_received": 0,
                "event_pair_token_received": 0,
                "error": v3_sell.get("error"),
            }
        else:
            router = get_router(fork_w3)
            sell = execute_sell(
                fork_w3, router, holder_address, token_address,
                quote_token, pair_address, amount,
            )

        test["success"] = bool(
            sell.get("success")
        )

        test["tx_hash"] = sell.get(
            "tx_hash"
        )

        test["gas_used"] = sell.get(
            "gas_used"
        )

        test["receipt_status"] = sell.get(
            "receipt_status"
        )

        test["token_spent"] = int(
            sell.get(
                "token_spent",
                0,
            )
        )

        test["quote_received"] = int(
            sell.get(
                "quote_received",
                0,
            )
        )

        test["event_spent"] = int(
            sell.get(
                "event_spent",
                0,
            )
        )

        test["event_received"] = int(
            sell.get(
                "event_received",
                0,
            )
        )

        test["event_pair_token_received"] = int(
            sell.get(
                "event_pair_token_received",
                0,
            )
        )

        test["before_token_balance"] = int(
            sell.get(
                "before_token_balance",
                0,
            )
        )

        test["after_token_balance"] = int(
            sell.get(
                "after_token_balance",
                0,
            )
        )

        test["before_quote_balance"] = int(
            sell.get(
                "before_quote_balance",
                0,
            )
        )

        test["after_quote_balance"] = int(
            sell.get(
                "after_quote_balance",
                0,
            )
        )

        if not test["success"]:
            test["error"] = sell.get("error") or (
                "Router SELL transaction reverted "
                "inside the temporary fork."
            )

    except Exception as e:
        test["error"] = str(e)

    finally:
        try:
            if fork_w3:
                stop_impersonating(
                    fork_w3,
                    holder_address,
                )
        except Exception:
            pass

        stop_anvil(
            process
        )

    return test

# ============================================================

# INFRASTRUCTURE ERROR DETECTION

# ============================================================

def _is_infrastructure_error(

    error,

):

    """

    Return True when a deep-test failure appears to come from

    RPC/Anvil infrastructure rather than the token/router itself.

    """

    if not error:

        return False

    text = str(

        error

    ).lower()

    infrastructure_markers = [

        "anvil did not become ready",

        "http error 403",

        "cloudflare",

        "just a moment",

        "failed to get account",

        "connection refused",

        "connection reset",

        "connection aborted",

        "timed out",

        "timeout",

        "rpc request failed",

        "unable to connect to rpc",
        "no suitable real quote-token holder had enough balance",

    ]

    return any(

        marker in text

        for marker in infrastructure_markers

    )

# ============================================================
# RUNTIME SELL TAX
# ============================================================

def calculate_runtime_sell_tax(
    test,
):

    if not isinstance(
        test,
        dict,
    ):
        return None

    if not test.get(
        "success"
    ):
        return None

    token_spent = int(
        test.get(
            "token_spent",
            0,
        )
        or 0
    )

    # A missing/zero pair Transfer-event amount means the pool receipt was
    # not measured. Treating that as zero would falsely report a 100% tax,
    # especially for V3 tests that currently verify swap balances instead.
    raw_pair_received = test.get("event_pair_token_received")
    if raw_pair_received is None:
        return None
    pair_received = int(raw_pair_received or 0)

    if token_spent <= 0:
        return None

    if pair_received <= 0:
        return None

    tax_amount = max(
        token_spent - pair_received,
        0,
    )

    return (
        tax_amount
        / token_spent
        * 100
    )

# ============================================================

# MAIN ANALYSIS

# ============================================================

def _run_specific_wallet_sell_test(token_address, liquidity, wallet_address):
    result = {
        "address": Web3.to_checksum_address(wallet_address),
        "status": "INCONCLUSIVE",
        "tested": False,
        "success": None,
        "balance": 0,
        "amount_in": 0,
        "tx_hash": None,
        "error": None,
        "warning": "Runs only inside a temporary local fork; no mainnet transaction is sent.",
    }
    pair_address = liquidity.get("pair") or liquidity.get("pair_address")
    quote_token = liquidity.get("quote_token")
    if not pair_address or not quote_token:
        result["error"] = "A supported pair and quote token are required."
        return result
    try:
        w3 = get_web3(RPC_URL)
        token = get_token_contract(w3, token_address)
        balance = int(get_balance(token, wallet_address))
        result["balance"] = balance
        if balance <= 0:
            result["error"] = "The supplied wallet has no token balance at the current block."
            return result
        amount = max(1, balance // 100)
        result["amount_in"] = amount
        test = run_isolated_sell_test(
            token_address,
            quote_token,
            pair_address,
            wallet_address,
            balance,
            "1% of supplied wallet balance",
            amount,
            version=liquidity.get("version", "V2"),
            fee=(liquidity.get("fee") or (liquidity.get("best_pool_data") or {}).get("fee") or 3000),
        )
        result.update({
            "status": "PASS" if test.get("success") else "FAIL",
            "tested": True,
            "success": bool(test.get("success")),
            "tx_hash": test.get("tx_hash"),
            "gas_used": test.get("gas_used"),
            "quote_received": test.get("quote_received"),
            "error": test.get("error"),
        })
    except Exception as exc:
        result["error"] = str(exc)
    return result


def _attach_wallet_specific_sell_test(result, token_address, liquidity, check_address):
    wallet_test = _run_specific_wallet_sell_test(token_address, liquidity, check_address)
    result["wallet_specific_sell_test"] = wallet_test
    if wallet_test["status"] == "FAIL":
        result["tested"] = True
        result["status"] = "WARNING"
        result["risk"] = "HIGH"
        result["warnings"].append(
            "The supplied wallet's router SELL failed in the temporary fork at the scan-time state. Review the failure details; one fork result is not proof of a permanent honeypot."
        )
    elif wallet_test["status"] == "PASS":
        result["tested"] = True
        if result.get("status") in ("UNAVAILABLE", "UNKNOWN"):
            result["status"] = "PASS"
            result["risk"] = "LOW"
            result["confidence"] = "MEDIUM"
        result["signals"].append(
            "Router SELL succeeded for the supplied wallet in a temporary fork at scan time."
        )
    else:
        result["warnings"].append(
            "A wallet-specific router SELL could not be confirmed; see wallet_specific_sell_test.error."
        )


def analyze_swap_simulation(

    token_address,

    liquidity,

    holders=None,

    deep=False,

    check_address=None,

):

    result = {

        "status": "UNAVAILABLE",

        "risk": "UNKNOWN",

        "confidence": "LOW",

        "tested": False,

        "deep": bool(

            deep

        ),

        "method": (

            "ANVIL_FORK_UNISWAP_V2_BUY_SELL"

        ),

        "fork_block": None,

        "holder": None,

        "holder_balance": 0,

        "tests": [],

        "buy_tests": [],

        "buy_tested": False,

        "runtime_sell_tax": None,

        "runtime_sell_tax_samples": [],

        "runtime_buy_tax": None,

        "runtime_buy_tax_samples": [],

        "warnings": [],

        "signals": [],

    }

    # ========================================================

    # NORMAL MODE

    # ========================================================

    if not deep:

        result["status"] = "SKIPPED"

        result["risk"] = "UNKNOWN"

        result["confidence"] = "NONE"

        result["warnings"].append(

            "Deep router swap execution testing was skipped "

            "for the normal scan."

        )

        result["signals"].append(

            "Run scanner.py with --deep to perform "

            "temporary-fork router execution testing."

        )

        return result

    # ========================================================

    # LIQUIDITY

    # ========================================================

    if not isinstance(

        liquidity,

        dict,

    ):

        result["warnings"].append(

            "Liquidity data was invalid."

        )

        return result

    if not liquidity.get(

        "found"

    ):

        result["warnings"].append(

            "Deep router simulation was not performed because "

            "no supported liquidity pool was detected."

        )

        return result

    dex = str(liquidity.get("dex") or "").strip().lower()
    version = str(liquidity.get("version") or "").strip().upper()
    is_v3 = version == "V3" or "v3" in dex
    is_v2 = version == "V2" or "v2" in dex
    if not (is_v2 or is_v3):
        result["warnings"].append(
            f"Deep router simulation does not support detected pool type: {liquidity.get('dex') or 'unknown'}."
        )
        return result

    fee = liquidity.get("fee")
    best_pool_data = liquidity.get("best_pool_data")
    if fee is None and isinstance(best_pool_data, dict):
        fee = best_pool_data.get("fee")
    try:
        fee = int(fee) if fee is not None else None
    except (TypeError, ValueError):
        fee = None
    if is_v3 and fee not in V3_FEE_TIERS:
        result["warnings"].append(
            "Deep V3 swap testing is unavailable because the pool fee tier is missing or unsupported."
        )
        return result
    if is_v3:
        pool_data = liquidity.get("best_pool_data")
        pool_data = pool_data if isinstance(pool_data, dict) else {}
        active_liquidity = liquidity.get(
            "v3_liquidity",
            pool_data.get("v3_liquidity"),
        )
        try:
            active_liquidity = int(active_liquidity)
        except (TypeError, ValueError):
            active_liquidity = None
        if active_liquidity == 0:
            result["pool_active_liquidity"] = 0
            result["warnings"].append(
                "V3 pool reports zero active liquidity at the current price. Router swaps were not attempted; positions outside the current price range were not analyzed. This does not establish whether token transfer restrictions exist."
            )
            return result
    if is_v3:
        result["method"] = "ANVIL_FORK_UNISWAP_V3_BUY_SELL"
        result["router"] = UNISWAP_V3_ROUTER
        result["fee_tier"] = fee
        result["warnings"].append(
            "Uniswap V3 exactInputSingle does not support fee-on-transfer tokens; a reverted swap can indicate V3 incompatibility and is not by itself proof of a honeypot."
        )

    # ========================================================

    # ADDRESSES

    # ========================================================

    token_address = safe_checksum(

        token_address

    )

    quote_token = safe_checksum(

        liquidity.get(

            "quote_token"

        )

    )

    if not quote_token:

        best_pool = liquidity.get(

            "best_pool",

            {},

        )

        if isinstance(

            best_pool,

            dict,

        ):

            quote_token = safe_checksum(

                best_pool.get(

                    "quote_token"

                )

            )

    if not token_address:

        result["warnings"].append(

            "Target token address is invalid."

        )

        return result

    if not quote_token:

        result["warnings"].append(

            "Quote token could not be determined."

        )

        return result

    # ========================================================

    # LIVE CHAIN

    # ========================================================

    try:

        live_w3 = get_web3(

            RPC_URL

        )

        live_token = get_token_contract(

            live_w3,

            token_address,

        )

        if is_v3:
            chain_id = int(live_w3.eth.chain_id)
            if chain_id != 4663:
                result["warnings"].append(
                    f"Deep V3 swap testing requires Robinhood Chain (4663); connected chain is {chain_id}."
                )
                return result
            router_code = live_w3.eth.get_code(UNISWAP_V3_ROUTER)
            if not router_code or not any(router_code):
                result["warnings"].append(
                    "The configured Uniswap V3 SwapRouter02 has no deployed code on the connected chain."
                )
                return result

    except Exception as e:

        result["status"] = "ERROR"

        result["warnings"].append(

            "Unable to connect to Robinhood Chain RPC: "

            + str(e)

        )

        return result

    # ========================================================

    # FIND REAL HOLDER

    # ========================================================

    pair_address = safe_checksum(

        liquidity.get(

            "pair"

        )

    )

    excluded_holder_addresses = []

    if pair_address:

        excluded_holder_addresses.append(

            pair_address

        )

    holder = find_test_holder(

        live_token,

        holders,

        excluded_addresses=excluded_holder_addresses,

    )

    if not holder:

        result["warnings"].append(

            "No discovered token holder with a positive "

            "on-chain token balance was found."

        )

        if check_address:
            _attach_wallet_specific_sell_test(
                result, token_address, liquidity, check_address
            )

        return result

    holder_address = safe_checksum(

        holder.get(

            "address"

        )

    )

    holder_balance = int(

        holder.get(

            "balance",

            0,

        )

    )

    if not holder_address:

        result["warnings"].append(

            "Selected holder address was invalid."

        )

        return result

    if holder_balance <= 0:

        result["warnings"].append(

            "Selected holder has no positive token balance."

        )

        return result

    result[

        "holder"

    ] = holder_address

    result[

        "holder_balance"

    ] = holder_balance

    # ========================================================

    # BUILD SIZES

    # ========================================================

    size_tests = build_test_amounts(

        holder_balance

    )

    if not size_tests:

        result["warnings"].append(

            "No valid deep SELL test sizes could be created."

        )

        return result

    result[

        "signals"

    ].append(

        "Deep SELL testing uses an independent temporary "

        "Anvil fork for each size."

    )

    result[

        "signals"

    ].append(

        f"Testing {len(size_tests)} holder-balance sizes."

    )

    # ========================================================

    # RUN ISOLATED TESTS

    # ========================================================

    passed = 0

    failed = 0

    for index, size_test in enumerate(

        size_tests,

        start=1,

    ):

        label = size_test[

            "label"

        ]

        amount = size_test[

            "amount"

        ]

        test = run_isolated_sell_test(
            token_address,
            quote_token,
            pair_address,
            holder_address,
            holder_balance,
            label,
            amount,
            version="V3" if is_v3 else "V2",
            fee=fee or 3000,
        )

        test[

            "index"

        ] = index

        test[

            "percentage_of_holder"

        ] = label

        result[

            "tests"

        ].append(

            test

        )

        if test.get(

            "success"

        ):

            passed += 1

        else:

            failed += 1

    result[

        "tested"

    ] = (

        len(

            result["tests"]

        ) > 0

    )

    # ========================================================
    # RUNTIME SELL TAX
    # ========================================================

    runtime_sell_tax_samples = []

    for test in result.get(
        "tests",
        [],
    ):

        runtime_tax = calculate_runtime_sell_tax(
            test
        )

        if runtime_tax is not None:

            runtime_sell_tax_samples.append(
                runtime_tax
            )

    if runtime_sell_tax_samples:

        result[
            "runtime_sell_tax_samples"
        ] = runtime_sell_tax_samples

        result[
            "runtime_sell_tax"
        ] = (
            sum(
                runtime_sell_tax_samples
            )
            / len(
                runtime_sell_tax_samples
            )
        )
    elif any(
        str(test.get("protocol", "")).upper() == "UNISWAP V3"
        for test in result.get("tests", [])
    ):
        result.setdefault("warnings", []).append(
            "Runtime V3 sell tax was not calculated because the token amount "
            "credited to the pool was not measured from Transfer events. "
            "Successful fork swaps do not by themselves prove zero sell tax."
        )

    # ========================================================

    # FINAL CLASSIFICATION

    # ========================================================

    if (

        passed == len(

            size_tests

        )

        and passed > 0

    ):

        result[

            "status"

        ] = "PASS"

        result[

            "risk"

        ] = "LOW"

        result[

            "confidence"

        ] = "HIGH"

        result[

            "signals"

        ].append(

            f"All {passed} isolated deep SELL simulations "

            "completed successfully."

        )

        result[

            "signals"

        ].append(

            "SELL succeeded across all tested holder-balance sizes."

        )

        result[

            "warnings"

        ].append(

            "Deep SELL tests execute only inside temporary "

            "local forks. No transaction was broadcast to "

            "Robinhood Chain."

        )

    elif passed > 0:

        result[

            "status"

        ] = "WARNING"

        result[

            "risk"

        ] = "MEDIUM"

        result[

            "confidence"

        ] = "HIGH"

        result[

            "signals"

        ].append(

            f"{passed} of {passed + failed} deep SELL "

            "sizes succeeded."

        )

        result[

            "warnings"

        ].append(

            f"{failed} deep SELL size simulations failed. "

            "This may indicate size-dependent transfer, "

            "tax, limit, or router behavior."

        )

        result[

            "warnings"

        ].append(

            "All deep tests were performed in temporary "

            "local forks; no real transaction was broadcast."

        )

    else:

        infrastructure_failures = 0

        for test in result.get(

            "tests",

            [],

        ):

            if not isinstance(

                test,

                dict,

            ):

                continue

            if _is_infrastructure_error(

                test.get(

                    "error"

                )

            ):

                infrastructure_failures += 1

        if (

            infrastructure_failures

            == len(

                result.get(

                    "tests",

                    [],

                )

            )

            and infrastructure_failures > 0

        ):

            result[

                "status"

            ] = "UNAVAILABLE"

            result[

                "risk"

            ] = "UNKNOWN"

            result[

                "confidence"

            ] = "LOW"

            result[

                "warnings"

            ].append(

                "Deep SELL execution could not be completed "

                "because the temporary fork infrastructure was "

                "unavailable."

            )

            result["warnings"].append(
                "This infrastructure failure is not evidence that the token is a honeypot."
            )

        else:
            result["status"] = "WARNING"
            result["risk"] = "HIGH"
            result["confidence"] = "HIGH"
            result["warnings"].append(
                "All deep SELL simulations failed inside temporary local forks."
            )

    if is_v3 and passed == 0 and result.get("status") != "UNAVAILABLE":
        result["status"] = "WARNING"
        result["risk"] = "MEDIUM"
        result["confidence"] = "LOW"
        result["warnings"].append(
            "All V3 deep SELL attempts failed. The result cannot distinguish token restrictions from V3 fee-on-transfer incompatibility or pool/router conditions."
        )

    # ========================================================

    # DEEP BUY EXECUTION

    # ========================================================

    pair_address = safe_checksum(

        liquidity.get(

            "pair"

        )

    )

    if not pair_address:

        result["warnings"].append(

            "Deep BUY execution was skipped because the "

            "liquidity-pair address could not be determined."

        )

        return result

    pair_quote_balance = 0

    try:

        pair_quote_balance = get_balance(

            get_token_contract(

                live_w3,

                quote_token,

            ),

            pair_address,

        )

    except Exception:

        pair_quote_balance = 0

    buy_size_tests = build_test_amounts(

        pair_quote_balance

    )

    if not buy_size_tests:

        result["warnings"].append(

            "No valid deep BUY test sizes could be created "

            "from the LP quote-token balance."

        )

        return result

    result["signals"].append(

        "Deep BUY testing uses independent temporary Anvil forks and funds the buyer from a real quote-token holder only inside each fork."

    )

    buy_passed = 0

    buy_failed = 0

    for index, buy_size_test in enumerate(

        buy_size_tests,

        start=1,

    ):

        buy_label = buy_size_test[

            "label"

        ]

        buy_amount = buy_size_test[

            "amount"

        ]

        buy_test = run_isolated_buy_test(

            token_address,

            quote_token,

            pair_address,

            holder_address,

            buy_label,

            buy_amount,

            version="V3" if is_v3 else "V2",

            fee=fee or 3000,

        )

        buy_test[

            "index"

        ] = index

        result[

            "buy_tests"

        ].append(

            buy_test

        )

        if buy_test.get(

            "success"

        ):

            buy_passed += 1

        else:

            buy_failed += 1

    result[

        "buy_tested"

    ] = (

        len(

            result[

                "buy_tests"

            ]

        ) > 0

    )

    # ========================================================
    # RUNTIME BUY TAX
    # ========================================================

    runtime_buy_tax_samples = []

    for test in result.get(
        "buy_tests",
        [],
    ):

        runtime_tax = test.get(
            "runtime_buy_tax"
        )

        if (
            runtime_tax is not None
            and 0 <= runtime_tax <= 100
        ):

            runtime_buy_tax_samples.append(
                runtime_tax
            )

    if runtime_buy_tax_samples:

        result[
            "runtime_buy_tax_samples"
        ] = runtime_buy_tax_samples

        result[
            "runtime_buy_tax"
        ] = (
            sum(
                runtime_buy_tax_samples
            )
            / len(
                runtime_buy_tax_samples
            )
        )

    if (

        buy_passed

        == len(

            buy_size_tests

        )

        and buy_passed > 0

    ):

        result["signals"].append(

            f"All {buy_passed} isolated deep BUY simulations "

            "completed successfully."

        )

        result["signals"].append(

            "BUY succeeded across all tested quote-token sizes."

        )

    elif buy_passed > 0:

        result["warnings"].append(

            f"{buy_failed} of {buy_passed + buy_failed} deep BUY "

            "size simulations failed."

        )

    else:

        infrastructure_buy_failures = 0

        for buy_test in result.get(

            "buy_tests",

            [],

        ):

            if _is_infrastructure_error(

                buy_test.get(

                    "error"

                )

            ):

                infrastructure_buy_failures += 1

        if (

            infrastructure_buy_failures

            == len(

                result.get(

                    "buy_tests",

                    [],

                )

            )

            and infrastructure_buy_failures > 0

        ):

            result["warnings"].append(

                "Deep BUY execution could not be completed because "

                "the temporary fork infrastructure was unavailable."

            )

        else:

            result["warnings"].append(

                "All deep BUY simulations failed inside temporary "

                "local forks."

            )

    # --------------------------------------------------------

    # Combined BUY + SELL status

    # --------------------------------------------------------

    if (

        passed == len(size_tests)

        and passed > 0

        and buy_passed == len(buy_size_tests)

        and buy_passed > 0

    ):

        result["signals"].append(

            "Deep BUY and SELL router execution both succeeded "

            "inside temporary local forks."

        )

    if check_address:
        _attach_wallet_specific_sell_test(
            result, token_address, liquidity, check_address
        )

    return result

# ============================================================

# COMPATIBILITY WRAPPER

# ============================================================

def analyze(

    token_address,

    liquidity,

    holders=None,

    deep=False,

):

    return analyze_swap_simulation(

        token_address,

        liquidity,

        holders,

        deep=deep,

    )
