from web3 import Web3

from config import RPC_URL


# ============================================================
# MINIMAL ERC-20 ABI
# ============================================================

TOKEN_ABI = [
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "to",
                "type": "address",
            },
            {
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256",
            },
        ],
        "name": "transfer",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool",
            }
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    },
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
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [
            {
                "internalType": "uint8",
                "name": "",
                "type": "uint8",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
]


# ============================================================
# WEB3
# ============================================================

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


# ============================================================
# ADDRESSES
# ============================================================

ZERO_ADDRESS = (
    "0x0000000000000000000000000000000000000000"
)

DEAD_ADDRESS = (
    "0x000000000000000000000000000000000000dead"
)


def is_valid_address(address):

    if not address:
        return False

    try:

        return Web3.is_address(
            address
        )

    except Exception:

        return False


def is_ignored_address(address):

    if not address:
        return True

    lowered = address.lower()

    return lowered in [
        ZERO_ADDRESS,
        DEAD_ADDRESS,
    ]


# ============================================================
# HOLDER SELECTION
# ============================================================

def get_candidate_holders(holders):
    """
    Return usable holder addresses.

    LP, pool, burn and obvious system addresses
    are ignored where possible.
    """

    candidates = []

    if not isinstance(
        holders,
        dict,
    ):
        return candidates

    items = holders.get(
        "items",
        []
    )

    if not isinstance(
        items,
        list,
    ):
        return candidates

    ignored_keywords = [
        "uniswap",
        "pair",
        "pool",
        "lp",
        "liquidity",
        "dead",
        "burn",
        "locker",
        "staking",
    ]

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

        address = address_info.get(
            "hash"
        )

        if not address:
            continue

        if not is_valid_address(
            address
        ):
            continue

        if is_ignored_address(
            address
        ):
            continue

        name = address_info.get(
            "name"
        )

        if name:

            lowered_name = str(
                name
            ).lower()

            if any(
                keyword in lowered_name
                for keyword in ignored_keywords
            ):

                continue

        try:

            checksum = Web3.to_checksum_address(
                address
            )

        except Exception:

            continue

        if checksum not in candidates:

            candidates.append(
                checksum
            )

    return candidates


# ============================================================
# TOKEN CONTRACT
# ============================================================

def get_token_contract(
    w3,
    token_address,
):

    return w3.eth.contract(
        address=Web3.to_checksum_address(
            token_address
        ),
        abi=TOKEN_ABI,
    )


# ============================================================
# TOKEN DECIMALS
# ============================================================

def get_token_decimals(
    token,
):

    try:

        decimals = int(
            token.functions.decimals().call()
        )

        if decimals < 0:

            return 18

        if decimals > 36:

            return 18

        return decimals

    except Exception:

        return 18


# ============================================================
# BALANCE
# ============================================================

def get_balance(
    token,
    address,
):

    try:

        balance = token.functions.balanceOf(
            Web3.to_checksum_address(
                address
            )
        ).call()

        return int(
            balance
        )

    except Exception:

        return 0


# ============================================================
# FIND USABLE HOLDER
# ============================================================

def find_test_holder(
    token,
    holders,
):
    """
    Find a candidate holder that actually owns
    a positive amount of the token.
    """

    candidates = get_candidate_holders(
        holders
    )

    for address in candidates:

        balance = get_balance(
            token,
            address,
        )

        if balance > 0:

            return {
                "address": address,
                "balance": balance,
            }

    return None


# ============================================================
# TRANSFER SIMULATION
# ============================================================

def simulate_transfer(
    token,
    from_address,
    to_address,
    amount,
):
    """
    Execute a read-only eth_call for token.transfer().

    This does NOT broadcast a transaction.
    """

    try:

        from_address = (
            Web3.to_checksum_address(
                from_address
            )
        )

        to_address = (
            Web3.to_checksum_address(
                to_address
            )
        )

        amount = int(
            amount
        )

        if amount <= 0:

            raise ValueError(
                "Transfer amount must be greater than zero."
            )

        result = token.functions.transfer(
            to_address,
            amount,
        ).call(
            {
                "from": from_address
            }
        )

        return {
            "success": bool(result),
            "error": None,
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e),
        }


# ============================================================
# TEST AMOUNTS
# ============================================================

