# =========================================================
# ROBINSHIELD OVERALL RISK ENGINE
# =========================================================


# =========================================================
# SAFE HELPERS
# =========================================================

def _safe_dict(value):
    return value if isinstance(value, dict) else {}


def _safe_list(value):
    return value if isinstance(value, list) else []


def _status(value):
    return str(
        value or "UNKNOWN"
    ).upper().strip()


def _add_unique(items, message):
    if message and message not in items:
        items.append(message)


# =========================================================
# CONTRACT SECURITY
# =========================================================

def _security_penalty(
    security,
    warnings,
):
    if isinstance(
        security,
        dict,
    ):
        security = security.get(
            "security",
            [],
        )

    security = _safe_list(
        security
    )

    penalty = 0

    if not security:
        return 0

    for item in security:

        if not isinstance(
            item,
            dict,
        ):
            continue

        check = str(
            item.get(
                "check",
                "Unknown",
            )
        ).strip()

        status = _status(
            item.get(
                "status",
            )
        )

        check_lower = check.lower()

        # -------------------------------------------------
        # Verification failure is uncertainty, not proof
        # of malicious behavior.
        # -------------------------------------------------

        if check_lower in (
            "contract verification",
            "verification",
        ):

            if status == "FAIL":

                _add_unique(
                    warnings,
                    "Contract source verification failed.",
                )

                penalty += 3

            continue

        # -------------------------------------------------
        # Confirmed failures.
        # -------------------------------------------------

        if status == "FAIL":

            if check_lower == "blacklist":

                penalty += 25

                _add_unique(
                    warnings,
                    "Potential blacklist functionality was detected.",
                )

            elif check_lower == "mint function":

                penalty += 25

                _add_unique(
                    warnings,
                    "Potential mint functionality was detected.",
                )

            elif check_lower == "pause functions":

                penalty += 15

                _add_unique(
                    warnings,
                    "Potential pause or freeze functionality was detected.",
                )

            elif check_lower in (
                "trading controls",
                "trading restrictions",
            ):

                penalty += 20

                _add_unique(
                    warnings,
                    "Potential trading restrictions were detected.",
                )

            elif check_lower in (
                "tax functions",
                "tax",
            ):

                penalty += 15

                _add_unique(
                    warnings,
                    "Potentially dangerous tax functionality was detected.",
                )

            elif check_lower == "ownership":

                penalty += 12

                _add_unique(
                    warnings,
                    "Potentially risky ownership controls were detected.",
                )

            else:

                penalty += 15

                _add_unique(
                    warnings,
                    f"Contract security check failed: {check}.",
                )

        # -------------------------------------------------
        # Warnings are moderate evidence.
        # -------------------------------------------------

        elif status == "WARNING":

            if check_lower == "blacklist":
                penalty += 10

            elif check_lower == "mint function":
                penalty += 10

            elif check_lower == "pause functions":
                penalty += 8

            elif check_lower in (
                "trading controls",
                "trading restrictions",
            ):
                penalty += 10

            elif check_lower in (
                "tax functions",
                "tax",
            ):
                penalty += 5

            elif check_lower == "ownership":
                penalty += 5

            else:
                penalty += 5

    return min(
        penalty,
        50,
    )


# =========================================================
# LIQUIDITY
# =========================================================

