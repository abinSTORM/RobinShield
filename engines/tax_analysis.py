from web3 import Web3

from config import (
    RPC_URL,
)

from core.bytecode import analyze_bytecode

from detectors.swap_simulator import (
    start_anvil,
    stop_anvil,
    ANVIL_RPC_URL,
)

# =========================================================
# TAX FUNCTION NAMES
# =========================================================

BUY_TAX_FUNCTIONS = [
    "buyTaxRate",
    "buyTax",
    "getBuyTax",
    "getBuyTaxRate",
]


SELL_TAX_FUNCTIONS = [
    "sellTaxRate",
    "sellTax",
    "getSellTax",
    "getSellTaxRate",
]


GENERAL_TAX_FUNCTIONS = [
    "taxRate",
    "tax",
    "totalTax",
    "feeRate",
]

TAX_STATE_FUNCTIONS = [
    "taxExpirationTime",
    "currentTaxExpirationTime",
    "state",
]

TAX_STATE_NAMES = {
    0: "BondingCurve",
    1: "Migrating",
    2: "TaxEnforcedAntiFarmer",
    3: "TaxEnforced",
    4: "TaxFree",
}

TAX_SETTER_FUNCTIONS = [
    "setTax",
    "setTaxes",
    "updateTaxes",
    "setBuyTax",
    "setSellTax",
    "setBuyTaxRate",
    "setSellTaxRate",
]


# =========================================================
# WEB3
# =========================================================

def get_web3():

    w3 = Web3(
        Web3.HTTPProvider(
            RPC_URL
        )
    )

    if not w3.is_connected():

        raise ConnectionError(
            "Unable to connect to Robinhood Chain RPC."
        )

    return w3


# =========================================================
# ABI HELPERS
# =========================================================

def find_function_abi(
    abi,
    function_name,
):

    if not abi:

        return None

    for item in abi:

        if not isinstance(
            item,
            dict,
        ):

            continue

        if item.get(
            "type"
        ) != "function":

            continue

        if item.get(
            "name"
        ) == function_name:

            return item

    return None

