from web3 import Web3

from config import RPC_URL


# =========================================================
# BURN ADDRESSES
# =========================================================

BURN_ADDRESSES = {
    "0x0000000000000000000000000000000000000000",
    "0x000000000000000000000000000000000000dead",
}


# =========================================================
# ERC-20 ABI
# =========================================================

ERC20_LP_ABI = [
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
]


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


# =========================================================
# WEB3
# =========================================================

def _get_web3():

    w3 = Web3(
        Web3.HTTPProvider(
            RPC_URL,
            request_kwargs={
                "timeout": 20,
            },
        )
    )

    if not w3.is_connected():

        raise ConnectionError(
            "Unable to connect to Robinhood Chain RPC."
        )

    return w3


# =========================================================
# LP TOKEN BALANCE
# =========================================================

def _get_lp_balance(
    lp_contract,
    address,
):

    checksum = _safe_checksum(
        address
    )

    if not checksum:

        return None

    try:

        return int(
            lp_contract.functions.balanceOf(
                checksum
            ).call()
        )

    except Exception:

        return None


# =========================================================
# LP SAFETY
# =========================================================

def calculate_lp_safety(
    pair_address,
    lp_total_supply,
):

    lp_total_supply = _safe_int(
        lp_total_supply
    )

    unknown_result = {
        "lp_total_supply": (
            lp_total_supply
            if lp_total_supply > 0
            else None
        ),
        "burned_lp": None,
        "burn_percentage": None,
        "active_lp": None,
        "safety": "UNKNOWN",
        "reason": (
            "LP safety could not be determined."
        ),
        "warnings": [],
        "signals": [],
    }

    # -----------------------------------------------------
    # Validate pair
    # -----------------------------------------------------

    if not pair_address:

        unknown_result[
            "reason"
        ] = (
            "LP pair address could not be determined."
        )

        return unknown_result

    # -----------------------------------------------------
    # Validate supply
    # -----------------------------------------------------

    if lp_total_supply <= 0:

        unknown_result[
            "reason"
        ] = (
            "LP total supply could not be determined."
        )

        return unknown_result

    # -----------------------------------------------------
    # Connect to chain
    # -----------------------------------------------------

    try:

        w3 = _get_web3()

    except Exception as e:

        unknown_result[
            "reason"
        ] = (
            "Unable to connect to chain for LP analysis: "
            + str(e)
        )

        return unknown_result

    # -----------------------------------------------------
    # LP contract
    # -----------------------------------------------------

    checksum_pair = _safe_checksum(
        pair_address
    )

    if not checksum_pair:

        unknown_result[
            "reason"
        ] = (
            "Invalid LP pair address."
        )

        return unknown_result

    try:

        lp_contract = w3.eth.contract(
            address=checksum_pair,
            abi=ERC20_LP_ABI,
        )

    except Exception as e:

        unknown_result[
            "reason"
        ] = (
            "Unable to initialize LP token contract: "
            + str(e)
        )

        return unknown_result

    # -----------------------------------------------------
    # Read burn-address balances directly.
    #
    # This does NOT depend on holder indexing.
    # -----------------------------------------------------

    burn_balances = {}

    for burn_address in BURN_ADDRESSES:

        balance = _get_lp_balance(
            lp_contract,
            burn_address,
        )

        if balance is None:

            unknown_result[
                "reason"
            ] = (
                "Unable to read LP balance at "
                f"burn address {burn_address}."
            )

            return unknown_result

        burn_balances[
            burn_address
        ] = balance

    # -----------------------------------------------------
    # Calculate exact burned LP.
    # -----------------------------------------------------

    burned_lp = sum(
        burn_balances.values()
    )

    # Prevent impossible values.
    burned_lp = min(
        burned_lp,
        lp_total_supply,
    )

    active_lp = max(
        lp_total_supply
        - burned_lp,
        0,
    )

    burn_percentage = (
        burned_lp
        / lp_total_supply
        * 100
    )

    burn_percentage = round(
        burn_percentage,
        4,
    )

    # -----------------------------------------------------
    # SAFETY CLASSIFICATION
    # -----------------------------------------------------

    if burn_percentage >= 99:

        safety = "VERY HIGH"

        reason = (
            "Almost all LP tokens are permanently held "
            "by known burn addresses."
        )

    elif burn_percentage >= 90:

        safety = "HIGH"

        reason = (
            "Most LP tokens are held by known burn addresses."
        )

    elif burn_percentage >= 50:

        safety = "MEDIUM"

        reason = (
            "A significant portion of LP tokens is "
            "held by known burn addresses."
        )

    else:

        safety = "LOW"

        reason = (
            "A large portion of LP tokens remains "
            "outside known burn addresses."
        )

    # -----------------------------------------------------
    # SIGNALS
    # -----------------------------------------------------

    signals = [
        "LP burn balances were read directly from "
        "the LP token contract.",
    ]

    zero_balance = burn_balances.get(
        "0x0000000000000000000000000000000000000000",
        0,
    )

    dead_balance = burn_balances.get(
        "0x000000000000000000000000000000000000dead",
        0,
    )

    if zero_balance > 0:

        signals.append(
            f"Zero address holds "
            f"{zero_balance} LP tokens."
        )

    else:

        signals.append(
            "Zero address holds no LP tokens."
        )

    if dead_balance > 0:

        signals.append(
            f"Dead address holds "
            f"{dead_balance} LP tokens."
        )

    else:

        signals.append(
            "Dead address holds no LP tokens."
        )

    signals.append(
        f"Total burned LP: "
        f"{burned_lp}"
    )

    signals.append(
        f"Active LP: "
        f"{active_lp}"
    )

    signals.append(
        f"Burn percentage: "
        f"{burn_percentage:.4f}%"
    )

    # -----------------------------------------------------
    # WARNINGS
    # -----------------------------------------------------

    warnings = []

    if burn_percentage < 50:

        warnings.append(
            "Less than 50% of LP tokens are held "
            "by known burn addresses."
        )

    # -----------------------------------------------------
    # RESULT
    # -----------------------------------------------------

    return {
        "lp_total_supply": lp_total_supply,
        "burned_lp": burned_lp,
        "burn_percentage": burn_percentage,
        "active_lp": active_lp,
        "safety": safety,
        "reason": reason,
        "warnings": warnings,
        "signals": signals,
    }