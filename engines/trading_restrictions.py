from web3 import Web3

from config import RPC_URL
from core.bytecode import analyze_bytecode


TRADING_STATE_FUNCTIONS = [
    "tradingEnabled",
    "tradingOpen",
    "isTradingEnabled",
    "isTradingOpen",
    "openTrading",
    "enableTrading",
    "tradingActive",
]

MAX_TX_FUNCTIONS = [
    "maxTxAmount",
    "maxTransactionAmount",
    "maxTransaction",
    "maximumTxAmount",
    "maxBuyAmount",
    "maxSellAmount",
    "maxTransferAmount",
]

MAX_WALLET_FUNCTIONS = [
    "maxWalletAmount",
    "maxWallet",
    "maxWalletSize",
    "maxHoldingAmount",
    "maxHolding",
    "maximumWalletAmount",
]

COOLDOWN_FUNCTIONS = [
    "cooldown",
    "cooldownEnabled",
    "coolDownEnabled",
    "transferDelayEnabled",
    "transferDelay",
]

LIMIT_CONTROL_FUNCTIONS = [
    "limitsInEffect",
    "limitsEnabled",
    "limitsActive",
    "removeLimits",
    "setLimits",
    "setMaxTxAmount",
    "setMaxWalletAmount",
]

EXEMPTION_FUNCTIONS = [
    "isExcludedFromLimits",
    "excludeFromLimits",
    "excludeFromFees",
    "isExcludedFromFees",
    "isFeeExempt",
]


# =========================================================
# WEB3
# =========================================================

def get_web3():

    w3 = Web3(
        Web3.HTTPProvider(RPC_URL)
    )

    if not w3.is_connected():

        raise ConnectionError(
            "Unable to connect to Robinhood Chain RPC."
        )

    return w3


# =========================================================
# ABI HELPERS
# =========================================================

def get_function_names(abi):

    names = set()

    if not abi:
        return names

    for item in abi:

        if not isinstance(
            item,
            dict
        ):
            continue

        if item.get("type") != "function":
            continue

        name = item.get("name")

        if name:
            names.add(name)

    return names


def find_functions(
    function_names,
    candidates,
):

    detected = []

    lower_map = {
        name.lower(): name
        for name in function_names
    }

    for candidate in candidates:

        actual = lower_map.get(
            candidate.lower()
        )

        if actual:
            detected.append(actual)

    return detected


# =========================================================
# ABI READ
# =========================================================

def read_no_arg_function(
    token_address,
    function_name,
    output_type="uint256",
):

    try:

        w3 = get_web3()

        token = w3.eth.contract(
            address=Web3.to_checksum_address(
                token_address
            ),
            abi=[
                {
                    "inputs": [],
                    "name": function_name,
                    "outputs": [
                        {
                            "internalType": output_type,
                            "name": "",
                            "type": output_type,
                        }
                    ],
                    "stateMutability": "view",
                    "type": "function",
                }
            ],
        )

        return token.functions[
            function_name
        ]().call()

    except Exception:

        return None


# =========================================================
# BYTECODE HELPERS
# =========================================================

def _selector_names(
    functions,
):

    names = []

    if not isinstance(
        functions,
        list
    ):
        return names

    for item in functions:

        if not isinstance(
            item,
            dict
        ):
            continue

        name = item.get(
            "function",
            item.get(
                "selector",
                ""
            )
        )

        if name:
            names.append(
                str(name)
            )

    return names


def _matches_bytecode_function(
    names,
    candidates,
):

    detected = []

    candidate_lower = {
        item.lower()
        for item in candidates
    }

    for name in names:

        # Example:
        # maxTxAmount(uint256)
        #
        # We compare the part before "(".

        base_name = name.split(
            "(",
            1
        )[0].lower()

        if base_name in candidate_lower:

            detected.append(
                name
            )

    return detected


# =========================================================
# BYTECODE FALLBACK
# =========================================================