def _liquidity_penalty(
    liquidity,
    warnings,
):
    liquidity = _safe_dict(
        liquidity
    )

    found = liquidity.get(
        "found"
    )

    risk = _status(
        liquidity.get(
            "risk",
        )
    )

    liquidity_usd = liquidity.get(
        "liquidity_usd",
        liquidity.get(
            "total_liquidity_usd",
            liquidity.get(
                "total_discovered_liquidity_usd",
                0,
            ),
        ),
    )

    try:
        liquidity_usd = float(
            liquidity_usd or 0
        )
    except (
        TypeError,
        ValueError,
    ):
        liquidity_usd = 0.0

    # -----------------------------------------------------
    # No pool / unavailable.
    # -----------------------------------------------------

    if found is False:

        _add_unique(
            warnings,
            "No supported liquidity pool was detected.",
        )

        return 5

    if found is None:

        _add_unique(
            warnings,
            "Liquidity detection status is unknown.",
        )

        return 0

    # -----------------------------------------------------
    # Explicit engine classification.
    # -----------------------------------------------------

    if risk == "HIGH":

        _add_unique(
            warnings,
            "Liquidity is very low.",
        )

        return 35

    if risk == "MEDIUM":

        _add_unique(
            warnings,
            "Liquidity is relatively low.",
        )

        return 18

    if risk == "LOW":

        return 0

    # -----------------------------------------------------
    # Fallback by actual liquidity value.
    # -----------------------------------------------------

    if liquidity_usd > 0:

        if liquidity_usd < 1000:

            _add_unique(
                warnings,
                "Liquidity is very low.",
            )

            return 30

        if liquidity_usd < 10000:

            _add_unique(
                warnings,
                "Liquidity is relatively low.",
            )

            return 18

    return 0


# =========================================================
# HOLDER RISK
# =========================================================

def _holder_penalty(
    holders,
    warnings,
):
    holders = _safe_dict(
        holders
    )

    level = _status(
        holders.get(
            "risk",
            holders.get(
                "level",
                holders.get(
                    "holder_risk",
                    "UNKNOWN",
                ),
            ),
        )
    )

    verified = bool(
        holders.get(
            "_verified",
            holders.get(
                "verified",
                False,
            ),
        )
    )

    complete = bool(
        holders.get(
            "_complete",
            False,
        )
    )

    coverage = _status(
        holders.get(
            "coverage",
            "",
        )
    )

    # -----------------------------------------------------
    # Partial/unknown coverage.
    #
    # Do not invent a concentration risk from incomplete
    # data.
    # -----------------------------------------------------

    if (
        not verified
        or not complete
        or coverage == "PARTIAL"
    ):

        _add_unique(
            warnings,
            "Holder distribution could not be fully verified.",
        )

        return 0

    if level in (
        "UNKNOWN",
        "UNAVAILABLE",
        "",
    ):

        return 0

    if level == "LOW":

        return 0

    if level == "MEDIUM":

        _add_unique(
            warnings,
            "Holder concentration is moderate.",
        )

        return 10

    if level == "HIGH":

        _add_unique(
            warnings,
            "Token ownership is highly concentrated.",
        )

        return 25

    return 0


# =========================================================
# LP SAFETY
# =========================================================

def _lp_penalty(
    lp_safety,
    warnings,
):
    lp_safety = _safe_dict(
        lp_safety
    )

    safety = _status(
        lp_safety.get(
            "safety",
            lp_safety.get(
                "risk",
                "UNKNOWN",
            ),
        )
    )

    # -----------------------------------------------------
    # Unknown is uncertainty.
    # -----------------------------------------------------

    if safety in (
        "UNKNOWN",
        "UNAVAILABLE",
        "",
    ):

        return 0

    if safety in (
        "VERY HIGH",
        "HIGH",
        "SAFE",
        "PASS",
    ):

        return 0

    if safety == "MEDIUM":

        _add_unique(
            warnings,
            "A significant amount of LP remains active.",
        )

        return 10

    if safety == "LOW":

        _add_unique(
            warnings,
            "A large portion of LP tokens remains active.",
        )

        return 20

    return 0


# =========================================================
# TAX
# =========================================================

