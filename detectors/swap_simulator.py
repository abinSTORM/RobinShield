import os
import socket
import subprocess
import time

from web3 import Web3

from config import RPC_URL

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
):

    holder = Web3.to_checksum_address(
        holder
    )

    tx = token.functions.approve(
        UNISWAP_V2_ROUTER,
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
        UNISWAP_V2_ROUTER,
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

    return {
        "success": (
            int(
                receipt.get(
                    "status",
                    0,
                )
            ) == 1
        ),
        "tx_hash": tx_hash.hex(),
        "gas_used": int(
            receipt.get(
                "gasUsed",
                0,
            )
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
    # TRANSFER EVENT INSPECTION
    # --------------------------------------------------------

    transfer_topic = Web3.keccak(
        text="Transfer(address,address,uint256)"
    ).hex()

    token_transfer_events = []

    for log in receipt.get(
        "logs",
        [],
    ):

        try:

            log_address = Web3.to_checksum_address(
                log.get(
                    "address"
                )
            )

        except Exception:

            continue

        if (
            log_address.lower()
            != token_address.lower()
        ):

            continue

        topics = log.get(
            "topics",
            []
        )

        if not isinstance(
            topics,
            list,
        ):

            continue

        if len(topics) < 3:

            continue

        topic0 = topics[0]

        if isinstance(
            topic0,
            bytes,
        ):

            topic0 = (
                "0x"
                + topic0.hex()
            )

        if (
            str(
                topic0
            ).lower()
            != transfer_topic.lower()
        ):

            continue

        try:

            from_address = (
                "0x"
                + (
                    topics[1].hex()
                    if isinstance(
                        topics[1],
                        bytes,
                    )
                    else str(
                        topics[1]
                    )[2:]
                )[-40:]
            )

            to_address = (
                "0x"
                + (
                    topics[2].hex()
                    if isinstance(
                        topics[2],
                        bytes,
                    )
                    else str(
                        topics[2]
                    )[2:]
                )[-40:]
            )

            transfer_value = int(
                log.get(
                    "data",
                    "0x0",
                ),
                16,
            )

            token_transfer_events.append(
                {
                    "from": Web3.to_checksum_address(
                        from_address
                    ),
                    "to": Web3.to_checksum_address(
                        to_address
                    ),
                    "value": transfer_value,
                }
            )

        except Exception:

            continue

    # --------------------------------------------------------
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

def run_isolated_buy_test(
    token_address,
    quote_token,
    pair_address,
    buyer_address,
    label,
    amount,
):

    test = {
        "side": "BUY",
        "label": label,
        "amount_in": int(
            amount
        ),
        "success": False,
        "fork_used": False,
        "funding": False,
        "approval": False,
        "quote_balance_verified": False,
        "token_received": 0,
        "tx_hash": None,
        "gas_used": None,
        "error": None,
    }

    process = None
    fork_w3 = None

    try:

        process = start_anvil()

        fork_w3 = get_web3(
            ANVIL_RPC_URL
        )

        test[
            "fork_used"
        ] = True

        buyer_address = Web3.to_checksum_address(
            buyer_address
        )

        pair_address = Web3.to_checksum_address(
            pair_address
        )

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
            funding[
                "received"
            ]
        )

        test[
            "funding"
        ] = True

        if received_quote <= 0:

            raise RuntimeError(
                "Temporary BUY quote-token funding produced zero balance."
            )

        test[
            "quote_balance_verified"
        ] = True

        quote_contract = get_token_contract(
            fork_w3,
            quote_token,
        )

        approval = approve_router(
            fork_w3,
            quote_contract,
            buyer_address,
            received_quote,
        )

        test[
            "approval"
        ] = True

        router = get_router(
            fork_w3
        )

        buy = execute_buy(
            fork_w3,
            router,
            buyer_address,
            token_address,
            quote_token,
            received_quote,
        )

        test[
            "success"
        ] = bool(
            buy.get(
                "success"
            )
        )

        test[
            "token_received"
        ] = int(
            buy.get(
                "token_received",
                0,
            )
        )

        test[
            "receipt_status"
        ] = buy.get(
            "receipt_status"
        )

        test[
            "quote_spent"
        ] = buy.get(
            "quote_spent",
            0,
        )

        test[
            "event_received"
        ] = buy.get(
            "event_received",
            0,
        )

        test[
            "tx_hash"
        ] = buy.get(
            "tx_hash"
        )

        test[
            "gas_used"
        ] = buy.get(
            "gas_used"
        )

        if not test[
            "success"
        ]:

            test[
                "error"
                ] = (
                    "BUY execution did not produce a positive "
                    "token balance increase."
                )

    except Exception as e:

        test[
            "error"
        ] = str(
            e
        )

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
    holder_address,
    expected_balance,
    label,
    amount,
):

    test = {
        "label": label,
        "amount_in": int(
            amount
        ),
        "success": False,
        "fork_used": False,
        "approval": False,
        "token_balance_verified": False,
        "tx_hash": None,
        "gas_used": None,
        "error": None,
    }

    process = None
    fork_w3 = None

    try:

        process = start_anvil()

        fork_w3 = get_web3(
            ANVIL_RPC_URL
        )

        test[
            "fork_used"
        ] = True

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

        test[
            "token_balance_verified"
        ] = True

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
        )

        test[
            "approval"
        ] = True

        # ----------------------------------------------------
        # SELL.
        # ----------------------------------------------------

        router = get_router(
            fork_w3
        )

        sell = execute_sell(
            fork_w3,
            router,
            holder_address,
            token_address,
            quote_token,
            amount,
        )

        test[
            "success"
        ] = bool(
            sell.get(
                "success"
            )
        )

        test[
            "tx_hash"
        ] = sell.get(
            "tx_hash"
        )

        test[
            "gas_used"
        ] = sell.get(
            "gas_used"
        )

        if not test[
            "success"
        ]:

            test[
                "error"
            ] = (
                "Router SELL transaction reverted "
                "inside the temporary fork."
            )

    except Exception as e:

        test[
            "error"
        ] = str(
            e
        )

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
    ]

    return any(
        marker in text
        for marker in infrastructure_markers
    )


# ============================================================
# MAIN ANALYSIS
# ============================================================

def analyze_swap_simulation(
    token_address,
    liquidity,
    holders=None,
    deep=False,
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

    if liquidity.get(
        "dex"
    ) != "Uniswap V2":

        result["warnings"].append(
            "Deep router simulation currently supports "
            "Uniswap V2 pools only."
        )

        return result

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
            holder_address,
            holder_balance,
            label,
            amount,
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

            result[
                "warnings"
            ].append(
                "This infrastructure failure is not evidence that "
                "the token is a honeypot."
            )

        else:

            result[
                "status"
            ] = "WARNING"

            result[
                "risk"
            ] = "HIGH"

            result[
                "confidence"
            ] = "HIGH"

            result[
                "warnings"
            ].append(
                "All deep SELL simulations failed inside "
                "temporary local forks."
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