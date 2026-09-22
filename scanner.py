import sys


# =========================================================
# COMMAND-LINE MODE
# =========================================================

DEEP_SCAN = "--deep" in sys.argv[1:]


from web3 import Web3

from config import RPC_URL

from engines.liquidity_engine import analyze_liquidity
from engines.security_engine import security_scan
from engines.tax_analysis import analyze_tax
from engines.ownership_analysis import analyze_ownership
from engines.trading_restrictions import analyze_trading_restrictions
from engines.trade_simulator import analyze_trade_simulation
from engines.overall_risk import calculate_overall_risk

from detectors.trade_safety_detector import analyze_trade_safety
from detectors.honeypot_detector import analyze_honeypot
from detectors.swap_simulator import analyze_swap_simulation

from analysis.holders import (
    get_holders,
    get_holder_risk,
)

from core.abi import get_abi
from core.bytecode import analyze_bytecode


# =========================================================
# CONSTANTS
# =========================================================

PAIR_ABI = [
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    }
]


TOKEN_ABI = [
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    }
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


def get_lp_total_supply(
    pair_address,
):

    w3 = get_web3()

    pair = w3.eth.contract(
        address=Web3.to_checksum_address(
            pair_address
        ),
        abi=PAIR_ABI,
    )

    return pair.functions.totalSupply().call()


def get_token_total_supply(
    token_address,
):

    w3 = get_web3()

    token = w3.eth.contract(
        address=Web3.to_checksum_address(
            token_address
        ),
        abi=TOKEN_ABI,
    )

    return token.functions.totalSupply().call()


# =========================================================
# PRINT HELPERS
# =========================================================

def print_section(
    title,
    icon="",
):

    print()
    print(
        f"{icon} {title}"
    )
    print(
        "-" * 50
    )


def print_warnings(
    report,
):

    if not isinstance(
        report,
        dict,
    ):
        return

    warnings = report.get(
        "warnings",
        [],
    )

    if warnings:

        print()
        print(
            "⚠️ Warnings:"
        )

        for warning in warnings:

            print(
                f"- {warning}"
            )


def print_signals(
    report,
):

    if not isinstance(
        report,
        dict,
    ):
        return

    signals = report.get(
        "signals",
        [],
    )

    if signals:

        print()
        print(
            "ℹ️ Signals:"
        )

        for signal in signals:

            print(
                f"- {signal}"
            )


def print_analysis_header(
    report,
):

    if not isinstance(
        report,
        dict,
    ):
        return

    print(
        f"Status: "
        f"{report.get('status', 'UNKNOWN')}"
    )

    print(
        f"Risk: "
        f"{report.get('risk', 'UNKNOWN')}"
    )

    print(
        f"Confidence: "
        f"{report.get('confidence', 'LOW')}"
    )


# =========================================================
# LIQUIDITY PRINTING
# =========================================================

def print_liquidity(
    liquidity,
):

    print(
        f"Found: "
        f"{liquidity.get('found', False)}"
    )

    print(
        f"DEX: "
        f"{liquidity.get('dex')}"
    )

    print(
        f"Version: "
        f"{liquidity.get('version')}"
    )

    print(
        f"Best pool: "
        f"{liquidity.get('pair')}"
    )

    print(
        f"Pools found: "
        f"{liquidity.get('pool_count', 0)}"
    )

    quote_token = liquidity.get(
        "quote_token"
    )

    quote_reserve = liquidity.get(
        "quote_reserve_raw"
    )

    if quote_token:

        print(
            f"Quote token: "
            f"{quote_token}"
        )

    if quote_reserve is not None:

        print(
            f"Quote reserve: "
            f"{quote_reserve}"
        )

    weth_reserve = liquidity.get(
        "weth_reserve",
        0,
    )

    liquidity_eth = liquidity.get(
        "liquidity_eth",
        0,
    )

    try:

        weth_reserve = float(
            weth_reserve or 0
        )

    except Exception:

        weth_reserve = 0.0

    try:

        liquidity_eth = float(
            liquidity_eth or 0
        )

    except Exception:

        liquidity_eth = 0.0

    if weth_reserve > 0:

        print(
            f"WETH reserve: "
            f"{weth_reserve}"
        )

    if liquidity_eth > 0:

        print(
            f"Liquidity ETH: "
            f"{liquidity_eth}"
        )

    print(
        f"Liquidity USD: "
        f"${liquidity.get('liquidity_usd', 0)}"
    )

    print(
        f"Total discovered liquidity USD: "
        f"${liquidity.get('total_liquidity_usd', liquidity.get('liquidity_usd', 0))}"
    )

    print(
        f"Risk: "
        f"{liquidity.get('risk', 'UNKNOWN')}"
    )

    print(
        f"Reason: "
        f"{liquidity.get('reason', '')}"
    )