def analyze_tax_setter_permissions(
    abi,
    setters,
):
    """
    Analyze ABI-level access-control hints for tax setters.

    This does not prove runtime authorization. It uses the
    function ABI and known ownership/admin patterns to identify
    whether setter permissions are explicitly represented.
    """

    result = {
        "status": "UNKNOWN",
        "confidence": "LOW",
        "owner_restricted": False,
        "admin_restricted": False,
        "unrestricted": False,
        "signals": [],
        "warnings": [],
    }

    if not setters:
        result["status"] = "NOT_APPLICABLE"
        result["confidence"] = "HIGH"
        result["signals"].append(
            "No recognized tax-setting functions were detected."
        )
        return result

    owner_functions = [
        "owner",
        "transferOwnership",
        "renounceOwnership",
    ]

    admin_functions = [
        "admin",
        "getAdmin",
        "DEFAULT_ADMIN_ROLE",
        "hasRole",
        "grantRole",
        "revokeRole",
    ]

    owner_present = any(
        find_function_abi(
            abi,
            name,
        )
        for name in owner_functions
    )

    admin_present = any(
        find_function_abi(
            abi,
            name,
        )
        for name in admin_functions
    )

    if owner_present:
        result["owner_restricted"] = True

        result["signals"].append(
            "Ownership functions are present; tax setter access "
            "may be controlled by ownership."
        )

    if admin_present:
        result["admin_restricted"] = True

        result["signals"].append(
            "Administrative access-control functions are present."
        )

    if not owner_present and not admin_present:
        result["unrestricted"] = True

        result["status"] = "WARNING"
        result["confidence"] = "MEDIUM"

        result["warnings"].append(
            "Tax setters were detected, but no recognized "
            "owner/admin access-control functions were found."
        )

        result["signals"].append(
            "Tax setter authorization could not be established "
            "from the available ABI."
        )

        return result

    result["status"] = "REVIEW"
    result["confidence"] = "MEDIUM"

    result["signals"].append(
        "Tax setter authorization requires runtime "
        "permission analysis."
    )

    return result

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
        [],
    )

    if len(inputs) != 0:

        return None

    outputs = function_abi.get(
        "outputs",
        [],
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

        value = getattr(
            contract.functions,
            function_name,
        )().call()

        return value

    except Exception:

        return None


def get_output_type(
    abi,
    function_name,
):

    function_abi = find_function_abi(
        abi,
        function_name,
    )

    if function_abi is None:

        return None

    outputs = function_abi.get(
        "outputs",
        [],
    )

    if not outputs:

        return None

    return outputs[0].get(
        "type"
    )

def analyze_tax_expiration_behavior(
    address,
    abi,
    expiration_time,
):
    result = {
        "tested": False,
        "status": "SKIPPED",
        "before_state": None,
        "after_state": None,
        "before_buy_tax": None,
        "after_buy_tax": None,
        "before_sell_tax": None,
        "after_sell_tax": None,
        "behavior": None,
        "reason": None,
    }

    if expiration_time is None:
        result["reason"] = (
            "No tax expiration timestamp detected."
        )
        return result

    process = None

    try:
        from web3 import Web3

        process = start_anvil()

        fork_w3 = get_web3(
            ANVIL_RPC_URL
        )

        token_address = (
            Web3.to_checksum_address(
                address
            )
        )

        token_contract = (
            fork_w3.eth.contract(
                address=token_address,
                abi=abi,
            )
        )

        def read_value(
            function_name,
        ):
            try:
                function = getattr(
                    token_contract.functions,
                    function_name,
                )

                return function().call()

            except Exception:
                return None

        result["before_state"] = (
            read_value("state")
        )

        result["before_buy_tax"] = (
            read_value("buyTaxRate")
        )

        result["before_sell_tax"] = (
            read_value("sellTaxRate")
        )

        current_block = (
            fork_w3.eth.get_block(
                "latest"
            )
        )

        current_timestamp = int(
            current_block["timestamp"]
        )

        target_timestamp = (
            max(
                current_timestamp,
                int(expiration_time),
            )
            + 1
        )

        fork_w3.provider.make_request(
            "evm_setNextBlockTimestamp",
            [target_timestamp],
        )

        fork_w3.provider.make_request(
            "evm_mine",
            [],
        )

        result["after_state"] = (
            read_value("state")
        )

        result["after_buy_tax"] = (
            read_value("buyTaxRate")
        )

        result["after_sell_tax"] = (
            read_value("sellTaxRate")
        )

        before_values = (
            result["before_state"],
            result["before_buy_tax"],
            result["before_sell_tax"],
        )

        after_values = (
            result["after_state"],
            result["after_buy_tax"],
            result["after_sell_tax"],
        )

        if before_values != after_values:
            result["behavior"] = (
                "CHANGED_AFTER_EXPIRATION"
            )
            result["status"] = "PASS"
        else:
            result["behavior"] = (
                "NO_CHANGE_AFTER_EXPIRATION"
            )
            result["status"] = "INFO"

        result["tested"] = True

    except Exception as exc:
        result["status"] = "ERROR"
        result["reason"] = str(exc)

    finally:
        stop_anvil(
            process
        )

    return result

# =========================================================
# TAX VALUE NORMALIZATION
# =========================================================

def normalize_tax_value(
    value,
    output_type=None,
):

    if value is None:

        return None

    try:

        value = int(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    # uint16 is the convention currently used by
    # RobinShield for basis-point tax values.
    if output_type == "uint16":

        percentage = (
            value
            / 100
        )

        convention = (
            "basis_points"
        )

    else:

        percentage = None

        convention = (
            "unknown"
        )

    return {
        "raw": value,
        "percentage": percentage,
        "convention": convention,
        "output_type": output_type,
    }


# =========================================================
# DEFAULT UNKNOWN RESULT
# =========================================================

def _unknown_result(
    reason=None,
):

    result = {
        "status": "UNKNOWN",
        "risk": "UNKNOWN",
        "confidence": "LOW",
        "buy_tax": None,
        "sell_tax": None,
        "general_tax": None,
        "setters": [],
        "detected_getters": [],
        "warnings": [],
        "signals": [],
    }

    if reason:

        result["warnings"].append(
            reason
        )

    return result


# =========================================================
# BYTECODE TAX ANALYSIS
# =========================================================

def _analyze_tax_from_bytecode(
    address,
):

    result = _unknown_result()

    try:

        bytecode = analyze_bytecode(
            address
        )

    except Exception as e:

        result["status"] = "UNKNOWN"
        result["risk"] = "UNKNOWN"
        result["confidence"] = "LOW"

        result["warnings"].append(
            "Bytecode tax analysis failed: "
            + str(e)
        )

        return result

    if not isinstance(
        bytecode,
        dict,
    ):

        result["status"] = "UNKNOWN"
        result["risk"] = "UNKNOWN"
        result["confidence"] = "LOW"

        result["warnings"].append(
            "Bytecode analyzer returned an invalid result."
        )

        return result

    # -----------------------------------------------------
    # Bytecode unavailable.
    # -----------------------------------------------------

    if not bytecode.get(
        "available",
        False,
    ):

        result["status"] = "UNAVAILABLE"
        result["risk"] = "UNKNOWN"
        result["confidence"] = "LOW"

        result["warnings"].append(
            "Tax analysis is unavailable because "
            "contract bytecode could not be loaded."
        )

        return result

    groups = bytecode.get(
        "groups",
        {},
    )

    if not isinstance(
        groups,
        dict,
    ):

        groups = {}

    tax_functions = groups.get(
        "tax",
        [],
    )

    if not isinstance(
        tax_functions,
        list,
    ):

        tax_functions = []

    names = []

    for item in tax_functions:

        if not isinstance(
            item,
            dict,
        ):

            continue

        name = item.get(
            "function",
            item.get(
                "selector",
                "",
            ),
        )

        if name:

            names.append(
                str(name)
            )

    # -----------------------------------------------------
    # NO TAX SELECTORS
    # -----------------------------------------------------

    if not names:

        result["status"] = "PASS"
        result["risk"] = "LOW"
        result["confidence"] = "LOW"

        result["signals"].append(
            "No recognized tax/fee selectors were "
            "detected in the bytecode."
        )

        result["warnings"].append(
            "Bytecode selector analysis cannot detect "
            "every possible tax implementation."
        )

        return result

    # -----------------------------------------------------
    # TAX SELECTORS FOUND
    # -----------------------------------------------------

    result["status"] = "WARNING"
    result["risk"] = "MEDIUM"
    result["confidence"] = "LOW"

    result["detected_getters"] = names

    result["signals"].append(
        "Tax/fee-related selectors detected in "
        "contract bytecode: "
        + ", ".join(names)
    )

    result["warnings"].append(
        "Tax percentages cannot be reliably determined "
        "from selectors alone."
    )

    return result


# =========================================================
# MAIN TAX ANALYSIS
# =========================================================

def analyze_tax(
    address,
    abi=None,
):

    result = _unknown_result()

    # =====================================================
    # ABI UNAVAILABLE
    # =====================================================

    if not abi:

        return _analyze_tax_from_bytecode(
            address
        )

    # =====================================================
    # DETECT GETTERS
    # =====================================================

    buy_getters = [

        name

        for name in BUY_TAX_FUNCTIONS

        if find_function_abi(
            abi,
            name,
        )

    ]

    sell_getters = [

        name

        for name in SELL_TAX_FUNCTIONS

        if find_function_abi(
            abi,
            name,
        )

    ]

    general_getters = [

        name

        for name in GENERAL_TAX_FUNCTIONS

        if find_function_abi(
            abi,
            name,
        )

    ]

    setters = [

        name

        for name in TAX_SETTER_FUNCTIONS

        if find_function_abi(
            abi,
            name,
        )

    ]

    result["detected_getters"] = (
        buy_getters
        + sell_getters
        + general_getters
    )

    tax_state_functions = [
        name
        for name in TAX_STATE_FUNCTIONS
        if find_function_abi(
            abi,
            name,
        )
    ]

    result["tax_state_functions"] = (
        tax_state_functions
    )

    result["setters"] = setters
    result["setter_permissions"] = (
        analyze_tax_setter_permissions(
            abi,
            setters,
        )
    )

    result["dynamic_tax"] = bool(
        setters
    )

    result["tax_expiration_active"] = None

    result["tax_expiration_time"] = None

    result["tax_state"] = None

    for function_name in tax_state_functions:
        if function_name in (
            "taxExpirationTime",
            "currentTaxExpirationTime",
        ):
            value = call_zero_argument_function(
                address,
                abi,
                function_name,
            )

            if value is not None:
                try:
                    result["tax_expiration_time"] = int(
                        value
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

                break

    if result["tax_expiration_time"] is not None:
        try:
            w3 = get_web3()
            current_block_timestamp = (
                w3.eth.get_block("latest")["timestamp"]
            )

            result["tax_expiration_active"] = (
                result["tax_expiration_time"]
                > current_block_timestamp
            )
        except Exception:
            result["tax_expiration_active"] = None

    if "state" in tax_state_functions:
        state_value = call_zero_argument_function(
            address,
            abi,
            "state",
        )

        if state_value is not None:
            try:
                result["tax_state"] = int(
                    state_value
                )
            except (
                TypeError,
                ValueError,
            ):
                result["tax_state"] = None

    result["tax_state_name"] = None

    if result["tax_state"] is not None:
        result["tax_state_name"] = TAX_STATE_NAMES.get(
            result["tax_state"],
            "Unknown",
        )

    result["time_dependent_tax"] = (
        result["tax_expiration_time"] is not None
    )

    result["tax_expiration_status"] = None

    if result["tax_expiration_time"] is not None:
        if result["tax_expiration_active"] is True:
            result["tax_expiration_status"] = "ACTIVE"
        elif result["tax_expiration_active"] is False:
            result["tax_expiration_status"] = "EXPIRED"

    result["tax_expiration_behavior"] = (
        analyze_tax_expiration_behavior(
            address,
            abi,
            result["tax_expiration_time"],
        )
    )

    result["tax_setters"] = setters

    # =====================================================
    # BUY TAX
    # =====================================================

    for function_name in buy_getters:

        value = call_zero_argument_function(
            address,
            abi,
            function_name,
        )

        output_type = get_output_type(
            abi,
            function_name,
        )

        normalized = normalize_tax_value(
            value,
            output_type,
        )

        if normalized is not None:

            result["buy_tax"] = {
                "function": function_name,
                **normalized,
            }

            break

    # =====================================================
    # SELL TAX
    # =====================================================

    for function_name in sell_getters:

        value = call_zero_argument_function(
            address,
            abi,
            function_name,
        )

        output_type = get_output_type(
            abi,
            function_name,
        )

        normalized = normalize_tax_value(
            value,
            output_type,
        )

        if normalized is not None:

            result["sell_tax"] = {
                "function": function_name,
                **normalized,
            }

            break

    # =====================================================
    # GENERAL TAX
    # =====================================================

    for function_name in general_getters:

        value = call_zero_argument_function(
            address,
            abi,
            function_name,
        )

        output_type = get_output_type(
            abi,
            function_name,
        )

        normalized = normalize_tax_value(
            value,
            output_type,
        )

        if normalized is not None:

            result["general_tax"] = {
                "function": function_name,
                **normalized,
            }

            break

    # =====================================================
    # NO TAX FUNCTIONALITY
    # =====================================================

    if (
        not result["detected_getters"]
        and
        not setters
    ):

        result["status"] = "PASS"
        result["risk"] = "LOW"
        result["confidence"] = "HIGH"

        result["signals"].append(
            "No recognized tax functions detected."
        )

        return result

    # =====================================================
    # TAX FUNCTIONALITY EXISTS
    # =====================================================

    result["status"] = "WARNING"
    result["risk"] = "MEDIUM"
    result["confidence"] = "MEDIUM"

    # =====================================================
    # BUY TAX SIGNAL
    # =====================================================

    if result["buy_tax"] is not None:

        buy = result["buy_tax"]

        if buy["percentage"] is not None:

            result["signals"].append(
                f"Buy tax: "
                f"{buy['percentage']:.2f}% "
                f"({buy['function']})."
            )

        else:

            result["warnings"].append(
                "Buy tax detected, but its percentage "
                "convention could not be determined."
            )

    elif buy_getters:

        result["warnings"].append(
            "Buy tax getter detected, but its current "
            "value could not be read."
        )

    # =====================================================
    # SELL TAX SIGNAL
    # =====================================================

    if result["sell_tax"] is not None:

        sell = result["sell_tax"]

        if sell["percentage"] is not None:

            result["signals"].append(
                f"Sell tax: "
                f"{sell['percentage']:.2f}% "
                f"({sell['function']})."
            )

        else:

            result["warnings"].append(
                "Sell tax detected, but its percentage "
                "convention could not be determined."
            )

    elif sell_getters:

        result["warnings"].append(
            "Sell tax getter detected, but its current "
            "value could not be read."
        )

    # =====================================================
    # GENERAL TAX
    # =====================================================

    if result["general_tax"] is not None:

        general = result["general_tax"]

        if general["percentage"] is not None:

            result["signals"].append(
                f"General tax: "
                f"{general['percentage']:.2f}% "
                f"({general['function']})."
            )

    # =====================================================
    # TAX SETTERS
    # =====================================================

    if setters:

        result["warnings"].append(
            "Tax-setting functions detected: "
            + ", ".join(setters)
        )

        result["signals"].append(
            "Dynamic tax configuration is present."
        )

        result["signals"].append(
            "Current tax values may not represent "
            "the maximum tax that can be configured."
        )

    if tax_state_functions:
        result["signals"].append(
            "Tax expiration/state mechanism detected: "
            + ", ".join(tax_state_functions)
        )

        if result.get(
            "tax_expiration_active"
        ) is True:
            result["signals"].append(
                "Tax expiration mechanism is currently active."
            )
        elif result.get(
            "tax_expiration_active"
        ) is False:
            result["signals"].append(
                "Tax expiration timestamp has already passed."
            )
    # =====================================================
    # TAX RISK
    # =====================================================

    percentages = []

    for key in [
        "buy_tax",
        "sell_tax",
        "general_tax",
    ]:

        tax = result.get(
            key
        )

        if (
            tax is not None
            and
            tax.get(
                "percentage"
            ) is not None
        ):

            percentages.append(
                tax["percentage"]
            )

    if percentages:

        maximum_tax = max(
            percentages
        )

        if maximum_tax >= 50:

            result["risk"] = "HIGH"
            result["confidence"] = "HIGH"

            result["warnings"].append(
                f"Extremely high tax detected: "
                f"{maximum_tax:.2f}%."
            )

        elif maximum_tax >= 20:

            result["risk"] = "HIGH"
            result["confidence"] = "HIGH"

            result["warnings"].append(
                f"Very high tax detected: "
                f"{maximum_tax:.2f}%."
            )

        elif maximum_tax >= 10:

            result["risk"] = "MEDIUM"
            result["confidence"] = "HIGH"

            result["warnings"].append(
                f"High tax detected: "
                f"{maximum_tax:.2f}%."
            )

        elif maximum_tax > 5:

            result["risk"] = "MEDIUM"
            result["confidence"] = "HIGH"

            result["signals"].append(
                f"Tax is above 5%: "
                f"{maximum_tax:.2f}%."
            )

        else:

            result["risk"] = "LOW"
            result["confidence"] = "HIGH"

            result["signals"].append(
                f"Tax level is relatively low: "
                f"{maximum_tax:.2f}%."
            )

    # =====================================================
    # FINAL
    # =====================================================

    if (
        not result["warnings"]
        and
        not result["signals"]
    ):

        result["signals"].append(
            "Tax-related functionality detected."
        )

    return result