def _tax_penalty(
    tax_analysis,
    warnings,
):
    data = _safe_dict(
        tax_analysis
    )

    status = _status(
        data.get(
            "status",
        )
    )

    risk = _status(
        data.get(
            "risk",
        )
    )

    # -----------------------------------------------------
    # Explicit high-risk analysis.
    # -----------------------------------------------------

    if (
        status == "FAIL"
        or risk == "HIGH"
    ):

        _add_unique(
            warnings,
            "High-risk tax behavior was detected.",
        )

        return 25

    if risk == "MEDIUM":

        _add_unique(
            warnings,
            "Moderate token tax was detected.",
        )

        return 10

    # -----------------------------------------------------
    # WARNING + LOW = informational.
    # -----------------------------------------------------

    if (
        status == "WARNING"
        and
        risk == "LOW"
    ):

        return 3

    # -----------------------------------------------------
    # Unknown ABI / unavailable analysis.
    # -----------------------------------------------------

    if status in (
        "UNKNOWN",
        "UNAVAILABLE",
        "",
    ):

        return 0

    return 0


# =========================================================
# OWNERSHIP
# =========================================================

def _ownership_penalty(
    ownership,
    warnings,
):
    ownership = _safe_dict(
        ownership
    )

    status = _status(
        ownership.get(
            "status",
        )
    )

    risk = _status(
        ownership.get(
            "risk",
        )
    )

    if (
        status == "FAIL"
        or risk == "HIGH"
    ):

        _add_unique(
            warnings,
            "High-risk administrative control was detected.",
        )

        return 20

    if risk == "MEDIUM":

        _add_unique(
            warnings,
            "Token retains potentially significant administrative control.",
        )

        return 8

    return 0


# =========================================================
# TRADE SAFETY
# =========================================================

def _trade_safety_penalty(
    trade_safety,
    warnings,
):
    trade_safety = _safe_dict(
        trade_safety
    )

    status = _status(
        trade_safety.get(
            "status",
        )
    )

    risk = _status(
        trade_safety.get(
            "risk",
        )
    )

    if (
        status == "FAIL"
        or risk == "HIGH"
    ):

        _add_unique(
            warnings,
            "Trade safety analysis detected dangerous restrictions.",
        )

        return 25

    if risk == "MEDIUM":

        _add_unique(
            warnings,
            "Trade safety analysis detected potentially risky trade functionality.",
        )

        return 8

    if (
        status == "WARNING"
        and
        risk == "LOW"
    ):

        return 2

    return 0


# =========================================================
# QUOTE SIMULATION
# =========================================================

def _simulation_penalty(
    simulation,
    warnings,
):
    simulation = _safe_dict(
        simulation
    )

    status = _status(
        simulation.get(
            "status",
        )
    )

    risk = _status(
        simulation.get(
            "risk",
        )
    )

    buy = _safe_dict(
        simulation.get(
            "buy",
        )
    )

    sell = _safe_dict(
        simulation.get(
            "sell",
        )
    )

    # -----------------------------------------------------
    # Actual SELL failure is strong evidence.
    # -----------------------------------------------------

    if sell.get(
        "success"
    ) is False:

        _add_unique(
            warnings,
            "SELL quote simulation failed.",
        )

        return 30

    # -----------------------------------------------------
    # BUY failure.
    # -----------------------------------------------------

    if buy.get(
        "success"
    ) is False:

        _add_unique(
            warnings,
            "BUY quote simulation failed.",
        )

        return 15

    # -----------------------------------------------------
    # Explicit high-risk warning.
    # -----------------------------------------------------

    if (
        status == "WARNING"
        and
        risk == "HIGH"
    ):

        _add_unique(
            warnings,
            "Trade simulation detected potentially high-risk behavior.",
        )

        return 12

    if status == "WARNING":

        _add_unique(
            warnings,
            "Trade simulation returned a warning.",
        )

        return 5

    return 0


# =========================================================
# HONEYPOT / SELLABILITY
# =========================================================