def analyze_trading_restrictions_bytecode(
    token_address,
):

    result = {

        "status": "PASS",
        "risk": "LOW",
        "confidence": "LOW",

        "trading_state": {
            "detected": [],
            "values": {},
        },

        "max_transaction": {
            "detected": [],
            "values": {},
        },

        "max_wallet": {
            "detected": [],
            "values": {},
        },

        "cooldown": {
            "detected": [],
            "values": {},
        },

        "limit_controls": {
            "detected": [],
        },

        "exemptions": {
            "detected": [],
        },

        "warnings": [],
        "signals": [],
    }

    try:

        bytecode_result = analyze_bytecode(
            token_address
        )

    except Exception as e:

        result["status"] = "UNKNOWN"
        result["risk"] = "HIGH"
        result["confidence"] = "LOW"

        result["warnings"].append(
            "Bytecode trading-restriction analysis failed: "
            + str(e)
        )

        return result

    if not isinstance(
        bytecode_result,
        dict
    ):

        result["status"] = "UNKNOWN"
        result["risk"] = "HIGH"

        result["warnings"].append(
            "Bytecode analyzer returned an invalid result."
        )

        return result

    if not bytecode_result.get(
        "available",
        False
    ):

        result["status"] = "UNAVAILABLE"
        result["risk"] = "HIGH"
        result["confidence"] = "LOW"

        result["warnings"].append(
            "Trading restriction analysis is unavailable "
            "because contract bytecode could not be loaded."
        )

        return result

    groups = bytecode_result.get(
        "groups",
        {}
    )

    if not isinstance(
        groups,
        dict
    ):

        groups = {}

    # =====================================================
    # TRADING
    # =====================================================

    trading_names = _selector_names(
        groups.get(
            "trading",
            []
        )
    )

    trading_state = _matches_bytecode_function(
        trading_names,
        TRADING_STATE_FUNCTIONS
    )

    result[
        "trading_state"
    ][
        "detected"
    ] = trading_state

    # =====================================================
    # LIMITS
    # =====================================================

    limit_names = _selector_names(
        groups.get(
            "limits",
            []
        )
    )

    max_tx = _matches_bytecode_function(
        limit_names,
        MAX_TX_FUNCTIONS
    )

    max_wallet = _matches_bytecode_function(
        limit_names,
        MAX_WALLET_FUNCTIONS
    )

    cooldown = _matches_bytecode_function(
        limit_names,
        COOLDOWN_FUNCTIONS
    )

    limit_controls = _matches_bytecode_function(
        limit_names,
        LIMIT_CONTROL_FUNCTIONS
    )

    exemptions = _matches_bytecode_function(
        limit_names,
        EXEMPTION_FUNCTIONS
    )

    result[
        "max_transaction"
    ][
        "detected"
    ] = max_tx

    result[
        "max_wallet"
    ][
        "detected"
    ] = max_wallet

    result[
        "cooldown"
    ][
        "detected"
    ] = cooldown

    result[
        "limit_controls"
    ][
        "detected"
    ] = limit_controls

    result[
        "exemptions"
    ][
        "detected"
    ] = exemptions

    # =====================================================
    # SIGNALS
    # =====================================================

    if trading_state:

        result["signals"].append(
            "Trading-state control selectors detected "
            "in the bytecode: "
            + ", ".join(
                trading_state
            )
        )

        result["warnings"].append(
            "Trading state cannot be determined from "
            "selectors alone."
        )

    if max_tx:

        result["signals"].append(
            "Maximum transaction limit selectors detected "
            "in the bytecode: "
            + ", ".join(
                max_tx
            )
        )

        result["warnings"].append(
            "Maximum transaction restrictions may exist."
        )

    if max_wallet:

        result["signals"].append(
            "Maximum wallet limit selectors detected "
            "in the bytecode: "
            + ", ".join(
                max_wallet
            )
        )

        result["warnings"].append(
            "Maximum wallet restrictions may exist."
        )

    if cooldown:

        result["signals"].append(
            "Cooldown/transfer-delay selectors detected "
            "in the bytecode: "
            + ", ".join(
                cooldown
            )
        )

        result["warnings"].append(
            "Cooldown or transfer-delay restrictions "
            "may exist."
        )

    if limit_controls:

        result["signals"].append(
            "Limit-control selectors detected "
            "in the bytecode: "
            + ", ".join(
                limit_controls
            )
        )

    if exemptions:

        result["signals"].append(
            "Limit/fee exemption selectors detected "
            "in the bytecode: "
            + ", ".join(
                exemptions
            )
        )

    # =====================================================
    # RISK
    # =====================================================

    restriction_count = (
        len(max_tx)
        + len(max_wallet)
        + len(cooldown)
    )

    if trading_state:

        result["status"] = "WARNING"
        result["risk"] = "MEDIUM"

    elif restriction_count >= 3:

        result["status"] = "WARNING"
        result["risk"] = "MEDIUM"

    elif restriction_count > 0:

        result["status"] = "WARNING"
        result["risk"] = "LOW"

    else:

        result["status"] = "PASS"
        result["risk"] = "LOW"

        result["signals"].append(
            "No recognized maximum transaction, maximum "
            "wallet, or cooldown selectors were detected "
            "in the bytecode."
        )

    result["warnings"].append(
        "Bytecode selector analysis is lower confidence "
        "than ABI analysis and cannot detect every "
        "runtime restriction."
    )

    return result


# =========================================================
# MAIN ANALYSIS
# =========================================================

