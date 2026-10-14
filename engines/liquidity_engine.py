from web3 import Web3
from concurrent.futures import ThreadPoolExecutor
import json
import os
import threading

import requests

from config import RPC_URL
from core.token import get_token_decimals
try:
    from core.price import (
        get_eth_price_usd,
        get_token_price_usd,
    )
except ImportError:
    from core.price import get_eth_price_usd

    def get_token_price_usd(token_address):
        return None
from core.lp import V2_FACTORY_ABI, PAIR_ABI


# =========================================================
# ROBINHOOD CHAIN
# =========================================================

V2_FACTORY = "0x8bcEaA40B9AcdfAedF85AdF4FF01F5Ad6517937f"

V3_FACTORY = "0x1f7d7550B1b028f7571E69A784071F0205FD2EfA"

WETH = "0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73"

ROBINHOOD_QUOTE_TOKEN = (
    "0x1b0E319c6A659F002271B69dB8A7df2F911c153E"
)

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

DEXSCREENER_CHAIN = "robinhood"

V3_FEE_TIERS = [
    100,
    500,
    3000,
    10000,
]

V2_EVENT_LOG_BATCH_SIZE = 20
V2_EVENT_LOG_WORKERS = 8


# =========================================================
# UNISWAP V3 ABIs
# =========================================================

