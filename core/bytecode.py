import requests

from config import RPC_URL


# =========================================================
# KNOWN FUNCTION SELECTORS
# =========================================================

KNOWN_SELECTORS = {

    # -----------------------------------------------------
    # ERC-20
    # -----------------------------------------------------

    "70a08231": "balanceOf(address)",
    "a9059cbb": "transfer(address,uint256)",
    "23b872dd": "transferFrom(address,address,uint256)",
    "095ea7b3": "approve(address,uint256)",
    "dd62ed3e": "allowance(address,address)",
    "18160ddd": "totalSupply()",
    "06fdde03": "name()",
    "95d89b41": "symbol()",
    "313ce567": "decimals()",

    # -----------------------------------------------------
    # OWNERSHIP
    # -----------------------------------------------------

    "8da5cb5b": "owner()",
    "715018a6": "renounceOwnership()",
    "f2fde38b": "transferOwnership(address)",

    # -----------------------------------------------------
    # PAUSABLE
    # -----------------------------------------------------

    "5c975abb": "paused()",
    "8456cb59": "pause()",
    "3f4ba83a": "unpause()",

    # -----------------------------------------------------
    # BLACKLIST
    # -----------------------------------------------------


    # -----------------------------------------------------
    # TRADING CONTROLS
    # -----------------------------------------------------

}


# =========================================================
# SELECTOR GENERATION
# =========================================================
#
# Ethereum uses Keccak-256 (not NIST SHA3-256) for function
# selectors. A small pure-Python implementation is included
# so this module does not require an extra crypto package.
# =========================================================

_KECCAK_MASK = (1 << 64) - 1

_KECCAK_ROUND_CONSTANTS = [
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
]

_KECCAK_ROTATION = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]


def _keccak_rotl64(value, shift):
    if shift == 0:
        return value

    return (
        (value << shift)
        | (value >> (64 - shift))
    ) & _KECCAK_MASK


def _keccak_f1600(state):
    for round_constant in _KECCAK_ROUND_CONSTANTS:

        # Theta
        column_parity = [
            state[x]
            ^ state[x + 5]
            ^ state[x + 10]
            ^ state[x + 15]
            ^ state[x + 20]
            for x in range(5)
        ]

        theta = [
            column_parity[(x - 1) % 5]
            ^ _keccak_rotl64(
                column_parity[(x + 1) % 5],
                1,
            )
            for x in range(5)
        ]

        for x in range(5):
            for y in range(5):
                state[x + 5 * y] ^= theta[x]

        # Rho + Pi
        temporary = [0] * 25

        for x in range(5):
            for y in range(5):
                temporary[
                    y + 5 * ((2 * x + 3 * y) % 5)
                ] = _keccak_rotl64(
                    state[x + 5 * y],
                    _KECCAK_ROTATION[x][y],
                )

        # Chi
        for x in range(5):
            for y in range(5):
                state[x + 5 * y] = (
                    temporary[x + 5 * y]
                    ^ (
                        (
                            ~temporary[(x + 1) % 5 + 5 * y]
                        )
                        & temporary[(x + 2) % 5 + 5 * y]
                    )
                ) & _KECCAK_MASK

        # Iota
        state[0] ^= round_constant


