import json
import os
import time

import requests
from web3 import Web3

from config import RPC_URL


# =========================================================
# CONFIG
# =========================================================

BASE_URL = (
    "https://robinhoodchain.blockscout.com/api/v2"
)

BLOCKSCOUT_PRO_BASE_URL = (
    "https://api.blockscout.com"
)

ROBINHOOD_CHAIN_ID = 4663

REQUEST_TIMEOUT = 20

HTTP_RETRIES = 2

HTTP_RETRY_DELAYS = (
    0.5,
    1.5,
)

# ---------------------------------------------------------
# Alchemy
# ---------------------------------------------------------

ALCHEMY_PAGE_SIZE = 100

# Normal scans must stay fast.
ALCHEMY_NORMAL_MAX_PAGES = 10

# Deep mode can inspect more transfer history.
ALCHEMY_DEEP_MAX_PAGES = 30

# Hard upper limit for candidate addresses.
ALCHEMY_MAX_CANDIDATES = 1000

# Number of eth_call requests sent in one JSON-RPC batch.
BALANCE_BATCH_SIZE = 50

# ---------------------------------------------------------
# RPC fallback
# ---------------------------------------------------------

RPC_CHUNK_SIZE = 5000
RPC_MIN_CHUNK_SIZE = 100

# ---------------------------------------------------------
# Cache
# ---------------------------------------------------------

CACHE_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "..",
        ".cache",
        "holders",
    )
)

CACHE_VERSION = 9


# =========================================================
# ENVIRONMENT
# =========================================================

def _read_env_value(
    name,
):
    """
    Read an environment variable.

    If it is not present in the process environment,
    read it directly from the project's .env file.

    This avoids requiring python-dotenv.
    """

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

                    value = value[
                        1:-1
                    ]

                elif (
                    len(value) >= 2
                    and value[0] == "'"
                    and value[-1] == "'"
                ):

                    value = value[
                        1:-1
                    ]

                return value.strip()

    except Exception:

        pass

    return None


BLOCKSCOUT_PRO_API_KEY = _read_env_value(
    "BLOCKSCOUT_API_KEY"
)

ALCHEMY_API_KEY = _read_env_value(
    "ALCHEMY_API_KEY"
)


# =========================================================
# ERC-20 CONSTANTS
# =========================================================

TRANSFER_TOPIC = (
    "0x"
    + Web3.keccak(
        text="Transfer(address,address,uint256)"
    ).hex()
)


BALANCE_OF_SELECTOR = (
    Web3.keccak(
        text="balanceOf(address)"
    ).hex()[
        :8
    ]
)


TOTAL_SUPPLY_ABI = [
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
    }
]


# =========================================================
# SPECIAL ADDRESSES
# =========================================================

ZERO_ADDRESS = (
    "0x0000000000000000000000000000000000000000"
)

DEAD_ADDRESS = (
    "0x000000000000000000000000000000000000dead"
)


# =========================================================
# SAFE HELPERS
# =========================================================

