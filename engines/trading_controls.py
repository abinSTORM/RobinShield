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

TRADING_STATE_GETTERS = {
    "tradingEnabled",
    "tradingOpen",
    "isTradingEnabled",
    "isTradingOpen",
    "tradingActive",
    "tradingStatus",
    "tradingState",
}

LAUNCH_FUNCTIONS = {
    "startTrading",
    "openTrading",
    "enableTrading",
    "launch",
}


def _find(functions, names):
    return sorted(
        name for name in names
        if name in functions
    )


def analyze_trading_controls(functions):

    if functions is None:
        functions = set()

    names = {
        str(item.get("name") or item.get("function") or "")
        if isinstance(item, dict) else str(item).split("(", 1)[0]
        for item in functions
    }
    detected = _find(
        names,
        TRADING_FUNCTIONS - TRADING_STATE_GETTERS - LAUNCH_FUNCTIONS
    )

    if detected:

        return create_report(
            "Trading Controls",
            "WARNING",
            "MEDIUM",
            "State-changing trading control functions detected: "
            + ", ".join(detected)
        )

    getters = _find(names, TRADING_STATE_GETTERS)
    launch = _find(names, LAUNCH_FUNCTIONS)
    if getters or launch:
        details = []
        if getters:
            details.append("read-only state getter(s): " + ", ".join(getters))
        if launch:
            details.append("launch/start function(s): " + ", ".join(launch))
        return create_report(
            "Trading Controls",
            "INFO",
            "LOW",
            "; ".join(details)
            + ". These names do not by themselves show that an authorized account can disable trading or block sells."
        )

    return create_report(
        "Trading Controls",
        "PASS",
        "LOW",
        "No recognized trading controls were found in the ABI; custom or obfuscated buy/sell restrictions may not be detected."
    )
