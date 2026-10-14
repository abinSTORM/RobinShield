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


def _analyze_lp_holders(
    w3,
    pair_address,
    lp_total_supply,
    burn_balances,
):

    """Classify current V2 LP custody using indexed holders and RPC checks.

    A holder index is treated as complete only when its on-chain-verified
    balances plus burn-address balances exactly account for totalSupply.
    """

    try:
        from analysis.holders import get_holders

        holder_data = get_holders(
            pair_address,
            deep=False,
        )
    except Exception:
        holder_data = None

    result = {
        "status": "UNAVAILABLE",
        "source": None,
        "holder_count": None,
        "accounted_lp": None,
        "accounted_percentage": None,
        "eoa_lp": None,
        "contract_lp": None,
        "eoa_percentage_of_supply": None,
        "eoa_percentage_of_active_lp": None,
        "holders": [],
        "reason": "LP holder data could not be fetched.",
    }

    if not isinstance(holder_data, dict):
        return result

    items = holder_data.get("items")
    if not isinstance(items, list):
        return result

    checksum_pair = _safe_checksum(pair_address)
    if not checksum_pair:
        return result

    try:
        lp_contract = w3.eth.contract(
            address=checksum_pair,
            abi=ERC20_LP_ABI,
        )
    except Exception:
        return result

    verified_holders = []
    accounted_lp = 0
    eoa_lp = 0
    contract_lp = 0

    for item in items:
        if not isinstance(item, dict):
            continue
        address_info = item.get("address")
        if not isinstance(address_info, dict):
            continue
        address = _safe_checksum(address_info.get("hash"))
        if not address:
            continue

        indexed_balance = _safe_int(item.get("value"))
        if indexed_balance <= 0:
            continue

        chain_balance = _get_lp_balance(lp_contract, address)
        if chain_balance is None or chain_balance != indexed_balance:
            continue

        if address.lower() in {item.lower() for item in BURN_ADDRESSES}:
            continue

        try:
            has_code = bool(w3.eth.get_code(address))
        except Exception:
            continue

        accounted_lp += chain_balance
        if has_code:
            contract_lp += chain_balance
            holder_type = "CONTRACT"
        else:
            eoa_lp += chain_balance
            holder_type = "EOA"

        verified_holders.append({
            "address": address,
            "balance": chain_balance,
            "percentage_of_supply": chain_balance / lp_total_supply * 100,
            "holder_type": holder_type,
        })

    burned_lp = sum(burn_balances.values())
    active_lp = max(lp_total_supply - burned_lp, 0)
    total_accounted = accounted_lp + burned_lp
    exact_coverage = total_accounted == lp_total_supply

    result.update({
        "status": "COMPLETE" if exact_coverage else "PARTIAL",
        "source": holder_data.get("_source", "holder_index"),
        "holder_count": len(verified_holders),
        "accounted_lp": total_accounted,
        "accounted_percentage": total_accounted / lp_total_supply * 100,
        "eoa_lp": eoa_lp,
        "contract_lp": contract_lp,
        "eoa_percentage_of_supply": eoa_lp / lp_total_supply * 100,
        "eoa_percentage_of_active_lp": (
            eoa_lp / active_lp * 100 if active_lp else 0
        ),
        "holders": verified_holders[:10],
        "reason": (
            "Indexed balances were checked against the LP contract and, "
            "together with burn balances, match totalSupply."
            if exact_coverage
            else "Only part of LP totalSupply was accounted for; unlisted holders may exist."
        ),
    })

    return result


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
        "lock_status_verified": False,
        "holder_distribution": None,
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

    # Burn is only one LP disposition. Remaining LP can be held by
    # legitimate lockers, multisigs, or ordinary wallets; without holder
    # and locker analysis we cannot call it unlocked or classify safety.
    safety = "UNKNOWN"
    reason = (
        f"{burn_percentage}% of LP tokens are at recognized burn addresses. "
        "The remaining LP tokens may be locked or unlocked; lock status "
        "was not verified."
    )

    # -----------------------------------------------------
    # SIGNALS
    # -----------------------------------------------------

    signals = [
        "LP burn balances were read directly from the LP token contract.",
        "Burn percentage does not establish whether remaining LP is locked.",
    ]

    zero_balance = burn_balances.get(
        "0x0000000000000000000000000000000000000000",
        0,
    )

    dead_balance = burn_balances.get(
        "0x000000000000000000000000000000000000dead",
        0,
    )

    warnings = []

    holder_distribution = _analyze_lp_holders(
        w3,
        checksum_pair,
        lp_total_supply,
        burn_balances,
    )

    eoa_percentage = holder_distribution.get(
        "eoa_percentage_of_supply"
    )
    eoa_active_percentage = holder_distribution.get(
        "eoa_percentage_of_active_lp"
    )

    if (
        holder_distribution.get("status") == "COMPLETE"
        and eoa_percentage is not None
        and float(eoa_percentage) > 0
    ):
        lock_status_verified = True
        safety = (
            "UNLOCKED"
            if float(eoa_active_percentage or 0) >= 99.999
            else "PARTIALLY_UNLOCKED"
        )
        reason = (
            f"{float(eoa_percentage):.4f}% of LP supply is held by externally "
            "owned wallet(s), with complete holder balances verified against "
            "the LP contract. Those wallets can transfer or redeem their LP."
        )
        signals.append(
            f"Verified externally owned wallets hold {float(eoa_percentage):.4f}% of total LP supply."
        )
        warnings.append(
            "LP held by externally owned wallets is not protected by an on-chain timelock; its holder(s) can withdraw liquidity."
        )
    else:
        lock_status_verified = False
        signals.append(
            "LP holder balances could not establish a complete, verified lock status."
        )

    if holder_distribution.get("status") == "PARTIAL":
        warnings.append(
            "LP holder index did not account for the full LP supply; lock classification remains incomplete."
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
        "lock_status_verified": lock_status_verified,
        "holder_distribution": holder_distribution,
        "warnings": warnings,
        "signals": signals,
    }