def print_discovered_pools(
    liquidity,
):

    pools = liquidity.get(
        "pools",
        [],
    )

    if not pools:

        return

    print()
    print(
        "Discovered pools:"
    )

    for index, pool in enumerate(
        pools,
        start=1,
    ):

        print()
        print(
            f"Pool #{index}"
        )

        print(
            f"  DEX: "
            f"{pool.get('dex', 'UNKNOWN')}"
        )

        print(
            f"  Version: "
            f"{pool.get('version', 'UNKNOWN')}"
        )

        print(
            f"  Address: "
            f"{pool.get('pair', 'UNKNOWN')}"
        )

        if pool.get("fee") is not None:

            fee_percent = pool.get(
                "fee_percent"
            )

            if fee_percent is not None:

                print(
                    f"  Fee tier: "
                    f"{fee_percent}%"
                )

            else:

                print(
                    f"  Fee tier: "
                    f"{pool.get('fee')}"
                )

        quote_token = pool.get(
            "quote_token"
        )

        quote_reserve = pool.get(
            "quote_reserve_raw"
        )

        if quote_token:

            print(
                f"  Quote token: "
                f"{quote_token}"
            )

        if quote_reserve is not None:

            print(
                f"  Quote reserve: "
                f"{quote_reserve}"
            )

        pool_weth = pool.get(
            "weth_reserve",
            0,
        )

        pool_eth = pool.get(
            "liquidity_eth",
            0,
        )

        try:

            pool_weth = float(
                pool_weth or 0
            )

        except Exception:

            pool_weth = 0.0

        try:

            pool_eth = float(
                pool_eth or 0
            )

        except Exception:

            pool_eth = 0.0

        if pool_weth > 0:

            print(
                f"  WETH reserve: "
                f"{pool_weth}"
            )

        if pool_eth > 0:

            print(
                f"  Liquidity ETH: "
                f"{pool_eth}"
            )

        print(
            f"  Liquidity USD: "
            f"${pool.get('liquidity_usd', 0)}"
        )

        print(
            f"  Risk: "
            f"{pool.get('risk', 'UNKNOWN')}"
        )

        print(
            f"  Reason: "
            f"{pool.get('reason', '')}"
        )


# =========================================================
# LP SAFETY
# =========================================================

def analyze_lp_safety(
    liquidity,
):

    lp_safety = {
        "safety": "UNKNOWN",
        "lp_total_supply": None,
        "burned_lp": None,
        "burn_percentage": None,
        "active_lp": None,
        "reason": "LP holder distribution could not be determined.",
        "warnings": [],
        "signals": [],
    }

    if not liquidity.get(
        "found"
    ):

        return lp_safety

    pair = liquidity.get(
        "pair"
    )

    if not pair:

        return lp_safety

    try:

        from core.lp_safety import (
            calculate_lp_safety
        )

        lp_total_supply = (
            get_lp_total_supply(
                pair
            )
        )

        return calculate_lp_safety(
            pair,
            lp_total_supply,
        )

    except Exception as e:

        print(
            f"LP safety analysis unavailable: {e}"
        )

        return lp_safety


def print_lp_safety(
    liquidity,
    lp_safety,
):

    if not liquidity.get(
        "found"
    ):

        return

    print_section(
        "LP SAFETY",
        "🔒"
    )

    pair = liquidity.get(
        "pair"
    )

    print(
        f"Pair: "
        f"{pair}"
    )

    print(
        f"LP total supply: "
        f"{lp_safety.get('lp_total_supply')}"
    )
    
    burned_lp = lp_safety.get(
        "burned_lp"
    )

    burn_percentage = lp_safety.get(
        "burn_percentage"
    )

    active_lp = lp_safety.get(
        "active_lp"
    )

    print(
        f"Burned LP: "
        f"{burned_lp if burned_lp is not None else 'UNKNOWN'}"
    )

    print(
        f"Burn percentage: "
        f"{burn_percentage if burn_percentage is not None else 'UNKNOWN'}"
        f"{'%' if burn_percentage is not None else ''}"
    )

    print(
        f"Active LP: "
        f"{active_lp if active_lp is not None else 'UNKNOWN'}"
    )

    print(
        f"Safety: "
        f"{lp_safety.get('safety')}"
    )

    print(
        f"Reason: "
        f"{lp_safety.get('reason')}"
    )


# =========================================================
# HOLDER ANALYSIS
# =========================================================