def _keccak256(data):
    rate = 136
    data = bytearray(data)

    # Keccak padding: domain 0x01, final bit 0x80.
    data.append(0x01)

    while len(data) % rate != rate - 1:
        data.append(0x00)

    data.append(0x80)

    state = [0] * 25

    for offset in range(0, len(data), rate):

        block = data[offset:offset + rate]

        for index in range(rate // 8):
            state[index] ^= int.from_bytes(
                block[index * 8:index * 8 + 8],
                "little",
            )

        _keccak_f1600(state)

    output = b"".join(
        value.to_bytes(8, "little")
        for value in state
    )

    return output[:32]


def _selector(signature):
    return _keccak256(
        signature.encode("utf-8")
    ).hex()[:8]


# =========================================================
# ADDITIONAL SECURITY SIGNATURES
# =========================================================
#
# These are generated at runtime, so the selector values
# cannot become stale or be accidentally mistyped.
# =========================================================

ADDITIONAL_SIGNATURES = {

    # -----------------------------------------------------
    # BLACKLIST
    # -----------------------------------------------------

    "blacklist(address)": "blacklist(address)",
    "unblacklist(address)": "unblacklist(address)",
    "isBlacklisted(address)": "isBlacklisted(address)",
    "isBlackListed(address)": "isBlackListed(address)",
    "blacklisted(address)": "blacklisted(address)",

    # -----------------------------------------------------
    # TRADING CONTROLS
    # -----------------------------------------------------

    "tradingEnabled()": "tradingEnabled()",
    "tradingOpen()": "tradingOpen()",
    "setTrading(bool)": "setTrading(bool)",
    "startTrading()": "startTrading()",
    "stopTrading()": "stopTrading()",
    "openTrading()": "openTrading()",
    "closeTrading()": "closeTrading()",
    "disableTrading()": "disableTrading()",
    "enableTrading()": "enableTrading()",
    "enableTrading(uint256)": "enableTrading(uint256)",
    "tradingActive()": "tradingActive()",
    "tradingAllowed()": "tradingAllowed()",

    # -----------------------------------------------------
    # LIMITS / ANTI-WHALE
    # -----------------------------------------------------

    "maxTransactionAmount()": "maxTransactionAmount()",
    "maxWalletAmount()": "maxWalletAmount()",
    "maxTxAmount()": "maxTxAmount()",
    "maxWallet()": "maxWallet()",
    "maxWalletSize()": "maxWalletSize()",
    "_maxTxAmount()": "_maxTxAmount()",
    "_maxWalletSize()": "_maxWalletSize()",
    "_maxWalletAmount()": "_maxWalletAmount()",
    "maxHoldingAmount()": "maxHoldingAmount()",
    "maxBuyAmount()": "maxBuyAmount()",
    "maxSellAmount()": "maxSellAmount()",
    "maxTransferAmount()": "maxTransferAmount()",

    "limitsInEffect()": "limitsInEffect()",
    "limited()": "limited()",

    "setMaxTxAmount(uint256)": "setMaxTxAmount(uint256)",
    "setMaxTxnAmount(uint256)": "setMaxTxnAmount(uint256)",
    "setMaxTransactionAmount(uint256)": "setMaxTransactionAmount(uint256)",
    "setMaxWalletAmount(uint256)": "setMaxWalletAmount(uint256)",
    "setMaxWallet(uint256)": "setMaxWallet(uint256)",

    "updateMaxTxAmount(uint256)": "updateMaxTxAmount(uint256)",
    "updateMaxTxnAmount(uint256)": "updateMaxTxnAmount(uint256)",
    "updateMaxTransactionAmount(uint256)": "updateMaxTransactionAmount(uint256)",
    "updateMaxWalletAmount(uint256)": "updateMaxWalletAmount(uint256)",
    "updateMaxWallet(uint256)": "updateMaxWallet(uint256)",

    "removeLimits()": "removeLimits()",
    "setLimitsInEffect(bool)": "setLimitsInEffect(bool)",
    "setMaxTransaction(uint256)": "setMaxTransaction(uint256)",

    # -----------------------------------------------------
    # COOLDOWN / TRANSFER DELAY
    # -----------------------------------------------------

    "cooldownEnabled()": "cooldownEnabled()",
    "transferDelayEnabled()": "transferDelayEnabled()",
    "setCooldownEnabled(bool)": "setCooldownEnabled(bool)",
    "setTransferDelayEnabled(bool)": "setTransferDelayEnabled(bool)",
    "disableTransferDelay()": "disableTransferDelay()",
    "setCooldown(uint256)": "setCooldown(uint256)",
    "setCooldownTime(uint256)": "setCooldownTime(uint256)",
    "tradeCooldownTime()": "tradeCooldownTime()",
    "updateTradeCooldownTime(uint256)": "updateTradeCooldownTime(uint256)",

    # -----------------------------------------------------
    # COMMON TAX GETTERS
    # -----------------------------------------------------

    "buyTaxRate()": "buyTaxRate()",
    "sellTaxRate()": "sellTaxRate()",
    "taxRate()": "taxRate()",
    "buyTotalFees()": "buyTotalFees()",
    "sellTotalFees()": "sellTotalFees()",
}


for _signature, _display_name in ADDITIONAL_SIGNATURES.items():

    KNOWN_SELECTORS[
        _selector(_signature)
    ] = _display_name


# =========================================================
# RPC
# =========================================================

def rpc_call(method, params):

    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1,
    }

    response = requests.post(
        RPC_URL,
        json=payload,
        timeout=10,
    )

    if response.status_code != 200:
        return None

    data = response.json()

    if "error" in data:
        return None

    return data.get("result")


# =========================================================
# BYTECODE
# =========================================================

def get_web3_bytecode(address):

    return rpc_call(
        "eth_getCode",
        [
            address,
            "latest",
        ],
    )


