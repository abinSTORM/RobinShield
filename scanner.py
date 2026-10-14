import json
import os
import sys
from datetime import datetime, timezone


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
from analysis.token_identity import analyze_token_identity
from engines.admin_control_audit import analyze_admin_controls
from analysis.deployer_history import analyze_deployer_history


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


def _merge_abis(*abis):
    merged = []
    seen = set()
    for abi in abis:
        if not isinstance(abi, list):
            continue
        for item in abi:
            if not isinstance(item, dict):
                continue
            key = (
                item.get("type"),
                item.get("name"),
                tuple(value.get("type") for value in item.get("inputs", []) if isinstance(value, dict)),
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)
    return merged


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

    liquidity_usd_status = liquidity.get("liquidity_usd_status", "CALCULATED")
    if liquidity_usd_status == "NOT_CALCULATED_V3_RANGE_VALUATION":
        liquidity_usd_display = "NOT CALCULATED (V3 position-range valuation unavailable)"
    elif liquidity_usd_status == "ESTIMATED_DEXSCREENER":
        liquidity_usd_display = f"${liquidity.get('liquidity_usd', 0)} (DexScreener estimate)"
    else:
        liquidity_usd_display = f"${liquidity.get('liquidity_usd', 0)}"
    print(f"Liquidity USD: {liquidity_usd_display}")

    if liquidity_usd_status == "NOT_CALCULATED_V3_RANGE_VALUATION":
        print("Total discovered liquidity USD: NOT CALCULATED (V3 position-range valuation unavailable)")
    elif any(
        pool.get("liquidity_usd_status") == "ESTIMATED_DEXSCREENER"
        for pool in liquidity.get("pools", [])
    ):
        print(
            "Total discovered liquidity USD (includes DexScreener estimates): "
            f"${liquidity.get('total_liquidity_usd', liquidity.get('liquidity_usd', 0))}"
        )
    else:
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

        if pool.get("v3_liquidity") is not None:
            print(
                f"  V3 active liquidity at current price: "
                f"{pool.get('v3_liquidity')}"
            )
            print(
                f"  Active liquidity status: "
                f"{pool.get('active_liquidity_status', 'UNKNOWN')}"
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

        if pool.get("liquidity_usd_status") == "NOT_CALCULATED_V3_RANGE_VALUATION":
            print("  Liquidity USD: NOT CALCULATED (V3 position-range valuation unavailable)")
        elif pool.get("liquidity_usd_status") == "ESTIMATED_DEXSCREENER":
            print(
                "  Liquidity USD (DexScreener estimate): "
                f"${pool.get('liquidity_usd', 0)}"
            )
        else:
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
        "lock_status_verified": False,
        "holder_distribution": None,
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

    if str(liquidity.get("version", "")).upper() == "V3":
        lp_safety.update({
            "method": "UNISWAP_V3_POSITION_NFT_ANALYSIS",
            "reason": (
                "Uniswap V3 liquidity is held in NFT positions; "
                "the V2 LP-token burn calculation does not apply. "
                "Position ownership and unlockability were not analyzed."
            ),
            "warnings": [
                "Uniswap V3 position ownership and lock status remain unknown."
            ],
        })
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

    if burn_percentage is None:
        burn_percentage_display = "UNKNOWN"
    elif 0 < float(burn_percentage) < 0.0001:
        burn_percentage_display = "<0.0001"
    else:
        burn_percentage_display = f"{float(burn_percentage):g}"

    active_lp = lp_safety.get(
        "active_lp"
    )

    print(
        f"Burned LP: "
        f"{burned_lp if burned_lp is not None else 'UNKNOWN'}"
    )

    print(
        f"Burn percentage: "
        f"{burn_percentage_display}"
        f"{'%' if burn_percentage is not None else ''}"
    )

    print(
        f"LP outside recognized burn addresses: "
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

    holder_distribution = lp_safety.get("holder_distribution")
    if isinstance(holder_distribution, dict):
        print(
            "LP holder coverage: "
            f"{holder_distribution.get('status', 'UNKNOWN')} "
            f"({holder_distribution.get('accounted_percentage') or 0:.4f}%)"
        )
        print(
            "LP held by EOAs: "
            f"{holder_distribution.get('eoa_percentage_of_supply') or 0:.4f}%"
        )
        for holder in holder_distribution.get("holders", [])[:5]:
            print(
                "  Holder: "
                f"{holder.get('address')} "
                f"({holder.get('holder_type')}, "
                f"{holder.get('percentage_of_supply') or 0:.4f}% LP)"
            )


# =========================================================
# HOLDER ANALYSIS
# =========================================================

def analyze_holders(
    token_address,
    liquidity=None,
    deep=False,
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
            token_address,
            deep=deep,
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

    contract_result = None

    try:

        contract_result = security_scan(
            token_address
        )

    except Exception as e:

        print(
            f"Security analysis failed: {e}"
        )

        return None

    if not contract_result:

        print(
            "Contract security analysis unavailable."
        )

        return contract_result

    print(
        "ℹ️ Explorer-verified source/ABI availability does not certify that a token is safe or that future sells will succeed."
    )

    # =====================================================
    # NORMALIZE SECURITY REPORT
    # =====================================================

    if isinstance(
        contract_result,
        dict,
    ):

        contract_security = contract_result.get(
            "security",
            [],
        )

        bytecode_result = contract_result.get(
            "bytecode",
            {},
        )

    else:

        # Backward compatibility if the engine ever
        # returns the old list format.

        contract_security = contract_result

        bytecode_result = {}

    if not isinstance(
        contract_security,
        list,
    ):

        contract_security = []

    # =====================================================
    # PRINT SECURITY DETECTORS
    # =====================================================

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

        # -------------------------------------------------
        # BYTECODE BEHAVIOR DETAILS
        # -------------------------------------------------

        if check == "Bytecode Behavior":

            details = item.get(
                "details",
                {},
            )

            if isinstance(
                details,
                dict,
            ):

                print(
                    "Delegatecall : "
                    f"{details.get('delegatecall', 0)}"
                )

                print(
                    "Selfdestruct : "
                    f"{details.get('selfdestruct', 0)}"
                )

                print(
                    "TX.origin : "
                    f"{details.get('tx_origin', 0)}"
                )

                print(
                    "External calls : "
                    f"{details.get('external_calls', 0)}"
                )

                print(
                    "Contract creation : "
                    f"{details.get('contract_creation', 0)}"
                )

                print(
                    "Storage writes : "
                    f"{details.get('storage_writes', 0)}"
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

                # =========================================
                # IMPLEMENTATION EVM BEHAVIOR
                # =========================================

                behavior = (
                    implementation_analysis.get(
                        "behavior",
                        {}
                    )
                )

                if isinstance(
                    behavior,
                    dict,
                ):

                    print()
                    print(
                        "EVM Behavior"
                    )

                    print(
                        f"Delegatecall: "
                        f"{behavior.get('delegatecall_count', 0)}"
                    )

                    print(
                        f"Selfdestruct: "
                        f"{behavior.get('selfdestruct_count', 0)}"
                    )

                    print(
                        f"TX.origin: "
                        f"{behavior.get('tx_origin_count', 0)}"
                    )

                    print(
                        f"External calls: "
                        f"{behavior.get('external_calls', 0)}"
                    )

                    print(
                        f"Contract creation: "
                        f"{behavior.get('contract_creation', 0)}"
                    )

                    print(
                        f"Storage writes: "
                        f"{behavior.get('storage_writes', 0)}"
                    )

                    print(
                        f"Behavior confidence: "
                        f"{behavior.get('confidence', 'LOW')}"
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

    pattern_reports = [("Token/proxy bytecode", bytecode_report.get("bytecode_patterns", {}))]
    if isinstance(implementation_analysis, dict):
        pattern_reports.append((
            "Implementation bytecode",
            implementation_analysis.get("bytecode_patterns", {}),
        ))

    print()
    print("Bytecode Pattern Review")
    for source, report in pattern_reports:
        matches = report.get("matches", []) if isinstance(report, dict) else []
        print(f"{source}: {len(matches)} indicator(s)")
        for match in matches:
            evidence = ", ".join(match.get("evidence", []))
            print(
                f"  [{match.get('severity', 'INFO')}] {match.get('id')}: "
                f"{match.get('title')} — {match.get('description')}"
            )
            if evidence:
                print(f"    Evidence: {evidence}")
    print(
        "Pattern indicators are not a definitive scam verdict; "
        "review the reported evidence and contract permissions."
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
    liquidity,
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
            liquidity=liquidity,
            deep_scan=DEEP_SCAN,
        )

        print_analysis_header(
            tax_analysis
        )

        dynamic_tax = tax_analysis.get(
            "dynamic_tax",
            False,
        )

        tax_setters = tax_analysis.get(
            "tax_setters",
            [],
        )

        print(
            f"Dynamic tax: "
            f"{'YES' if dynamic_tax else 'NO'}"
        )

        if tax_setters:
            print(
                "Tax setters: "
                + ", ".join(tax_setters)
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

        tax_expiration_time = tax_analysis.get(
            "tax_expiration_time"
        )

        if tax_expiration_time is not None:
            print(
                f"Tax expiration time: "
                f"{tax_expiration_time}"
            )

        tax_expiration_active = tax_analysis.get(
            "tax_expiration_active"
        )

        if tax_expiration_active is not None:
            print(
                "Tax expiration active: "
                f"{'YES' if tax_expiration_active else 'NO'}"
            )

        tax_state_functions = tax_analysis.get(
            "tax_state_functions",
            [],
        )

        if tax_state_functions:
            print(
                "Tax state functions: "
                + ", ".join(
                    tax_state_functions
                )
            )

        tax_state = tax_analysis.get(
            "tax_state"
        )

        tax_state_name = tax_analysis.get(
            "tax_state_name"
        )

        if tax_state is not None:
            if tax_state_name is not None:
                print(
                    f"Tax state: "
                    f"{tax_state} ({tax_state_name})"
                )
            else:
                print(
                    f"Tax state: {tax_state}"
                )

        time_dependent_tax = tax_analysis.get(
            "time_dependent_tax"
        )

        if time_dependent_tax is not None:
            print(
                "Time-dependent tax: "
                f"{'YES' if time_dependent_tax else 'NO'}"
            )

        tax_expiration_status = tax_analysis.get(
            "tax_expiration_status"
        )

        if tax_expiration_status is not None:
            print(
                f"Tax expiration status: "
                f"{tax_expiration_status}"
            )

        tax_expiration_behavior = tax_analysis.get(
            "tax_expiration_behavior",
            {},
        )

        if isinstance(tax_expiration_behavior, dict):
            behavior_tested = tax_expiration_behavior.get(
                "tested",
                False,
            )

            behavior_status = tax_expiration_behavior.get(
                "status",
            )

            if behavior_tested:
                print(
                    "Expiration behavior: "
                    f"{tax_expiration_behavior.get('behavior')}"
                )

                print(
                    "Expiration test status: "
                    f"{behavior_status}"
                )

                print(
                    "State before/after: "
                    f"{tax_expiration_behavior.get('before_state')} / "
                    f"{tax_expiration_behavior.get('after_state')}"
                )

                print(
                    "BUY tax getter before/after: "
                    f"{tax_expiration_behavior.get('before_buy_tax')} / "
                    f"{tax_expiration_behavior.get('after_buy_tax')}"
                )

                print(
                    "SELL tax getter before/after: "
                    f"{tax_expiration_behavior.get('before_sell_tax')} / "
                    f"{tax_expiration_behavior.get('after_sell_tax')}"
                )

                for phase in ("before", "after"):
                    details = tax_expiration_behavior.get(
                        f"{phase}_swap_details",
                        {},
                    )
                    if isinstance(details, dict):
                        buy = details.get("buy", {})
                        sell = details.get("sell", {})
                        print(
                            f"Router swaps {phase} expiration: "
                            f"BUY={'PASS' if buy.get('success') else 'FAIL'} "
                            f"({buy.get('tx_hash') or 'no tx'}), "
                            f"SELL={'PASS' if sell.get('success') else 'FAIL'} "
                            f"({sell.get('tx_hash') or 'no tx'})"
                        )

                if behavior_status == "INCONCLUSIVE":
                    print(
                        "Expiration test reason: "
                        f"{tax_expiration_behavior.get('reason')}"
                    )
                    getter_errors = tax_expiration_behavior.get(
                        "getter_errors",
                        {},
                    )
                    if getter_errors:
                        for function_name, error in getter_errors.items():
                            print(
                                f"Fork getter {function_name} error: {error}"
                            )

            elif behavior_status in ("ERROR", "INCONCLUSIVE"):
                print(
                    f"Expiration behavior test {behavior_status.lower()}: "
                    f"{tax_expiration_behavior.get('reason')}"
                )

            elif behavior_status == "SKIPPED":
                print(
                    "Expiration behavior test: SKIPPED "
                    f"({tax_expiration_behavior.get('reason')})"
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

        owner_value = ownership_analysis.get("owner")
        renounced_value = ownership_analysis.get("ownership_renounced")
        print(f"Current owner: {owner_value or 'UNKNOWN'}")

        print(
            f"Ownership renounced: "
            f"{'YES' if renounced_value is True else 'NO' if renounced_value is False else 'UNKNOWN'}"
        )

        print(
            f"Transfer function detected (not caller permission): "
            f"{ownership_analysis.get('transfer_function_detected')}"
        )

        print(
            f"Renounce function detected (not caller permission): "
            f"{ownership_analysis.get('renounce_function_detected')}"
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

def analyze_supply_section(
    token_address,
    token_abi,
    ownership_analysis=None,
):

    from engines.supply_analysis import (
        analyze_supply,
    )

    print_section(
        "SUPPLY / MINT ANALYSIS",
        "📈"
    )

    supply_analysis = {
        "status": "UNKNOWN",
        "risk": "UNKNOWN",
        "confidence": "LOW",
        "mintable": None,
        "mint_functions": [],
        "supply_controls": [],
        "burn_functions": [],
        "warnings": [],
        "signals": [],
    }

    try:

        supply_analysis = analyze_supply(
            abi=token_abi,
            ownership_analysis=ownership_analysis,
        )

    except Exception as e:

        supply_analysis = {
            "status": "UNKNOWN",
            "risk": "UNKNOWN",
            "confidence": "LOW",
            "mintable": None,
            "mint_functions": [],
            "supply_controls": [],
            "burn_functions": [],
            "warnings": [
                "Supply analysis failed: "
                f"{e}"
            ],
            "signals": [],
        }

    print(
        f"Status: "
        f"{supply_analysis.get('status', 'UNKNOWN')}"
    )

    print(
        f"Risk: "
        f"{supply_analysis.get('risk', 'UNKNOWN')}"
    )

    print(
        f"Confidence: "
        f"{supply_analysis.get('confidence', 'LOW')}"
    )

    mintable = supply_analysis.get(
        "mintable"
    )

    if mintable is not None:

        print(
            f"Mintable: "
            f"{mintable}"
        )

    mint_functions = supply_analysis.get(
        "mint_functions",
        [],
    )

    if mint_functions:

        print(
            "Mint functions: "
            + ", ".join(
                mint_functions
            )
        )

    supply_controls = supply_analysis.get(
        "supply_controls",
        [],
    )

    if supply_controls:

        print(
            "Supply controls: "
            + ", ".join(
                supply_controls
            )
        )

    burn_functions = supply_analysis.get(
        "burn_functions",
        [],
    )

    if burn_functions:

        print(
            "Burn functions: "
            + ", ".join(
                burn_functions
            )
        )

    warnings = supply_analysis.get(
        "warnings",
        [],
    )

    if warnings:

        print(
            "\n⚠️ Warnings:"
        )

        for warning in warnings:

            print(
                f"- {warning}"
            )

    signals = supply_analysis.get(
        "signals",
        [],
    )

    if signals:

        print(
            "\nℹ️ Signals:"
        )

        for signal in signals:

            print(
                f"- {signal}"
            )

    return supply_analysis

def analyze_trading_restrictions_section(
    token_address,
    token_abi,
    ownership_analysis=None,
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

        trading_restrictions = analyze_trading_restrictions(
            token_address,
            token_abi,
            ownership_analysis,
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

        print(
            f"DEBUG Trading restrictions error: {e}"
        )

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
    check_address=None,
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
            check_address=check_address,
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
                    "token_spent"
                ) is not None:

                    print(
                        f"  Token spent: "
                        f"{test.get('token_spent')}"
                    )

                if test.get(
                    "event_token_spent"
                ) is not None:

                    print(
                        f"  Event token spent: "
                        f"{test.get('event_token_spent')}"
                    )

                if test.get(
                    "quote_received"
                ) is not None:

                    print(
                        f"  Quote received: "
                        f"{test.get('quote_received')}"
                    )

                if test.get(
                    "event_quote_received"
                ) is not None:

                    print(
                        f"  Event quote received: "
                        f"{test.get('event_quote_received')}"
                    )

                if test.get(
                    "runtime_token_consumption_percent"
                ) is not None:

                    print(
                        f"  Runtime token consumption: "
                        f"{test.get('runtime_token_consumption_percent'):.4f}%"
                    )

                if test.get(
                    "runtime_sell_observation"
                ):

                    print(
                        f"  Runtime SELL observation: "
                        f"{test.get('runtime_sell_observation')}"
                    )

                if (
                    swap_simulation.get(
                        "runtime_sell_tax"
                    ) is not None
                ):

                    print(
                        f"  Runtime SELL tax: "
                        f"{swap_simulation.get('runtime_sell_tax'):.4f}%"
                    )

                if test.get(
                    "error"
                ):

                    print(
                        f"  Error: "
                        f"{test.get('error')}"
                    )

                if test.get(
                    "error"
                ):

                    print(
                        f"  Error: "
                        f"{test.get('error')}"
                    )

        wallet_sell_test = swap_simulation.get(
            "wallet_specific_sell_test"
        )
        if isinstance(wallet_sell_test, dict):
            print()
            print("Wallet-specific router SELL test")
            print(f"  Wallet: {wallet_sell_test.get('address')}")
            print(f"  Status: {wallet_sell_test.get('status')}")
            print(f"  Balance raw: {wallet_sell_test.get('balance')}")
            print(f"  Amount raw: {wallet_sell_test.get('amount_in')}")
            if wallet_sell_test.get("error"):
                print(f"  Detail: {wallet_sell_test.get('error')}")

        print_warnings(
            swap_simulation
        )

        if (
            swap_simulation.get(
                "runtime_buy_tax"
            ) is not None
        ):

            print(
                f"Runtime BUY tax: "
                f"{swap_simulation.get('runtime_buy_tax'):.4f}%"
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
    expected_name=None,
    expected_symbol=None,
    check_address=None,
):

    token_address = Web3.to_checksum_address(
        token_address
    )
    if check_address:
        check_address = Web3.to_checksum_address(check_address)

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
            token_address,
            deep_scan=DEEP_SCAN,
        )

    except Exception as e:

        liquidity = {
            "found": False,
            "analysis_status": "UNAVAILABLE",
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
            "risk": "UNKNOWN",
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
        deep=DEEP_SCAN,
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

    implementation_abi = None
    implementation_address = (
        proxy_info.get("implementation")
        if isinstance(proxy_info, dict)
        else None
    )
    if implementation_address:
        try:
            implementation_abi = get_abi(implementation_address)
        except Exception:
            implementation_abi = None

    # A proxy dispatches calls through its implementation. When the proxy
    # address has no explorer ABI, use the verified implementation ABI for
    # function analysis while still calling the proxy address on-chain.
    analysis_abi = _merge_abis(token_abi, implementation_abi)
    combined_analysis_abi = analysis_abi

    # =====================================================
    # TAX
    # =====================================================

    tax_analysis = analyze_tax_section(
        token_address,
        analysis_abi,
        liquidity,
    )

    # =====================================================
    # OWNERSHIP
    # =====================================================

    ownership_analysis = (
        analyze_ownership_section(
            token_address,
            analysis_abi,
        )
    )

    token_identity = analyze_token_identity(
        token_address,
        abi=combined_analysis_abi,
        expected_name=expected_name,
        expected_symbol=expected_symbol,
        proxy=proxy_info,
    )

    print_section(
        "TOKEN IDENTITY / IMPERSONATION REVIEW",
        "🏷️",
    )
    print(f"On-chain name: {token_identity.get('name') or 'UNAVAILABLE'}")
    print(f"On-chain symbol: {token_identity.get('symbol') or 'UNAVAILABLE'}")
    print(f"Expected name comparison: {token_identity['name_comparison']['status']}")
    print(f"Expected symbol comparison: {token_identity['symbol_comparison']['status']}")
    for warning in token_identity.get("warnings", []):
        print(f"⚠️ {warning}")

    deployer_history = analyze_deployer_history(token_address)
    print_section("DEPLOYER HISTORY / FUNDING CONTEXT", "🧾")
    print(f"Explorer evidence: {deployer_history.get('status', 'UNAVAILABLE')}")
    if deployer_history.get("deployer"):
        print(
            f"Creation sender: {deployer_history['deployer']} "
            f"({deployer_history.get('deployer_type', 'UNKNOWN')})"
        )
    if deployer_history.get("prior_contract_creations") is not None:
        qualifier = "complete indexed history" if deployer_history.get("history_complete") else "partial history; lower bound"
        print(
            "Earlier contract creations found: "
            f"{deployer_history['prior_contract_creations']} ({qualifier})"
        )
    funding = deployer_history.get("recent_funding")
    if funding:
        print(
            "Recent inbound funding: observed within 24 hours before deployment; "
            f"sender {funding.get('from') or 'unresolved'}; this is context, not proof of coordination."
        )
    else:
        print(
            "Recent inbound funding: "
            + ("none found in indexed data" if deployer_history.get("funding_history_complete") else "UNKNOWN / not fully checked")
        )
    for signal in deployer_history.get("signals", []):
        print(f"ℹ️ {signal}")
    for warning in deployer_history.get("warnings", []):
        print(f"⚠️ {warning}")

    admin_control_audit = analyze_admin_controls(
        token_address,
        abi=combined_analysis_abi,
        ownership=ownership_analysis,
        proxy=proxy_info,
        bytecode_report=bytecode_report,
        check_address=check_address,
    )

    print_section(
        "ADMIN CONTROL / FUTURE SELL-RISK REVIEW",
        "🛡️",
    )
    print(f"Status: {admin_control_audit['status']}")
    detected_control_groups = [
        group
        for group, functions in admin_control_audit.get("controls", {}).items()
        if functions
    ]
    print(
        "Detected control groups: "
        + (", ".join(detected_control_groups) or "none recognized")
    )
    print(f"Role/admin functions: {', '.join(admin_control_audit['role_functions']) or 'none recognized'}")
    print(f"Authorization: {admin_control_audit['authorization']}")
    if admin_control_audit.get("address_check"):
        print(f"Checked wallet: {check_address}")
        for getter, value in admin_control_audit["address_check"]["results"].items():
            print(f"{getter}: {value}")
    for warning in admin_control_audit.get("warnings", []):
        print(f"⚠️ {warning}")

    # =====================================================
    # TRADING RESTRICTIONS
    # =====================================================

    trading_restrictions = (
        analyze_trading_restrictions_section(
            token_address,
            analysis_abi,
            ownership_analysis,
        )
    )
    
    # =====================================================
    # SUPPLY / MINT ANALYSIS
    # =====================================================

    supply_analysis = (
        analyze_supply_section(
            token_address,
            analysis_abi,
            ownership_analysis,
        )
    )

    # =====================================================
    # INITIAL MINT / DISTRIBUTION
    # =====================================================

    from analysis.initial_distribution import (
        analyze_initial_distribution,
    )

    print_section(
        "INITIAL MINT / DISTRIBUTION",
        "🎯"
    )

    initial_distribution = (
        analyze_initial_distribution(
            token_address
        )
    )

    print(
        f"Status: "
        f"{initial_distribution.get('status', 'UNKNOWN')}"
    )

    print(
        f"Risk: "
        f"{initial_distribution.get('risk', 'UNKNOWN')}"
    )

    print(
        f"Confidence: "
        f"{initial_distribution.get('confidence', 'LOW')}"
    )

    print(
        f"Mint found: "
        f"{initial_distribution.get('mint_found', False)}"
    )

    print(
        f"Mint recipients: "
        f"{initial_distribution.get('recipient_count', 0)}"
    )

    largest_percentage = (
        initial_distribution.get(
            "largest_percentage"
        )
    )

    if largest_percentage is not None:

        print(
            f"Largest observed mint recipient: "
            f"{largest_percentage:.2f}%"
        )

    top5_percentage = (
        initial_distribution.get(
            "top5_percentage"
        )
    )

    if top5_percentage is not None:

        print(
            f"Top 5 observed mint recipients: "
            f"{top5_percentage:.2f}%"
        )

    earliest_block = (
        initial_distribution.get(
            "earliest_block"
        )
    )

    if earliest_block is not None:

        print(
            f"Earliest observed mint block: "
            f"{earliest_block}"
        )

    warnings = initial_distribution.get(
        "warnings",
        []
    )

    if warnings:

        print(
            "\n⚠️ Warnings:"
        )

        for warning in warnings:

            print(
                f"- {warning}"
            )

    signals = initial_distribution.get(
        "signals",
        []
    )

    if signals:

        print(
            "\nℹ️ Signals:"
        )

        for signal in signals:

            print(
                f"- {signal}"
            )

    # =====================================================
    # TRADE SAFETY
    # =====================================================

    trade_safety = (
        analyze_trade_safety_section(
            token_address,
            analysis_abi,
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
            check_address=check_address,
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
            holders=holders,
            holder_risk=holder_risk,
            contract_security=contract_security,
            trade_safety=trade_safety,
            trade_simulation=simulation,
            honeypot=honeypot,
            swap_simulation=swap_simulation,
            tax_analysis=tax_analysis,
            ownership=ownership_analysis,
            trading_limits=trading_restrictions,
            proxy_info=proxy_info,
            implementation_info=implementation_info,
            admin_control_audit=admin_control_audit,
            token_identity=token_identity,
            deployer_history=deployer_history,
            abi_available=token_abi is not None,
        )

    except Exception as e:

        overall = {
            "score": 100,
            "risk": "HIGH",
            "score_band": "HIGH",
            "assessment": "INCONCLUSIVE",
            "coverage_confidence": "LOW",
            "unresolved_checks": ["overall risk calculation failed"],
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

            proxy_type = str(
                proxy_info.get(
                    "type",
                    "supported",
                )
            )

            if proxy_type.upper() == "ERC-1167":

                proxy_warning = (
                    "Token uses an ERC-1167 minimal proxy."
                )

            else:

                proxy_warning = (
                    f"Token uses an {proxy_type} proxy."
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

        for finding in (
            admin_control_audit.get("warnings", [])
            + token_identity.get("warnings", [])
            + deployer_history.get("warnings", [])
        ):
            if finding not in overall.setdefault("warnings", []):
                overall["warnings"].append(finding)

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
        f"Overall risk severity: {overall.get('score', 100)}/100 "
        f"(score band {overall.get('score_band', overall.get('risk', 'HIGH'))})"
    )

    if overall.get("assessment"):
        print(
            f"Overall assessment: {overall.get('assessment')} "
            f"(coverage confidence {overall.get('coverage_confidence', 'LOW')})"
        )
        for unresolved in overall.get("unresolved_checks", []):
            print(f"  Unavailable: {unresolved}")
    else:
        print(f"Overall assessment: {overall.get('risk', 'HIGH')}")

    score_band = str(overall.get("score_band", overall.get("risk", "UNKNOWN"))).upper()
    assessment = str(overall.get("assessment", "")).upper()
    dimensions = overall.get("risk_dimensions", {})
    market_dimension = dimensions.get("market_and_exit_risk", {}) if isinstance(dimensions, dict) else {}
    contract_dimension = dimensions.get("contract_and_sellability", {}) if isinstance(dimensions, dict) else {}
    if (
        score_band in ("CRITICAL", "HIGH")
        and market_dimension.get("status") == "HIGH"
        and contract_dimension.get("status") in ("REVIEW", "PASS_FOR_TESTED_STATE")
    ):
        print("Beginner guidance: High market/exit risk. The scan did not prove this token is a scam; thin liquidity, concentrated holdings, or withdrawable LP can make trading risky.")
    elif score_band in ("CRITICAL", "HIGH"):
        print("Beginner guidance: Avoid buying this token based on this scan; investigate the listed risks first.")
    elif assessment in ("INCONCLUSIVE", "LIMITED"):
        print("Beginner guidance: This scan could not verify important safety checks. Do not treat the token as safe.")
    else:
        print("Beginner guidance: This scan is not a guarantee of safety; verify the evidence before making a decision.")
    print("RobinShield reports risk; it does not execute or block trades on external wallets or exchanges.")
    print("The overall score measures severity of detected risks; it is not a probability that the token is a scam.")

    if isinstance(dimensions, dict):
        market = dimensions.get("market_and_exit_risk", {})
        contract = dimensions.get("contract_and_sellability", {})
        if isinstance(market, dict) and isinstance(contract, dict):
            print()
            print("Risk dimensions:")
            print(
                "- Market / exit risk: "
                f"{market.get('status', 'UNKNOWN')} "
                f"({market.get('severity_points', 0)} weighted points). "
                f"{market.get('summary', '')}"
            )
            print(
                "- Contract / sellability: "
                f"{contract.get('status', 'UNKNOWN')}. "
                f"{contract.get('summary', '')}"
            )
            print(
                "  Tested buy/sell: "
                f"honeypot={contract.get('tested_honeypot_status', 'UNKNOWN')}, "
                f"deep router={contract.get('deep_router_swap_status', 'UNKNOWN')}; "
                f"admin controls={contract.get('admin_control_status', 'UNKNOWN')}"
            )

    breakdown = overall.get(
        "breakdown",
        {},
    )

    if isinstance(
        breakdown,
        dict,
    ) and breakdown:

        print()
        print(
            "🧮 Risk evidence breakdown:"
        )

        for name, value in breakdown.items():

            if name == "Evidence-based floors":

                continue

            try:

                value = int(
                    value
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

            print(
                f"- {name}: +{value}"
            )

        print(f"- CAPPED SCORE (0–100): {overall.get('score', 0)}")

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


    holder_snapshot = {
        "source": (
            holders.get("_source")
            if isinstance(holders, dict)
            else None
        ),
        "verified": bool(
            holders.get("_verified", False)
            if isinstance(holders, dict)
            else False
        ),
        "complete": bool(
            holders.get("_complete", False)
            if isinstance(holders, dict)
            else False
        ),
        "candidate_count": (
            holders.get("_candidate_count")
            if isinstance(holders, dict)
            else None
        ),
        "holder_count": (
            holders.get("_holder_count")
            if isinstance(holders, dict)
            else 0
        ),
        "records": (
            holders.get("items", [])
            if isinstance(holders, dict)
            else []
        ),
        "risk": holder_risk,
    }

    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat().replace(
            "+00:00",
            "Z",
        ),
        "network": {
            "name": "Robinhood Chain",
            "chain_id": 4663,
        },
        "token_address": token_address,
        "verification": {
            "token_abi_available": token_abi is not None,
            "implementation_abi_available": implementation_abi is not None,
            "implementation_source_reported_verified": (
                implementation_info.get("verified")
                if isinstance(implementation_info, dict)
                else None
            ),
            "meaning": "Explorer source/ABI availability is not a safety guarantee; behavior and sellability are assessed separately and remain limited to the checks performed.",
        },
        "token_identity": token_identity,
        "deployer_history": deployer_history,
        "mode": "deep" if DEEP_SCAN else "normal",
        "analyses": {
            "liquidity": liquidity,
            "lp_safety": lp_safety,
            "holder_distribution": holder_snapshot,
            "contract_security": contract_security,
            "bytecode": bytecode_report,
            "proxy": proxy_info,
            "implementation": implementation_info,
            "tax": tax_analysis,
            "ownership": ownership_analysis,
            "trading_restrictions": trading_restrictions,
            "admin_control_audit": admin_control_audit,
            "deployer_history": deployer_history,
            "supply": supply_analysis,
            "initial_distribution": initial_distribution,
            "trade_safety": trade_safety,
            "trade_simulation": simulation,
            "honeypot": honeypot,
            "deep_swap_simulation": swap_simulation,
        },
        "overall": overall,
    }


def _json_default(value):

    if isinstance(
        value,
        (bytes, bytearray, memoryview),
    ):

        return "0x" + bytes(value).hex()

    if hasattr(
        value,
        "hex",
    ) and callable(
        value.hex
    ):

        try:

            return value.hex()

        except Exception:

            pass

    return str(value)


def write_json_report(
    report,
    output_path,
):

    output_path = os.path.abspath(
        os.path.expanduser(
            output_path
        )
    )

    output_directory = os.path.dirname(
        output_path
    )

    os.makedirs(
        output_directory,
        exist_ok=True,
    )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as output_file:

        json.dump(
            report,
            output_file,
            indent=2,
            sort_keys=True,
            default=_json_default,
        )

        output_file.write(
            "\n"
        )

    return output_path


# =========================================================
# ENTRY POINT
# =========================================================

def main():

    arguments = sys.argv[1:]

    deep = (
        "--deep"
        in arguments
    )

    token_arguments = []
    json_output = None
    expected_name = None
    expected_symbol = None
    check_address = None
    index = 0

    while index < len(
        arguments
    ):

        argument = arguments[index]

        if argument == "--deep":

            index += 1
            continue

        if argument in (
            "--json-output",
            "--json-out",
        ):

            if index + 1 >= len(
                arguments
            ):

                print(
                    f"❌ {argument} requires a file path."
                )

                sys.exit(1)

            json_output = arguments[
                index + 1
            ]

            index += 2
            continue

        if argument in ("--expect-name", "--expect-symbol", "--check-address"):
            if index + 1 >= len(arguments):
                print(f"❌ {argument} requires a value.")
                sys.exit(1)
            if argument == "--expect-name":
                expected_name = arguments[index + 1]
            elif argument == "--expect-symbol":
                expected_symbol = arguments[index + 1]
            else:
                check_address = arguments[index + 1]
            index += 2
            continue

        if argument.startswith("--expect-name="):
            expected_name = argument.split("=", 1)[1]
            index += 1
            continue

        if argument.startswith("--expect-symbol="):
            expected_symbol = argument.split("=", 1)[1]
            index += 1
            continue

        if argument.startswith("--check-address="):
            check_address = argument.split("=", 1)[1]
            index += 1
            continue

        if argument.startswith(
            "--json-output="
        ):

            json_output = argument.split(
                "=",
                1,
            )[1]

            index += 1
            continue

        token_arguments.append(
            argument
        )

        index += 1

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

        print(
            "python3 scanner.py <TOKEN_ADDRESS> --json-output <FILE>"
        )

        print(
            "python3 scanner.py <TOKEN_ADDRESS> --expect-name <NAME> --expect-symbol <SYMBOL>"
        )

        print(
            "python3 scanner.py <TOKEN_ADDRESS> --check-address <WALLET_ADDRESS>"
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

        report = scan_token(
            checksum_token,
            expected_name=expected_name,
            expected_symbol=expected_symbol,
            check_address=check_address,
        )

        if json_output:

            output_path = write_json_report(
                report,
                json_output,
            )

            print()
            print(
                f"JSON report saved: {output_path}"
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
