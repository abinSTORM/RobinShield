from core.abi import get_abi
from core.function_index import build_function_index
from core.bytecode import analyze_bytecode

from detectors.mint_detector import scan as mint_scan
from detectors.tax_detector import scan as tax_scan
from detectors.ownership_detector import scan as ownership_scan
from detectors.blacklist_detector import scan as blacklist_scan
from detectors.pause_detector import scan as pause_scan


def security_scan(address):

    # ==================================================
    # TRY ABI FIRST
    # ==================================================

    abi = get_abi(address)

    if abi is not None:

        functions = build_function_index(
            abi
        )

        report = []

        report.append(
            mint_scan(functions)
        )

        report.append(
            tax_scan(functions)
        )

        report.append(
            ownership_scan(functions)
        )

        report.append(
            blacklist_scan(functions)
        )

        report.append(
            pause_scan(functions)
        )

        return report

    # ==================================================
    # ABI UNAVAILABLE
    # FALL BACK TO BYTECODE
    # ==================================================

    print(
        "⚠️ ABI unavailable. "
        "Falling back to bytecode analysis."
    )

    bytecode = analyze_bytecode(
        address
    )

    report = []

    # ==================================================
    # CONTRACT VERIFICATION
    # ==================================================

    report.append({
        "check": "Contract Verification",
        "status": "FAIL",
        "confidence": "HIGH",
        "reason": (
            "Contract source code / ABI is not verified."
        ),
    })

    # ==================================================
    # BYTECODE AVAILABILITY
    # ==================================================

    if not bytecode["available"]:

        report.append({
            "check": "Bytecode Analysis",
            "status": "FAIL",
            "confidence": "HIGH",
            "reason": (
                "Contract bytecode could not be "
                "retrieved from the RPC."
            ),
        })

        return report

    # ==================================================
    # BYTECODE ANALYSIS
    # ==================================================

    report.append({
        "check": "Bytecode Analysis",
        "status": "PASS",
        "confidence": "MEDIUM",
        "reason": (
            f"Contract bytecode retrieved successfully "
            f"({bytecode['bytecode_size']} bytes)."
        ),
    })

    known_functions = (
        bytecode["known_functions"]
    )

    # ==================================================
    # MINT
    # ==================================================

    mint_functions = [
        fn
        for fn in known_functions
        if fn.startswith("mint")
    ]

    if mint_functions:

        report.append({
            "check": "Mint Function",
            "status": "FAIL",
            "confidence": "MEDIUM",
            "reason": (
                "Potential mint selector detected: "
                + ", ".join(
                    mint_functions
                )
            ),
        })

    else:

        report.append({
            "check": "Mint Function",
            "status": "PASS",
            "confidence": "LOW",
            "reason": (
                "No recognized mint selector was detected "
                "in the contract bytecode."
            ),
        })

    # ==================================================
    # TAX
    # ==================================================

    tax_functions = [
        fn
        for fn in known_functions
        if (
            "tax" in fn.lower()
            or "fee" in fn.lower()
        )
    ]

    if tax_functions:

        report.append({
            "check": "Tax Functions",
            "status": "INFO",
            "confidence": "MEDIUM",
            "reason": (
                "Potential tax/fee selectors detected: "
                + ", ".join(
                    tax_functions
                )
            ),
        })

    else:

        report.append({
            "check": "Tax Functions",
            "status": "PASS",
            "confidence": "LOW",
            "reason": (
                "No recognized tax/fee selectors were "
                "detected in the bytecode."
            ),
        })

    # ==================================================
    # OWNERSHIP
    # ==================================================

    ownership_functions = [
        fn
        for fn in known_functions
        if (
            fn.startswith("owner")
            or fn.startswith(
                "renounceOwnership"
            )
            or fn.startswith(
                "transferOwnership"
            )
        )
    ]

    if ownership_functions:

        report.append({
            "check": "Ownership",
            "status": "INFO",
            "confidence": "MEDIUM",
            "reason": (
                "Ownership-related selectors detected: "
                + ", ".join(
                    ownership_functions
                )
            ),
        })

    else:

        report.append({
            "check": "Ownership",
            "status": "INFO",
            "confidence": "LOW",
            "reason": (
                "No recognized ownership selectors "
                "were detected."
            ),
        })

    # ==================================================
    # BLACKLIST
    # ==================================================

    blacklist_functions = [
        fn
        for fn in known_functions
        if (
            "blacklist" in fn.lower()
            or "unblacklist" in fn.lower()
        )
    ]

    if blacklist_functions:

        report.append({
            "check": "Blacklist",
            "status": "FAIL",
            "confidence": "MEDIUM",
            "reason": (
                "Potential blacklist selectors detected: "
                + ", ".join(
                    blacklist_functions
                )
            ),
        })

    else:

        report.append({
            "check": "Blacklist",
            "status": "PASS",
            "confidence": "LOW",
            "reason": (
                "No recognized blacklist selectors "
                "were detected."
            ),
        })

    # ==================================================
    # PAUSE
    # ==================================================

    pause_functions = [
        fn
        for fn in known_functions
        if (
            fn.startswith("pause")
            or fn.startswith("unpause")
        )
    ]

    if pause_functions:

        report.append({
            "check": "Pause Functions",
            "status": "INFO",
            "confidence": "MEDIUM",
            "reason": (
                "Pause-related selectors detected: "
                + ", ".join(
                    pause_functions
                )
            ),
        })

    else:

        report.append({
            "check": "Pause Functions",
            "status": "PASS",
            "confidence": "LOW",
            "reason": (
                "No recognized pause selectors "
                "were detected."
            ),
        })

    # ==================================================
    # BYTECODE WARNINGS
    # ==================================================

    for warning in bytecode.get(
        "warnings",
        []
    ):

        report.append({
            "check": "Bytecode Warning",
            "status": "INFO",
            "confidence": "MEDIUM",
            "reason": warning,
        })

    return report