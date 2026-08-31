from core.abi import get_abi
from core.function_index import build_function_index
from core.bytecode import analyze_bytecode

from detectors.mint_detector import scan as mint_scan
from detectors.tax_detector import scan as tax_scan
from detectors.ownership_detector import scan as ownership_scan
from detectors.blacklist_detector import scan as blacklist_scan
from detectors.pause_detector import scan as pause_scan

from engines.trading_controls import (
    analyze_trading_controls
)


# =========================================================
# SAFE DETECTOR RESULT
# =========================================================

def _normalize_report_item(
    item,
    default_check="Security Check"
):
    """
    Ensure every detector result is a dictionary.

    Some detectors may return malformed data or a string.
    Never allow that to crash the scanner.
    """

    if isinstance(item, dict):

        result = dict(item)

        if "check" not in result:
            result["check"] = default_check

        if "status" not in result:
            result["status"] = "UNKNOWN"

        if "confidence" not in result:
            result["confidence"] = "LOW"

        if "reason" not in result:
            result["reason"] = (
                "Detector returned no reason."
            )

        return result

    return {
        "check": default_check,
        "status": "UNKNOWN",
        "confidence": "LOW",
        "reason": (
            "Security detector returned an unexpected "
            f"result type: {type(item).__name__}."
        ),
    }


# =========================================================
# ABI ANALYSIS
# =========================================================

def _analyze_abi(functions):
    """
    Run all existing ABI-based security detectors.
    """

    report = []

    detectors = [
        (
            "Mint Function",
            mint_scan,
        ),
        (
            "Tax Functions",
            tax_scan,
        ),
        (
            "Ownership",
            ownership_scan,
        ),
        (
            "Blacklist",
            blacklist_scan,
        ),
        (
            "Pause Functions",
            pause_scan,
        ),
        (
            "Trading Controls",
            analyze_trading_controls,
        ),
    ]

    for name, detector in detectors:

        try:

            result = detector(
                functions
            )

            report.append(
                _normalize_report_item(
                    result,
                    name,
                )
            )

        except Exception as e:

            report.append(
                {
                    "check": name,
                    "status": "UNKNOWN",
                    "confidence": "LOW",
                    "reason": (
                        "Security detector failed: "
                        f"{e}"
                    ),
                }
            )

    return report


# =========================================================
# BYTECODE ANALYSIS
# =========================================================

