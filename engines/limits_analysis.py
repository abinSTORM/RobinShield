from core.function_index import build_function_index


# =========================================================
# LIMIT GETTERS
# =========================================================

LIMIT_GETTERS = {
    "maxTxAmount": "Maximum transaction amount",
    "maxTransactionAmount": "Maximum transaction amount",
    "maxTxnAmount": "Maximum transaction amount",
    "maxWallet": "Maximum wallet amount",
    "maxWalletAmount": "Maximum wallet amount",
    "maxWalletSize": "Maximum wallet size",
    "maxHoldingAmount": "Maximum holding amount",
    "maxBuyAmount": "Maximum buy amount",
    "maxSellAmount": "Maximum sell amount",
    "maxTransferAmount": "Maximum transfer amount",
}


COOLDOWN_GETTERS = {
    "cooldownEnabled": "Cooldown",
    "transferDelayEnabled": "Transfer delay",
    "limitsInEffect": "Limits enabled",
}


LIMIT_SETTERS = {
    "setMaxTxAmount",
    "setMaxTxnAmount",
    "setMaxTransactionAmount",
    "setMaxWalletAmount",
    "setMaxWallet",
    "updateMaxTxAmount",
    "updateMaxTxnAmount",
    "updateMaxTransactionAmount",
    "updateMaxWalletAmount",
    "updateMaxWallet",
    "setLimitsInEffect",
    "removeLimits",
    "setCooldownEnabled",
    "setTransferDelayEnabled",
}


def analyze_limits(abi):
    """
    Analyze transaction, wallet and cooldown controls.

    This version performs ABI-level detection only.
    It does NOT claim that a limit is currently active
    unless the ABI exposes enough information to establish it.
    """

    if not abi:
        return {
            "status": "UNAVAILABLE",
            "risk": "HIGH",
            "confidence": "LOW",
            "detected_getters": [],
            "setters": [],
            "cooldown_controls": [],
            "warnings": [
                "Contract ABI could not be loaded."
            ],
            "signals": [],
        }

    functions = build_function_index(abi)

    detected_getters = []
    detected_setters = []
    cooldown_controls = []

    # -----------------------------------------------------
    # LIMIT GETTERS
    # -----------------------------------------------------

    for name in LIMIT_GETTERS:

        if name in functions:
            detected_getters.append(name)

    # -----------------------------------------------------
    # LIMIT SETTERS / ADMIN CONTROLS
    # -----------------------------------------------------

    for name in LIMIT_SETTERS:

        if name in functions:
            detected_setters.append(name)

    # -----------------------------------------------------
    # COOLDOWN / DELAY
    # -----------------------------------------------------

    for name in COOLDOWN_GETTERS:

        if name in functions:
            cooldown_controls.append(name)

    warnings = []
    signals = []

    # -----------------------------------------------------
    # SIGNALS
    # -----------------------------------------------------

    if detected_getters:

        signals.append(
            "Transaction/wallet limit getters detected: "
            + ", ".join(detected_getters)
            + "."
        )

    if detected_setters:

        signals.append(
            "Functions capable of modifying/removing limits detected: "
            + ", ".join(detected_setters)
            + "."
        )

    if cooldown_controls:

        signals.append(
            "Cooldown/transfer-delay controls detected: "
            + ", ".join(cooldown_controls)
            + "."
        )

    # -----------------------------------------------------
    # NO LIMITS
    # -----------------------------------------------------

    if not detected_getters and not cooldown_controls:

        return {
            "status": "PASS",
            "risk": "LOW",
            "confidence": "HIGH",
            "detected_getters": [],
            "setters": detected_setters,
            "cooldown_controls": [],
            "warnings": [],
            "signals": [
                "No recognized transaction, wallet, "
                "cooldown, or transfer-delay controls "
                "were detected in the ABI."
            ],
        }

    # -----------------------------------------------------
    # LIMITS DETECTED
    # -----------------------------------------------------

    if detected_getters and detected_setters:

        status = "WARNING"
        risk = "MEDIUM"
        confidence = "HIGH"

        warnings.append(
            "The contract exposes configurable transaction "
            "or wallet limits."
        )

    elif detected_getters:

        status = "INFO"
        risk = "LOW"
        confidence = "HIGH"

        warnings.append(
            "Limit getter functions were detected, but "
            "current limit values were not read."
        )

    else:

        status = "INFO"
        risk = "LOW"
        confidence = "MEDIUM"

        warnings.append(
            "Cooldown or transfer-delay controls were detected."
        )

    return {
        "status": status,
        "risk": risk,
        "confidence": confidence,
        "detected_getters": detected_getters,
        "setters": detected_setters,
        "cooldown_controls": cooldown_controls,
        "warnings": warnings,
        "signals": signals,
    }