def _safe_int(
    value,
):

    try:

        return int(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0


def _safe_checksum(
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


def _safe_lower(
    address,
):

    if not address:

        return None

    try:

        return str(
            address
        ).lower()

    except Exception:

        return None


# =========================================================
# WEB3
# =========================================================

def _get_web3():

    w3 = Web3(
        Web3.HTTPProvider(
            RPC_URL,
            request_kwargs={
                "timeout": REQUEST_TIMEOUT,
            },
        )
    )

    if not w3.is_connected():

        raise ConnectionError(
            "Unable to connect to Robinhood Chain RPC."
        )

    return w3


# =========================================================
# HOLDER NORMALIZATION
# =========================================================

def _normalize_holder_response(
    holders,
):

    if not isinstance(
        holders,
        dict,
    ):

        return None

    items = holders.get(
        "items"
    )

    if not isinstance(
        items,
        list,
    ):

        return None

    normalized = []

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

        holder_hash = _safe_checksum(
            address_info.get(
                "hash"
            )
        )

        if not holder_hash:

            continue

        value = _safe_int(
            holder.get(
                "value",
                0,
            )
        )

        if value <= 0:

            continue

        normalized.append(
            {
                "address": {
                    "hash": holder_hash,
                    "name": address_info.get(
                        "name"
                    ),
                },
                "value": str(
                    value
                ),
            }
        )

    if not normalized:

        return None

    normalized.sort(
        key=lambda holder: _safe_int(
            holder.get(
                "value",
                0,
            )
        ),
        reverse=True,
    )

    return {
        "items": normalized,
        "next_page_params": None,
    }


# =========================================================
# CACHE
# =========================================================

def _ensure_cache_dir():

    try:

        os.makedirs(
            CACHE_DIR,
            exist_ok=True,
        )

    except Exception:

        pass


def _cache_path(
    address,
):

    return os.path.join(
        CACHE_DIR,
        f"{str(address).lower()}.json",
    )


def _save_cache(
    address,
    holders,
    source,
    verified,
    metadata=None,
):

    normalized = _normalize_holder_response(
        holders
    )

    if not normalized:

        return

    _ensure_cache_dir()

    path = _cache_path(
        address
    )

    payload = {
        "cache_version": CACHE_VERSION,
        "token": str(
            address
        ).lower(),
        "saved_at": int(
            time.time()
        ),
        "source": source,
        "verified": bool(
            verified
        ),
        "metadata": (
            metadata
            if isinstance(
                metadata,
                dict,
            )
            else {}
        ),
        "holders": normalized,
    }

    temporary_path = (
        path
        + ".tmp"
    )

    try:

        with open(
            temporary_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                payload,
                file,
                separators=(
                    ",",
                    ":",
                ),
            )

        os.replace(
            temporary_path,
            path,
        )

    except Exception:

        try:

            if os.path.exists(
                temporary_path
            ):

                os.remove(
                    temporary_path
                )

        except Exception:

            pass


def _load_cache(
    address,
):

    path = _cache_path(
        address
    )

    try:

        if not os.path.isfile(
            path
        ):

            return None

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(
                file
            )

        if not isinstance(
            data,
            dict,
        ):

            return None

        if data.get(
            "cache_version"
        ) != CACHE_VERSION:

            return None

        holders = _normalize_holder_response(
            data.get(
                "holders"
            )
        )

        if not holders:

            return None

        holders[
            "_source"
        ] = data.get(
            "source",
            "verified_cache",
        )

        holders[
            "_verified"
        ] = bool(
            data.get(
                "verified",
                False,
            )
        )

        metadata = data.get(
            "metadata",
            {}
        )

        if not isinstance(
            metadata,
            dict,
        ):

            metadata = {}

        holders[
            "_complete"
        ] = bool(
            metadata.get(
                "complete",
                False,
            )
        )

        holders[
            "_candidate_count"
        ] = metadata.get(
            "candidate_count"
        )

        holders[
            "_holder_count"
        ] = metadata.get(
            "holder_count"
        )

        return holders

    except Exception:

        return None


# =========================================================
# BLOCKSCOUT
# =========================================================

def _blockscout_get(
    url,
    headers=None,
):

    request_headers = {
        "Accept": "application/json",
        "User-Agent": (
            "RobinShield/1.0"
        ),
    }

    if isinstance(
        headers,
        dict,
    ):

        request_headers.update(
            headers
        )

    for attempt in range(
        HTTP_RETRIES
    ):

        try:

            response = requests.get(
                url,
                timeout=REQUEST_TIMEOUT,
                headers=request_headers,
            )

            if response.status_code == 200:

                try:

                    data = response.json()

                except ValueError:

                    data = None

                if isinstance(
                    data,
                    dict,
                ):

                    return data

            elif response.status_code in (
                403,
                404,
            ):

                return None

        except Exception:

            pass

        if attempt < (
            HTTP_RETRIES - 1
        ):

            time.sleep(
                HTTP_RETRY_DELAYS[
                    attempt
                ]
            )

    return None


def _get_blockscout_holders(
    address,
):

    url = (
        f"{BASE_URL}/tokens/"
        f"{address}/holders"
    )

    data = _blockscout_get(
        url
    )

    return _normalize_holder_response(
        data
    )


def _get_blockscout_pro_holders(
    address,
):

    if not BLOCKSCOUT_PRO_API_KEY:

        return None

    url = (
        f"{BLOCKSCOUT_PRO_BASE_URL}/"
        f"{ROBINHOOD_CHAIN_ID}/api/v2/"
        f"tokens/{address}/holders"
    )

    data = _blockscout_get(
        url,
        headers={
            "Authorization": (
                "Bearer "
                + BLOCKSCOUT_PRO_API_KEY
            )
        },
    )

    return _normalize_holder_response(
        data
    )


# =========================================================
# ALCHEMY
# =========================================================

def _get_alchemy_url():

    if not ALCHEMY_API_KEY:

        return None

    return (
        "https://robinhood-mainnet.g.alchemy.com/v2/"
        + ALCHEMY_API_KEY
    )


def _alchemy_request(
    method,
    params,
):

    url = _get_alchemy_url()

    if not url:

        return None

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params,
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=REQUEST_TIMEOUT,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": (
                    "RobinShield/1.0"
                ),
            },
        )

        if response.status_code != 200:

            return None

        data = response.json()

        if not isinstance(
            data,
            dict,
        ):

            return None

        if data.get(
            "error"
        ):

            return None

        return data.get(
            "result"
        )

    except Exception:

        return None