def build_test_amounts(
    balance,
):
    """
    Create multiple realistic test amounts based on
    the holder's actual token balance.

    Tests progressively larger portions.

    Important:
    eth_call does not modify chain state.
    """

    try:

        balance = int(
            balance
        )

    except Exception:

        return []

    if balance <= 0:

        return []

    amounts = []

    # Smallest possible transfer.
    amounts.append(
        1
    )

    # Very small fraction.
    amounts.append(
        max(
            1,
            balance // 10000
        )
    )

    # 0.1%.
    amounts.append(
        max(
            1,
            balance // 1000
        )
    )

    # 1%.
    amounts.append(
        max(
            1,
            balance // 100
        )
    )

    # 10%.
    amounts.append(
        max(
            1,
            balance // 10
        )
    )

    # 50%.
    amounts.append(
        max(
            1,
            balance // 2
        )
    )

    # Full balance.
    amounts.append(
        balance
    )

    cleaned = []

    for amount in amounts:

        try:

            amount = int(
                amount
            )

        except Exception:

            continue

        if amount <= 0:

            continue

        if amount > balance:

            continue

        if amount not in cleaned:

            cleaned.append(
                amount
            )

    cleaned.sort()

    return cleaned


# ============================================================
# MULTI-SIZE TRANSFER TEST
# ============================================================

def run_transfer_tests(
    token,
    from_address,
    to_address,
    amounts,
):
    """
    Test multiple transfer sizes.
    """

    results = []

    for amount in amounts:

        test = simulate_transfer(
            token,
            from_address,
            to_address,
            amount,
        )

        results.append(
            {
                "amount": int(
                    amount
                ),
                "success": test.get(
                    "success",
                    False,
                ),
                "error": test.get(
                    "error"
                ),
            }
        )

    return results


# ============================================================
# TEST RESULT SUMMARY
# ============================================================

def summarize_tests(
    tests,
):
    """
    Summarize multi-size test results.
    """

    if not tests:

        return {
            "tested": 0,
            "passed": 0,
            "failed": 0,
            "all_passed": False,
            "any_passed": False,
            "any_failed": False,
            "largest_passed": 0,
            "largest_tested": 0,
        }

    passed = 0
    failed = 0

    largest_passed = 0
    largest_tested = 0

    for test in tests:

        try:

            amount = int(
                test.get(
                    "amount",
                    0,
                )
            )

        except Exception:

            amount = 0

        if amount > largest_tested:

            largest_tested = amount

        if test.get(
            "success"
        ):

            passed += 1

            if amount > largest_passed:

                largest_passed = amount

        else:

            failed += 1

    return {
        "tested": len(
            tests
        ),
        "passed": passed,
        "failed": failed,
        "all_passed": (
            failed == 0
            and passed > 0
        ),
        "any_passed": (
            passed > 0
        ),
        "any_failed": (
            failed > 0
        ),
        "largest_passed": largest_passed,
        "largest_tested": largest_tested,
    }


# ============================================================
# MAIN ANALYSIS
# ============================================================