def get_bytecode(address):

    bytecode = get_web3_bytecode(address)

    if not bytecode:
        return None

    if bytecode == "0x":
        return None

    return bytecode


def bytecode_size(bytecode):

    if not bytecode:
        return 0

    if bytecode.startswith("0x"):
        bytecode = bytecode[2:]

    return len(bytecode) // 2


def normalize_bytecode(bytecode):

    if not bytecode:
        return ""

    bytecode = bytecode.lower()

    if bytecode.startswith("0x"):
        bytecode = bytecode[2:]

    return bytecode


def selector_present(
    bytecode,
    selector,
):

    normalized = normalize_bytecode(
        bytecode
    )

    return selector.lower() in normalized


def detect_selectors(bytecode):

    detected = []

    if not bytecode:
        return detected

    for selector, name in KNOWN_SELECTORS.items():

        if selector_present(
            bytecode,
            selector,
        ):

            detected.append(
                {
                    "selector": selector,
                    "function": name,
                }
            )

    return detected


# =========================================================
# GROUP SELECTORS
# =========================================================

def group_detected_selectors(
    detected,
):

    groups = {
        "erc20": [],
        "ownership": [],
        "pause": [],
        "blacklist": [],
        "trading": [],
        "limits": [],
        "tax": [],
    }

    for item in detected:

        function = item["function"]

        lower = function.lower()

        # -------------------------------------------------
        # ERC20
        # -------------------------------------------------

        if function in [
            "balanceOf(address)",
            "transfer(address,uint256)",
            "transferFrom(address,address,uint256)",
            "approve(address,uint256)",
            "allowance(address,address)",
            "totalSupply()",
            "name()",
            "symbol()",
            "decimals()",
        ]:

            groups["erc20"].append(item)

        # -------------------------------------------------
        # OWNERSHIP
        # -------------------------------------------------

        elif (
            function == "owner()"
            or "ownership" in lower
            or "renounceownership" in lower
            or "transferownership" in lower
        ):

            groups["ownership"].append(item)

        # -------------------------------------------------
        # PAUSE
        # -------------------------------------------------

        elif (
            "pause" in lower
            or "unpause" in lower
        ):

            groups["pause"].append(item)

        # -------------------------------------------------
        # BLACKLIST
        # -------------------------------------------------

        elif "blacklist" in lower:

            groups["blacklist"].append(item)

        # -------------------------------------------------
        # TRADING
        # -------------------------------------------------

        elif (
            "trading" in lower
            or "starttrading" in lower
            or "opentrading" in lower
            or "settrading" in lower
        ):

            groups["trading"].append(item)

        # -------------------------------------------------
        # LIMITS
        # -------------------------------------------------

        elif (
            "maxtx" in lower
            or "maxtransaction" in lower
            or "maxwallet" in lower
            or "maxholding" in lower
            or "maxbuy" in lower
            or "maxsell" in lower
            or "maxtransfer" in lower
            or "cooldown" in lower
            or "transferdelay" in lower
            or "transactionlimit" in lower
            or "limitsineffect" in lower
            or "setlimits" in lower
            or "removelimits" in lower
        ):

            groups["limits"].append(item)

        # -------------------------------------------------
        # TAX
        # -------------------------------------------------

        elif (
            "tax" in lower
            or "fee" in lower
        ):

            groups["tax"].append(item)

    return groups


# =========================================================
# PROXY DETECTION
# =========================================================

EIP1967_IMPLEMENTATION_SLOT = (
    "0x360894a13ba1a3210667c828492db98d"
    "ca3e2076cc3735a920a3ca505d382bbc"
)


def get_storage_at(
    address,
    slot,
):

    return rpc_call(
        "eth_getStorageAt",
        [
            address,
            slot,
            "latest",
        ],
    )


def extract_address_from_storage(
    storage_value,
):

    if not storage_value:
        return None

    value = storage_value.lower()

    if value.startswith("0x"):
        value = value[2:]

    if len(value) < 40:
        return None

    address_hex = value[-40:]

    if address_hex == "0" * 40:
        return None

    return "0x" + address_hex


def is_contract(address):

    code = get_bytecode(address)

    return code is not None