def _analyze_bytecode(address):
    """
    Analyze contract bytecode when ABI is unavailable.
    """

    try:

        result = analyze_bytecode(
            address
        )

    except Exception as e:

        return [
            {
                "check": "Bytecode Analysis",
                "status": "FAIL",
                "confidence": "HIGH",
                "reason": (
                    "Contract bytecode analysis failed: "
                    f"{e}"
                ),
            }
        ]

    if not isinstance(result, dict):

        return [
            {
                "check": "Bytecode Analysis",
                "status": "FAIL",
                "confidence": "HIGH",
                "reason": (
                    "Bytecode analyzer returned an "
                    "unexpected result."
                ),
            }
        ]

    if not result.get("available"):

        return [
            {
                "check": "Bytecode Analysis",
                "status": "FAIL",
                "confidence": "HIGH",
                "reason": (
                    "Contract bytecode could not be retrieved."
                ),
            }
        ]

    reports = []

    # =====================================================
    # BYTECODE
    # =====================================================

    reports.append(
        {
            "check": "Bytecode Analysis",
            "status": "PASS",
            "confidence": result.get(
                "confidence",
                "MEDIUM",
            ),
            "reason": (
                "Contract bytecode retrieved successfully "
                f"({result.get('bytecode_size', 0)} bytes)."
            ),
        }
    )

    groups = result.get(
        "groups",
        {},
    )

    if not isinstance(groups, dict):
        groups = {}

    # =====================================================
    # MINT
    # =====================================================

    mint_functions = groups.get(
        "mint",
        [],
    )

    if not isinstance(
        mint_functions,
        list,
    ):
        mint_functions = []

    if mint_functions:

        reports.append(
            {
                "check": "Mint Function",
                "status": "WARNING",
                "confidence": "LOW",
                "reason": (
                    "Mint-related selectors were detected "
                    "in the contract bytecode."
                ),
            }
        )

    else:

        reports.append(
            {
                "check": "Mint Function",
                "status": "PASS",
                "confidence": "LOW",
                "reason": (
                    "No recognized mint selector was detected "
                    "in the analyzed bytecode."
                ),
            }
        )

    # =====================================================
    # TAX
    # =====================================================

    tax_functions = groups.get(
        "tax",
        [],
    )

    if not isinstance(
        tax_functions,
        list,
    ):
        tax_functions = []

    if tax_functions:

        names = []

        for item in tax_functions:

            if isinstance(item, dict):

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

        reports.append(
            {
                "check": "Tax Functions",
                "status": "INFO",
                "confidence": "LOW",
                "reason": (
                    "Tax/fee-related selectors detected: "
                    + ", ".join(names)
                ),
            }
        )

    else:

        reports.append(
            {
                "check": "Tax Functions",
                "status": "PASS",
                "confidence": "LOW",
                "reason": (
                    "No recognized tax/fee selectors were "
                    "detected in the bytecode."
                ),
            }
        )

    # =====================================================
    # OWNERSHIP
    # =====================================================

    ownership_functions = groups.get(
        "ownership",
        [],
    )

    if not isinstance(
        ownership_functions,
        list,
    ):
        ownership_functions = []

    if ownership_functions:

        names = []

        for item in ownership_functions:

            if isinstance(item, dict):

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

        reports.append(
            {
                "check": "Ownership",
                "status": "INFO",
                "confidence": "MEDIUM",
                "reason": (
                    "Ownership-related selectors detected: "
                    + ", ".join(names)
                ),
            }
        )

    else:

        reports.append(
            {
                "check": "Ownership",
                "status": "PASS",
                "confidence": "LOW",
                "reason": (
                    "No recognized ownership selectors "
                    "were detected."
                ),
            }
        )

    # =====================================================
    # BLACKLIST
    # =====================================================

    blacklist_functions = groups.get(
        "blacklist",
        [],
    )

    if not isinstance(
        blacklist_functions,
        list,
    ):
        blacklist_functions = []

    if blacklist_functions:

        names = []

        for item in blacklist_functions:

            if isinstance(item, dict):

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

        reports.append(
            {
                "check": "Blacklist",
                "status": "WARNING",
                "confidence": "MEDIUM",
                "reason": (
                    "Blacklist-related selectors detected: "
                    + ", ".join(names)
                ),
            }
        )

    else:

        reports.append(
            {
                "check": "Blacklist",
                "status": "PASS",
                "confidence": "LOW",
                "reason": (
                    "No recognized blacklist selectors "
                    "were detected."
                ),
            }
        )

    # =====================================================
    # PAUSE
    # =====================================================

    pause_functions = groups.get(
        "pause",
        [],
    )

    if not isinstance(
        pause_functions,
        list,
    ):
        pause_functions = []

    if pause_functions:

        names = []

        for item in pause_functions:

            if isinstance(item, dict):

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

        reports.append(
            {
                "check": "Pause Functions",
                "status": "WARNING",
                "confidence": "MEDIUM",
                "reason": (
                    "Pause-related selectors detected: "
                    + ", ".join(names)
                ),
            }
        )

    else:

        reports.append(
            {
                "check": "Pause Functions",
                "status": "PASS",
                "confidence": "LOW",
                "reason": (
                    "No recognized pause selectors "
                    "were detected."
                ),
            }
        )

    # =====================================================
    # TRADING CONTROLS
    # =====================================================

    trading_functions = groups.get(
        "trading",
        [],
    )

    if not isinstance(
        trading_functions,
        list,
    ):
        trading_functions = []

    if trading_functions:

        names = []

        for item in trading_functions:

            if isinstance(item, dict):

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

        reports.append(
            {
                "check": "Trading Controls",
                "status": "WARNING",
                "confidence": "LOW",
                "reason": (
                    "Trading-control selectors detected: "
                    + ", ".join(names)
                ),
            }
        )

    else:

        reports.append(
            {
                "check": "Trading Controls",
                "status": "PASS",
                "confidence": "LOW",
                "reason": (
                    "No recognized trading-control "
                    "selectors were detected in "
                    "the contract bytecode."
                ),
            }
        )

    return reports