# =========================================================
# ALCHEMY CANDIDATES
# =========================================================

def _get_alchemy_candidate_addresses(
    token_address,
    deep=False,
):
    """
    Discover candidate addresses from both:
        1. historical transfers starting at token creation
        2. recent transfers near the current chain head

    This avoids crawling an entire active token history while
    improving the chance of finding current holders.
    """

    if not ALCHEMY_API_KEY:

        return None

    if deep:

        max_pages_each = (
            ALCHEMY_DEEP_MAX_PAGES
        )

    else:

        max_pages_each = (
            ALCHEMY_NORMAL_MAX_PAGES
        )

    candidates = set()

    # -----------------------------------------------------
    # Get latest block.
    # -----------------------------------------------------

    latest_block = None

    try:

        w3 = _get_web3()

        latest_block = int(
            w3.eth.block_number
        )

    except Exception:

        latest_block = None

    # -----------------------------------------------------
    # Recent window.
    #
    # We deliberately keep this bounded.
    # -----------------------------------------------------

    if latest_block is not None:

        if deep:

            recent_window = 500_000

        else:

            recent_window = 100_000

        recent_from_block = max(
            0,
            latest_block
            - recent_window,
        )

    else:

        recent_from_block = None

    # -----------------------------------------------------
    # Helper for one transfer-search range.
    # -----------------------------------------------------

    def collect_range(
        from_block,
        to_block,
        max_pages,
    ):

        page_key = None
        page_count = 0

        while page_count < max_pages:

            params = {
                "fromBlock": (
                    hex(
                        int(
                            from_block
                        )
                    )
                    if isinstance(
                        from_block,
                        int,
                    )
                    else from_block
                ),
                "toBlock": (
                    hex(
                        int(
                            to_block
                        )
                    )
                    if isinstance(
                        to_block,
                        int,
                    )
                    else to_block
                ),
                "contractAddresses": [
                    token_address
                ],
                "category": [
                    "erc20"
                ],
                "withMetadata": False,
                "excludeZeroValue": True,
                "maxCount": hex(
                    ALCHEMY_PAGE_SIZE
                ),
            }

            if page_key:

                params[
                    "pageKey"
                ] = page_key

            result = _alchemy_request(
                "alchemy_getAssetTransfers",
                [
                    params
                ],
            )

            if not isinstance(
                result,
                dict,
            ):

                break

            transfers = result.get(
                "transfers",
                [],
            )

            if not isinstance(
                transfers,
                list,
            ):

                transfers = []

            for transfer in transfers:

                if not isinstance(
                    transfer,
                    dict,
                ):

                    continue

                from_address = _safe_checksum(
                    transfer.get(
                        "from"
                    )
                )

                to_address = _safe_checksum(
                    transfer.get(
                        "to"
                    )
                )

                if from_address:

                    normalized = _safe_lower(
                        from_address
                    )

                    if normalized not in (
                        ZERO_ADDRESS,
                        DEAD_ADDRESS,
                    ):

                        candidates.add(
                            from_address
                        )

                if to_address:

                    normalized = _safe_lower(
                        to_address
                    )

                    if normalized not in (
                        ZERO_ADDRESS,
                        DEAD_ADDRESS,
                    ):

                        candidates.add(
                            to_address
                        )

                if (
                    len(candidates)
                    >= ALCHEMY_MAX_CANDIDATES
                ):

                    return

            page_count += 1

            if (
                len(candidates)
                >= ALCHEMY_MAX_CANDIDATES
            ):

                return

            page_key = result.get(
                "pageKey"
            )

            if not page_key:

                return

    # -----------------------------------------------------
    # Pass 1: oldest/history.
    # -----------------------------------------------------

    collect_range(
        "0x0",
        "latest",
        max_pages_each,
    )

    # -----------------------------------------------------
    # Pass 2: recent activity.
    #
    # We intentionally use a second independent query so
    # recent active holders don't get buried behind old
    # transfer history.
    # -----------------------------------------------------

    if (
        recent_from_block is not None
        and len(candidates)
        < ALCHEMY_MAX_CANDIDATES
    ):

        collect_range(
            recent_from_block,
            latest_block,
            max_pages_each,
        )

    if not candidates:

        return None

    return sorted(
        candidates,
        key=lambda address: address.lower()
    )


