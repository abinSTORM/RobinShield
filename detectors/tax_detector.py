from core.detector import detect_functions
from core.report import create_report
TAX_FUNCTIONS = [
    "buyTaxRate",
    "sellTaxRate",
    "taxRate",
    "setTax",
    "setTaxes",
    "setTaxRate",
    "setTaxRates",
    "setTaxPercent",
    "updateTaxes",
    "updateTax",
    "updateTaxRates",
    "updateBuyTax",
    "updateSellTax",
    "setBuyTax",
    "setSellTax",
    "setFee",
    "setFees",
    "setFeeRate",
    "setFeePercent",
    "setBuyFee",
    "setSellFee",
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
        "LOW",
        "No recognized tax functions were found in the ABI; custom fee logic may not be detected."
    )