def _honeypot_penalty(
    honeypot,
    warnings,
):
    honeypot = _safe_dict(
        honeypot
    )

    status = _status(
        honeypot.get(
            "status",
        )
    )

    risk = _status(
        honeypot.get(
            "risk",
        )
    )

    confidence = _status(
        honeypot.get(
            "confidence",
            "LOW",
        )
    )

    buy = _safe_dict(
        honeypot.get(
            "buy",
        )
    )

    sell = _safe_dict(
        honeypot.get(
            "sell",
        )
    )

    # -----------------------------------------------------
    # Actual SELL-side failure.
    # -----------------------------------------------------

    if sell.get(
        "success"
    ) is False:

        _add_unique(
            warnings,
            "SELL-side transfer simulation failed. Possible honeypot or transfer restriction.",
        )

        if confidence == "HIGH":

            return 40

        return 25

    # -----------------------------------------------------
    # Explicit analysis failure.
    # -----------------------------------------------------

    if status == "FAIL":

        _add_unique(
            warnings,
            "Honeypot analysis detected high-risk transfer behavior.",
        )

        return 30

    if (
        risk == "HIGH"
        and
        status not in (
            "UNKNOWN",
            "UNAVAILABLE",
        )
    ):

        _add_unique(
            warnings,
            "Honeypot analysis detected high-risk transfer behavior.",
        )

        return 25

    if status == "WARNING":

        _add_unique(
            warnings,
            "Honeypot analysis detected potentially restricted transfer behavior.",
        )

        if risk == "MEDIUM":

            return 12

        return 6

    # -----------------------------------------------------
    # Unknown / unavailable = no danger penalty.
    # -----------------------------------------------------

    return 0


# =========================================================
# DEEP SWAP EXECUTION
# =========================================================

def _swap_execution_penalty(
    swap_simulation,
    warnings,
):
    swap_simulation = _safe_dict(
        swap_simulation
    )

    status = _status(
        swap_simulation.get(
            "status",
        )
    )

    risk = _status(
        swap_simulation.get(
            "risk",
        )
    )

    tested = swap_simulation.get(
        "tested",
        False,
    )

    # -----------------------------------------------------
    # Successful deep execution.
    # -----------------------------------------------------

    if (
        status == "PASS"
        and
        risk == "LOW"
        and
        tested is True
    ):

        return 0

    # -----------------------------------------------------
    # Unknown / skipped.
    # -----------------------------------------------------

    if status in (
        "UNKNOWN",
        "UNAVAILABLE",
        "SKIPPED",
        "",
    ):

        return 0

    if (
        status == "FAIL"
        or
        risk == "HIGH"
    ):

        _add_unique(
            warnings,
            "Deep router swap execution simulation detected a high-risk failure.",
        )

        return 25

    if (
        status == "WARNING"
        and
        risk == "MEDIUM"
    ):

        _add_unique(
            warnings,
            "Deep router swap execution simulation returned a warning.",
        )

        return 12

    if status == "WARNING":

        _add_unique(
            warnings,
            "Deep router swap execution simulation returned a warning.",
        )

        return 5

    return 0


# =========================================================
# PROXY
# =========================================================

def _proxy_penalty(
    proxy,
    implementation,
    warnings,
):
    proxy = _safe_dict(
        proxy
    )

    implementation = _safe_dict(
        implementation
    )

    if not proxy.get(
        "detected",
        False,
    ):

        return 0

    proxy_type = proxy.get(
        "type",
        "UNKNOWN",
    )

    _add_unique(
        warnings,
        f"Token uses an {proxy_type} proxy.",
    )

    implementation_address = (
        proxy.get(
            "implementation"
        )
    )

    if implementation_address:

        _add_unique(
            warnings,
            f"Proxy implementation: {implementation_address}",
        )

    # -----------------------------------------------------
    # A proxy is complexity, not proof of maliciousness.
    # -----------------------------------------------------

    if implementation.get(
        "verified"
    ) is True:

        return 2

    return 3


# =========================================================
# POSITIVE SIGNALS
# =========================================================