def detect_eip1967_proxy(
    address,
):

    result = {
        "detected": False,
        "type": None,
        "implementation": None,
        "confidence": "LOW",
        "reason": None,
    }

    storage = get_storage_at(
        address,
        EIP1967_IMPLEMENTATION_SLOT,
    )

    implementation = (
        extract_address_from_storage(
            storage
        )
    )

    if implementation:

        result["detected"] = True
        result["type"] = "EIP-1967"
        result["implementation"] = implementation
        result["confidence"] = "HIGH"
        result["reason"] = (
            "EIP-1967 implementation address "
            "was found in the standard storage slot."
        )

        return result

    result["reason"] = (
        "No EIP-1967 implementation address "
        "was found in the standard storage slot."
    )

    return result


def detect_minimal_proxy(
    bytecode,
):

    result = {
        "detected": False,
        "implementation": None,
        "confidence": "LOW",
        "reason": None,
    }

    normalized = normalize_bytecode(
        bytecode
    )

    prefix = "363d3d373d3d3d363d73"
    suffix = "5af43d82803e903d91602b57fd5bf3"

    if not normalized.startswith(prefix):

        result["reason"] = (
            "ERC-1167 minimal proxy prefix "
            "not detected."
        )

        return result

    if not normalized.endswith(suffix):

        result["reason"] = (
            "ERC-1167 minimal proxy suffix "
            "not detected."
        )

        return result

    implementation_start = len(prefix)

    implementation_end = (
        implementation_start + 40
    )

    if len(normalized) < implementation_end:

        result["reason"] = (
            "Minimal proxy bytecode is incomplete."
        )

        return result

    implementation = (
        "0x"
        + normalized[
            implementation_start:
            implementation_end
        ]
    )

    result["detected"] = True

    result["implementation"] = (
        implementation
    )

    result["confidence"] = "HIGH"

    result["reason"] = (
        "ERC-1167 minimal proxy detected."
    )

    return result


def analyze_proxy(
    address,
    bytecode,
):

    result = {
        "detected": False,
        "type": None,
        "implementation": None,
        "confidence": "LOW",
        "reason": None,
    }

    # -----------------------------------------------------
    # EIP-1967
    # -----------------------------------------------------

    try:

        eip1967 = detect_eip1967_proxy(
            address
        )

        if eip1967["detected"]:

            return eip1967

    except Exception:

        pass

    # -----------------------------------------------------
    # ERC-1167
    # -----------------------------------------------------

    try:

        minimal = detect_minimal_proxy(
            bytecode
        )

        if minimal["detected"]:

            return {
                "detected": True,
                "type": "ERC-1167",
                "implementation": minimal[
                    "implementation"
                ],
                "confidence": minimal[
                    "confidence"
                ],
                "reason": minimal[
                    "reason"
                ],
            }

    except Exception:

        pass

    result["reason"] = (
        "No supported proxy pattern was detected."
    )

    return result


# =========================================================
# IMPLEMENTATION ANALYSIS
# =========================================================

def analyze_implementation(
    implementation_address,
):

    if not implementation_address:

        return {
            "available": False,
            "reason": (
                "No implementation address provided."
            ),
        }

    try:

        implementation_bytecode = (
            get_bytecode(
                implementation_address
            )
        )

    except Exception as e:

        return {
            "available": False,
            "reason": (
                "Implementation bytecode "
                f"retrieval failed: {e}"
            ),
        }

    if not implementation_bytecode:

        return {
            "available": False,
            "reason": (
                "Implementation contract bytecode "
                "could not be retrieved."
            ),
        }

    size = bytecode_size(
        implementation_bytecode
    )

    detected = detect_selectors(
        implementation_bytecode
    )

    groups = group_detected_selectors(
        detected
    )

    result = {
        "available": True,
        "status": "PASS",
        "confidence": "MEDIUM",
        "address": implementation_address,
        "bytecode_size": size,
        "detected_selectors": detected,
        "groups": groups,
        "warnings": [],
        "signals": [],
    }

    result["signals"].append(
        "Proxy implementation bytecode "
        "retrieved successfully."
    )

    result["signals"].append(
        f"Implementation bytecode size: "
        f"{size} bytes."
    )

    if groups["ownership"]:

        result["signals"].append(
            "Implementation contains "
            "ownership selectors: "
            + ", ".join(
                item["function"]
                for item in groups[
                    "ownership"
                ]
            )
        )

    if groups["blacklist"]:

        result["warnings"].append(
            "Implementation contains "
            "blacklist-related selectors."
        )

    if groups["pause"]:

        result["warnings"].append(
            "Implementation contains "
            "pause-related selectors."
        )

    if groups["trading"]:

        result["signals"].append(
            "Implementation contains "
            "trading-control selectors: "
            + ", ".join(
                item["function"]
                for item in groups[
                    "trading"
                ]
            )
        )

    if groups["limits"]:

        result["signals"].append(
            "Implementation contains "
            "transaction-limit selectors."
        )

    if groups["tax"]:

        result["signals"].append(
            "Implementation contains "
            "tax/fee selectors."
        )

    return result


