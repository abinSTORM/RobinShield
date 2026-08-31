from core.report import create_report


TRADING_FUNCTIONS = {
    "enableTrading",
    "disableTrading",
    "openTrading",
    "setTrading",
    "setTradingEnabled",
    "tradingEnabled",
    "tradingOpen",
    "startTrading",
    "stopTrading",
    "launch",
    "startTrading",
}


def _find(functions, names):
    return sorted(
        name for name in names
        if name in functions
    )


def analyze_trading_controls(functions):

    if functions is None:
        functions = set()

    detected = _find(
        functions,
        TRADING_FUNCTIONS
    )

    if detected:

        return create_report(
            "Trading Controls",
            "WARNING",
            "HIGH",
            "Trading control functions detected: "
            + ", ".join(detected)
        )

    return create_report(
        "Trading Controls",
        "PASS",
        "HIGH",
        "No recognized trading enable/disable controls detected."
    )