# =========================================================
# PROXY IMPLEMENTATION ANALYSIS
# =========================================================

def _analyze_implementation(
    implementation_address
):
    """
    Analyze the proxy implementation.

    ABI is preferred.
    Bytecode is used as fallback.
    """

    result = {
        "address": implementation_address,
        "source": "UNKNOWN",
        "verified": False,
        "security": [],
    }

    # =====================================================
    # IMPLEMENTATION ABI
    # =====================================================

    try:

        abi = get_abi(
            implementation_address
        )

    except Exception as e:

        abi = None
        result["error"] = str(e)

    if abi is not None:

        result["source"] = "ABI"
        result["verified"] = True

        try:

            functions = build_function_index(
                abi
            )

            result["security"] = _analyze_abi(
                functions
            )

        except Exception as e:

            result["source"] = "ABI"
            result["verified"] = True
            result["error"] = str(e)

            result["security"] = [
                {
                    "check": "Implementation ABI Analysis",
                    "status": "UNKNOWN",
                    "confidence": "LOW",
                    "reason": (
                        "Implementation ABI analysis failed: "
                        f"{e}"
                    ),
                }
            ]

        return result

    # =====================================================
    # IMPLEMENTATION BYTECODE FALLBACK
    # =====================================================

    result["source"] = "BYTECODE"

    result["security"] = _analyze_bytecode(
        implementation_address
    )

    return result


# =========================================================
# MAIN SECURITY SCAN
# =========================================================

