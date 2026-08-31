from web3 import Web3

from config import RPC_URL
from core.bytecode import analyze_bytecode


# =========================================================
# OWNERSHIP / ADMIN FUNCTION NAMES
# =========================================================

OWNER_GETTERS = [
    "owner",
    "getOwner",
]

OWNERSHIP_TRANSFER_FUNCTIONS = [
    "transferOwnership",
    "safeTransferOwnership",
]

OWNERSHIP_RENOUNCE_FUNCTIONS = [
    "renounceOwnership",
]

ADMIN_CONTROL_FUNCTIONS = [

    # Trading
    "setTradingEnabled",
    "enableTrading",
    "disableTrading",
    "setTradingOpen",
    "openTrading",
    "closeTrading",

    # Fees
    "setTax",
    "setTaxes",
    "updateTaxes",
    "setBuyTax",
    "setSellTax",
    "setBuyTaxRate",
    "setSellTaxRate",

    # Blacklist
    "blacklist",
    "addBlacklist",
    "removeBlacklist",
    "setBlacklist",
    "setBlacklisted",

    # Limits
    "setMaxTxAmount",
    "setMaxTransactionAmount",
    "setMaxWallet",
    "setMaxWalletAmount",

    # Pausing
    "pause",
    "unpause",

    # Fee exclusions
    "excludeFromFees",
    "excludeFromFee",
    "includeInFees",

    # Wallet / address configuration
    "setFeeWallet",
    "setTaxWallet",
    "setMarketingWallet",
    "setDevWallet",

    # Router / pair
    "setRouter",
    "setPair",

    # Rescue functions
    "rescueTokens",
    "rescueETH",
    "withdraw",
    "withdrawETH",
]


ZERO_ADDRESS = (
    "0x0000000000000000000000000000000000000000"
)


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
# FIND FUNCTION ABI
# =========================================================

def find_function_abi(
    abi,
    function_name,
):

    if not abi:
        return None

    for item in abi:

        if not isinstance(item, dict):
            continue

        if item.get("type") != "function":
            continue

        if item.get("name") == function_name:
            return item

    return None


# =========================================================
# READ ZERO-ARGUMENT FUNCTION
# =========================================================

def call_zero_argument_function(
    address,
    abi,
    function_name,
):

    function_abi = find_function_abi(
        abi,
        function_name,
    )

    if function_abi is None:
        return None

    inputs = function_abi.get(
        "inputs",
        []
    )

    if len(inputs) != 0:
        return None

    outputs = function_abi.get(
        "outputs",
        []
    )

    if not outputs:
        return None

    try:

        w3 = get_web3()

        contract = w3.eth.contract(
            address=Web3.to_checksum_address(
                address
            ),
            abi=[
                function_abi
            ],
        )

        function = getattr(
            contract.functions,
            function_name
        )

        return function().call()

    except Exception:

        return None


# =========================================================
# NORMALIZE ADDRESS
# =========================================================

def normalize_address(value):

    if value is None:
        return None

    if not isinstance(value, str):
        return None

    if not Web3.is_address(value):
        return None

    return Web3.to_checksum_address(
        value
    )


# =========================================================
# BYTECODE OWNERSHIP ANALYSIS
# =========================================================