def analyze_trading_restrictions(
    token_address,
    abi,
):

    # =====================================================
    # ABI UNAVAILABLE → BYTECODE
    # =====================================================

    if not abi:

        return analyze_trading_restrictions_bytecode(
            token_address
        )

    # =====================================================
    # INITIAL RESULT
    # =====================================================

    functions = get_function_names(
        abi
    )

    result = {

        "status": "PASS",
        "risk": "LOW",
        "confidence": "MEDIUM",

        "trading_state": {
            "detected": [],
            "values": {},
        },

        "max_transaction": {
            "detected": [],
            "values": {},
        },

        "max_wallet": {
            "detected": [],
            "values": {},
        },

        "cooldown": {
            "detected": [],
            "values": {},
        },

        "limit_controls": {
            "detected": [],
        },

        "exemptions": {
            "detected": [],
        },

        "warnings": [],
        "signals": [],
    }

    # =====================================================
    # TRADING STATE
    # =====================================================

    trading_state = find_functions(
        functions,
        TRADING_STATE_FUNCTIONS,
    )

    result[
        "trading_state"
    ][
        "detected"
    ] = trading_state

    for function_name in trading_state:

        value = read_no_arg_function(
            token_address,
            function_name,
            "bool",
        )

        if value is not None:

            result[
                "trading_state"
            ][
                "values"
            ][
                function_name
            ] = bool(value)

            if value is False:

                result["warnings"].append(
                    f"{function_name}() currently returns "
                    "false; trading may be disabled."
                )

            else:

                result["signals"].append(
                    f"{function_name}() currently returns true."
                )

    if trading_state:

        result["signals"].append(
            "Trading-state control functionality detected."
        )

    # =====================================================
    # MAX TRANSACTION
    # =====================================================

    max_tx = find_functions(
        functions,
        MAX_TX_FUNCTIONS,
    )

    result[
        "max_transaction"
    ][
        "detected"
    ] = max_tx

    for function_name in max_tx:

        value = read_no_arg_function(
            token_address,
            function_name,
            "uint256",
        )

        if value is not None:

            result[
                "max_transaction"
            ][
                "values"
            ][
                function_name
            ] = int(value)

    if max_tx:

        result["signals"].append(
            "Maximum transaction limit functionality detected: "
            + ", ".join(
                max_tx
            )
        )

        result["warnings"].append(
            "The token may restrict the maximum amount "
            "that can be transferred in a transaction."
        )

    # =====================================================
    # MAX WALLET
    # =====================================================

    max_wallet = find_functions(
        functions,
        MAX_WALLET_FUNCTIONS,
    )

    result[
        "max_wallet"
    ][
        "detected"
    ] = max_wallet

    for function_name in max_wallet:

        value = read_no_arg_function(
            token_address,
            function_name,
            "uint256",
        )

        if value is not None:

            result[
                "max_wallet"
            ][
                "values"
            ][
                function_name
            ] = int(value)

    if max_wallet:

        result["signals"].append(
            "Maximum wallet/holding limit functionality detected: "
            + ", ".join(
                max_wallet
            )
        )

        result["warnings"].append(
            "The token may restrict the maximum amount "
            "a wallet can hold."
        )

    # =====================================================
    # COOLDOWN
    # =====================================================

    cooldown = find_functions(
        functions,
        COOLDOWN_FUNCTIONS,
    )

    result[
        "cooldown"
    ][
        "detected"
    ] = cooldown

    for function_name in cooldown:

        value = read_no_arg_function(
            token_address,
            function_name,
            "bool",
        )

        if value is not None:

            result[
                "cooldown"
            ][
                "values"
            ][
                function_name
            ] = bool(value)

    if cooldown:

        result["signals"].append(
            "Cooldown/transfer-delay functionality detected: "
            + ", ".join(
                cooldown
            )
        )

        result["warnings"].append(
            "The token may impose cooldowns or transfer delays."
        )

    # =====================================================
    # LIMIT CONTROLS
    # =====================================================

    limit_controls = find_functions(
        functions,
        LIMIT_CONTROL_FUNCTIONS,
    )

    result[
        "limit_controls"
    ][
        "detected"
    ] = limit_controls

    if limit_controls:

        result["signals"].append(
            "Transaction/wallet limit control functions detected: "
            + ", ".join(
                limit_controls
            )
        )

    # =====================================================
    # EXEMPTIONS
    # =====================================================

    exemptions = find_functions(
        functions,
        EXEMPTION_FUNCTIONS,
    )

    result[
        "exemptions"
    ][
        "detected"
    ] = exemptions

    if exemptions:

        result["signals"].append(
            "Limit/fee exemption functionality detected: "
            + ", ".join(
                exemptions
            )
        )

    # =====================================================
    # RISK
    # =====================================================

    restriction_count = (
        len(max_tx)
        + len(max_wallet)
        + len(cooldown)
    )

    disabled_trading = any(
        value is False
        for value in result[
            "trading_state"
        ][
            "values"
        ].values()
    )

    if disabled_trading:

        result["status"] = "WARNING"
        result["risk"] = "HIGH"
        result["confidence"] = "HIGH"

    elif restriction_count >= 3:

        result["status"] = "WARNING"
        result["risk"] = "MEDIUM"
        result["confidence"] = "MEDIUM"

    elif restriction_count > 0:

        result["status"] = "WARNING"
        result["risk"] = "LOW"
        result["confidence"] = "MEDIUM"

    else:

        result["status"] = "PASS"
        result["risk"] = "LOW"
        result["confidence"] = "MEDIUM"

        result["signals"].append(
            "No recognized maximum transaction, maximum wallet, "
            "or cooldown controls were detected."
        )

    return result