def analyze_holders(
    token_address,
    liquidity=None,
):

    print_section(
        "HOLDER DISTRIBUTION",
        "👥"
    )

    holders = None

    holder_risk = {
        "score": 0,
        "level": "UNKNOWN",
        "largest_wallet": None,
        "top5": None,
        "top10": None,
        "coverage": "UNKNOWN",
        "verified": False,
        "reasons": [
            "Holder distribution could not be determined."
        ],
    }

    try:

        # -------------------------------------------------
        # HOLDER DATA
        # -------------------------------------------------

        holders = get_holders(
            token_address
        )

        if not holders:

            raise ValueError(
                "No verified holder data was returned."
            )

        total_supply = (
            get_token_total_supply(
                token_address
            )
        )

        if not total_supply:

            raise ValueError(
                "Token total supply could not be determined."
            )

        # -------------------------------------------------
        # KNOWN EXCLUDED ADDRESSES
        #
        # Do not treat the LP pair or the token contract
        # itself as a normal holder.
        # -------------------------------------------------

        excluded_addresses = [
        token_address,
        ]

        pair = None

        if isinstance(
            liquidity,
            dict,
        ):

            pair = liquidity.get(
                "pair"
            )

        if pair:

            excluded_addresses.append(
                pair
            )

        # -------------------------------------------------
        # HOLDER RISK
        # -------------------------------------------------

        holder_risk = get_holder_risk(
            holders,
            total_supply,
            excluded_addresses=excluded_addresses,
        )

        source = holders.get(
            "_source",
            "unknown",
        )

        verified = bool(
            holders.get(
                "_verified",
                False,
            )
        )

        complete = bool(
            holders.get(
                "_complete",
                False,
            )
        )

        # -------------------------------------------------
        # SOURCE / COVERAGE
        # -------------------------------------------------

        print(
            f"Source: "
            f"{source}"
        )

        print(
            f"Verified: "
            f"{'YES' if verified else 'NO'}"
        )

        print(
            f"Coverage: "
            f"{'COMPLETE' if complete else 'PARTIAL'}"
        )

        candidate_count = holders.get(
            "_candidate_count"
        )

        holder_count = holders.get(
            "_holder_count"
        )

        if candidate_count is not None:

            print(
                f"Candidates discovered: "
                f"{candidate_count}"
            )

        if holder_count is not None:

            print(
                f"Positive-balance addresses: "
                f"{holder_count}"
            )

        contract_count = holder_risk.get(
            "contract_count"
        )

        eoa_count = holder_risk.get(
            "eoa_count"
        )

        unknown_count = holder_risk.get(
            "unknown_count"
        )

        if contract_count is not None:

            print(
                f"Contract holders: "
                f"{contract_count}"
            )

        if eoa_count is not None:

            print(
                f"EOA holders: "
                f"{eoa_count}"
            )

        if unknown_count is not None:

            print(
                f"Unknown type holders: "
                f"{unknown_count}"
            )

        # -------------------------------------------------
        # HOLDER CONCENTRATION
        # -------------------------------------------------

        largest_wallet = holder_risk.get(
            "largest_wallet"
        )

        top5 = holder_risk.get(
            "top5"
        )

        top10 = holder_risk.get(
            "top10"
        )

        if largest_wallet is not None:

            print(
                f"Largest discovered wallet: "
                f"{largest_wallet}%"
            )

        if top5 is not None:

            print(
                f"Top 5 discovered wallets: "
                f"{top5}%"
            )

        if top10 is not None:

            print(
                f"Top 10 discovered wallets: "
                f"{top10}%"
            )

        print(
            f"Holder score: "
            f"{holder_risk.get('score', 0)}"
        )

        # -------------------------------------------------
        # RISK
        # -------------------------------------------------

        if complete:

            print(
                f"Holder risk: "
                f"{holder_risk.get('level', 'UNKNOWN')}"
            )

        else:

            print(
                "Holder risk: "
                "UNKNOWN / PARTIAL COVERAGE"
            )

        # -------------------------------------------------
        # REASONS
        # -------------------------------------------------

        reasons = holder_risk.get(
            "reasons",
            []
        )

        if reasons:

            print(
                "Reasons:"
            )

            for reason in reasons:

                print(
                    f"- {reason}"
                )

    except Exception as e:

        holders = None

        holder_risk = {
            "score": 0,
            "level": "UNKNOWN",
            "largest_wallet": None,
            "top5": None,
            "top10": None,
            "coverage": "UNKNOWN",
            "verified": False,
            "reasons": [
                "Holder distribution could not be determined."
            ],
        }

        print(
            "Holder analysis unavailable."
        )

        print(
            f"Reason: {e}"
        )

    return (
        holders,
        holder_risk,
    )


# =========================================================
# CONTRACT SECURITY
# =========================================================

def analyze_contract_security(
    token_address,
):

    print_section(
        "CONTRACT SECURITY",
        "🧠"
    )

    contract_security = None

    try:

        contract_security = security_scan(
            token_address
        )

    except Exception as e:

        print(
            f"Security analysis failed: {e}"
        )

    if not contract_security:

        print(
            "Contract security analysis unavailable."
        )

        return contract_security

    for item in contract_security:

        if not isinstance(
            item,
            dict,
        ):

            continue

        check = item.get(
            "check",
            "Unknown",
        )

        status = item.get(
            "status",
            "UNKNOWN",
        )

        confidence = item.get(
            "confidence",
            "LOW",
        )

        reason = item.get(
            "reason",
            "",
        )

        if status == "PASS":

            icon = "✅"

        elif status == "FAIL":

            icon = "🔴"

        elif status == "WARNING":

            icon = "⚠️"

        else:

            icon = "ℹ️"

        print()
        print(
            f"{icon} {check}"
        )

        print(
            f"Status : {status}"
        )

        print(
            f"Confidence : {confidence}"
        )

        print(
            f"Reason : {reason}"
        )

    return contract_security


