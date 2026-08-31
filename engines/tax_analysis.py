from web3 import Web3

from config import RPC_URL
from core.bytecode import analyze_bytecode


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

        value = int(value)

    except (
        TypeError,
        ValueError,
    ):

        return None

    if output_type == "uint16":

        percentage = value / 100

        convention = "basis_points"

    else:

        percentage = None

        convention = "unknown"

    return {
        "raw": value,
        "percentage": percentage,
        "convention": convention,
        "output_type": output_type,
    }


# =========================================================
# BYTECODE TAX ANALYSIS
# =========================================================

def _analyze_tax_from_bytecode(
    address,
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

    try:

        bytecode = analyze_bytecode(
            address
        )

    except Exception as e:

        result["status"] = "UNKNOWN"
        result["risk"] = "HIGH"

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
        result["risk"] = "HIGH"

        result["warnings"].append(
            "Bytecode analyzer returned an invalid result."
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

    result["setters"] = setters

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
        and not setters
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
            "Tax configuration may be changeable."
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
            and tax.get("percentage") is not None
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
        and not result["signals"]
    ):

        result["signals"].append(
            "Tax-related functionality detected."
        )

    return result