def analyze_ownership_bytecode(
    address
):

    result = {

        "status": "UNKNOWN",

        "risk": "UNKNOWN",

        "confidence": "LOW",

        "owner": None,

        "owner_readable": False,

        "ownership_renounced": None,

        "can_transfer_ownership": False,

        "can_renounce_ownership": False,

        "admin_functions": [],

        "warnings": [],

        "signals": [],

    }

    try:

        bytecode_result = analyze_bytecode(
            address
        )

    except Exception as e:

        result["status"] = "UNKNOWN"
        result["risk"] = "HIGH"
        result["confidence"] = "LOW"

        result["warnings"].append(
            "Bytecode ownership analysis failed: "
            + str(e)
        )

        return result

    if not bytecode_result:

        result["status"] = "UNKNOWN"
        result["risk"] = "HIGH"
        result["confidence"] = "LOW"

        result["warnings"].append(
            "Bytecode ownership analysis returned no result."
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
            "Ownership analysis is unavailable because "
            "contract bytecode could not be loaded."
        )

        return result

    groups = bytecode_result.get(
        "groups",
        {}
    )

    ownership_functions = groups.get(
        "ownership",
        []
    )

    if not isinstance(
        ownership_functions,
        list
    ):

        ownership_functions = []

    ownership_names = []

    for item in ownership_functions:

        if not isinstance(item, dict):
            continue

        function_name = item.get(
            "function"
        )

        if function_name:
            ownership_names.append(
                function_name
            )

    # -----------------------------------------------------
    # DETECT OWNERSHIP FUNCTIONS
    # -----------------------------------------------------

    has_owner = (
        "owner()" in ownership_names
        or "getOwner()" in ownership_names
    )

    has_transfer = (
        "transferOwnership(address)"
        in ownership_names
    )

    has_renounce = (
        "renounceOwnership()"
        in ownership_names
    )

    result[
        "can_transfer_ownership"
    ] = has_transfer

    result[
        "can_renounce_ownership"
    ] = has_renounce

    # -----------------------------------------------------
    # NO OWNERSHIP SELECTORS
    # -----------------------------------------------------

    if not ownership_names:

        result["status"] = "PASS"
        result["risk"] = "LOW"
        result["confidence"] = "LOW"

        result["signals"].append(
            "No recognized ownership selectors "
            "were detected in the bytecode."
        )

        result["warnings"].append(
            "Bytecode selector analysis cannot determine "
            "every possible ownership implementation."
        )

        return result

    # -----------------------------------------------------
    # OWNER DETECTED
    # -----------------------------------------------------

    if has_owner:

        result["status"] = "INFO"
        result["risk"] = "LOW"
        result["confidence"] = "LOW"

        result["signals"].append(
            "Ownership getter detected in bytecode."
        )

        result["warnings"].append(
            "Current owner address cannot be determined "
            "from selectors alone."
        )

    # -----------------------------------------------------
    # TRANSFER OWNERSHIP
    # -----------------------------------------------------

    if has_transfer:

        result["signals"].append(
            "Ownership transfer function detected "
            "in bytecode: transferOwnership(address)."
        )

    # -----------------------------------------------------
    # RENOUNCE OWNERSHIP
    # -----------------------------------------------------

    if has_renounce:

        result["signals"].append(
            "Ownership renunciation function detected "
            "in bytecode: renounceOwnership()."
        )

    # -----------------------------------------------------
    # OWNERSHIP RISK
    # -----------------------------------------------------

    if has_owner and (
        has_transfer
        or has_renounce
    ):

        result["status"] = "INFO"
        result["risk"] = "LOW"
        result["confidence"] = "LOW"

        result["warnings"].append(
            "Ownership-related functions were detected, "
            "but the current owner state cannot be read "
            "without a verified ABI."
        )

    else:

        result["status"] = "INFO"
        result["risk"] = "LOW"
        result["confidence"] = "LOW"

    return result


# =========================================================
# ANALYZE OWNERSHIP
# =========================================================