# =========================================================
# PROXY / IMPLEMENTATION
# =========================================================

def analyze_proxy(
    token_address,
):

    print_section(
        "PROXY / IMPLEMENTATION",
        "🔗"
    )

    bytecode_report = {
        "available": False,
        "proxy": {
            "detected": False,
        },
    }

    proxy = {}
    implementation_analysis = None

    try:

        bytecode_report = analyze_bytecode(
            token_address
        )

        if not isinstance(
            bytecode_report,
            dict,
        ):

            bytecode_report = {
                "available": False,
                "proxy": {
                    "detected": False,
                },
            }

        proxy = bytecode_report.get(
            "proxy",
            {}
        ) or {}

        if proxy.get(
            "detected"
        ):

            print(
                f"Proxy detected: "
                f"{proxy.get('type', 'UNKNOWN')}"
            )

            implementation = proxy.get(
                "implementation"
            )

            if implementation:

                print(
                    f"Implementation: "
                    f"{implementation}"
                )

            print(
                f"Confidence: "
                f"{proxy.get('confidence', 'LOW')}"
            )

            print(
                f"Reason: "
                f"{proxy.get('reason', '')}"
            )

            implementation_analysis = (
                proxy.get(
                    "implementation_analysis"
                )
            )

            if implementation_analysis:

                print()
                print(
                    "Implementation Analysis"
                )

                print(
                    f"Status: "
                    f"{implementation_analysis.get('status', 'UNKNOWN')}"
                )

                print(
                    f"Confidence: "
                    f"{implementation_analysis.get('confidence', 'LOW')}"
                )

                print(
                    f"Bytecode size: "
                    f"{implementation_analysis.get('bytecode_size', 0)} bytes"
                )

                groups = (
                    implementation_analysis.get(
                        "groups",
                        {}
                    )
                )

                print(
                    f"ERC-20 selectors: "
                    f"{len(groups.get('erc20', []))}"
                )

                print(
                    f"Ownership selectors: "
                    f"{len(groups.get('ownership', []))}"
                )

                print(
                    f"Blacklist selectors: "
                    f"{len(groups.get('blacklist', []))}"
                )

                print(
                    f"Pause selectors: "
                    f"{len(groups.get('pause', []))}"
                )

                print(
                    f"Trading selectors: "
                    f"{len(groups.get('trading', []))}"
                )

                print(
                    f"Limit selectors: "
                    f"{len(groups.get('limits', []))}"
                )

                print(
                    f"Tax selectors: "
                    f"{len(groups.get('tax', []))}"
                )

                print_signals(
                    implementation_analysis
                )

                print_warnings(
                    implementation_analysis
                )

            else:

                print()
                print(
                    "Implementation analysis unavailable."
                )

        else:

            print(
                "Proxy detected: False"
            )

            print(
                "No supported proxy pattern was detected."
            )

    except Exception as e:

        print(
            f"Proxy analysis failed: {e}"
        )

    return (
        bytecode_report,
        proxy,
        implementation_analysis,
    )


# =========================================================
# TAX
# =========================================================

def analyze_tax_section(
    token_address,
    token_abi,
):

    print_section(
        "TAX ANALYSIS",
        "💰"
    )

    tax_analysis = {
        "status": "UNAVAILABLE",
        "risk": "UNKNOWN",
        "confidence": "LOW",
        "warnings": [],
        "signals": [],
    }

    if token_abi is None:

        print(
            "Contract source code not verified"
        )

        print(
            "Status: UNAVAILABLE"
        )

        print(
            "Risk: UNKNOWN"
        )

        print(
            "Confidence: LOW"
        )

        print(
            "Reason: Contract ABI could not be loaded."
        )

        return tax_analysis

    try:

        tax_analysis = analyze_tax(
            token_address,
            token_abi,
        )

        print_analysis_header(
            tax_analysis
        )

        buy_tax = tax_analysis.get(
            "buy_tax"
        )

        sell_tax = tax_analysis.get(
            "sell_tax"
        )

        general_tax = tax_analysis.get(
            "general_tax"
        )

        if buy_tax and (
            buy_tax.get("percentage")
            is not None
        ):

            print(
                f"Buy tax: "
                f"{buy_tax['percentage']:.2f}%"
            )

        if sell_tax and (
            sell_tax.get("percentage")
            is not None
        ):

            print(
                f"Sell tax: "
                f"{sell_tax['percentage']:.2f}%"
            )

        if general_tax and (
            general_tax.get("percentage")
            is not None
        ):

            print(
                f"General tax: "
                f"{general_tax['percentage']:.2f}%"
            )

        print_warnings(
            tax_analysis
        )

        print_signals(
            tax_analysis
        )

    except Exception as e:

        tax_analysis = {
            "status": "UNKNOWN",
            "risk": "UNKNOWN",
            "confidence": "LOW",
            "warnings": [
                f"Tax analysis failed: {e}"
            ],
            "signals": [],
        }

        print_analysis_header(
            tax_analysis
        )

    return tax_analysis


