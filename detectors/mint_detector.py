from core.detector import detect_functions
from core.report import create_report

MINT_FUNCTIONS = [
    "mint",
    "_mint",
    "mintTokens",
    "createTokens",
    "issue",
    "issueTokens",
]


def scan(functions):

    result = detect_functions(functions, MINT_FUNCTIONS)

    detected = []

    for name, exists in result.items():
        if exists:
            detected.append(name)

    # If any mint function is found
    if detected:
        return create_report(
            "Mint Function",
            "FAIL",
            "HIGH",
            f"Mint capability detected: {', '.join(detected)}"
        )

    # If no mint function is found
    return create_report(
        "Mint Function",
        "PASS",
        "HIGH",
        "No known mint function detected."
    )