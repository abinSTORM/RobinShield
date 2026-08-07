from detector import detect_functions
from report import create_report

BLACKLIST_FUNCTIONS = [
    "blacklist",
    "_blacklist",
    "isBlacklisted",
    "addToBlacklist",
    "removeFromBlacklist",
    "setBlacklist",
    "blacklistAddress",
    "blacklisted",
]


def scan(functions):

    result = detect_functions(functions, BLACKLIST_FUNCTIONS)

    detected = []

    for name, exists in result.items():
        if exists:
            detected.append(name)

    if detected:
        return create_report(
            "Blacklist",
            "WARNING",
            "HIGH",
            f"Blacklist-related functions detected: {', '.join(detected)}"
        )

    return create_report(
        "Blacklist",
        "PASS",
        "HIGH",
        "No blacklist-related functions detected."
    )