# =========================================================
# OWNERSHIP
# =========================================================

def analyze_ownership_section(
    token_address,
    token_abi,
):

    print_section(
        "OWNERSHIP / ADMIN CONTROL",
        "🔐"
    )

    ownership_analysis = {
        "status": "UNAVAILABLE",
        "risk": "UNKNOWN",
        "confidence": "LOW",
        "warnings": [],
        "signals": [],
    }

    if token_abi is None:

        print(
            "Contract source code not verified"
        )

        print(
            "Status: UNAVAILABLE"
        )

        print(
            "Risk: UNKNOWN"
        )

        print(
            "Confidence: LOW"
        )

        print(
            "Reason: Contract ABI could not be loaded."
        )

        return ownership_analysis

    try:

        ownership_analysis = (
            analyze_ownership(
                token_address,
                token_abi,
            )
        )

        print_analysis_header(
            ownership_analysis
        )

        print(
            f"Current owner: "
            f"{ownership_analysis.get('owner')}"
        )

        print(
            f"Ownership renounced: "
            f"{ownership_analysis.get('ownership_renounced')}"
        )

        print(
            f"Can transfer ownership: "
            f"{ownership_analysis.get('can_transfer_ownership')}"
        )

        print(
            f"Can renounce ownership: "
            f"{ownership_analysis.get('can_renounce_ownership')}"
        )

        print_warnings(
            ownership_analysis
        )

        print_signals(
            ownership_analysis
        )

    except Exception as e:

        ownership_analysis = {
            "status": "UNKNOWN",
            "risk": "UNKNOWN",
            "confidence": "LOW",
            "warnings": [
                f"Ownership analysis failed: {e}"
            ],
            "signals": [],
        }

        print_analysis_header(
            ownership_analysis
        )

    return ownership_analysis


# =========================================================
# TRADING RESTRICTIONS
# =========================================================

def analyze_trading_restrictions_section(
    token_address,
    token_abi,
):

    print_section(
        "TRADING RESTRICTIONS / LIMITS",
        "🚧"
    )

    trading_restrictions = {
        "status": "UNAVAILABLE",
        "risk": "UNKNOWN",
        "confidence": "LOW",
        "warnings": [],
        "signals": [],
    }

    if token_abi is None:

        print(
            "Contract source code not verified"
        )

        print(
            "Status: UNAVAILABLE"
        )

        print(
            "Risk: UNKNOWN"
        )

        print(
            "Confidence: LOW"
        )

        print(
            "Reason: Contract ABI could not be loaded."
        )

        return trading_restrictions

    try:

        trading_restrictions = (
            analyze_trading_restrictions(
                token_address,
                token_abi,
            )
        )

        print_analysis_header(
            trading_restrictions
        )

        print_warnings(
            trading_restrictions
        )

        print_signals(
            trading_restrictions
        )

    except Exception as e:

        trading_restrictions = {
            "status": "UNKNOWN",
            "risk": "UNKNOWN",
            "confidence": "LOW",
            "warnings": [
                f"Trading restrictions analysis failed: {e}"
            ],
            "signals": [],
        }

        print_analysis_header(
            trading_restrictions
        )

    return trading_restrictions


# =========================================================
# TRADE SAFETY
# =========================================================

def analyze_trade_safety_section(
    token_address,
    token_abi,
    tax_analysis,
):

    print_section(
        "TRADE SAFETY",
        "🧪"
    )

    trade_safety = {
        "status": "UNKNOWN",
        "risk": "LOW",
        "confidence": "LOW",
        "warnings": [],
        "signals": [],
    }

    try:

        functions = []

        if token_abi is not None:

            from core.function_index import (
                build_function_index
            )

            functions = build_function_index(
                token_abi
            )

        else:

            print(
                "⚠️ ABI unavailable; using bytecode "
                "selector analysis."
            )

            bytecode_result = analyze_bytecode(
                token_address
            )

            if isinstance(
                bytecode_result,
                dict,
            ):

                detected_selectors = (
                    bytecode_result.get(
                        "detected_selectors",
                        [],
                    )
                )

                if isinstance(
                    detected_selectors,
                    list,
                ):

                    functions = (
                        detected_selectors
                    )

        trade_safety = (
            analyze_trade_safety(
                functions
            )
        )

        if isinstance(
            trade_safety,
            dict,
        ):

            trade_safety.setdefault(
                "warnings",
                []
            )

            trade_safety.setdefault(
                "signals",
                []
            )

            if token_abi is None:

                trade_safety[
                    "confidence"
                ] = "LOW"

                message = (
                    "Bytecode selector analysis cannot "
                    "detect every possible trade restriction."
                )

                if message not in trade_safety[
                    "warnings"
                ]:

                    trade_safety[
                        "warnings"
                    ].append(
                        message
                    )

            if (
                not functions
                and token_abi is None
            ):

                trade_safety[
                    "status"
                ] = "UNKNOWN"

                trade_safety[
                    "risk"
                ] = "LOW"

                trade_safety[
                    "signals"
                ].append(
                    "No ABI was available and no recognized "
                    "bytecode selectors were available for "
                    "trade-safety analysis."
                )

        print_analysis_header(
            trade_safety
        )

        print_warnings(
            trade_safety
        )

        print_signals(
            trade_safety
        )

    except Exception as e:

        trade_safety = {
            "status": "UNKNOWN",
            "risk": "LOW",
            "confidence": "LOW",
            "warnings": [
                f"Trade safety analysis failed: {e}"
            ],
            "signals": [],
        }

        print_analysis_header(
            trade_safety
        )

    return trade_safety


