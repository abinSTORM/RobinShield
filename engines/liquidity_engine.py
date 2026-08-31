from web3 import Web3
import requests

from config import RPC_URL
from core.token import get_token_decimals
from core.price import get_eth_price_usd
from core.lp import V2_FACTORY_ABI, PAIR_ABI


# =========================================================
# ROBINHOOD CHAIN
# =========================================================

V2_FACTORY = "0x8bcEaA40B9AcdfAedF85AdF4FF01F5Ad6517937f"

V3_FACTORY = "0x1f7d7550B1b028f7571E69A784071F0205FD2EfA"

WETH = "0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73"

ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

DEXSCREENER_CHAIN = "robinhood"

V3_FEE_TIERS = [
    100,
    500,
    3000,
    10000,
]


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
            "NONE",
            "Pool exists but currently has no usable liquidity.",
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

    return {
        "found": False,

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

        "risk": "NONE",
        "reason": reason,

        "pools": [],
    }


# =========================================================
# V2 POOL DISCOVERY
# =========================================================

def find_v2_pair(
    token_address,
    quote_address=WETH,
    w3=None,
):

    if w3 is None:

        w3 = get_web3()

    token_address = Web3.to_checksum_address(
        token_address
    )

    quote_address = Web3.to_checksum_address(
        quote_address
    )

    factory = w3.eth.contract(
        address=Web3.to_checksum_address(
            V2_FACTORY
        ),
        abi=V2_FACTORY_ABI,
    )

    pair = factory.functions.getPair(
        token_address,
        quote_address,
    ).call()

    if _is_zero_address(pair):

        return None

    return Web3.to_checksum_address(
        pair
    )


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
        token0.lower()
        != token_address.lower()
        and token1.lower()
        != token_address.lower()
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

    if quote_address.lower() == WETH.lower():

        weth_reserve = quote_reserve

        liquidity_eth = (
            weth_reserve * 2
        )

        eth_price_usd = _safe_float(
            get_eth_price_usd()
        )

        liquidity_usd = (
            liquidity_eth
            * eth_price_usd
        )

        risk, reason = _liquidity_risk(
            liquidity_eth
        )

    else:

        risk, reason = (
            _liquidity_risk_from_usd(
                0
            )
        )

        reason = (
            "Non-WETH liquidity pool detected. "
            "On-chain reserves were verified, but USD "
            "valuation requires quote-token pricing."
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

    liquidity = _safe_int(
        pool.functions.liquidity().call()
    )

    slot0 = (
        pool.functions.slot0().call()
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

        "sqrt_price_x96": slot0[0],

        "quote_token": None,

        "token_reserve_raw": None,
        "quote_reserve_raw": None,

        "token_reserve": 0,
        "quote_reserve": 0,

        "token_decimals": None,
        "quote_decimals": None,

        "weth_reserve": 0,

        "liquidity_eth": 0,

        "eth_price_usd": 0,

        "liquidity_usd": 0,

        "risk": "UNKNOWN",

        "reason": (
            "Uniswap V3 pool detected. "
            "Raw V3 liquidity is available but "
            "USD liquidity requires price-range analysis."
        ),

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
            token0.lower()
            != token_address.lower()
            and token1.lower()
            != token_address.lower()
        ):

            return None

        if (
            token0.lower()
            == token_address.lower()
        ):

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

        liquidity_usd = _safe_float(
            discovered_pair.get(
                "liquidity_usd"
            )
        )

        risk, reason = (
            _liquidity_risk_from_usd(
                liquidity_usd
            )
        )

        weth_reserve = 0.0
        liquidity_eth = 0.0
        eth_price_usd = 0.0

        if quote_address.lower() == WETH.lower():

            weth_reserve = quote_reserve

            liquidity_eth = (
                weth_reserve * 2
            )

            eth_price_usd = _safe_float(
                get_eth_price_usd()
            )

            calculated_usd = (
                liquidity_eth
                * eth_price_usd
            )

            if calculated_usd > 0:

                liquidity_usd = calculated_usd

                risk, reason = (
                    _liquidity_risk(
                        liquidity_eth
                    )
                )

        reason = (
            reason
            + " Pool discovered through DexScreener "
            "and verified on-chain."
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

            "liquidity_usd": liquidity_usd,

            "risk": risk,

            "reason": reason,

            "source": (
                "DexScreener + on-chain verification"
            ),

            "dexscreener_url": discovered_pair.get(
                "url"
            ),
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


# =========================================================
# MAIN LIQUIDITY ANALYSIS
# =========================================================

def analyze_liquidity(
    token_address,
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
    # 1. UNISWAP V2 WETH
    # =====================================================

    try:

        pair = find_v2_pair(
            token_address,
            WETH,
            w3,
        )

        if pair:

            result = analyze_v2_pool(
                token_address,
                pair,
                w3,
            )

            if result:

                pools.append(
                    result
                )

    except Exception:

        pass

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

        already_exists = False

        for pool in pools:

            existing = (
                pool.get(
                    "pair_address"
                )
                or pool.get(
                    "pair"
                )
                or pool.get(
                    "pool"
                )
            )

            if (
                existing
                and str(existing).lower()
                == str(pair_address).lower()
            ):

                already_exists = True

                break

        if already_exists:

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