from core.detector import detect_functions
from core.report import create_report

OWNERSHIP_FUNCTIONS = [
    "owner",
    "transferOwnership",
    "renounceOwnership",
]


def scan(functions):

    result = detect_functions(functions, OWNERSHIP_FUNCTIONS)

    has_owner = result["owner"]
    can_transfer = result["transferOwnership"]
    can_renounce = result["renounceOwnership"]

    if not has_owner:
        return create_report(
            "Ownership",
            "INFO",
            "MEDIUM",
            "No ownership function detected."
        )

    if can_renounce:
        return create_report(
            "Ownership",
            "PASS",
            "HIGH",
            "Ownership functions detected and ownership can be renounced."
        )

    return create_report(
        "Ownership",
        "WARNING",
        "HIGH",
        "Ownership functions detected but no renounceOwnership function found."
    )