def _positive_signals(
    liquidity,
    lp_safety,
    holders,
    security,
    simulation,
    honeypot,
    swap_simulation=None,
):
    positives = []

    liquidity = _safe_dict(
        liquidity
    )

    lp_safety = _safe_dict(
        lp_safety
    )

    holders = _safe_dict(
        holders
    )

    simulation = _safe_dict(
        simulation
    )

    honeypot = _safe_dict(
        honeypot
    )

    swap_simulation = _safe_dict(
        swap_simulation
    )

    # -----------------------------------------------------
    # LIQUIDITY
    # -----------------------------------------------------

    if _status(
        liquidity.get(
            "risk",
        )
    ) == "LOW":

        _add_unique(
            positives,
            "Liquidity level is healthy.",
        )

    # -----------------------------------------------------
    # LP
    # -----------------------------------------------------

    if _status(
        lp_safety.get(
            "safety",
        )
    ) in (
        "VERY HIGH",
        "HIGH",
        "SAFE",
        "PASS",
    ):

        burned = lp_safety.get(
            "burn_percentage"
        )

        if burned is not None:

            try:
                burned_value = float(
                    burned
                )
            except (
                TypeError,
                ValueError,
            ):
                burned_value = 0

            if burned_value >= 99:

                _add_unique(
                    positives,
                    "Almost all LP tokens are burned.",
                )

            else:

                _add_unique(
                    positives,
                    "LP safety appears strong.",
                )

        else:

            _add_unique(
                positives,
                "LP safety appears strong.",
            )

    # -----------------------------------------------------
    # HOLDERS
    #
    # Only call distribution healthy if coverage is
    # complete and verified.
    # -----------------------------------------------------

    holder_level = _status(
        holders.get(
            "risk",
            holders.get(
                "level",
                holders.get(
                    "holder_risk",
                    "",
                ),
            ),
        )
    )

    holder_verified = bool(
        holders.get(
            "_verified",
            holders.get(
                "verified",
                False,
            ),
        )
    )

    holder_complete = bool(
        holders.get(
            "_complete",
            False,
        )
    )

    holder_coverage = _status(
        holders.get(
            "coverage",
            "",
        )
    )

    if (
        holder_level == "LOW"
        and
        holder_verified
        and
        holder_complete
        and
        holder_coverage == "COMPLETE"
    ):

        _add_unique(
            positives,
            "Holder distribution is relatively healthy.",
        )

    # -----------------------------------------------------
    # SECURITY
    # -----------------------------------------------------

    if isinstance(
        security,
        dict,
    ):

        security_items = security.get(
            "security",
            [],
        )

    else:

        security_items = security

    security_items = _safe_list(
        security_items
    )

    security_failures = []

    for item in security_items:

        if not isinstance(
            item,
            dict,
        ):

            continue

        status = _status(
            item.get(
                "status",
            )
        )

        check = str(
            item.get(
                "check",
                "",
            )
        ).lower()

        if (
            status == "FAIL"
            and
            check != "contract verification"
        ):

            security_failures.append(
                item
            )

    if (
        security_items
        and
        not security_failures
    ):

        _add_unique(
            positives,
            "No major contract security check failures were detected.",
        )

    # -----------------------------------------------------
    # QUOTE SIMULATION
    # -----------------------------------------------------

    buy = _safe_dict(
        simulation.get(
            "buy",
        )
    )

    sell = _safe_dict(
        simulation.get(
            "sell",
        )
    )

    if (
        buy.get(
            "success"
        ) is True
        and
        sell.get(
            "success"
        ) is True
    ):

        _add_unique(
            positives,
            "Both BUY and SELL quote simulations returned successfully.",
        )

    # -----------------------------------------------------
    # HONEYPOT
    # -----------------------------------------------------

    hp_buy = _safe_dict(
        honeypot.get(
            "buy",
        )
    )

    hp_sell = _safe_dict(
        honeypot.get(
            "sell",
        )
    )

    if (
        hp_buy.get(
            "success"
        ) is True
        and
        hp_sell.get(
            "success"
        ) is True
    ):

        _add_unique(
            positives,
            "BUY and SELL transfer simulations both passed.",
        )

    # -----------------------------------------------------
    # DEEP ROUTER
    # -----------------------------------------------------

    deep_status = _status(
        swap_simulation.get(
            "status",
        )
    )

    deep_risk = _status(
        swap_simulation.get(
            "risk",
        )
    )

    deep_tested = (
        swap_simulation.get(
            "tested",
            False,
        )
        is True
    )

    if (
        deep_status == "PASS"
        and
        deep_risk == "LOW"
        and
        deep_tested
    ):

        # Look for explicit simulator evidence first.
        signals = _safe_list(
            swap_simulation.get(
                "signals",
                [],
            )
        )

        signal_text = " ".join(
            str(signal).lower()
            for signal in signals
        )

        if (
            "sell succeeded across all"
            in signal_text
            or
            "deep sell" in signal_text
        ):

            _add_unique(
                positives,
                "Deep router SELL execution succeeded in a temporary fork.",
            )

        # BUY
        if (
            swap_simulation.get(
                "buy_success"
            ) is True
            or
            "buy succeeded across all"
            in signal_text
            or
            "deep buy and sell router execution both succeeded"
            in signal_text
        ):

            _add_unique(
                positives,
                "Deep router BUY execution succeeded in a temporary fork.",
            )

        # Combined result.
        if (
            "deep buy and sell router execution both succeeded"
            in signal_text
        ):

            _add_unique(
                positives,
                "Deep BUY and SELL router execution both succeeded inside temporary local forks.",
            )

    # -----------------------------------------------------
    # ALWAYS RETURN A LIST
    # -----------------------------------------------------

    return positives