V3_FACTORY_ABI = [
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
            {
                "internalType": "uint24",
                "name": "fee",
                "type": "uint24",
            },
        ],
        "name": "getPool",
        "outputs": [
            {
                "internalType": "address",
                "name": "pool",
                "type": "address",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


V3_POOL_ABI = [
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
        "name": "liquidity",
        "outputs": [
            {
                "internalType": "uint128",
                "name": "",
                "type": "uint128",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "slot0",
        "outputs": [
            {
                "internalType": "uint160",
                "name": "sqrtPriceX96",
                "type": "uint160",
            },
            {
                "internalType": "int24",
                "name": "tick",
                "type": "int24",
            },
            {
                "internalType": "uint16",
                "name": "observationIndex",
                "type": "uint16",
            },
            {
                "internalType": "uint16",
                "name": "observationCardinality",
                "type": "uint16",
            },
            {
                "internalType": "uint16",
                "name": "observationCardinalityNext",
                "type": "uint16",
            },
            {
                "internalType": "uint8",
                "name": "feeProtocol",
                "type": "uint8",
            },
            {
                "internalType": "bool",
                "name": "unlocked",
                "type": "bool",
            },
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


# =========================================================
# CONNECTION
# =========================================================

def get_web3():

    w3 = Web3(
        Web3.HTTPProvider(
            RPC_URL,
            request_kwargs={
                "timeout": 15,
            },
        )
    )

    if not w3.is_connected():

        raise ConnectionError(
            "Unable to connect to Robinhood Chain RPC."
        )

    return w3


# =========================================================
# HELPERS
# =========================================================

def _is_zero_address(address):

    if not address:
        return True

    return (
        str(address).lower()
        == ZERO_ADDRESS.lower()
    )


def _safe_float(value):

    try:
        return float(value)

    except Exception:
        return 0.0


def _safe_int(value):

    try:
        return int(value)

    except Exception:
        return 0


def _safe_checksum(address):

    try:
        return Web3.to_checksum_address(address)

    except Exception:
        return None


def _liquidity_risk_from_usd(liquidity_usd):

    liquidity_usd = _safe_float(
        liquidity_usd
    )

    if liquidity_usd <= 0:

        return (
            "UNKNOWN",
            "Pool exists and reserves were verified, but USD valuation is unavailable for the quote token.",
        )

    if liquidity_usd < 1000:

        return (
            "HIGH",
            "Very low liquidity detected.",
        )

    if liquidity_usd < 10000:

        return (
            "MEDIUM",
            "Moderate liquidity detected.",
        )

    return (
        "LOW",
        "Healthy liquidity detected.",
    )


def _liquidity_risk(liquidity_eth):

    liquidity_eth = _safe_float(
        liquidity_eth
    )

    if liquidity_eth <= 0:

        return (
            "NONE",
            "Pool exists but currently has no usable ETH-side liquidity.",
        )

    if liquidity_eth < 1:

        return (
            "HIGH",
            "Very low ETH liquidity detected.",
        )

    if liquidity_eth < 10:

        return (
            "MEDIUM",
            "Moderate ETH liquidity detected.",
        )

    return (
        "LOW",
        "Healthy ETH liquidity detected.",
    )


def _empty_result(reason):

    reason_text = str(reason or "")
    unavailable = any(
        marker in reason_text.lower()
        for marker in ("rpc", "connect", "connection", "timed out", "timeout")
    )

    return {
        "found": False,
        "analysis_status": "UNAVAILABLE" if unavailable else "COMPLETE",

        "dex": None,
        "version": None,

        "pair": None,
        "best_pool": None,
        "best_pool_data": None,

        "quote_token": None,
        "quote_reserve_raw": None,
        "quote_reserve": 0,

        "token_reserve_raw": None,
        "token_reserve": 0,

        "token_decimals": None,
        "quote_decimals": None,

        "pools_found": 0,
        "pool_count": 0,

        "weth_reserve": 0,

        "liquidity_eth": 0,
        "total_liquidity_eth": 0,

        "liquidity_usd": 0,

        "total_discovered_liquidity_usd": 0,
        "total_liquidity_usd": 0,

        "risk": "UNKNOWN" if unavailable else "NONE",
        "reason": reason,

        "pools": [],
    }


# =========================================================
# V2 POOL DISCOVERY
# =========================================================

def _get_v2_pair_event_log_results(
    w3,
    filters,
):

    results = [
        None
        for _ in filters
    ]

    fallback_indices = []

    provider = getattr(
        w3,
        "provider",
        None,
    )

    batch_method = getattr(
        provider,
        "make_batch_request",
        None,
    )

    for start in range(
        0,
        len(filters),
        V2_EVENT_LOG_BATCH_SIZE,
    ):

        batch_filters = filters[
            start:start + V2_EVENT_LOG_BATCH_SIZE
        ]

        responses = None

        if callable(
            batch_method
        ):

            try:

                responses = batch_method(
                    [
                        (
                            "eth_getLogs",
                            [query],
                        )
                        for query in batch_filters
                    ]
                )

                if not isinstance(
                    responses,
                    list,
                ) or len(responses) != len(
                    batch_filters
                ):

                    responses = None

            except Exception:

                responses = None

        for index, query in enumerate(
            batch_filters
        ):

            result_index = start + index

            response = (
                responses[index]
                if responses is not None
                else None
            )

            if (
                isinstance(
                    response,
                    dict,
                )
                and not response.get(
                    "error"
                )
                and isinstance(
                    response.get(
                        "result"
                    ),
                    list,
                )
            ):

                results[result_index] = (
                    (
                        response["result"],
                        True,
                    )
                )

                continue

            fallback_indices.append(
                result_index
            )

    if fallback_indices:

        thread_state = threading.local()

        def fetch_logs(query):

            worker_w3 = getattr(
                thread_state,
                "w3",
                None,
            )

            if worker_w3 is None:

                worker_w3 = Web3(
                    Web3.HTTPProvider(
                        RPC_URL,
                        request_kwargs={
                            "timeout": 15,
                        },
                    )
                )

                thread_state.w3 = worker_w3

            try:

                return (
                    worker_w3.eth.get_logs(
                        query
                    ),
                    True,
                )

            except Exception:

                return (
                    [],
                    False,
                )

        with ThreadPoolExecutor(
            max_workers=min(
                V2_EVENT_LOG_WORKERS,
                len(fallback_indices),
            )
        ) as executor:

            fallback_results = executor.map(
                fetch_logs,
                [
                    filters[index]
                    for index in fallback_indices
                ],
            )

            for index, result in zip(
                fallback_indices,
                fallback_results,
            ):

                results[index] = result

    return results

def find_v2_pair(
    token_address,
    quote_address=WETH,
    w3=None,
    allow_event_scan=True,
):

    if w3 is None:

        w3 = get_web3()

    token_address = Web3.to_checksum_address(
        token_address
    )

    quote_address = Web3.to_checksum_address(
        quote_address
    )

    factory_address = Web3.to_checksum_address(
        V2_FACTORY
    )

    factory = w3.eth.contract(
        address=factory_address,
        abi=V2_FACTORY_ABI,
    )

    # =====================================================
    # 1. EXACT PAIR LOOKUP
    # =====================================================

    try:

        pair = factory.functions.getPair(
            token_address,
            quote_address,
        ).call()

        if not _is_zero_address(
            pair
        ):

            return Web3.to_checksum_address(
                pair
            )

    except Exception:

        pass

    if not allow_event_scan:
        return None

    # =====================================================
    # 2. FALLBACK FOR WETH LOOKUP
    #
    # If token/WETH does not exist, search PairCreated
    # events for any V2 pair containing this token.
    # =====================================================

    if (
        quote_address.lower()
        != WETH.lower()
    ):

        return None

    try:

        event_topic = Web3.keccak(
            text=(
                "PairCreated("
                "address,address,address,uint256"
                ")"
            )
        ).hex()

        token_topic = (
            "0x"
            + token_address[
                2:
            ].lower().rjust(
                64,
                "0",
            )
        )

        latest_block = int(
            w3.eth.block_number
        )

        chunk_size = 1_000_000

        cache_path = os.path.join(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            ),
            ".cache",
            "liquidity",
            "v2_pair_event_scans",
            f"{token_address.lower()}.json",
        )

        scan_from = 0
        cached_candidates = []

        try:

            with open(
                cache_path,
                "r",
                encoding="utf-8",
            ) as cache_file:

                cached_scan = json.load(
                    cache_file
                )

            cached_through = int(
                cached_scan.get(
                    "scanned_through",
                    -1,
                )
            )

            for candidate in cached_scan.get(
                "candidates",
                [],
            ):

                try:

                    cached_candidates.append(
                        (
                            int(
                                candidate[
                                    "block_number"
                                ]
                            ),
                            Web3.to_checksum_address(
                                candidate[
                                    "pair_address"
                                ]
                            ),
                        )
                    )

                except Exception:

                    continue

            if 0 <= cached_through <= latest_block:

                scan_from = cached_through + 1

        except Exception:

            pass

        candidates = list(
            cached_candidates
        )

        scan_complete = True

        log_filters = []

        current_to = latest_block

        while current_to >= scan_from:

            current_from = max(
                scan_from,
                current_to
                - chunk_size
                + 1,
            )

            for topics in (
                [
                    event_topic,
                    token_topic,
                ],
                [
                    event_topic,
                    None,
                    token_topic,
                ],
            ):

                log_filters.append(
                    {
                        "address": factory_address,
                        "fromBlock": current_from,
                        "toBlock": current_to,
                        "topics": topics,
                    }
                )

            current_to = (
                current_from - 1
            )

        log_results = _get_v2_pair_event_log_results(
            w3,
            log_filters,
        )

        for logs, request_succeeded in log_results:

            if not request_succeeded:

                scan_complete = False

            for log in logs:

                try:

                    data = log.get(
                        "data",
                        "",
                    )

                    if not data:

                        continue

                    data_hex = str(
                        data
                    )

                    if data_hex.startswith(
                        "0x"
                    ):

                        data_hex = (
                            data_hex[2:]
                        )

                    # PairCreated data:
                    # address pair, uint256 index
                    if len(
                        data_hex
                    ) < 64:

                        continue

                    pair_address = (
                        "0x"
                        + data_hex[
                            24:64
                        ]
                    )

                    pair_address = (
                        Web3.to_checksum_address(
                            pair_address
                        )
                    )

                    block_number = int(
                        log.get(
                            "blockNumber",
                            0,
                        )
                    )

                    candidates.append(
                        (
                            block_number,
                            pair_address,
                        )
                    )

                except Exception:

                    continue

        # -------------------------------------------------
        # Newest candidate first.
        # -------------------------------------------------

        unique = {}

        for block_number, pair_address in candidates:

            unique[
                pair_address.lower()
            ] = (
                block_number,
                pair_address,
            )

        candidates = list(
            unique.values()
        )

        if scan_complete:

            try:

                os.makedirs(
                    os.path.dirname(
                        cache_path
                    ),
                    exist_ok=True,
                )

                temporary_path = (
                    cache_path + ".tmp"
                )

                with open(
                    temporary_path,
                    "w",
                    encoding="utf-8",
                ) as cache_file:

                    json.dump(
                        {
                            "scanned_through": latest_block,
                            "candidates": [
                                {
                                    "block_number": block_number,
                                    "pair_address": pair_address,
                                }
                                for block_number, pair_address
                                in candidates
                            ],
                        },
                        cache_file,
                    )

                os.replace(
                    temporary_path,
                    cache_path,
                )

            except Exception:

                pass

        candidates = sorted(
            unique.values(),
            key=lambda item: item[0],
            reverse=True,
        )

        # -------------------------------------------------
        # Verify candidates directly on-chain.
        # -------------------------------------------------

        for _, pair_address in candidates:

            try:

                pair_contract = w3.eth.contract(
                    address=pair_address,
                    abi=PAIR_ABI,
                )

                token0 = Web3.to_checksum_address(
                    pair_contract.functions.token0().call()
                )

                token1 = Web3.to_checksum_address(
                    pair_contract.functions.token1().call()
                )

                if (
                    token0.lower()
                    != token_address.lower()
                    and
                    token1.lower()
                    != token_address.lower()
                ):

                    continue

                reserve0, reserve1, _ = (
                    pair_contract.functions.getReserves().call()
                )

                if (
                    int(reserve0) <= 0
                    or int(reserve1) <= 0
                ):

                    continue

                return pair_address

            except Exception:

                continue

    except Exception:

        pass

    return None


# =========================================================
# V2 POOL ANALYSIS
# =========================================================

def analyze_v2_pool(
    token_address,
    pair_address,
    w3,
):

    token_address = Web3.to_checksum_address(
        token_address
    )

    pair_address = Web3.to_checksum_address(
        pair_address
    )

    pair = w3.eth.contract(
        address=pair_address,
        abi=PAIR_ABI,
    )

    token0 = Web3.to_checksum_address(
        pair.functions.token0().call()
    )

    token1 = Web3.to_checksum_address(
        pair.functions.token1().call()
    )

    reserve0, reserve1, _ = (
        pair.functions.getReserves().call()
    )

    if (
        token0.lower() != token_address.lower()
        and token1.lower() != token_address.lower()
    ):

        return None

    token_decimals = get_token_decimals(
        w3,
        token_address,
    )

    if token_decimals is None:
        token_decimals = 18

    if token0.lower() == token_address.lower():

        token_reserve_raw = reserve0
        quote_reserve_raw = reserve1
        quote_address = token1

    else:

        token_reserve_raw = reserve1
        quote_reserve_raw = reserve0
        quote_address = token0

    quote_decimals = get_token_decimals(
        w3,
        quote_address,
    )

    if quote_decimals is None:
        quote_decimals = 18

    token_reserve = (
        token_reserve_raw
        / (10 ** token_decimals)
    )

    quote_reserve = (
        quote_reserve_raw
        / (10 ** quote_decimals)
    )

    weth_reserve = 0.0
    liquidity_eth = 0.0
    liquidity_usd = 0.0
    eth_price_usd = 0.0
    quote_price_usd = 0.0

    if quote_reserve <= 0 or token_reserve <= 0:

        risk = "HIGH"
        reason = "Pool was found, but one or both token reserves are empty."

    elif quote_address.lower() == WETH.lower():

        weth_reserve = quote_reserve

        liquidity_eth = (
            weth_reserve * 2
        )

        try:
            eth_price_usd = _safe_float(
                get_eth_price_usd()
            )
        except Exception:
            eth_price_usd = 0.0

        if eth_price_usd > 0:

            liquidity_usd = (
                liquidity_eth
                * eth_price_usd
            )

            risk, reason = _liquidity_risk(
                liquidity_eth
            )

        else:

            risk = "UNKNOWN"
            reason = (
                "WETH liquidity was verified on-chain, but ETH/USD pricing is unavailable."
            )

    else:

        try:
            quote_price_usd = _safe_float(
                get_token_price_usd(
                    quote_address
                )
            )
        except Exception:
            quote_price_usd = 0.0

        if quote_price_usd > 0:

            liquidity_usd = (
                quote_reserve
                * 2
                * quote_price_usd
            )

            risk, reason = _liquidity_risk_from_usd(
                liquidity_usd
            )

        else:

            risk = "UNKNOWN"
            reason = (
                "Non-WETH liquidity pool detected. On-chain reserves were verified, but USD valuation requires quote-token pricing."
            )

    return {
        "found": True,

        "dex": "Uniswap V2",
        "version": "V2",

        "pool": pair_address,
        "pair": pair_address,
        "pair_address": pair_address,

        "token0": token0,
        "token1": token1,

        "quote_token": quote_address,

        "token_reserve_raw": int(
            token_reserve_raw
        ),

        "quote_reserve_raw": int(
            quote_reserve_raw
        ),

        "token_reserve": token_reserve,
        "quote_reserve": quote_reserve,

        "token_decimals": token_decimals,
        "quote_decimals": quote_decimals,

        "weth_reserve": weth_reserve,
        "liquidity_eth": liquidity_eth,

        "eth_price_usd": eth_price_usd,
        "quote_price_usd": quote_price_usd,
        "liquidity_usd": liquidity_usd,

        "risk": risk,
        "reason": reason,

        "source": "On-chain verification",
    }


# =========================================================
# V3 POOL DISCOVERY
# =========================================================

def find_v3_pools(
    token_address,
    w3=None,
):

    if w3 is None:

        w3 = get_web3()

    token_address = Web3.to_checksum_address(
        token_address
    )

    factory = w3.eth.contract(
        address=Web3.to_checksum_address(
            V3_FACTORY
        ),
        abi=V3_FACTORY_ABI,
    )

    pools = []

    for fee in V3_FEE_TIERS:

        try:

            pool = factory.functions.getPool(
                token_address,
                Web3.to_checksum_address(
                    WETH
                ),
                fee,
            ).call()

            if not _is_zero_address(pool):

                pools.append(
                    {
                        "pool": Web3.to_checksum_address(
                            pool
                        ),
                        "fee": fee,
                    }
                )

        except Exception:

            continue

    return pools


# =========================================================
# V3 POOL ANALYSIS
# =========================================================

def analyze_v3_pool(
    pool_address,
    fee,
    w3,
    token_address=None,
):

    pool_address = Web3.to_checksum_address(
        pool_address
    )

    pool = w3.eth.contract(
        address=pool_address,
        abi=V3_POOL_ABI,
    )

    token0 = Web3.to_checksum_address(
        pool.functions.token0().call()
    )

    token1 = Web3.to_checksum_address(
        pool.functions.token1().call()
    )

    quote_token = None
    if token_address:
        token_checksum = Web3.to_checksum_address(token_address)
        if token0.lower() == token_checksum.lower():
            quote_token = token1
        elif token1.lower() == token_checksum.lower():
            quote_token = token0

    liquidity = _safe_int(
        pool.functions.liquidity().call()
    )

    slot0 = (
        pool.functions.slot0().call()
    )

    liquidity_status = (
        "ACTIVE_AT_CURRENT_PRICE"
        if liquidity > 0
        else "ZERO_AT_CURRENT_PRICE"
    )
    reason = (
        "Uniswap V3 pool detected. Raw V3 liquidity is available but USD liquidity requires price-range analysis."
        if liquidity > 0
        else "Uniswap V3 pool reports zero active liquidity at the current price. Out-of-range positions and liquidity reached after price movement were not analyzed."
    )

    return {
        "found": True,

        "dex": "Uniswap V3",
        "version": "V3",

        "pool": pool_address,
        "pair": pool_address,
        "pair_address": pool_address,

        "token0": token0,
        "token1": token1,

        "fee": fee,

        "v3_liquidity": liquidity,

        "active_liquidity_status": liquidity_status,

        "sqrt_price_x96": slot0[0],

        "quote_token": quote_token,

        "token_reserve_raw": None,
        "quote_reserve_raw": None,

        "token_reserve": 0,
        "quote_reserve": 0,

        "token_decimals": None,
        "quote_decimals": None,

        "weth_reserve": 0,

        "liquidity_eth": 0,

        "risk": "UNKNOWN",

        "reason": reason,

        "eth_price_usd": 0,
        "quote_price_usd": 0,

        "liquidity_usd": 0,

        # V3 positions can be outside the current tick; the pool's raw
        # active-liquidity value cannot be converted to USD without range data.
        "liquidity_usd_status": "NOT_CALCULATED_V3_RANGE_VALUATION",

        "risk": "UNKNOWN",

        "reason": reason,

        "source": "On-chain verification",
    }


# =========================================================
# DEXSCREENER DISCOVERY
# =========================================================

def discover_dexscreener_pools(
    token_address,
):

    token_address = Web3.to_checksum_address(
        token_address
    )

    url = (
        "https://api.dexscreener.com/"
        "latest/dex/tokens/"
        f"{token_address}"
    )

    try:

        response = requests.get(
            url,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

    except Exception:

        return []

    pairs = data.get(
        "pairs"
    ) or []

    results = []

    for pair in pairs:

        chain_id = str(
            pair.get(
                "chainId",
                ""
            )
        ).lower()

        if chain_id != DEXSCREENER_CHAIN:

            continue

        pair_address = pair.get(
            "pairAddress"
        )

        if not pair_address:

            continue

        liquidity = (
            pair.get(
                "liquidity"
            )
            or {}
        )

        liquidity_usd = _safe_float(
            liquidity.get(
                "usd"
            )
        )

        base_token = (
            pair.get(
                "baseToken"
            )
            or {}
        )

        quote_token = (
            pair.get(
                "quoteToken"
            )
            or {}
        )

        results.append(
            {
                "pair_address": pair_address,

                "dex": pair.get(
                    "dexId"
                ),

                "url": pair.get(
                    "url"
                ),

                "base_token": base_token,

                "quote_token": quote_token,

                "liquidity_usd": liquidity_usd,

                "liquidity_base": _safe_float(
                    liquidity.get(
                        "base"
                    )
                ),

                "liquidity_quote": _safe_float(
                    liquidity.get(
                        "quote"
                    )
                ),
            }
        )

    results.sort(
        key=lambda item: item.get(
            "liquidity_usd",
            0
        ),
        reverse=True,
    )

    return results


# =========================================================
# VERIFY DEXSCREENER V2 PAIR ON-CHAIN
# =========================================================

def verify_discovered_v2_pair(
    token_address,
    discovered_pair,
    w3,
):

    token_address = Web3.to_checksum_address(
        token_address
    )

    pair_address = discovered_pair.get(
        "pair_address"
    )

    if not pair_address:
        return None

    try:
        pair_address = Web3.to_checksum_address(
            pair_address
        )

        pair = w3.eth.contract(
            address=pair_address,
            abi=PAIR_ABI,
        )

        token0 = Web3.to_checksum_address(
            pair.functions.token0().call()
        )

        token1 = Web3.to_checksum_address(
            pair.functions.token1().call()
        )

        reserve0, reserve1, _ = (
            pair.functions.getReserves().call()
        )

        if (
            token0.lower() != token_address.lower()
            and token1.lower() != token_address.lower()
        ):
            return None

        if token0.lower() == token_address.lower():
            quote_address = token1
            token_reserve_raw = reserve0
            quote_reserve_raw = reserve1
        else:
            quote_address = token0
            token_reserve_raw = reserve1
            quote_reserve_raw = reserve0

        token_decimals = get_token_decimals(
            w3,
            token_address,
        )
        if token_decimals is None:
            token_decimals = 18

        quote_decimals = get_token_decimals(
            w3,
            quote_address,
        )
        if quote_decimals is None:
            quote_decimals = 18

        token_reserve = (
            token_reserve_raw
            / (10 ** token_decimals)
        )

        quote_reserve = (
            quote_reserve_raw
            / (10 ** quote_decimals)
        )

        weth_reserve = 0.0
        liquidity_eth = 0.0
        eth_price_usd = 0.0
        quote_price_usd = 0.0

        discovered_liquidity_usd = _safe_float(
            discovered_pair.get(
                "liquidity_usd",
                0,
            )
        )

        liquidity_usd = discovered_liquidity_usd

        if quote_reserve <= 0 or token_reserve <= 0:

            risk = "HIGH"
            reason = "Pair was discovered, but one or both token reserves are empty."

        elif quote_address.lower() == WETH.lower():

            weth_reserve = quote_reserve
            liquidity_eth = weth_reserve * 2

            try:
                eth_price_usd = _safe_float(
                    get_eth_price_usd()
                )
            except Exception:
                eth_price_usd = 0.0

            if eth_price_usd > 0:

                liquidity_usd = (
                    liquidity_eth
                    * eth_price_usd
                )

                risk, reason = _liquidity_risk(
                    liquidity_eth
                )

            elif discovered_liquidity_usd > 0:

                risk, reason = _liquidity_risk_from_usd(
                    discovered_liquidity_usd
                )
                reason = (
                    f"DexScreener reported ${discovered_liquidity_usd:,.2f} liquidity; "
                    "on-chain WETH reserves were also verified, but live ETH/USD pricing is unavailable."
                )

            else:

                liquidity_usd = 0.0
                risk = "UNKNOWN"
                reason = (
                    "WETH pair was verified on-chain, but USD valuation is unavailable."
                )

        else:

            try:
                quote_price_usd = _safe_float(
                    get_token_price_usd(
                        quote_address
                    )
                )
            except Exception:
                quote_price_usd = 0.0

            if quote_price_usd > 0:

                liquidity_usd = (
                    quote_reserve
                    * 2
                    * quote_price_usd
                )

                risk, reason = _liquidity_risk_from_usd(
                    liquidity_usd
                )

            elif discovered_liquidity_usd > 0:

                liquidity_usd = discovered_liquidity_usd
                risk, reason = _liquidity_risk_from_usd(
                    liquidity_usd
                )
                reason = (
                    f"DexScreener reported ${discovered_liquidity_usd:,.2f} liquidity; "
                    "on-chain reserves were verified, but quote-token pricing is unavailable."
                )

            else:

                liquidity_usd = 0.0
                risk = "UNKNOWN"
                reason = (
                    "Non-WETH liquidity pool detected. On-chain reserves were verified, but USD valuation requires quote-token pricing."
                )

        return {
            "found": True,

            "dex": discovered_pair.get(
                "dex"
            ) or "Verified V2 Pair",
            "version": "V2",

            "pool": pair_address,
            "pair": pair_address,
            "pair_address": pair_address,

            "token0": token0,
            "token1": token1,

            "quote_token": quote_address,

            "token_reserve_raw": int(
                token_reserve_raw
            ),
            "quote_reserve_raw": int(
                quote_reserve_raw
            ),

            "token_reserve": token_reserve,
            "quote_reserve": quote_reserve,

            "token_decimals": token_decimals,
            "quote_decimals": quote_decimals,

            "weth_reserve": weth_reserve,
            "liquidity_eth": liquidity_eth,

            "eth_price_usd": eth_price_usd,
            "quote_price_usd": quote_price_usd,

            "liquidity_usd": liquidity_usd,

            "dexscreener_liquidity_usd": discovered_liquidity_usd,
            "dexscreener_url": discovered_pair.get(
                "url"
            ),

            "risk": risk,
            "reason": reason,

            "source": "DexScreener discovery + on-chain verification",
        }

    except Exception:
        return None


# =========================================================
# SELECT BEST POOL
# =========================================================

def select_best_pool(pools):

    if not pools:

        return None

    return max(
        pools,
        key=lambda item: (
            _safe_float(
                item.get(
                    "liquidity_usd",
                    0,
                )
            ),
            _safe_float(
                item.get(
                    "liquidity_eth",
                    0,
                )
            ),
        ),
    )


def _pool_identity(pool):

    address = (
        pool.get("pair_address")
        or pool.get("pair")
        or pool.get("pool")
    )

    return str(address).lower() if address else None


# =========================================================
# MAIN LIQUIDITY ANALYSIS
# =========================================================

def analyze_liquidity(
    token_address,
    deep_scan=False,
):

    try:

        w3 = get_web3()

        token_address = Web3.to_checksum_address(
            token_address
        )

    except Exception as error:

        return _empty_result(
            f"Unable to connect to RPC: {error}"
        )

    pools = []

    # =====================================================
    # 1. UNISWAP V2 QUOTE TOKENS
    # =====================================================

    # Check Robinhood's common quote token first in normal mode. If
    # it yields a supported pool, avoid scanning the full PairCreated
    # history just to find less common WETH pools. Deep mode retains
    # the broader historical discovery pass.
    v2_quote_tokens = (
        [WETH, ROBINHOOD_QUOTE_TOKEN]
        if deep_scan
        else [ROBINHOOD_QUOTE_TOKEN, WETH]
    )

    for quote_token in v2_quote_tokens:

        try:

            pair = find_v2_pair(
                token_address,
                quote_token,
                w3,
                allow_event_scan=(
                    deep_scan
                    or not pools
                ),
            )

            if not pair:

                continue

            result = analyze_v2_pool(
                token_address,
                pair,
                w3,
            )

            if not result:

                continue

            if _pool_identity(result) not in {
                _pool_identity(pool) for pool in pools
            }:
                pools.append(result)

        except Exception:

            continue
    # =====================================================
    # 2. UNISWAP V3 WETH
    # =====================================================

    try:

        v3_pools = find_v3_pools(
            token_address,
            w3,
        )

        for item in v3_pools:

            result = analyze_v3_pool(
                item["pool"],
                item["fee"],
                w3,
                token_address=token_address,
            )

            if result:

                pools.append(
                    result
                )

    except Exception:

        pass

    # =====================================================
    # 3. DEXSCREENER GENERIC PAIR DISCOVERY
    # =====================================================

    try:

        discovered = discover_dexscreener_pools(
            token_address
        )

    except Exception:

        discovered = []

    for item in discovered:

        pair_address = item.get(
            "pair_address"
        )

        if not pair_address:

            continue

        existing_pool = next(
            (
                pool
                for pool in pools
                if pair_address
                and pair_address.lower() == _pool_identity(pool)
            ),
            None,
        )

        if existing_pool:
            # Native discovery already verified this V3 pool on-chain. Keep
            # that result, but enrich its unvalued USD field with the
            # third-party estimate instead of discarding the duplicate.
            if existing_pool.get("version") == "V3":
                discovered_liquidity_usd = _safe_float(
                    item.get("liquidity_usd", 0)
                )
                if discovered_liquidity_usd > 0:
                    existing_pool["liquidity_usd"] = discovered_liquidity_usd
                    existing_pool["dexscreener_liquidity_usd"] = discovered_liquidity_usd
                    existing_pool["dexscreener_url"] = item.get("url")
                    existing_pool["liquidity_usd_status"] = "ESTIMATED_DEXSCREENER"
                    existing_pool["liquidity_usd_source"] = "DexScreener estimate"
                    existing_pool["source"] = (
                        "On-chain V3 pool verification + DexScreener USD estimate"
                    )
                    existing_pool["risk"], _ = _liquidity_risk_from_usd(
                        discovered_liquidity_usd
                    )
                    existing_pool["reason"] = (
                        f"DexScreener estimates ${discovered_liquidity_usd:,.2f} "
                        "of pool liquidity. V3 active liquidity was verified "
                        "on-chain; the USD value is a third-party estimate, "
                        "not an independent position-range calculation."
                    )
            continue

        verified = verify_discovered_v2_pair(
            token_address,
            item,
            w3,
        )

        if verified:

            pools.append(
                verified
            )

    # =====================================================
    # NO POOLS
    # =====================================================

    if not pools:

        return _empty_result(
            "No supported liquidity pool was found. "
            "No WETH pool or verified discovered "
            "DEX pair was detected."
        )

    # =====================================================
    # TOTAL LIQUIDITY
    # =====================================================

    total_liquidity_usd = sum(
        _safe_float(
            pool.get(
                "liquidity_usd",
                0,
            )
        )
        for pool in pools
    )

    total_liquidity_eth = sum(
        _safe_float(
            pool.get(
                "liquidity_eth",
                0,
            )
        )
        for pool in pools
    )

    # =====================================================
    # BEST POOL
    # =====================================================

    best_pool = select_best_pool(
        pools
    )

    if not best_pool:

        return _empty_result(
            "Liquidity pools were discovered but no usable "
            "pool could be selected."
        )

    pair_address = (
        best_pool.get("pair")
        or best_pool.get("pair_address")
        or best_pool.get("pool")
    )

    liquidity_usd = _safe_float(
        best_pool.get(
            "liquidity_usd",
            0,
        )
    )

    liquidity_eth = _safe_float(
        best_pool.get(
            "liquidity_eth",
            0,
        )
    )

    weth_reserve = _safe_float(
        best_pool.get(
            "weth_reserve",
            0,
        )
    )

    risk = best_pool.get(
        "risk",
        "UNKNOWN",
    )

    reason = best_pool.get(
        "reason",
        "Liquidity pool detected.",
    )

    # =====================================================
    # FINAL RESULT
    # =====================================================

    return {
        "found": True,

        "dex": best_pool.get(
            "dex"
        ),

        "version": best_pool.get(
            "version"
        ),

        "v3_liquidity": best_pool.get("v3_liquidity"),

        "active_liquidity_status": best_pool.get("active_liquidity_status"),

        "liquidity_usd_status": best_pool.get(
            "liquidity_usd_status",
            "CALCULATED",
        ),

        "liquidity_usd_source": best_pool.get("liquidity_usd_source"),

        "pair": pair_address,

        "best_pool": pair_address,

        "best_pool_data": best_pool,

        "quote_token": best_pool.get(
            "quote_token"
        ),

        "quote_reserve_raw": best_pool.get(
            "quote_reserve_raw"
        ),

        "quote_reserve": best_pool.get(
            "quote_reserve",
            0,
        ),

        "token_reserve_raw": best_pool.get(
            "token_reserve_raw"
        ),

        "token_reserve": best_pool.get(
            "token_reserve",
            0,
        ),

        "token_decimals": best_pool.get(
            "token_decimals",
            18,
        ),

        "quote_decimals": best_pool.get(
            "quote_decimals",
            18,
        ),

        "pools": pools,

        "pools_found": len(
            pools
        ),

        "pool_count": len(
            pools
        ),

        "weth_reserve": weth_reserve,

        "liquidity_eth": round(
            liquidity_eth,
            8,
        ),

        "total_liquidity_eth": round(
            total_liquidity_eth,
            8,
        ),

        "eth_price_usd": best_pool.get(
            "eth_price_usd",
            0,
        ),

        "quote_price_usd": best_pool.get(
            "quote_price_usd",
            0,
        ),

        "liquidity_usd": round(
            liquidity_usd,
            2,
        ),

        "total_discovered_liquidity_usd": round(
            total_liquidity_usd,
            2,
        ),

        "total_liquidity_usd": round(
            total_liquidity_usd,
            2,
        ),

        "risk": risk,

        "reason": reason,
    }


# =========================================================
# COMPATIBILITY ALIASES
# =========================================================

def get_liquidity(
    token_address,
):

    return analyze_liquidity(
        token_address
    )


def check_liquidity(
    token_address,
):

    return analyze_liquidity(
        token_address
    )
