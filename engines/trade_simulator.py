from decimal import Decimal

from web3 import Web3

from config import RPC_URL


# ============================================================
# ROBINHOOD CHAIN DEFAULTS
# ============================================================

WETH = Web3.to_checksum_address(
    "0x0Bd7D308f8E1639FAb988df18A8011f41EAcAD73"
)

UNISWAP_V2_ROUTER = Web3.to_checksum_address(
    "0x89e5DB8B5aA49aA85AC63f691524311AEB649eba"
)


# ============================================================
# ABIs
# ============================================================

ROUTER_ABI = [
    {
        "inputs": [
            {
                "internalType": "uint256",
                "name": "amountIn",
                "type": "uint256",
            },
            {
                "internalType": "address[]",
                "name": "path",
                "type": "address[]",
            },
        ],
        "name": "getAmountsOut",
        "outputs": [
            {
                "internalType": "uint256[]",
                "name": "amounts",
                "type": "uint256[]",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


ERC20_ABI = [
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
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    }
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
# CONTRACT HELPERS
# ============================================================

def get_router(w3):

    return w3.eth.contract(
        address=UNISWAP_V2_ROUTER,
        abi=ROUTER_ABI,
    )


def get_token_contract(
    w3,
    token_address,
):

    return w3.eth.contract(
        address=Web3.to_checksum_address(
            token_address
        ),
        abi=ERC20_ABI,
    )


# ============================================================
# SAFE HELPERS
# ============================================================

def safe_checksum(
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


def safe_decimals(
    w3,
    token_address,
    default=18,
):

    try:

        token = get_token_contract(
            w3,
            token_address,
        )

        decimals = int(
            token.functions.decimals().call()
        )

        if decimals < 0 or decimals > 255:

            return default

        return decimals

    except Exception:

        return default


def safe_symbol(
    w3,
    token_address,
):

    try:

        token = get_token_contract(
            w3,
            token_address,
        )

        return token.functions.symbol().call()

    except Exception:

        return None


def to_raw_amount(
    amount,
    decimals,
):

    value = Decimal(
        str(amount)
    )

    multiplier = (
        Decimal(10)
        ** int(decimals)
    )

    return int(
        value * multiplier
    )


def from_raw_amount(
    amount_raw,
    decimals,
):

    try:

        return float(
            Decimal(
                int(amount_raw)
            )
            /
            (
                Decimal(10)
                ** int(decimals)
            )
        )

    except Exception:

        return 0.0


def safe_percent(
    numerator,
    denominator,
):

    try:

        numerator = Decimal(
            str(numerator)
        )

        denominator = Decimal(
            str(denominator)
        )

        if denominator == 0:

            return 0.0

        return float(
            (
                numerator
                / denominator
            )
            * 100
        )

    except Exception:

        return 0.0


# ============================================================
# ROUTER QUOTE
# ============================================================

def get_amounts_out(
    amount_in,
    path,
):

    result = {
        "success": False,
        "amounts": None,
        "error": None,
        "path": None,
    }

    try:

        w3 = get_web3()

        router = get_router(
            w3
        )

        normalized_path = []

        for address in path:

            checksum = safe_checksum(
                address
            )

            if not checksum:

                raise ValueError(
                    f"Invalid address in route: {address}"
                )

            normalized_path.append(
                checksum
            )

        if len(normalized_path) < 2:

            raise ValueError(
                "A swap route requires at least two addresses."
            )

        amount_in = int(
            amount_in
        )

        if amount_in <= 0:

            raise ValueError(
                "amount_in must be greater than zero."
            )

        amounts = (
            router.functions.getAmountsOut(
                amount_in,
                normalized_path,
            ).call()
        )

        if not amounts:

            raise ValueError(
                "Router returned an empty quote."
            )

        if len(amounts) != len(
            normalized_path
        ):

            raise ValueError(
                "Router returned an invalid quote length."
            )

        result["success"] = True

        result["amounts"] = [
            int(value)
            for value in amounts
        ]

        result["path"] = normalized_path

        return result

    except Exception as e:

        result["error"] = str(
            e
        )

        return result


# ============================================================
# DETERMINE QUOTE TOKEN
# ============================================================

def get_quote_token(
    liquidity,
):

    if not isinstance(
        liquidity,
        dict,
    ):

        return None

    quote_token = liquidity.get(
        "quote_token"
    )

    if quote_token:

        return safe_checksum(
            quote_token
        )

    best_pool = liquidity.get(
        "best_pool"
    )

    if isinstance(
        best_pool,
        dict,
    ):

        quote_token = best_pool.get(
            "quote_token"
        )

        if quote_token:

            return safe_checksum(
                quote_token
            )

    return None


# ============================================================
# TOKEN DECIMALS
# ============================================================

def get_target_token_decimals(
    w3,
    token_address,
    liquidity,
):

    if isinstance(
        liquidity,
        dict,
    ):

        decimals = liquidity.get(
            "token_decimals"
        )

        if decimals is not None:

            try:

                return int(
                    decimals
                )

            except Exception:

                pass

        best_pool = liquidity.get(
            "best_pool"
        )

        if isinstance(
            best_pool,
            dict,
        ):

            decimals = best_pool.get(
                "token_decimals"
            )

            if decimals is not None:

                try:

                    return int(
                        decimals
                    )

                except Exception:

                    pass

    return safe_decimals(
        w3,
        token_address,
        18,
    )


# ============================================================
# SINGLE BUY QUOTE
# ============================================================

def simulate_buy(
    token_address,
    quote_token,
    quote_amount="0.001",
):

    result = {
        "simulated": True,
        "success": False,
        "amount_in_raw": None,
        "amount_in_quote": quote_amount,
        "amount_out_raw": None,
        "amount_out_token": None,
        "quote_token": quote_token,
        "reason": None,
        "error": None,
    }

    try:

        w3 = get_web3()

        token_address = safe_checksum(
            token_address
        )

        quote_token = safe_checksum(
            quote_token
        )

        if not token_address:

            raise ValueError(
                "Invalid target token address."
            )

        if not quote_token:

            raise ValueError(
                "Invalid quote token address."
            )

        if (
            token_address.lower()
            ==
            quote_token.lower()
        ):

            raise ValueError(
                "Target token and quote token are identical."
            )

        quote_decimals = safe_decimals(
            w3,
            quote_token,
            18,
        )

        token_decimals = safe_decimals(
            w3,
            token_address,
            18,
        )

        amount_in = to_raw_amount(
            quote_amount,
            quote_decimals,
        )

        if amount_in <= 0:

            amount_in = 1

        quote = get_amounts_out(
            amount_in,
            [
                quote_token,
                token_address,
            ],
        )

        if not quote["success"]:

            result["reason"] = (
                "Router could not produce a BUY quote."
            )

            result["error"] = quote.get(
                "error"
            )

            return result

        amount_out_raw = int(
            quote["amounts"][-1]
        )

        if amount_out_raw <= 0:

            result["reason"] = (
                "Router returned a zero BUY output."
            )

            return result

        result["success"] = True

        result["amount_in_raw"] = amount_in

        result["amount_out_raw"] = (
            amount_out_raw
        )

        result["amount_out_token"] = (
            from_raw_amount(
                amount_out_raw,
                token_decimals,
            )
        )

        result["reason"] = (
            "Router returned a valid BUY quote."
        )

        return result

    except Exception as e:

        result["reason"] = (
            "BUY quote simulation failed."
        )

        result["error"] = str(
            e
        )

        return result


# ============================================================
# SINGLE SELL QUOTE
# ============================================================

def simulate_sell(
    token_address,
    quote_token,
    amount_in_raw,
    token_decimals=18,
    quote_decimals=18,
):

    result = {
        "simulated": True,
        "success": False,
        "amount_in_raw": None,
        "amount_in_token": None,
        "amount_out_raw": None,
        "amount_out_quote": None,
        "quote_token": quote_token,
        "reason": None,
        "error": None,
    }

    try:

        token_address = safe_checksum(
            token_address
        )

        quote_token = safe_checksum(
            quote_token
        )

        if not token_address:

            raise ValueError(
                "Invalid target token address."
            )

        if not quote_token:

            raise ValueError(
                "Invalid quote token address."
            )

        amount_in_raw = int(
            amount_in_raw
        )

        if amount_in_raw <= 0:

            raise ValueError(
                "SELL amount must be greater than zero."
            )

        quote = get_amounts_out(
            amount_in_raw,
            [
                token_address,
                quote_token,
            ],
        )

        if not quote["success"]:

            result["reason"] = (
                "Router could not produce a SELL quote."
            )

            result["error"] = quote.get(
                "error"
            )

            return result

        amount_out_raw = int(
            quote["amounts"][-1]
        )

        if amount_out_raw <= 0:

            result["reason"] = (
                "Router returned a zero SELL output."
            )

            return result

        result["success"] = True

        result["amount_in_raw"] = (
            amount_in_raw
        )

        result["amount_in_token"] = (
            from_raw_amount(
                amount_in_raw,
                token_decimals,
            )
        )

        result["amount_out_raw"] = (
            amount_out_raw
        )

        result["amount_out_quote"] = (
            from_raw_amount(
                amount_out_raw,
                quote_decimals,
            )
        )

        result["reason"] = (
            "Router returned a valid SELL quote."
        )

        return result

    except Exception as e:

        result["reason"] = (
            "SELL quote simulation failed."
        )

        result["error"] = str(
            e
        )

        return result


# ============================================================
# ROUND-TRIP ANALYSIS
# ============================================================

def analyze_round_trip(
    token_address,
    quote_token,
    quote_amount,
    token_decimals,
    quote_decimals,
):

    result = {
        "quote_amount": quote_amount,
        "buy_success": False,
        "sell_success": False,
        "buy": None,
        "sell": None,
        "round_trip_return_percent": None,
        "round_trip_loss_percent": None,
    }

    buy = simulate_buy(
        token_address,
        quote_token,
        quote_amount,
    )

    result["buy"] = buy

    if not buy.get(
        "success"
    ):

        return result

    result["buy_success"] = True

    bought_amount_raw = buy.get(
        "amount_out_raw"
    )

    if not bought_amount_raw:

        return result

    sell = simulate_sell(
        token_address,
        quote_token,
        bought_amount_raw,
        token_decimals,
        quote_decimals,
    )

    result["sell"] = sell

    if not sell.get(
        "success"
    ):

        return result

    result["sell_success"] = True

    quote_in_raw = buy.get(
        "amount_in_raw"
    )

    quote_out_raw = sell.get(
        "amount_out_raw"
    )

    if quote_in_raw and quote_out_raw:

        return_percent = safe_percent(
            quote_out_raw,
            quote_in_raw,
        )

        loss_percent = max(
            0.0,
            100.0 - return_percent,
        )

        result[
            "round_trip_return_percent"
        ] = round(
            return_percent,
            4,
        )

        result[
            "round_trip_loss_percent"
        ] = round(
            loss_percent,
            4,
        )

    return result


# ============================================================
# MULTI-SIZE ROUTE CHECK
# ============================================================

def run_multi_size_analysis(
    token_address,
    quote_token,
    token_decimals,
    quote_decimals,
):

    test_amounts = [
        "0.0001",
        "0.001",
        "0.01",
    ]

    tests = []

    for amount in test_amounts:

        test = analyze_round_trip(
            token_address,
            quote_token,
            amount,
            token_decimals,
            quote_decimals,
        )

        tests.append(
            test
        )

    return tests


# ============================================================
# MAIN TRADE SIMULATION
# ============================================================

def analyze_trade_simulation(
    token_address,
    liquidity,
):

    result = {
        "status": "UNAVAILABLE",
        "risk": "UNKNOWN",
        "confidence": "LOW",

        "quote_token": None,
        "quote_symbol": None,

        "buy": {
            "simulated": False,
            "success": None,
            "reason": None,
        },

        "sell": {
            "simulated": False,
            "success": None,
            "reason": None,
        },

        "round_trip": {
            "return_percent": None,
            "loss_percent": None,
        },

        "multi_size_tests": [],

        "warnings": [],
        "signals": [],
    }

    # --------------------------------------------------------
    # VALIDATE LIQUIDITY
    # --------------------------------------------------------

    if not isinstance(
        liquidity,
        dict,
    ):

        result["warnings"].append(
            "Liquidity analysis data was invalid."
        )

        return result

    if not liquidity.get(
        "found"
    ):

        result["warnings"].append(
            "Buy/sell simulation was not performed because "
            "no supported liquidity pool was detected."
        )

        return result

    dex = liquidity.get(
        "dex"
    )

    if dex != "Uniswap V2":

        result["confidence"] = "MEDIUM"

        result["warnings"].append(
            "Trade quote simulation currently supports "
            f"Uniswap V2 pools only. Detected: {dex}"
        )

        return result

    # --------------------------------------------------------
    # QUOTE TOKEN
    # --------------------------------------------------------

    quote_token = get_quote_token(
        liquidity
    )

    if not quote_token:

        result["warnings"].append(
            "Liquidity pool was found, but its quote token "
            "could not be determined."
        )

        return result

    result["quote_token"] = quote_token

    # --------------------------------------------------------
    # TOKEN INFORMATION
    # --------------------------------------------------------

    try:

        w3 = get_web3()

        token_address = safe_checksum(
            token_address
        )

        if not token_address:

            raise ValueError(
                "Invalid token address."
            )

        token_decimals = (
            get_target_token_decimals(
                w3,
                token_address,
                liquidity,
            )
        )

        quote_decimals = safe_decimals(
            w3,
            quote_token,
            18,
        )

        result["quote_symbol"] = (
            safe_symbol(
                w3,
                quote_token,
            )
        )

    except Exception as e:

        result["status"] = "ERROR"

        result["warnings"].append(
            "Unable to prepare trade simulation: "
            + str(e)
        )

        return result

    # --------------------------------------------------------
    # PRIMARY TEST
    # --------------------------------------------------------

    primary_test = analyze_round_trip(
        token_address,
        quote_token,
        "0.001",
        token_decimals,
        quote_decimals,
    )

    result["buy"] = (
        primary_test.get("buy")
        or result["buy"]
    )

    result["sell"] = (
        primary_test.get("sell")
        or result["sell"]
    )

    result["round_trip"] = {
        "return_percent":
            primary_test.get(
                "round_trip_return_percent"
            ),

        "loss_percent":
            primary_test.get(
                "round_trip_loss_percent"
            ),
    }

    # --------------------------------------------------------
    # MULTI-SIZE TEST
    # --------------------------------------------------------

    multi_size_tests = (
        run_multi_size_analysis(
            token_address,
            quote_token,
            token_decimals,
            quote_decimals,
        )
    )

    result[
        "multi_size_tests"
    ] = multi_size_tests

    successful_tests = [
        test
        for test in multi_size_tests
        if test.get("buy_success")
        and test.get("sell_success")
    ]

    failed_buy_tests = [
        test
        for test in multi_size_tests
        if not test.get("buy_success")
    ]

    failed_sell_tests = [
        test
        for test in multi_size_tests
        if test.get("buy_success")
        and not test.get("sell_success")
    ]

    # --------------------------------------------------------
    # EVALUATION
    # --------------------------------------------------------

    total_tests = len(
        multi_size_tests
    )

    successful_count = len(
        successful_tests
    )

    failed_buy_count = len(
        failed_buy_tests
    )

    failed_sell_count = len(
        failed_sell_tests
    )

    # --------------------------------------------------------
    # ALL BUY TESTS FAILED
    # --------------------------------------------------------

    if (
        total_tests > 0
        and failed_buy_count == total_tests
    ):

        result["status"] = "WARNING"
        result["risk"] = "MEDIUM"
        result["confidence"] = "MEDIUM"

        result["warnings"].append(
            "All tested BUY quote sizes failed."
        )

    # --------------------------------------------------------
    # ALL BUY QUOTES WORK BUT ALL SELLS FAILED
    # --------------------------------------------------------

    elif (
        total_tests > 0
        and failed_sell_count == total_tests
    ):

        result["status"] = "WARNING"
        result["risk"] = "HIGH"
        result["confidence"] = "MEDIUM"

        result["signals"].append(
            "BUY routes returned valid router quotes."
        )

        result["warnings"].append(
            "All tested SELL quote sizes failed after "
            "successful BUY quotes."
        )

    # --------------------------------------------------------
    # PARTIAL FAILURES
    # --------------------------------------------------------

    elif (
        failed_buy_tests
        or failed_sell_tests
    ):

        result["status"] = "WARNING"
        result["risk"] = "MEDIUM"
        result["confidence"] = "MEDIUM"

        if successful_count:

            result["signals"].append(
                f"{successful_count} of {total_tests} "
                "quote round-trip tests completed successfully."
            )

        if failed_buy_tests:

            result["warnings"].append(
                f"{failed_buy_count} BUY quote test size(s) "
                "failed."
            )

        if failed_sell_tests:

            result["warnings"].append(
                f"{failed_sell_count} SELL quote test size(s) "
                "failed after successful BUY quotes."
            )

    # --------------------------------------------------------
    # NO COMPLETE TEST
    # --------------------------------------------------------

    elif not successful_tests:

        result["status"] = "WARNING"
        result["risk"] = "MEDIUM"
        result["confidence"] = "LOW"

        result["warnings"].append(
            "No complete BUY and SELL quote round-trip "
            "could be completed."
        )

    # --------------------------------------------------------
    # ALL TESTS PASSED
    # --------------------------------------------------------

    else:

        losses = []

        for test in successful_tests:

            loss = test.get(
                "round_trip_loss_percent"
            )

            if loss is not None:

                losses.append(
                    float(loss)
                )

        max_loss = (
            max(losses)
            if losses
            else 0.0
        )

        result["status"] = "PASS"
        result["risk"] = "LOW"
        result["confidence"] = "MEDIUM"

        result["signals"].append(
            "BUY routes returned valid router quotes."
        )

        result["signals"].append(
            "SELL routes returned valid router quotes."
        )

        result["signals"].append(
            f"All {successful_count} quote round-trip "
            "tests completed successfully."
        )

        # ----------------------------------------------------
        # ROUND-TRIP LOSS ANALYSIS
        # ----------------------------------------------------

        if max_loss > 50:

            result["status"] = "WARNING"
            result["risk"] = "HIGH"

            result["warnings"].append(
                f"Maximum quoted round-trip loss was "
                f"{max_loss:.2f}%, indicating extreme "
                "price impact or trading costs."
            )

        elif max_loss > 30:

            result["status"] = "WARNING"
            result["risk"] = "MEDIUM"

            result["warnings"].append(
                f"Maximum quoted round-trip loss was "
                f"{max_loss:.2f}%, indicating potentially "
                "high price impact or trading costs."
            )

        elif max_loss > 10:

            result["status"] = "WARNING"
            result["risk"] = "MEDIUM"

            result["warnings"].append(
                f"Maximum quoted round-trip loss was "
                f"{max_loss:.2f}%."
            )

        else:

            result["signals"].append(
                f"Maximum quoted round-trip loss across "
                f"tested sizes: {max_loss:.2f}%."
            )

    # --------------------------------------------------------
    # IMPORTANT LIMITATION
    # --------------------------------------------------------

    result["warnings"].append(
        "Router quotes confirm that routes can be "
        "quoted on-chain, but they do not guarantee "
        "that a real wallet transaction will succeed. "
        "Token taxes, transfer restrictions, approvals, "
        "and state-dependent honeypot logic may still "
        "affect actual swaps."
    )

    return result