# =========================================================
# MAIN
# =========================================================

def calculate_overall_risk(
    liquidity=None,
    lp_safety=None,

    holders=None,
    holder_risk=None,

    security=None,
    security_report=None,
    contract_security=None,

    tax_analysis=None,

    ownership=None,
    ownership_analysis=None,

    trading_limits=None,

    trade_safety=None,

    trade_simulation=None,

    honeypot=None,

    swap_simulation=None,

    proxy=None,
    proxy_info=None,

    implementation=None,
    implementation_info=None,

    **kwargs,
):

    """
    RobinShield overall risk calculator.

    UNKNOWN / UNAVAILABLE
        = lack of evidence

    FAIL / HIGH RISK
        = evidence of danger
    """

    # =====================================================
    # NORMALIZE ALTERNATE ARGUMENT NAMES
    # =====================================================

    if not holders:

        holders = holder_risk

    if not security:

        security = contract_security

    if not security:

        security = security_report

    if not ownership:

        ownership = ownership_analysis

    if not proxy:

        proxy = proxy_info

    if not implementation:

        implementation = implementation_info

    if not liquidity:

        liquidity = kwargs.get(
            "liquidity_result",
            kwargs.get(
                "liquidity_data",
            ),
        )

    if not lp_safety:

        lp_safety = kwargs.get(
            "lp",
            kwargs.get(
                "lp_result",
                kwargs.get(
                    "lp_safety_result",
                ),
            ),
        )

    if not holders:

        holders = kwargs.get(
            "holder_distribution",
            kwargs.get(
                "holder_data",
                kwargs.get(
                    "holders_result",
                ),
            ),
        )

    if not security:

        security = kwargs.get(
            "contract_security",
            kwargs.get(
                "security_result",
            ),
        )

    if not tax_analysis:

        tax_analysis = kwargs.get(
            "tax",
            kwargs.get(
                "tax_result",
            ),
        )

    if not ownership:

        ownership = kwargs.get(
            "ownership_result",
        )

    if not trade_safety:

        trade_safety = kwargs.get(
            "trade_safety_result",
        )

    if not trade_simulation:

        trade_simulation = kwargs.get(
            "simulation",
            kwargs.get(
                "simulation_result",
            ),
        )

    if not honeypot:

        honeypot = kwargs.get(
            "honeypot_result",
            kwargs.get(
                "sellability",
            ),
        )

    if not swap_simulation:

        swap_simulation = kwargs.get(
            "deep_swap",
            kwargs.get(
                "swap_result",
                kwargs.get(
                    "swap_simulation_result",
                ),
            ),
        )

    # =====================================================
    # PENALTIES
    # =====================================================

    warnings = []

    penalty = 0

    penalty_breakdown = {}

    # -----------------------------------------------------
    # Individual engine penalties
    # -----------------------------------------------------

    security_penalty = _security_penalty(
        security,
        warnings,
    )

    penalty_breakdown[
        "Security"
    ] = security_penalty

    penalty += security_penalty

    liquidity_penalty = _liquidity_penalty(
        liquidity,
        warnings,
    )

    penalty_breakdown[
        "Liquidity"
    ] = liquidity_penalty

    penalty += liquidity_penalty

    holder_penalty = _holder_penalty(
        holders,
        warnings,
    )

    penalty_breakdown[
        "Holder concentration"
    ] = holder_penalty

    penalty += holder_penalty

    lp_penalty = _lp_penalty(
        lp_safety,
        warnings,
    )

    penalty_breakdown[
        "LP safety"
    ] = lp_penalty

    penalty += lp_penalty

    tax_penalty = _tax_penalty(
        tax_analysis,
        warnings,
    )

    penalty_breakdown[
        "Tax"
    ] = tax_penalty

    penalty += tax_penalty

    ownership_penalty = _ownership_penalty(
        ownership,
        warnings,
    )

    penalty_breakdown[
        "Ownership"
    ] = ownership_penalty

    penalty += ownership_penalty

    trade_safety_penalty = _trade_safety_penalty(
        trade_safety,
        warnings,
    )

    penalty_breakdown[
        "Trade safety"
    ] = trade_safety_penalty

    penalty += trade_safety_penalty

    simulation_penalty = _simulation_penalty(
        trade_simulation,
        warnings,
    )

    penalty_breakdown[
        "Trade simulation"
    ] = simulation_penalty

    penalty += simulation_penalty

    honeypot_penalty = _honeypot_penalty(
        honeypot,
        warnings,
    )

    penalty_breakdown[
        "Honeypot / sellability"
    ] = honeypot_penalty

    penalty += honeypot_penalty

    swap_penalty = _swap_execution_penalty(
        swap_simulation,
        warnings,
    )

    penalty_breakdown[
        "Deep swap execution"
    ] = swap_penalty

    penalty += swap_penalty

    proxy_penalty = _proxy_penalty(
        proxy,
        implementation,
        warnings,
    )

    penalty_breakdown[
        "Proxy"
    ] = proxy_penalty

    penalty += proxy_penalty

    # =====================================================
    # EVIDENCE-BASED RISK FLOORS
    # =====================================================
    #
    # These are applied only when concrete evidence exists.
    # UNKNOWN / UNAVAILABLE by themselves do not create risk.
    #

    # -----------------------------------------------------
    # No supported liquidity
    # -----------------------------------------------------

    penalty_breakdown[
        "Evidence-based floors"
    ] = 0

    liquidity_found = None

    if isinstance(
        liquidity,
        dict,
    ):

        liquidity_found = liquidity.get(
            "found"
        )

    if (
        liquidity_found is False
        or (
            isinstance(
                liquidity,
                dict,
            )
            and str(
                liquidity.get(
                    "risk",
                    "",
                )
            ).upper()
            == "NONE"
        )
    ):

        penalty += 25

        penalty_breakdown[
            "Evidence: No liquidity"
        ] = 25

        penalty_breakdown[
            "Evidence-based floors"
        ] += 25

        warning = (
            "No supported liquidity pool was detected."
        )

        if warning not in warnings:

            warnings.append(
                warning
            )

    # -----------------------------------------------------
    # Holder concentration
    # -----------------------------------------------------

    if isinstance(
        holders,
        dict,
    ):

        coverage = str(
            holders.get(
                "coverage",
                "",
            )
        ).upper()

        largest_wallet = holders.get(
            "largest_wallet"
        )

        top5 = holders.get(
            "top5"
        )

        top10 = holders.get(
            "top10"
        )

        try:

            largest_wallet = float(
                largest_wallet
            )

        except (
            TypeError,
            ValueError,
        ):

            largest_wallet = None

        try:

            top5 = float(
                top5
            )

        except (
            TypeError,
            ValueError,
        ):

            top5 = None

        try:

            top10 = float(
                top10
            )

        except (
            TypeError,
            ValueError,
        ):

            top10 = None

        # Partial coverage is still a warning signal when
        # the discovered concentration is extreme.

        if (
            coverage == "PARTIAL"
            and largest_wallet is not None
            and largest_wallet >= 50
        ):

            penalty += 20

            penalty_breakdown[
                "Evidence: Extreme concentration"
            ] = 20

            penalty_breakdown[
                "Evidence-based floors"
            ] += 20

            warning = (
                "Extreme discovered holder concentration "
                "was detected despite partial coverage."
            )

            if warning not in warnings:

                warnings.append(
                    warning
                )

        elif (
            coverage == "COMPLETE"
            and largest_wallet is not None
            and largest_wallet >= 50
        ):

            penalty += 30

            penalty_breakdown[
                "Evidence: Extreme concentration"
            ] = 30

            penalty_breakdown[
                "Evidence-based floors"
            ] += 30

            warning = (
                "A single holder controls an extremely "
                "large share of token supply."
            )

            if warning not in warnings:

                warnings.append(
                    warning
                )

        # -------------------------------------------------
        # Top 10 concentration
        # -------------------------------------------------

        if (
            top10 is not None
            and top10 >= 80
        ):

            penalty += 10

            penalty_breakdown[
                "Evidence: Top 10 concentration"
            ] = 10

            penalty_breakdown[
                "Evidence-based floors"
            ] += 10

            warning = (
                "The top 10 discovered holders control "
                f"{top10:.2f}% of supply."
            )

            if warning not in warnings:

                warnings.append(
                    warning
                )

    # =====================================================
    # LIMIT PENALTY
    # =====================================================

    penalty = max(
        0,
        min(
            int(
                penalty
            ),
            100,
        ),
    )

    # =====================================================
    # RISK SCORE
    # =====================================================

    score = penalty

    score = max(
        0,
        min(
            100,
            score
        )
    )

    if score >= 75:

        risk = "CRITICAL"

    elif score >= 50:

        risk = "HIGH"

    elif score >= 25:

        risk = "MEDIUM"

    else:

        risk = "LOW"

    # =====================================================
    # POSITIVE SIGNALS
    # =====================================================

    positives = _positive_signals(
        liquidity,
        lp_safety,
        holders,
        security,
        trade_simulation,
        honeypot,
        swap_simulation,
    )

    # =====================================================
    # RETURN
    # =====================================================

    return {
        "score": score,
        "risk": risk,
        "breakdown": penalty_breakdown,
        "warnings": warnings,
        "positive_signals": positives,
    }


# =========================================================
# COMPATIBILITY WRAPPERS
# =========================================================

def analyze(
    *args,
    **kwargs,
):
    return calculate_overall_risk(
        *args,
        **kwargs,
    )


def get_overall_risk(
    *args,
    **kwargs,
):
    return calculate_overall_risk(
        *args,
        **kwargs,
    )