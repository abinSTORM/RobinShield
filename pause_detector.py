from detector import detect_functions
from report import create_report

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
        "HIGH",
        "No pause-related functions detected."
    )