def security_scan(
    address,
    abi=None,
):
    """
    Complete contract security analysis.

    Flow:

    1. Detect proxy / bytecode.
    2. Try ABI for the token/proxy.
    3. If proxy ABI is unavailable, try the implementation ABI.
    4. Use ABI detectors when available.
    5. Fall back to bytecode analysis only when no ABI is available.
    6. Analyze proxy implementation separately.

    For ERC-1167 minimal proxies, the implementation contract
    contains the actual token logic, so its ABI is preferred
    when the proxy itself has no verified ABI.
    """

    # =====================================================
    # INITIAL BYTECODE / PROXY ANALYSIS
    # =====================================================

    try:

        bytecode_result = analyze_bytecode(
            address
        )

    except Exception as e:

        bytecode_result = {
            "available": False,
            "proxy": {
                "detected": False,
            },
            "error": str(e),
        }

    if not isinstance(
        bytecode_result,
        dict,
    ):

        bytecode_result = {
            "available": False,
            "proxy": {
                "detected": False,
            },
            "error": (
                "Invalid bytecode analyzer result."
            ),
        }

    proxy = bytecode_result.get(
        "proxy",
        {},
    )

    if not isinstance(
        proxy,
        dict,
    ):

        proxy = {
            "detected": False,
        }

    # =====================================================
    # TOKEN ABI
    # =====================================================

    token_abi = abi

    if token_abi is None:

        try:

            token_abi = get_abi(
                address
            )

        except Exception:

            token_abi = None

    # =====================================================
    # PROXY IMPLEMENTATION
    # =====================================================

    implementation = proxy.get(
        "implementation"
    )

    proxy_detected = proxy.get(
        "detected",
        False,
    )

    implementation_abi = None

    # =====================================================
    # TRY TOKEN ABI FIRST
    # =====================================================

    if token_abi is not None:

        print(
            "✅ Contract ABI/source available."
        )

        try:

            functions = build_function_index(
                token_abi
            )

            security_report = _analyze_abi(
                functions
            )

        except Exception as e:

            security_report = [
                {
                    "check": "ABI Analysis",
                    "status": "UNKNOWN",
                    "confidence": "LOW",
                    "reason": (
                        "Contract ABI analysis failed: "
                        f"{e}"
                    ),
                }
            ]

    # =====================================================
    # PROXY WITH NO TOKEN ABI
    # =====================================================

    elif (
        proxy_detected
        and implementation
    ):

        print(
            "⚠️ Proxy ABI unavailable."
        )

        print(
            "   Trying implementation ABI..."
        )

        try:

            implementation_abi = get_abi(
                implementation
            )

        except Exception:

            implementation_abi = None

        if implementation_abi is not None:

            print(
                "✅ Implementation ABI/source available."
            )

            try:

                functions = build_function_index(
                    implementation_abi
                )

                security_report = _analyze_abi(
                    functions
                )

            except Exception as e:

                security_report = [
                    {
                        "check": "Implementation ABI Analysis",
                        "status": "UNKNOWN",
                        "confidence": "LOW",
                        "reason": (
                            "Implementation ABI analysis failed: "
                            f"{e}"
                        ),
                    }
                ]

        else:

            print(
                "⚠️ Implementation ABI unavailable."
            )

            print(
                "   Falling back to bytecode analysis."
            )

            security_report = _analyze_bytecode(
                address
            )

    # =====================================================
    # NON-PROXY WITHOUT ABI
    # =====================================================

    else:

        print(
            "⚠️ Contract source code / ABI not verified."
        )

        print(
            "   Falling back to bytecode analysis."
        )

        security_report = [
            {
                "check": "Contract Verification",
                "status": "FAIL",
                "confidence": "HIGH",
                "reason": (
                    "Contract source code / ABI "
                    "is not verified."
                ),
            }
        ]

        security_report.extend(
            _analyze_bytecode(
                address
            )
        )

    # =====================================================
    # PROXY / IMPLEMENTATION ANALYSIS
    # =====================================================

    implementation_analysis = None

    if proxy_detected:

        if implementation:

            print()

            print(
                "🔗 Proxy detected: "
                f"{proxy.get('type', 'UNKNOWN')}"
            )

            print(
                "Implementation: "
                f"{implementation}"
            )

            try:

                # If we already successfully loaded the
                # implementation ABI above, avoid fetching it
                # again and triggering another rate limit.
                if implementation_abi is not None:

                    implementation_analysis = {
                        "address": implementation,
                        "source": "ABI",
                        "verified": True,
                        "security": [],
                    }

                    try:

                        implementation_functions = (
                            build_function_index(
                                implementation_abi
                            )
                        )

                        implementation_analysis[
                            "security"
                        ] = _analyze_abi(
                            implementation_functions
                        )

                    except Exception as e:

                        implementation_analysis[
                            "security"
                        ] = [
                            {
                                "check": (
                                    "Implementation "
                                    "ABI Analysis"
                                ),
                                "status": "UNKNOWN",
                                "confidence": "LOW",
                                "reason": (
                                    "Implementation ABI "
                                    "analysis failed: "
                                    f"{e}"
                                ),
                            }
                        ]

                else:

                    implementation_analysis = (
                        _analyze_implementation(
                            implementation
                        )
                    )

                print(
                    "✅ Proxy implementation analyzed."
                )

                print(
                    "Implementation source: "
                    f"{implementation_analysis.get('source')}"
                )

            except Exception as e:

                implementation_analysis = {
                    "address": implementation,
                    "source": "ERROR",
                    "verified": False,
                    "security": [],
                    "error": str(e),
                }

                print(
                    "⚠️ Implementation analysis failed:"
                )

                print(
                    str(e)
                )

    # =====================================================
    # COMPLETE RESULT
    # =====================================================

    return {
        "security": security_report,
        "proxy": proxy,
        "implementation": implementation_analysis,
        "bytecode": bytecode_result,
    }