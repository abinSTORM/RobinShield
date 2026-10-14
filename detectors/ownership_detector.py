from core.detector import detect_functions
from core.report import create_report

OWNERSHIP_FUNCTIONS = [
    "owner",
    "getOwner",
    "transferOwnership",
    "safeTransferOwnership",
    "renounceOwnership",
]


def scan(functions):

    result = detect_functions(functions, OWNERSHIP_FUNCTIONS)

    has_owner = result["owner"] or result["getOwner"]
    can_transfer = result["transferOwnership"] or result["safeTransferOwnership"]
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
            "INFO",
            "MEDIUM",
            "Ownership and renunciation functions were detected; this does not prove which addresses can call them or that the current owner is renounced."
        )

    return create_report(
        "Ownership",
        "WARNING",
        "HIGH",
        "Ownership function detected; caller permissions and current owner state require separate verification."
    )
