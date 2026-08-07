from core.detector import detect_functions
from core.report import create_report
TAX_FUNCTIONS = [
    "buyTaxRate",
    "sellTaxRate",
    "taxRate",
    "setTax",
    "setTaxes",
    "updateTaxes",
    "setBuyTax",
    "setSellTax",
]


def scan(functions):

    result = detect_functions(functions, TAX_FUNCTIONS)

    detected = []

    for name, exists in result.items():
        if exists:
            detected.append(name)

    if detected:
        return create_report(
            "Tax Functions",
            "INFO",
            "HIGH",
            f"Tax-related functions detected: {', '.join(detected)}"
        )

    return create_report(
        "Tax Functions",
        "PASS",
        "HIGH",
        "No tax-related functions detected."
    )