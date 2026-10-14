from core.detector import detect_functions
from core.report import create_report

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
        "LOW",
        "No recognized blacklist functions were found in the ABI; custom or obfuscated restrictions may not be detected."
    )