# =========================================================
# TRADE SIMULATION
# =========================================================

def analyze_trade_simulation_section(
    token_address,
    liquidity,
):

    print_section(
        "TRADE SIMULATION",
        "🔬"
    )

    simulation = {
        "status": "UNKNOWN",
        "risk": "HIGH",
        "confidence": "LOW",
        "buy": {},
        "sell": {},
        "warnings": [],
        "signals": [],
    }

    try:

        simulation = (
            analyze_trade_simulation(
                token_address,
                liquidity,
            )
        )

        print_analysis_header(
            simulation
        )

        buy = simulation.get(
            "buy",
            {}
        )

        sell = simulation.get(
            "sell",
            {}
        )

        print()
        print(
            "BUY"
        )

        print(
            f"Simulated: "
            f"{buy.get('simulated', False)}"
        )

        print(
            f"Success: "
            f"{buy.get('success')}"
        )

        if buy.get(
            "reason"
        ):

            print(
                f"Reason: "
                f"{buy.get('reason')}"
            )

        print()
        print(
            "SELL"
        )

        print(
            f"Simulated: "
            f"{sell.get('simulated', False)}"
        )

        print(
            f"Success: "
            f"{sell.get('success')}"
        )

        if sell.get(
            "reason"
        ):

            print(
                f"Reason: "
                f"{sell.get('reason')}"
            )

        print_warnings(
            simulation
        )

        print_signals(
            simulation
        )

    except Exception as e:

        simulation = {
            "status": "UNKNOWN",
            "risk": "HIGH",
            "confidence": "LOW",
            "buy": {},
            "sell": {},
            "warnings": [
                f"Trade simulation failed: {e}"
            ],
            "signals": [],
        }

        print_analysis_header(
            simulation
        )

    return simulation


# =========================================================
# HONEYPOT
# =========================================================

def analyze_honeypot_section(
    token_address,
    liquidity,
    holders,
):

    print_section(
        "HONEYPOT / SELLABILITY",
        "🍯"
    )

    honeypot = {
        "status": "UNKNOWN",
        "risk": "HIGH",
        "confidence": "LOW",
        "buy": {},
        "sell": {},
        "warnings": [],
        "signals": [],
    }

    try:

        honeypot = analyze_honeypot(
            token_address,
            liquidity,
            holders,
        )

        print_analysis_header(
            honeypot
        )

        buy = honeypot.get(
            "buy",
            {}
        )

        sell = honeypot.get(
            "sell",
            {}
        )

        print()
        print(
            "BUY"
        )

        print(
            f"Tested: "
            f"{buy.get('tested', False)}"
        )

        print(
            f"Success: "
            f"{buy.get('success')}"
        )

        if buy.get(
            "reason"
        ):

            print(
                f"Reason: "
                f"{buy.get('reason')}"
            )

        print()
        print(
            "SELL"
        )

        print(
            f"Tested: "
            f"{sell.get('tested', False)}"
        )

        print(
            f"Success: "
            f"{sell.get('success')}"
        )

        if sell.get(
            "reason"
        ):

            print(
                f"Reason: "
                f"{sell.get('reason')}"
            )

        print_warnings(
            honeypot
        )

        print_signals(
            honeypot
        )

    except Exception as e:

        honeypot = {
            "status": "UNKNOWN",
            "risk": "HIGH",
            "confidence": "LOW",
            "buy": {},
            "sell": {},
            "warnings": [
                f"Honeypot analysis failed: {e}"
            ],
            "signals": [],
        }

        print_analysis_header(
            honeypot
        )

    return honeypot


# =========================================================
# DEEP ROUTER SWAP SIMULATION
# =========================================================