# =========================================================
# MAIN BYTECODE ANALYSIS
# =========================================================

def analyze_bytecode(
    address,
):

    result = {

        "available": False,

        "status": "UNAVAILABLE",

        "confidence": "LOW",

        "bytecode_size": 0,

        "proxy": {

            "detected": False,

            "type": None,

            "implementation": None,

            "confidence": "LOW",

            "reason": None,

        },

        "detected_selectors": [],

        "groups": {

            "erc20": [],

            "ownership": [],

            "pause": [],

            "blacklist": [],

            "trading": [],

            "limits": [],

            "tax": [],

        },

        "warnings": [],

        "signals": [],

    }

    # =====================================================
    # RETRIEVE BYTECODE
    # =====================================================

    try:

        bytecode = get_bytecode(
            address
        )

    except Exception as e:

        result["warnings"].append(
            f"Bytecode retrieval failed: {e}"
        )

        return result

    if not bytecode:

        result["warnings"].append(
            "No contract bytecode was retrieved."
        )

        return result

    result["available"] = True

    result["status"] = "PASS"

    result["confidence"] = "MEDIUM"

    result["bytecode_size"] = (
        bytecode_size(
            bytecode
        )
    )

    # =====================================================
    # PROXY
    # =====================================================

    try:

        proxy = analyze_proxy(
            address,
            bytecode,
        )

        result["proxy"] = proxy

        if proxy["detected"]:

            result["signals"].append(
                "Proxy detected: "
                f"{proxy['type']}."
            )

            if proxy.get(
                "implementation"
            ):

                result["signals"].append(
                    "Implementation: "
                    + proxy[
                        "implementation"
                    ]
                )

                implementation_report = (
                    analyze_implementation(
                        proxy[
                            "implementation"
                        ]
                    )
                )

                result["proxy"][
                    "implementation_analysis"
                ] = implementation_report

                if implementation_report.get(
                    "available"
                ):

                    result["signals"].append(
                        "Proxy implementation "
                        "bytecode was successfully "
                        "analyzed."
                    )

    except Exception as e:

        result["warnings"].append(
            f"Proxy analysis failed: {e}"
        )

    # =====================================================
    # SELECTOR ANALYSIS
    # =====================================================

    detected = detect_selectors(
        bytecode
    )

    result["detected_selectors"] = (
        detected
    )

    result["groups"] = (
        group_detected_selectors(
            detected
        )
    )

    result["signals"].append(
        "Contract bytecode retrieved "
        "successfully."
    )

    # =====================================================
    # BYTECODE SIZE
    # =====================================================

    if result["bytecode_size"] < 100:

        result["warnings"].append(
            "Contract bytecode is unusually "
            "small. It may be a proxy, "
            "minimal contract, forwarder, "
            "or another special contract type."
        )

    # =====================================================
    # OWNERSHIP
    # =====================================================

    if result["groups"]["ownership"]:

        result["signals"].append(
            "Ownership-related selectors "
            "detected: "
            + ", ".join(
                item["function"]
                for item in result[
                    "groups"
                ]["ownership"]
            )
        )

    # =====================================================
    # BLACKLIST
    # =====================================================

    if result["groups"]["blacklist"]:

        result["warnings"].append(
            "Blacklist-related selectors "
            "detected."
        )

    # =====================================================
    # PAUSE
    # =====================================================

    if result["groups"]["pause"]:

        result["warnings"].append(
            "Pause-related selectors detected."
        )

    # =====================================================
    # TRADING
    # =====================================================

    if result["groups"]["trading"]:

        result["signals"].append(
            "Trading-control selectors "
            "detected: "
            + ", ".join(
                item["function"]
                for item in result[
                    "groups"
                ]["trading"]
            )
        )

    # =====================================================
    # LIMITS
    # =====================================================

    if result["groups"]["limits"]:

        result["signals"].append(
            "Transaction-limit selectors "
            "detected."
        )

    # =====================================================
    # TAX
    # =====================================================

    if result["groups"]["tax"]:

        result["signals"].append(
            "Tax/fee selectors detected."
        )

    # =====================================================
    # NO SELECTORS
    # =====================================================

    if not detected:

        result["signals"].append(
            "No recognized selectors were "
            "detected in the bytecode."
        )

    return result