def analyze_ownership(
    address,
    abi,
):

    result = {

        "status": "UNKNOWN",

        "risk": "UNKNOWN",

        "confidence": "LOW",

        "owner": None,

        "owner_readable": False,

        "ownership_renounced": False,

        "can_transfer_ownership": False,

        "can_renounce_ownership": False,

        "admin_functions": [],

        "warnings": [],

        "signals": [],

    }

    # =====================================================
    # ABI UNAVAILABLE
    # =====================================================

    if not abi:

        return analyze_ownership_bytecode(
            address
        )

    # =====================================================
    # DETECT OWNERSHIP FUNCTIONS
    # =====================================================

    owner_function = None

    for name in OWNER_GETTERS:

        if find_function_abi(
            abi,
            name
        ):

            owner_function = name
            break

    transfer_function = None

    for name in OWNERSHIP_TRANSFER_FUNCTIONS:

        if find_function_abi(
            abi,
            name
        ):

            transfer_function = name
            break

    renounce_function = None

    for name in OWNERSHIP_RENOUNCE_FUNCTIONS:

        if find_function_abi(
            abi,
            name
        ):

            renounce_function = name
            break

    result[
        "can_transfer_ownership"
    ] = transfer_function is not None

    result[
        "can_renounce_ownership"
    ] = renounce_function is not None

    # =====================================================
    # READ CURRENT OWNER
    # =====================================================

    if owner_function:

        owner_value = (
            call_zero_argument_function(
                address,
                abi,
                owner_function,
            )
        )

        owner_address = normalize_address(
            owner_value
        )

        if owner_address:

            result["owner"] = (
                owner_address
            )

            result[
                "owner_readable"
            ] = True

            if (
                owner_address.lower()
                == ZERO_ADDRESS.lower()
            ):

                result[
                    "ownership_renounced"
                ] = True

            else:

                result[
                    "ownership_renounced"
                ] = False

    # =====================================================
    # DETECT ADMIN FUNCTIONS
    # =====================================================

    detected_admin_functions = []

    for function_name in ADMIN_CONTROL_FUNCTIONS:

        if find_function_abi(
            abi,
            function_name
        ):

            detected_admin_functions.append(
                function_name
            )

    result[
        "admin_functions"
    ] = detected_admin_functions

    # =====================================================
    # NO OWNERSHIP SYSTEM
    # =====================================================

    if (
        owner_function is None
        and not detected_admin_functions
    ):

        result["status"] = "INFO"
        result["risk"] = "UNKNOWN"
        result["confidence"] = "MEDIUM"

        result["signals"].append(
            "No recognized ownership or "
            "administrative control functions detected."
        )

        return result

    # =====================================================
    # RENOUNCED OWNERSHIP
    # =====================================================

    if result[
        "ownership_renounced"
    ]:

        result["status"] = "PASS"
        result["risk"] = "LOW"
        result["confidence"] = "HIGH"

        result["signals"].append(
            "Current owner is the zero address."
        )

        result["signals"].append(
            "Ownership appears to be renounced."
        )

    # =====================================================
    # ACTIVE OWNER
    # =====================================================

    elif result["owner_readable"]:

        result["status"] = "WARNING"
        result["risk"] = "MEDIUM"
        result["confidence"] = "HIGH"

        result["warnings"].append(
            "Contract currently has an active owner."
        )

        result["signals"].append(
            f"Current owner: {result['owner']}"
        )

    # =====================================================
    # OWNER EXISTS BUT CANNOT BE READ
    # =====================================================

    elif owner_function:

        result["status"] = "WARNING"
        result["risk"] = "MEDIUM"
        result["confidence"] = "MEDIUM"

        result["warnings"].append(
            "An owner() function was detected, "
            "but the current owner could not be read."
        )

    # =====================================================
    # OWNERSHIP TRANSFER
    # =====================================================

    if transfer_function:

        result["signals"].append(
            f"Ownership transfer function detected: "
            f"{transfer_function}."
        )

    # =====================================================
    # OWNERSHIP RENOUNCE
    # =====================================================

    if renounce_function:

        result["signals"].append(
            f"Ownership renunciation function detected: "
            f"{renounce_function}."
        )

    # =====================================================
    # ADMIN CONTROLS
    # =====================================================

    if detected_admin_functions:

        result["warnings"].append(
            "Administrative control functions detected: "
            + ", ".join(
                detected_admin_functions
            )
        )

        # Stronger risk if an active owner exists
        # together with powerful admin controls.

        if result["owner_readable"]:

            result["risk"] = "HIGH"

            result["confidence"] = "HIGH"

            result["warnings"].append(
                "An active owner appears to have "
                "administrative control functions."
            )

    else:

        result["signals"].append(
            "No recognized administrative control "
            "functions were detected."
        )

    # =====================================================
    # FINAL SIGNAL
    # =====================================================

    if (
        not result["warnings"]
        and not result["signals"]
    ):

        result["signals"].append(
            "Ownership analysis completed."
        )

    return result