def analyze_deep_swap_section(
    token_address,
    liquidity,
    holders,
):

    print_section(
        "DEEP ROUTER SWAP EXECUTION TEST",
        "⚡"
    )

    if not DEEP_SCAN:

        print(
            "Skipped in normal scan."
        )

        print(
            "Use --deep to enable router execution testing."
        )

        return {
            "status": "SKIPPED",
            "risk": "UNKNOWN",
            "confidence": "NONE",
            "tested": False,
            "warnings": [
                "Deep router swap execution testing was "
                "skipped for the normal scan."
            ],
            "signals": [
                "Run scanner.py with --deep to perform "
                "router execution simulation."
            ],
        }

    swap_simulation = {
        "status": "UNAVAILABLE",
        "risk": "UNKNOWN",
        "confidence": "LOW",
        "tested": False,
        "warnings": [],
        "signals": [],
        "tests": [],
    }

    try:

        swap_simulation = analyze_swap_simulation(
            token_address,
            liquidity,
            holders,
            deep=True,
        )

        print_analysis_header(
            swap_simulation
        )

        print(
            f"Tested: "
            f"{swap_simulation.get('tested', False)}"
        )

        holder = swap_simulation.get(
            "holder"
        )

        if holder:

            print(
                f"Test holder: "
                f"{holder}"
            )

        holder_balance = swap_simulation.get(
            "holder_balance",
            0,
        )

        if holder_balance:

            print(
                f"Holder balance raw: "
                f"{holder_balance}"
            )

        allowance = swap_simulation.get(
            "holder_allowance",
            0,
        )

        if allowance:

            print(
                f"Router allowance raw: "
                f"{allowance}"
            )

        if swap_simulation.get(
            "state_override_used"
        ):

            print(
                f"State override used: True"
            )

        tests = swap_simulation.get(
            "tests",
            []
        )

        if tests:

            print()
            print(
                f"Swap tests: {len(tests)}"
            )

            for index, test in enumerate(
                tests,
                start=1,
            ):

                print()
                print(
                    f"Test #{index}"
                )

                print(
                    f"  Amount raw: "
                    f"{test.get('amount_in')}"
                )

                print(
                    f"  Success: "
                    f"{test.get('success')}"
                )

                if test.get(
                    "error"
                ):

                    print(
                        f"  Error: "
                        f"{test.get('error')}"
                    )

        print_warnings(
            swap_simulation
        )

        print_signals(
            swap_simulation
        )

    except Exception as e:

        swap_simulation = {
            "status": "ERROR",
            "risk": "UNKNOWN",
            "confidence": "LOW",
            "tested": False,
            "tests": [],
            "warnings": [
                f"Deep router swap simulation failed: {e}"
            ],
            "signals": [],
        }

        print_analysis_header(
            swap_simulation
        )

        print_warnings(
            swap_simulation
        )

    return swap_simulation


# =========================================================
# MAIN SCANNER
# =========================================================