# =========================================================
# BALANCE CALL DATA
# =========================================================

def _balance_call_data(
    address,
):

    raw_address = (
        str(
            address
        )
        .lower()
        .replace(
            "0x",
            "",
        )
    )

    encoded_address = (
        raw_address.rjust(
            64,
            "0",
        )
    )

    return (
        "0x"
        + BALANCE_OF_SELECTOR
        + encoded_address
    )


# =========================================================
# BATCH BALANCE OF
# =========================================================

def _batch_balance_of(
    token_address,
    addresses,
):

    if not addresses:

        return {}

    url = _get_alchemy_url()

    if not url:

        return {}

    balances = {}

    for start in range(
        0,
        len(addresses),
        BALANCE_BATCH_SIZE,
    ):

        batch_addresses = addresses[
            start:
            start + BALANCE_BATCH_SIZE
        ]

        batch = []

        for index, address in enumerate(
            batch_addresses,
            start=1,
        ):

            batch.append(
                {
                    "jsonrpc": "2.0",
                    "id": index,
                    "method": "eth_call",
                    "params": [
                        {
                            "to": token_address,
                            "data": _balance_call_data(
                                address
                            ),
                        },
                        "latest",
                    ],
                }
            )

        try:

            response = requests.post(
                url,
                json=batch,
                timeout=REQUEST_TIMEOUT,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": (
                        "RobinShield/1.0"
                    ),
                },
            )

            if response.status_code != 200:

                continue

            data = response.json()

            if not isinstance(
                data,
                list,
            ):

                continue

            response_by_id = {}

            for item in data:

                if not isinstance(
                    item,
                    dict,
                ):

                    continue

                response_by_id[
                    item.get(
                        "id"
                    )
                ] = item

            for index, address in enumerate(
                batch_addresses,
                start=1,
            ):

                item = response_by_id.get(
                    index
                )

                if not isinstance(
                    item,
                    dict,
                ):

                    continue

                if item.get(
                    "error"
                ):

                    continue

                raw_balance = item.get(
                    "result"
                )

                if not isinstance(
                    raw_balance,
                    str,
                ):

                    continue

                try:

                    balance = int(
                        raw_balance,
                        16,
                    )

                except Exception:

                    balance = 0

                if balance > 0:

                    balances[
                        _safe_lower(
                            address
                        )
                    ] = balance

        except Exception:

            continue

    return balances


# =========================================================
# ALCHEMY HOLDER DISCOVERY
# =========================================================

def _get_alchemy_holders(
    token_address,
    deep=False,
):
    """
    Discover candidate addresses through Alchemy and then
    read their CURRENT token balances directly from the
    token contract.
    """

    candidates = (
        _get_alchemy_candidate_addresses(
            token_address,
            deep=deep,
        )
    )

    if not candidates:

        return None

    balances = _batch_balance_of(
        token_address,
        candidates,
    )

    if not balances:

        return None

    items = []

    for address in candidates:

        key = _safe_lower(
            address
        )

        balance = balances.get(
            key,
            0,
        )

        if balance <= 0:

            continue

        items.append(
            {
                "address": {
                    "hash": address,
                    "name": None,
                },
                "value": str(
                    balance
                ),
            }
        )

    if not items:

        return None

    items.sort(
        key=lambda holder: _safe_int(
            holder.get(
                "value",
                0,
            )
        ),
        reverse=True,
    )

    holders = {
        "items": items,
        "next_page_params": None,
    }

    # -----------------------------------------------------
    # Coverage check.
    # -----------------------------------------------------

    total_supply = 0

    try:

        w3 = _get_web3()

        total_supply = _get_total_supply(
            w3,
            token_address,
        )

    except Exception:

        pass

    discovered_total = _holder_total(
        holders
    )

    complete = (
        total_supply > 0
        and discovered_total
        == total_supply
    )

    if complete:

        source = (
            "alchemy_asset_transfers"
        )

        verified = True

    else:

        source = (
            "alchemy_asset_transfers_partial"
        )

        verified = False

    holders[
        "_source"
    ] = source

    holders[
        "_verified"
    ] = verified

    holders[
        "_complete"
    ] = complete

    holders[
        "_candidate_count"
    ] = len(
        candidates
    )

    holders[
        "_holder_count"
    ] = len(
        items
    )

    holders[
        "_deep"
    ] = bool(
        deep
    )

    _save_cache(
        token_address,
        holders,
        source=source,
        verified=verified,
        metadata={
            "deep": bool(
                deep
            ),
            "candidate_count": len(
                candidates
            ),
            "holder_count": len(
                items
            ),
            "discovered_total": (
                discovered_total
            ),
            "total_supply": total_supply,
            "complete": complete,
        },
    )

    return holders


