from core.detector import detect_functions
from core.report import create_report

PAUSE_FUNCTIONS = [
    "pause",
    "_pause",
    "unpause",
    "_unpause",
    "paused",
]


def scan(functions):

    result = detect_functions(functions, PAUSE_FUNCTIONS)

    detected = []

    for name, exists in result.items():
        if exists:
            detected.append(name)

    if detected:
        return create_report(
            "Pause Functions",
            "INFO",
            "HIGH",
            f"Pause-related functions detected: {', '.join(detected)}"
        )

    return create_report(
        "Pause Functions",
        "PASS",
        "LOW",
        "No recognized pause functions were found in the ABI; custom or obfuscated transfer controls may not be detected."
    )