def scan_token(
    token_address,
):

    token_address = Web3.to_checksum_address(
        token_address
    )

    print()
    print(
        "🛡️ RobinShield Token Security Scanner"
    )
    print(
        "=" * 50
    )

    print(
        f"Token: "
        f"{token_address}"
    )

    if DEEP_SCAN:

        print(
            "Mode: DEEP"
        )

    else:

        print(
            "Mode: NORMAL"
        )

    # =====================================================
    # LIQUIDITY
    # =====================================================

    print_section(
        "LIQUIDITY",
        "💧"
    )

    try:

        liquidity = analyze_liquidity(
            token_address
        )

    except Exception as e:

        liquidity = {
            "found": False,
            "dex": None,
            "version": None,
            "pair": None,
            "quote_token": None,
            "quote_reserve_raw": None,
            "weth_reserve": 0,
            "token_reserve": 0,
            "token_decimals": None,
            "liquidity_eth": 0,
            "eth_price_usd": 0,
            "liquidity_usd": 0,
            "total_liquidity_eth": 0,
            "total_liquidity_usd": 0,
            "pool_count": 0,
            "pools": [],
            "risk": "HIGH",
            "reason": (
                f"Liquidity analysis failed: {e}"
            ),
        }

    print_liquidity(
        liquidity
    )

    print_discovered_pools(
        liquidity
    )

    # =====================================================
    # LP SAFETY
    # =====================================================

    lp_safety = analyze_lp_safety(
        liquidity
    )

    print_lp_safety(
        liquidity,
        lp_safety,
    )

    # =====================================================
    # HOLDERS
    # =====================================================

    holders, holder_risk = analyze_holders(
        token_address,
        liquidity,
    )

    # =====================================================
    # ABI
    # =====================================================

    print()

    token_abi = None

    try:

        token_abi = get_abi(
            token_address
        )

        if token_abi is not None:

            print(
                "✅ ABI loaded from cache"
            )

        else:

            print(
                "⚠️ Token ABI/source unavailable."
            )

    except Exception as e:

        print(
            f"Token ABI fetch failed: {e}"
        )

    # =====================================================
    # CONTRACT SECURITY
    # =====================================================

    contract_security = analyze_contract_security(
        token_address
    )

    # =====================================================
    # PROXY
    # =====================================================

    (
        bytecode_report,
        proxy_info,
        implementation_info,
    ) = analyze_proxy(
        token_address
    )

    # =====================================================
    # TAX
    # =====================================================

    tax_analysis = analyze_tax_section(
        token_address,
        token_abi,
    )

    # =====================================================
    # OWNERSHIP
    # =====================================================

    ownership_analysis = (
        analyze_ownership_section(
            token_address,
            token_abi,
        )
    )

    # =====================================================
    # TRADING RESTRICTIONS
    # =====================================================

    trading_restrictions = (
        analyze_trading_restrictions_section(
            token_address,
            token_abi,
        )
    )

    # =====================================================
    # TRADE SAFETY
    # =====================================================

    trade_safety = (
        analyze_trade_safety_section(
            token_address,
            token_abi,
            tax_analysis,
        )
    )

    # =====================================================
    # TRADE SIMULATION
    # =====================================================

    simulation = (
        analyze_trade_simulation_section(
            token_address,
            liquidity,
        )
    )

    # =====================================================
    # HONEYPOT
    # =====================================================

    honeypot = analyze_honeypot_section(
        token_address,
        liquidity,
        holders,
    )

    # =====================================================
    # DEEP ROUTER SIMULATION
    # =====================================================

    swap_simulation = (
        analyze_deep_swap_section(
            token_address,
            liquidity,
            holders,
        )
    )

    # =====================================================
    # OVERALL RISK
    # =====================================================

    print_section(
        "OVERALL RISK",
        "🛡️"
    )

    try:

        overall = calculate_overall_risk(
            liquidity=liquidity,
            lp_safety=lp_safety,
            holder_risk=holder_risk,
            contract_security=contract_security,
            trade_safety=trade_safety,
            trade_simulation=simulation,
            honeypot=honeypot,
            tax_analysis=tax_analysis,
            ownership=ownership_analysis,
            trading_limits=trading_restrictions,
            proxy_info=proxy_info,
            implementation_info=implementation_info,
            swap_simulation=swap_simulation,
        )

    except Exception as e:

        overall = {
            "score": 100,
            "risk": "HIGH",
            "warnings": [
                f"Overall risk calculation failed: {e}"
            ],
            "positives": [],
        }

    # =====================================================
    # PROXY WARNING
    #
    # Only add proxy information here if the overall engine
    # did not already include it.
    # =====================================================

    try:

        if proxy_info.get(
            "detected"
        ):

            implementation = proxy_info.get(
                "implementation"
            )

            proxy_warning = (
                "Token uses an "
                f"{proxy_info.get('type', 'supported')} proxy."
            )

            implementation_warning = None

            if implementation:

                implementation_warning = (
                    "Proxy implementation: "
                    f"{implementation}"
                )

            overall.setdefault(
                "warnings",
                []
            )

            if (
                proxy_warning
                not in overall["warnings"]
            ):

                # Only add if the overall engine hasn't
                # already reported the proxy.
                overall["warnings"].append(
                    proxy_warning
                )

            if (
                implementation_warning
                and implementation_warning
                not in overall["warnings"]
            ):

                overall["warnings"].append(
                    implementation_warning
                )

    except Exception:

        pass

    # =====================================================
    # REMOVE DUPLICATE WARNINGS
    # =====================================================

    if isinstance(
        overall,
        dict,
    ):

        warnings = overall.get(
            "warnings",
            []
        )

        positives = overall.get(
            "positives",
            []
        )

        if isinstance(
            warnings,
            list,
        ):

            overall["warnings"] = list(
                dict.fromkeys(
                    warnings
                )
            )

        if isinstance(
            positives,
            list,
        ):

            overall["positives"] = list(
                dict.fromkeys(
                    positives
                )
            )

    # =====================================================
    # FINAL REPORT
    # =====================================================

    print(
        f"Risk score: "
        f"{overall.get('score', 100)}/100"
    )

    print(
        f"Overall risk: "
        f"{overall.get('risk', 'HIGH')}"
    )

    warnings = overall.get(
        "warnings",
        []
    )

    if warnings:

        print()
        print(
            "⚠️ Warnings:"
        )

        for warning in warnings:

            print(
                f"- {warning}"
            )

    positives = overall.get(
        "positives",
        overall.get(
            "positive_signals",
            [],
        )
    )

    if positives:

        print()
        print(
            "✅ Positive signals:"
        )

        for positive in positives:

            print(
                f"- {positive}"
            )

    print()
    print(
        "=" * 50
    )


# =========================================================
# ENTRY POINT
# =========================================================

def main():

    arguments = sys.argv[1:]

    deep = (
        "--deep"
        in arguments
    )

    token_arguments = [
        argument
        for argument in arguments
        if argument != "--deep"
    ]

    if len(
        token_arguments
    ) != 1:

        print(
            "Usage:"
        )

        print(
            "python3 scanner.py <TOKEN_ADDRESS>"
        )

        print(
            "python3 scanner.py <TOKEN_ADDRESS> --deep"
        )

        sys.exit(1)

    token = token_arguments[0]

    global DEEP_SCAN

    DEEP_SCAN = deep

    try:

        checksum_token = (
            Web3.to_checksum_address(
                token
            )
        )

    except Exception:

        print(
            "❌ Invalid token address."
        )

        sys.exit(1)

    try:

        scan_token(
            checksum_token
        )

    except KeyboardInterrupt:

        print()
        print(
            "⚠️ Scan interrupted."
        )

        sys.exit(130)

    except Exception as e:

        print()
        print(
            "❌ Scanner failed:"
        )

        print(
            str(e)
        )

        sys.exit(1)


if __name__ == "__main__":

    main()