# =========================================================
# RPC FALLBACK
# =========================================================

def _rpc_request(
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


def _has_code_at_block(
    w3,
    address,
    block_number,
):

    try:

        code = _rpc_request(
            w3,
            "eth_getCode",
            [
                _safe_checksum(
                    address
                ),
                hex(
                    int(
                        block_number
                    )
                ),
            ],
        )

        return (
            isinstance(
                code,
                str,
            )
            and len(code) > 2
            and code not in (
                "0x",
                "0x0",
            )
        )

    except Exception:

        return False


def _find_creation_block(
    w3,
    address,
):

    latest = int(
        w3.eth.block_number
    )

    if not _has_code_at_block(
        w3,
        address,
        latest,
    ):

        return None

    low = 0
    high = latest

    while low < high:

        middle = (
            low
            + high
        ) // 2

        if _has_code_at_block(
            w3,
            address,
            middle,
        ):

            high = middle

        else:

            low = middle + 1

    return low


def _decode_topic_address(
    topic,
):

    if not isinstance(
        topic,
        str,
    ):

        return None

    if topic.startswith(
        "0x"
    ):

        topic = topic[2:]

    if len(topic) != 64:

        return None

    return _safe_checksum(
        "0x"
        + topic[24:]
    )


def _decode_uint256(
    value,
):

    if not isinstance(
        value,
        str,
    ):

        return 0

    if value.startswith(
        "0x"
    ):

        value = value[2:]

    try:

        return int(
            value,
            16,
        )

    except Exception:

        return 0


def _get_transfer_logs(
    w3,
    token_address,
    from_block,
    to_block,
):

    logs = []

    current = int(
        from_block
    )

    end = int(
        to_block
    )

    chunk_size = RPC_CHUNK_SIZE

    while current <= end:

        chunk_end = min(
            current
            + chunk_size
            - 1,
            end,
        )

        try:

            chunk = _rpc_request(
                w3,
                "eth_getLogs",
                [
                    {
                        "address": _safe_checksum(
                            token_address
                        ),
                        "topics": [
                            TRANSFER_TOPIC
                        ],
                        "fromBlock": hex(
                            current
                        ),
                        "toBlock": hex(
                            chunk_end
                        ),
                    }
                ],
            )

            if not isinstance(
                chunk,
                list,
            ):

                raise RuntimeError(
                    "Invalid eth_getLogs result."
                )

            logs.extend(
                chunk
            )

            current = (
                chunk_end
                + 1
            )

        except Exception:

            if chunk_size <= RPC_MIN_CHUNK_SIZE:

                raise

            chunk_size = max(
                RPC_MIN_CHUNK_SIZE,
                chunk_size // 2,
            )

    return logs


def _get_rpc_holders(
    address,
):

    w3 = _get_web3()

    latest = int(
        w3.eth.block_number
    )

    creation = _find_creation_block(
        w3,
        address,
    )

    if creation is None:

        return None

    logs = _get_transfer_logs(
        w3,
        address,
        creation,
        latest,
    )

    if not logs:

        return None

    balances = {}

    for log in logs:

        if not isinstance(
            log,
            dict,
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

        from_address = (
            _decode_topic_address(
                topics[1]
            )
        )

        to_address = (
            _decode_topic_address(
                topics[2]
            )
        )

        amount = _decode_uint256(
            log.get(
                "data",
                "0x",
            )
        )

        if amount <= 0:

            continue

        if from_address:

            key = _safe_lower(
                from_address
            )

            balances[key] = (
                balances.get(
                    key,
                    0,
                )
                - amount
            )

        if to_address:

            key = _safe_lower(
                to_address
            )

            balances[key] = (
                balances.get(
                    key,
                    0,
                )
                + amount
            )

    balances = {
        address: balance
        for address, balance in balances.items()
        if balance > 0
    }

    holders = _balances_to_holder_data(
        balances
    )

    if not holders:

        return None

    total_supply = _get_total_supply(
        w3,
        address,
    )

    reconstructed_total = _holder_total(
        holders
    )

    if (
        total_supply <= 0
        or reconstructed_total
        != total_supply
    ):

        return None

    holders[
        "_source"
    ] = "rpc_transfer_logs"

    holders[
        "_verified"
    ] = True

    holders[
        "_complete"
    ] = True

    holders[
        "_candidate_count"
    ] = len(
        holders.get(
            "items",
            []
        )
    )

    holders[
        "_holder_count"
    ] = len(
        holders.get(
            "items",
            []
        )
    )

    _save_cache(
        address,
        holders,
        source="rpc_transfer_logs",
        verified=True,
        metadata={
            "creation_block": creation,
            "latest_block": latest,
            "transfer_count": len(
                logs
            ),
            "reconstructed_total": (
                reconstructed_total
            ),
            "total_supply": total_supply,
            "complete": True,
            "candidate_count": len(
                holders.get(
                    "items",
                    []
                )
            ),
            "holder_count": len(
                holders.get(
                    "items",
                    []
                )
            ),
        },
    )

    return holders


def _balances_to_holder_data(
    balances,
):

    if not balances:

        return None

    items = []

    for address, balance in balances.items():

        if balance <= 0:

            continue

        checksum = _safe_checksum(
            address
        )

        if not checksum:

            continue

        items.append(
            {
                "address": {
                    "hash": checksum,
                    "name": None,
                },
                "value": str(
                    balance
                ),
            }
        )

    if not items:

        return None

    items.sort(
        key=lambda holder: _safe_int(
            holder.get(
                "value",
                0,
            )
        ),
        reverse=True,
    )

    return {
        "items": items,
        "next_page_params": None,
    }


def _get_total_supply(
    w3,
    address,
):

    token = w3.eth.contract(
        address=_safe_checksum(
            address
        ),
        abi=TOTAL_SUPPLY_ABI,
    )

    return int(
        token.functions.totalSupply().call()
    )


def _holder_total(
    holders,
):

    if not isinstance(
        holders,
        dict,
    ):

        return 0

    total = 0

    for holder in holders.get(
        "items",
        [],
    ):

        if not isinstance(
            holder,
            dict,
        ):

            continue

        total += _safe_int(
            holder.get(
                "value",
                0,
            )
        )

    return total


# =========================================================
# PUBLIC HOLDER API
# =========================================================

def get_holders(
    address,
    deep=False,
):

    checksum = _safe_checksum(
        address
    )

    if not checksum:

        return None

    # -----------------------------------------------------
    # 1. Direct Blockscout
    # -----------------------------------------------------

    holders = _get_blockscout_holders(
        checksum
    )

    if holders:

        holders[
            "_source"
        ] = "blockscout"

        holders[
            "_verified"
        ] = True

        holders[
            "_complete"
        ] = True

        holders[
            "_candidate_count"
        ] = len(
            holders.get(
                "items",
                []
            )
        )

        holders[
            "_holder_count"
        ] = len(
            holders.get(
                "items",
                []
            )
        )

        _save_cache(
            checksum,
            holders,
            source="blockscout",
            verified=True,
            metadata={
                "complete": True,
                "candidate_count": len(
                    holders.get(
                        "items",
                        []
                    )
                ),
                "holder_count": len(
                    holders.get(
                        "items",
                        []
                    )
                ),
            },
        )

        return holders

    # -----------------------------------------------------
    # 2. Blockscout PRO
    # -----------------------------------------------------

    holders = _get_blockscout_pro_holders(
        checksum
    )

    if holders:

        holders[
            "_source"
        ] = "blockscout_pro"

        holders[
            "_verified"
        ] = True

        holders[
            "_complete"
        ] = True

        holders[
            "_candidate_count"
        ] = len(
            holders.get(
                "items",
                []
            )
        )

        holders[
            "_holder_count"
        ] = len(
            holders.get(
                "items",
                []
            )
        )

        _save_cache(
            checksum,
            holders,
            source="blockscout_pro",
            verified=True,
            metadata={
                "complete": True,
                "candidate_count": len(
                    holders.get(
                        "items",
                        []
                    )
                ),
                "holder_count": len(
                    holders.get(
                        "items",
                        []
                    )
                ),
            },
        )

        return holders

    # -----------------------------------------------------
    # 3. Alchemy
    # -----------------------------------------------------

    holders = _get_alchemy_holders(
        checksum,
        deep=deep,
    )

    if holders:

        return holders

    # -----------------------------------------------------
    # 4. Verified cache
    # -----------------------------------------------------

    cached = _load_cache(
        checksum
    )

    if cached:

        return cached

    # -----------------------------------------------------
    # 5. Complete RPC reconstruction
    # -----------------------------------------------------

    try:

        holders = _get_rpc_holders(
            checksum
        )

        if holders:

            return holders

    except Exception:

        pass

    return None


# =========================================================
# HOLDER HELPERS
# =========================================================

def _get_items(
    holders,
):

    if not isinstance(
        holders,
        dict,
    ):

        return []

    items = holders.get(
        "items",
        []
    )

    if not isinstance(
        items,
        list,
    ):

        return []

    return items


def _get_holder_address(
    holder,
):

    if not isinstance(
        holder,
        dict,
    ):

        return None

    address = holder.get(
        "address",
        {}
    )

    if not isinstance(
        address,
        dict,
    ):

        return None

    value = address.get(
        "hash"
    )

    if not value:

        return None

    return str(
        value
    ).lower()


def _get_holder_name(
    holder,
):

    if not isinstance(
        holder,
        dict,
    ):

        return ""

    address = holder.get(
        "address",
        {}
    )

    if not isinstance(
        address,
        dict,
    ):

        return ""

    name = address.get(
        "name"
    )

    if not name:

        return ""

    return str(
        name
    ).lower()


def _get_holder_balance(
    holder,
):

    if not isinstance(
        holder,
        dict,
    ):

        return 0

    return _safe_int(
        holder.get(
            "value",
            0,
        )
    )


# =========================================================
# LP / BURN DETECTION
# =========================================================

def is_lp_wallet(
    holder,
):

    name = _get_holder_name(
        holder
    )

    if not name:

        return False

    keywords = [
        "uniswap",
        "pair",
        "pool",
        "liquidity",
        "lp",
    ]

    return any(
        keyword in name
        for keyword in keywords
    )


def is_burn_wallet(
    holder,
):

    address = _get_holder_address(
        holder
    )

    if not address:

        return False

    return address in (
        ZERO_ADDRESS,
        DEAD_ADDRESS,
    )


def should_ignore_holder(
    holder,
    excluded_addresses=None,
):

    address = _get_holder_address(
        holder
    )

    if (
        address
        and excluded_addresses
    ):

        excluded = {
            _safe_lower(
                value
            )
            for value in excluded_addresses
            if value
        }

        if address in excluded:

            return True

    if is_lp_wallet(
        holder
    ):

        return True

    if is_burn_wallet(
        holder
    ):

        return True

    return False


# =========================================================
# VALID HOLDERS
# =========================================================

def get_valid_holders(
    holders,
    excluded_addresses=None,
):

    valid = []

    for holder in _get_items(
        holders
    ):

        if not isinstance(
            holder,
            dict,
        ):

            continue

        if should_ignore_holder(
            holder,
            excluded_addresses=excluded_addresses,
        ):

            continue

        balance = _get_holder_balance(
            holder
        )

        if balance <= 0:

            continue

        valid.append(
            holder
        )

    valid.sort(
        key=lambda holder: _get_holder_balance(
            holder
        ),
        reverse=True,
    )

    return valid


# =========================================================
# PERCENTAGES
# =========================================================

def calculate_wallet_percentage(
    balance,
    total_supply,
):

    balance = _safe_int(
        balance
    )

    total_supply = _safe_int(
        total_supply
    )

    if total_supply <= 0:

        return 0.0

    return round(
        (
            balance
            / total_supply
        )
        * 100,
        2,
    )


def calculate_top_holder_percentage(
    holders,
    total_supply,
    excluded_addresses=None,
):

    valid = get_valid_holders(
        holders,
        excluded_addresses=excluded_addresses,
    )

    if not valid:

        return 0.0

    return calculate_wallet_percentage(
        _get_holder_balance(
            valid[0]
        ),
        total_supply,
    )


def get_top_holders_percentage(
    holders,
    total_supply,
    limit,
    excluded_addresses=None,
):

    total_supply = _safe_int(
        total_supply
    )

    if total_supply <= 0:

        return 0.0

    try:

        limit = int(
            limit
        )

    except (
        TypeError,
        ValueError,
    ):

        return 0.0

    if limit <= 0:

        return 0.0

    valid = get_valid_holders(
        holders,
        excluded_addresses=excluded_addresses,
    )

    total_balance = 0

    for holder in valid[:limit]:

        total_balance += (
            _get_holder_balance(
                holder
            )
        )

    return calculate_wallet_percentage(
        total_balance,
        total_supply,
    )


def get_top5_percentage(
    holders,
    total_supply,
    excluded_addresses=None,
):

    return get_top_holders_percentage(
        holders,
        total_supply,
        5,
        excluded_addresses=excluded_addresses,
    )


def get_top10_percentage(
    holders,
    total_supply,
    excluded_addresses=None,
):

    return get_top_holders_percentage(
        holders,
        total_supply,
        10,
        excluded_addresses=excluded_addresses,
    )


# =========================================================
# LARGEST WALLET
# =========================================================

def get_largest_wallet(
    holders,
    excluded_addresses=None,
):

    valid = get_valid_holders(
        holders,
        excluded_addresses=excluded_addresses,
    )

    if not valid:

        return None

    return valid[0]


# =========================================================
# HOLDER RISK
# =========================================================

def get_holder_risk(
    holders,
    total_supply,
    excluded_addresses=None,
):

    total_supply = _safe_int(
        total_supply
    )

    if total_supply <= 0:

        return {
            "score": 0,
            "level": "UNKNOWN",
            "largest_wallet": None,
            "top5": None,
            "top10": None,
            "coverage": "UNKNOWN",
            "verified": False,
            "reasons": [
                "Token total supply could not be determined."
            ],
        }

    if not isinstance(
        holders,
        dict,
    ):

        return {
            "score": 0,
            "level": "UNKNOWN",
            "largest_wallet": None,
            "top5": None,
            "top10": None,
            "coverage": "UNKNOWN",
            "verified": False,
            "reasons": [
                "Holder data could not be determined."
            ],
        }

    valid = get_valid_holders(
        holders,
        excluded_addresses=excluded_addresses,
    )

    if not valid:

        return {
            "score": 0,
            "level": "UNKNOWN",
            "largest_wallet": None,
            "top5": None,
            "top10": None,
            "coverage": "UNKNOWN",
            "verified": False,
            "reasons": [
                "No valid non-LP, non-burn holders were found."
            ],
        }

    verified = bool(
        holders.get(
            "_verified",
            False,
        )
    )

    complete = bool(
        holders.get(
            "_complete",
            False,
        )
    )

    coverage = (
        "COMPLETE"
        if complete
        else "PARTIAL"
    )

    largest = valid[0]

    largest_percentage = (
        calculate_wallet_percentage(
            _get_holder_balance(
                largest
            ),
            total_supply,
        )
    )

    top5 = get_top5_percentage(
        holders,
        total_supply,
        excluded_addresses=excluded_addresses,
    )

    top10 = get_top10_percentage(
        holders,
        total_supply,
        excluded_addresses=excluded_addresses,
    )

    score = 0

    reasons = []

    # -----------------------------------------------------
    # Largest wallet
    # -----------------------------------------------------

    if largest_percentage >= 30:

        score += 3

        reasons.append(
            f"Largest discovered wallet controls "
            f"{largest_percentage:.2f}% of supply."
        )

    elif largest_percentage >= 20:

        score += 2

        reasons.append(
            f"Largest discovered wallet controls "
            f"{largest_percentage:.2f}% of supply."
        )

    elif largest_percentage >= 10:

        score += 1

        reasons.append(
            f"Largest discovered wallet controls "
            f"{largest_percentage:.2f}% of supply."
        )

    # -----------------------------------------------------
    # Top 5
    # -----------------------------------------------------

    if top5 >= 60:

        score += 3

        reasons.append(
            f"Top 5 discovered wallets control "
            f"{top5:.2f}% of supply."
        )

    elif top5 >= 40:

        score += 2

        reasons.append(
            f"Top 5 discovered wallets control "
            f"{top5:.2f}% of supply."
        )

    elif top5 >= 25:

        score += 1

        reasons.append(
            f"Top 5 discovered wallets control "
            f"{top5:.2f}% of supply."
        )

    # -----------------------------------------------------
    # Top 10
    # -----------------------------------------------------

    if top10 >= 80:

        score += 3

        reasons.append(
            f"Top 10 discovered wallets control "
            f"{top10:.2f}% of supply."
        )

    elif top10 >= 60:

        score += 2

        reasons.append(
            f"Top 10 discovered wallets control "
            f"{top10:.2f}% of supply."
        )

    elif top10 >= 40:

        score += 1

        reasons.append(
            f"Top 10 discovered wallets control "
            f"{top10:.2f}% of supply."
        )

    # -----------------------------------------------------
    # Risk classification
    # -----------------------------------------------------

    if score >= 7:

        level = "HIGH"

    elif score >= 3:

        level = "MEDIUM"

    else:

        level = "LOW"

    if not complete:

        reasons.append(
            "Holder coverage is partial; concentration "
            "figures represent discovered holders and "
            "may not represent the complete distribution."
        )

    if not reasons:

        reasons.append(
            "Holder distribution appears relatively healthy."
        )

    return {
        "score": score,
        "level": level,
        "largest_wallet": largest_percentage,
        "top5": top5,
        "top10": top10,
        "coverage": coverage,
        "verified": verified,
        "reasons": reasons,
    }


# =========================================================
# COMPATIBILITY
# =========================================================

def get_holder_distribution(
    holders,
):

    return get_valid_holders(
        holders
    )