def analyze_honeypot(
    token_address,
    liquidity,
    holders=None,
):
    """
    Read-only transfer restriction analysis.

    This module tests ERC-20 transfer behavior in
    directions commonly involved in DEX trading.

    IMPORTANT:

    This does NOT execute an actual router swap.

    It therefore cannot independently prove that a token
    is sellable on a DEX.

    It performs:

    1. Multiple holder -> pair transfer simulations.
    2. Multiple pair -> holder transfer simulations.
    3. Uses actual holder balances.
    4. Tests progressively larger transfer amounts.

    Passing this analysis does NOT guarantee that a real
    DEX swap will succeed.
    """

    result = {
        "status": "UNKNOWN",
        "risk": "UNKNOWN",
        "confidence": "LOW",

        "analysis_type": (
            "TRANSFER_RESTRICTION_SIMULATION"
        ),

        "router_swap_simulated": False,

        "buy": {
            "tested": False,
            "success": None,
            "reason": None,
            "tests": [],
        },

        "sell": {
            "tested": False,
            "success": None,
            "reason": None,
            "tests": [],
        },

        "test_holder": None,
        "test_holder_balance": 0,
        "token_decimals": 18,

        "warnings": [],
        "signals": [],
    }

    # --------------------------------------------------
    # LIQUIDITY
    # --------------------------------------------------

    if not isinstance(
        liquidity,
        dict,
    ):

        result["status"] = "UNAVAILABLE"
        result["risk"] = "UNKNOWN"
        result["confidence"] = "LOW"

        result["warnings"].append(
            "Transfer testing was not performed because "
            "liquidity analysis data was unavailable."
        )

        return result

    if not liquidity.get(
        "found"
    ):

        result["status"] = "UNAVAILABLE"
        result["risk"] = "UNKNOWN"
        result["confidence"] = "LOW"

        result["warnings"].append(
            "Transfer testing was not performed because "
            "no supported liquidity pool was detected."
        )

        return result

    pair_address = liquidity.get(
        "pair"
    )

    if not pair_address:

        best_pool = liquidity.get(
            "best_pool"
        )

        if isinstance(
            best_pool,
            dict,
        ):

            pair_address = best_pool.get(
                "address"
            )

    if not pair_address:

        result["status"] = "UNAVAILABLE"
        result["risk"] = "UNKNOWN"
        result["confidence"] = "LOW"

        result["warnings"].append(
            "Liquidity pair address could not be determined."
        )

        return result

    if not is_valid_address(
        pair_address
    ):

        result["status"] = "UNAVAILABLE"
        result["risk"] = "UNKNOWN"
        result["confidence"] = "LOW"

        result["warnings"].append(
            "Detected liquidity pair address is invalid."
        )

        return result

    try:

        pair_address = Web3.to_checksum_address(
            pair_address
        )

    except Exception:

        result["status"] = "UNAVAILABLE"

        result["warnings"].append(
            "Unable to normalize liquidity pair address."
        )

        return result

    # --------------------------------------------------
    # WEB3
    # --------------------------------------------------

    try:

        w3 = get_web3()

        token = get_token_contract(
            w3,
            token_address,
        )

    except Exception as e:

        result["status"] = "ERROR"
        result["risk"] = "UNKNOWN"
        result["confidence"] = "LOW"

        result["warnings"].append(
            f"Unable to initialize token analysis: {e}"
        )

        return result

    # --------------------------------------------------
    # DECIMALS
    # --------------------------------------------------

    decimals = get_token_decimals(
        token
    )

    result[
        "token_decimals"
    ] = decimals

    # --------------------------------------------------
    # FIND REAL HOLDER
    # --------------------------------------------------

    holder = find_test_holder(
        token,
        holders,
    )

    if not holder:

        result["status"] = "UNAVAILABLE"
        result["risk"] = "UNKNOWN"
        result["confidence"] = "LOW"

        result["warnings"].append(
            "No suitable holder with a positive on-chain "
            "token balance was found for testing."
        )

        return result

    holder_address = holder[
        "address"
    ]

    holder_balance = int(
        holder[
            "balance"
        ]
    )

    result[
        "test_holder"
    ] = holder_address

    result[
        "test_holder_balance"
    ] = holder_balance

    result["signals"].append(
        "A holder with a verified positive on-chain "
        "token balance was selected for testing."
    )

    # --------------------------------------------------
    # BUILD MULTI-SIZE TESTS
    # --------------------------------------------------

    sell_amounts = build_test_amounts(
        holder_balance
    )

    if not sell_amounts:

        result["status"] = "UNAVAILABLE"
        result["risk"] = "UNKNOWN"
        result["confidence"] = "LOW"

        result["warnings"].append(
            "Unable to create valid transfer test amounts."
        )

        return result

    # --------------------------------------------------
    # SELL-DIRECTION TRANSFER TESTS
    #
    # holder -> pair
    #
    # This is NOT an actual DEX sell.
    # --------------------------------------------------

    sell_tests = run_transfer_tests(
        token,
        holder_address,
        pair_address,
        sell_amounts,
    )

    sell_summary = summarize_tests(
        sell_tests
    )

    result["sell"]["tested"] = True

    result["sell"]["tests"] = (
        sell_tests
    )

    result["sell"]["success"] = (
        sell_summary["all_passed"]
    )

    if sell_summary[
        "all_passed"
    ]:

        result["sell"]["reason"] = (
            f"All {sell_summary['tested']} holder-to-pair "
            "transfer sizes completed successfully."
        )

        result["signals"].append(
            f"Holder-to-pair transfer simulation passed "
            f"for all {sell_summary['tested']} tested sizes."
        )

    elif sell_summary[
        "any_passed"
    ]:

        result["sell"]["reason"] = (
            f"{sell_summary['passed']} of "
            f"{sell_summary['tested']} holder-to-pair "
            "transfer sizes succeeded."
        )

        result["warnings"].append(
            "Transfer behavior changed across different "
            "holder-to-pair test sizes. This may indicate "
            "size-dependent restrictions or transaction "
            "limits."
        )

    else:

        result["sell"]["reason"] = (
            "All holder-to-pair transfer simulations failed."
        )

        result["warnings"].append(
            "No tested holder-to-pair transfer succeeded."
        )

    # --------------------------------------------------
    # BUY-DIRECTION TRANSFER TESTS
    #
    # pair -> holder
    #
    # This is NOT an actual DEX buy.
    # --------------------------------------------------

    buy_amounts = []

    for amount in sell_amounts:

        if amount <= holder_balance:

            buy_amounts.append(
                amount
            )

        if len(
            buy_amounts
        ) >= 4:

            break

    if not buy_amounts:

        buy_amounts = [
            1
        ]

    buy_tests = run_transfer_tests(
        token,
        pair_address,
        holder_address,
        buy_amounts,
    )

    buy_summary = summarize_tests(
        buy_tests
    )

    result["buy"]["tested"] = True

    result["buy"]["tests"] = (
        buy_tests
    )

    result["buy"]["success"] = (
        buy_summary["all_passed"]
    )

    if buy_summary[
        "all_passed"
    ]:

        result["buy"]["reason"] = (
            f"All {buy_summary['tested']} pair-to-holder "
            "transfer sizes completed successfully."
        )

        result["signals"].append(
            f"Pair-to-holder transfer simulation passed "
            f"for all {buy_summary['tested']} tested sizes."
        )

    elif buy_summary[
        "any_passed"
    ]:

        result["buy"]["reason"] = (
            f"{buy_summary['passed']} of "
            f"{buy_summary['tested']} pair-to-holder "
            "transfer sizes succeeded."
        )

        result["warnings"].append(
            "Some pair-to-holder transfer sizes failed."
        )

    else:

        result["buy"]["reason"] = (
            "All pair-to-holder transfer simulations failed."
        )

        result["warnings"].append(
            "No tested pair-to-holder transfer succeeded."
        )

    # --------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------

    buy_success = result[
        "buy"
    ][
        "success"
    ]

    sell_success = result[
        "sell"
    ][
        "success"
    ]

    sell_any_passed = sell_summary[
        "any_passed"
    ]

    sell_any_failed = sell_summary[
        "any_failed"
    ]

    buy_any_passed = buy_summary[
        "any_passed"
    ]

    buy_any_failed = buy_summary[
        "any_failed"
    ]

    # --------------------------------------------------
    # COMPLETE SELL-DIRECTION FAILURE
    # --------------------------------------------------

    if not sell_any_passed:

        result["status"] = "WARNING"
        result["risk"] = "HIGH"
        result["confidence"] = "HIGH"

        result["warnings"].append(
            "All tested holder-to-pair transfers failed. "
            "This may indicate a transfer restriction or "
            "sell-related blocking mechanism."
        )

    # --------------------------------------------------
    # SIZE-DEPENDENT SELL-DIRECTION FAILURE
    # --------------------------------------------------

    elif sell_any_failed:

        result["status"] = "WARNING"
        result["risk"] = "MEDIUM"
        result["confidence"] = "MEDIUM"

        result["warnings"].append(
            "Some holder-to-pair transfer sizes failed "
            "while others succeeded. Possible size-dependent "
            "transfer restrictions or transaction limits "
            "were detected."
        )

    # --------------------------------------------------
    # COMPLETE BUY-DIRECTION FAILURE
    # --------------------------------------------------

    elif not buy_any_passed:

        result["status"] = "WARNING"
        result["risk"] = "MEDIUM"
        result["confidence"] = "MEDIUM"

        result["warnings"].append(
            "All tested pair-to-holder transfers failed. "
            "This may indicate transfer restrictions, "
            "insufficient pair balance, or unusual token logic."
        )

    # --------------------------------------------------
    # PARTIAL BUY-DIRECTION FAILURE
    # --------------------------------------------------

    elif buy_any_failed:

        result["status"] = "WARNING"
        result["risk"] = "LOW"
        result["confidence"] = "MEDIUM"

        result["warnings"].append(
            "Some pair-to-holder transfer sizes failed, "
            "although at least one transfer succeeded."
        )

    # --------------------------------------------------
    # ALL TRANSFER TESTS PASSED
    # --------------------------------------------------

    elif (
        sell_success is True
        and buy_success is True
    ):

        result["status"] = "PASS"
        result["risk"] = "LOW"
        result["confidence"] = "MEDIUM"

        result["signals"].append(
            "All tested transfer directions and sizes "
            "completed successfully."
        )

        result["warnings"].append(
            "This analysis tested ERC-20 transfers only. "
            "It does not execute a real router swap and "
            "does not independently prove DEX sellability. "
            "Router quotes, approvals, taxes, slippage, "
            "and state-dependent contract logic may still "
            "affect an actual trade."
        )

    return result


# ============================================================
# COMPATIBILITY WRAPPERS
# ============================================================

def analyze(
    token_address,
    liquidity,
    holders=None,
):

    return analyze_honeypot(
        token_address,
        liquidity,
        holders,
    )


def detect(
    token_address,
    liquidity,
    holders=None,
):

    return analyze_honeypot(
        token_address,
        liquidity,
        holders,
    )