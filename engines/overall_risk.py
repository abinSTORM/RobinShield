# =========================================================
# SAFE HELPERS
# =========================================================

def _safe_dict(value):

    return value if isinstance(value, dict) else {}


def _safe_list(value):

    return value if isinstance(value, list) else []


def _add_unique(items, message):

    if message and message not in items:

        items.append(message)


# =========================================================
# SECURITY
# =========================================================

def _security_penalty(
    security,
    warnings,
):

    penalty = 0

    if isinstance(
        security,
        dict,
    ):

        security = security.get(
            "security",
            []
        )

    security = _safe_list(
        security
    )

    if not security:

        _add_unique(
            warnings,
            "Contract security results could not be determined.",
        )

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
        )

        status = str(
            item.get(
                "status",
                "UNKNOWN",
            )
        ).upper()

        if (
            check.lower()
            == "contract verification"
        ):

            if status == "FAIL":

                penalty += 3

                _add_unique(
                    warnings,
                    "Contract source verification failed.",
                )

            continue

        if status == "FAIL":

            penalty += 20

            _add_unique(
                warnings,
                f"Contract security check failed: {check}.",
            )

        elif status == "WARNING":

            penalty += 8

            _add_unique(
                warnings,
                f"Contract security warning: {check}.",
            )

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

    risk = str(
        liquidity.get(
            "risk",
            "UNKNOWN",
        )
    ).upper()

    liquidity_usd = liquidity.get(
        "liquidity_usd",
        0,
    )

    try:

        liquidity_usd = float(
            liquidity_usd or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        liquidity_usd = 0

    # -----------------------------------------------------
    # Unknown / unavailable is uncertainty, not danger.
    # -----------------------------------------------------

    if found is None:

        _add_unique(
            warnings,
            "Liquidity detection status is unknown.",
        )

        return 0

    if found is False:

        _add_unique(
            warnings,
            "No supported liquidity pool was detected.",
        )

        return 5

    # -----------------------------------------------------
    # Actual liquidity risk.
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
    # Pool exists but value unknown.
    # -----------------------------------------------------

    if liquidity_usd <= 0:

        _add_unique(
            warnings,
            "Liquidity value could not be reliably determined.",
        )

        return 0

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

    safety = str(
        lp_safety.get(
            "safety",
            lp_safety.get(
                "risk",
                "UNKNOWN",
            )
        )
    ).upper()

    # -----------------------------------------------------
    # UNKNOWN MUST NOT BE TREATED AS DANGEROUS.
    # -----------------------------------------------------

    if safety in (
        "UNKNOWN",
        "UNAVAILABLE",
        "",
    ):

        _add_unique(
            warnings,
            "LP safety could not be determined.",
        )

        return 0

    if safety in (
        "VERY HIGH",
        "HIGH",
        "SAFE",
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
# HOLDER RISK
# =========================================================

def _holder_penalty(
    holders,
    warnings,
):

    holders = _safe_dict(
        holders
    )

    level = str(
        holders.get(
            "risk",
            holders.get(
                "level",
                holders.get(
                    "holder_risk",
                    "UNKNOWN",
                )
            )
        )
    ).upper()

    coverage = str(
        holders.get(
            "coverage",
            "UNKNOWN",
        )
    ).upper()

    verified = bool(
        holders.get(
            "verified",
            holders.get(
                "_verified",
                False,
            )
        )
    )

    complete = bool(
        holders.get(
            "_complete",
            False,
        )
    )

    # -----------------------------------------------------
    # COMPLETE + VERIFIED
    # -----------------------------------------------------

    if (
        complete
        and verified
        and coverage == "COMPLETE"
    ):

        if level == "LOW":

            return 0

        if level == "MEDIUM":

            _add_unique(
                warnings,
                "Holder concentration is moderate.",
            )

            return 12

        if level == "HIGH":

            _add_unique(
                warnings,
                "Token ownership is highly concentrated.",
            )

            return 25

        _add_unique(
            warnings,
            "Holder risk classification is unknown.",
        )

        return 0

    # -----------------------------------------------------
    # PARTIAL / UNVERIFIED
    # -----------------------------------------------------

    if (
        coverage == "PARTIAL"
        or not complete
        or not verified
    ):

        _add_unique(
            warnings,
            "Holder distribution could not be fully verified.",
        )

        return 0

    # -----------------------------------------------------
    # UNKNOWN
    # -----------------------------------------------------

    _add_unique(
        warnings,
        "Holder distribution could not be determined.",
    )

    return 0


# =========================================================
# TAX
# =========================================================

def _tax_penalty(
    tax_analysis,
    warnings,
):

    tax_analysis = _safe_dict(
        tax_analysis
    )

    status = str(
        tax_analysis.get(
            "status",
            "UNKNOWN",
        )
    ).upper()

    risk = str(
        tax_analysis.get(
            "risk",
            "UNKNOWN",
        )
    ).upper()

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

    # A measured low tax with WARNING status
    # is only a small informational penalty.
    if (
        status == "WARNING"
        and risk == "LOW"
    ):

        return 3

    # Unknown tax analysis = uncertainty.
    if status in (
        "UNKNOWN",
        "UNAVAILABLE",
        "",
    ):

        _add_unique(
            warnings,
            "Tax behavior could not be fully determined.",
        )

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

    status = str(
        ownership.get(
            "status",
            "UNKNOWN",
        )
    ).upper()

    risk = str(
        ownership.get(
            "risk",
            "UNKNOWN",
        )
    ).upper()

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
            "Token retains potentially significant admin control.",
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

    status = str(
        trade_safety.get(
            "status",
            "UNKNOWN",
        )
    ).upper()

    risk = str(
        trade_safety.get(
            "risk",
            "UNKNOWN",
        )
    ).upper()

    if (
        status == "FAIL"
        or risk == "HIGH"
    ):

        _add_unique(
            warnings,
            "Trade safety analysis detected high-risk behavior.",
        )

        return 25

    if (
        status == "WARNING"
        and risk == "MEDIUM"
    ):

        _add_unique(
            warnings,
            "Trade safety analysis detected potentially risky trade functionality.",
        )

        return 8

    if (
        status == "WARNING"
        and risk == "LOW"
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

    status = str(
        simulation.get(
            "status",
            "UNKNOWN",
        )
    ).upper()

    risk = str(
        simulation.get(
            "risk",
            "UNKNOWN",
        )
    ).upper()

    buy = _safe_dict(
        simulation.get(
            "buy"
        )
    )

    sell = _safe_dict(
        simulation.get(
            "sell"
        )
    )

    buy_success = buy.get(
        "success"
    )

    sell_success = sell.get(
        "success"
    )

    if sell_success is False:

        _add_unique(
            warnings,
            "SELL quote simulation failed.",
        )

        return 30

    if buy_success is False:

        _add_unique(
            warnings,
            "BUY quote simulation failed.",
        )

        return 15

    # Unknown or unavailable = no danger penalty.
    if status in (
        "UNKNOWN",
        "UNAVAILABLE",
        "SKIPPED",
    ):

        return 0

    if (
        status == "WARNING"
        and risk == "HIGH"
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
# HONEYPOT
# =========================================================

def _honeypot_penalty(
    honeypot,
    warnings,
):

    honeypot = _safe_dict(
        honeypot
    )

    status = str(
        honeypot.get(
            "status",
            "UNKNOWN",
        )
    ).upper()

    risk = str(
        honeypot.get(
            "risk",
            "UNKNOWN",
        )
    ).upper()

    confidence = str(
        honeypot.get(
            "confidence",
            "LOW",
        )
    ).upper()

    buy = _safe_dict(
        honeypot.get(
            "buy"
        )
    )

    sell = _safe_dict(
        honeypot.get(
            "sell"
        )
    )

    sell_success = sell.get(
        "success"
    )

    # -----------------------------------------------------
    # Actual SELL-side failure.
    # -----------------------------------------------------

    if sell_success is False:

        _add_unique(
            warnings,
            "SELL-side transfer simulation failed. Possible honeypot or transfer restriction.",
        )

        if confidence == "HIGH":

            return 40

        return 25

    # -----------------------------------------------------
    # Explicit failure.
    # -----------------------------------------------------

    if status == "FAIL":

        _add_unique(
            warnings,
            "Honeypot analysis detected high-risk transfer behavior.",
        )

        return 30

    # -----------------------------------------------------
    # High risk.
    # -----------------------------------------------------

    if (
        risk == "HIGH"
        and status not in (
            "UNKNOWN",
            "UNAVAILABLE",
        )
    ):

        _add_unique(
            warnings,
            "Honeypot analysis detected high-risk transfer behavior.",
        )

        return 25

    # -----------------------------------------------------
    # Warning.
    # -----------------------------------------------------

    if status == "WARNING":

        _add_unique(
            warnings,
            "Honeypot analysis detected potentially restricted transfer behavior.",
        )

        if risk == "MEDIUM":

            return 12

        return 6

    # -----------------------------------------------------
    # Unknown/unavailable = zero risk penalty.
    # -----------------------------------------------------

    if status in (
        "UNKNOWN",
        "UNAVAILABLE",
    ):

        _add_unique(
            warnings,
            "Honeypot / sellability could not be fully determined.",
        )

        return 0

    return 0


    # -----------------------------------------------------
    # DEEP ROUTER
    # -----------------------------------------------------

    if (
        swap_simulation.get(
            "status"
        ) == "PASS"
        and
        swap_simulation.get(
            "risk"
        ) == "LOW"
        and
        swap_simulation.get(
            "tested"
        ) is True
    ):

        _add_unique(
            positives,
            "Deep router SELL execution succeeded in a temporary fork.",
        )

        # -------------------------------------------------
        # BUY execution
        # -------------------------------------------------

        buy_tests = swap_simulation.get(
            "buy_tests",
            []
        )

        buy_passed = 0
        buy_failed = 0

        if isinstance(
            buy_tests,
            list,
        ):

            for test in buy_tests:

                if not isinstance(
                    test,
                    dict,
                ):

                    continue

                if test.get(
                    "success"
                ) is True:

                    buy_passed += 1

                else:

                    buy_failed += 1

        # If the simulator exposes an explicit BUY success
        # flag, prefer that.
        deep_buy_success = (
            swap_simulation.get(
                "buy_success"
            )
        )

        if deep_buy_success is True:

            _add_unique(
                positives,
                "Deep router BUY execution succeeded in a temporary fork.",
            )

        elif (
            buy_tests
            and buy_failed == 0
            and buy_passed > 0
        ):

            _add_unique(
                positives,
                "Deep router BUY execution succeeded in a temporary fork.",
            )


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

    if str(
        liquidity.get(
            "risk",
            "",
        )
    ).upper() == "LOW":

        _add_unique(
            positives,
            "Liquidity level is healthy.",
        )

    # -----------------------------------------------------
    # LP SAFETY
    # -----------------------------------------------------

    if str(
        lp_safety.get(
            "safety",
            "",
        )
    ).upper() in (
        "VERY HIGH",
        "HIGH",
        "SAFE",
        "PASS",
    ):

        _add_unique(
            positives,
            "Almost all LP tokens are burned.",
        )

    # -----------------------------------------------------
    # HOLDERS
    #
    # Only claim healthy distribution when coverage is
    # actually complete and verified.
    # -----------------------------------------------------

    holder_level = str(
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
    ).upper()

    holder_coverage = str(
        holders.get(
            "coverage",
            "",
        )
    ).upper()

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

    if (
        holder_level == "LOW"
        and holder_verified
        and holder_complete
        and holder_coverage == "COMPLETE"
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

        security = security.get(
            "security",
            [],
        )

    security = _safe_list(
        security
    )

    failures = []

    for item in security:

        if not isinstance(
            item,
            dict,
        ):

            continue

        status = str(
            item.get(
                "status",
                "",
            )
        ).upper()

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

            failures.append(
                item
            )

    if (
        security
        and not failures
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
            "buy"
        )
    )

    sell = _safe_dict(
        simulation.get(
            "sell"
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
    # HONEYPOT / TRANSFER SIMULATION
    # -----------------------------------------------------

    hp_buy = _safe_dict(
        honeypot.get(
            "buy"
        )
    )

    hp_sell = _safe_dict(
        honeypot.get(
            "sell"
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
    # DEEP ROUTER EXECUTION
    # -----------------------------------------------------

    if (
        swap_simulation.get(
            "status"
        ) == "PASS"
        and
        swap_simulation.get(
            "risk"
        ) == "LOW"
        and
        swap_simulation.get(
            "tested"
        ) is True
    ):

        _add_unique(
            positives,
            "Deep router SELL execution succeeded in a temporary fork.",
        )

        # BUY result can be exposed directly by the simulator.
        if (
            swap_simulation.get(
                "buy_success"
            ) is True
        ):

            _add_unique(
                positives,
                "Deep router BUY execution succeeded in a temporary fork.",
            )

        else:

            buy_tests = swap_simulation.get(
                "buy_tests",
                [],
            )

            if (
                isinstance(
                    buy_tests,
                    list,
                )
                and buy_tests
                and all(
                    isinstance(
                        test,
                        dict,
                    )
                    and
                    test.get(
                        "success"
                    ) is True
                    for test in buy_tests
                )
            ):

                _add_unique(
                    positives,
                    "Deep router BUY execution succeeded in a temporary fork.",
                )

        # Combined signal when both are explicitly confirmed.
        if (
            swap_simulation.get(
                "buy_success"
            ) is True
        ):

            _add_unique(
                positives,
                "Deep BUY and SELL router execution both succeeded inside temporary local forks.",
            )

    # -----------------------------------------------------
    # IMPORTANT
    #
    # Always return a list.
    # -----------------------------------------------------

    return positives

# =====================================================
# DEEP SWAP EXECUTION
# =====================================================

def _swap_execution_penalty(
    swap_simulation,
    warnings,
):

    swap_simulation = _safe_dict(
        swap_simulation
    )

    status = str(
        swap_simulation.get(
            "status",
            "UNKNOWN",
        )
    ).upper()

    risk = str(
        swap_simulation.get(
            "risk",
            "UNKNOWN",
        )
    ).upper()

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
    # Infrastructure / unavailable.
    #
    # Do NOT treat this as token danger.
    # -----------------------------------------------------

    if status in (
        "UNKNOWN",
        "UNAVAILABLE",
        "SKIPPED",
    ):

        return 0

    # -----------------------------------------------------
    # Explicit high-risk execution failure.
    # -----------------------------------------------------

    if (
        status == "FAIL"
        or risk == "HIGH"
    ):

        _add_unique(
            warnings,
            "Deep router swap execution simulation detected a high-risk failure.",
        )

        return 25

    # -----------------------------------------------------
    # Partial / warning result.
    # -----------------------------------------------------

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

    **kwargs
):

    """
    RobinShield overall risk calculator.

    Important design rule:

    UNKNOWN / UNAVAILABLE
        = lack of evidence

    FAIL / HIGH RISK
        = evidence of danger
    """

    # =====================================================
    # NORMALIZE
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
                "liquidity_data"
            )
        )

    if not lp_safety:

        lp_safety = kwargs.get(
            "lp",
            kwargs.get(
                "lp_result",
                kwargs.get(
                    "lp_safety_result"
                )
            )
        )

    if not holders:

        holders = kwargs.get(
            "holder_distribution",
            kwargs.get(
                "holder_data",
                kwargs.get(
                    "holders_result"
                )
            )
        )

    if not security:

        security = kwargs.get(
            "contract_security",
            kwargs.get(
                "security_result"
            )
        )

    if not tax_analysis:

        tax_analysis = kwargs.get(
            "tax",
            kwargs.get(
                "tax_result"
            )
        )

    if not ownership:

        ownership = kwargs.get(
            "ownership_result"
        )

    if not trade_safety:

        trade_safety = kwargs.get(
            "trade_safety_result"
        )

    if not trade_simulation:

        trade_simulation = kwargs.get(
            "simulation",
            kwargs.get(
                "simulation_result"
            )
        )

    if not honeypot:

        honeypot = kwargs.get(
            "honeypot_result",
            kwargs.get(
                "sellability"
            )
        )

    if not swap_simulation:

        swap_simulation = kwargs.get(
            "deep_swap",
            kwargs.get(
                "swap_result",
                kwargs.get(
                    "swap_simulation_result"
                )
            )
        )

    # =====================================================
    # PENALTIES
    # =====================================================

    warnings = []

    penalty = 0

    penalty += _security_penalty(
        security,
        warnings,
    )

    penalty += _liquidity_penalty(
        liquidity,
        warnings,
    )

    penalty += _holder_penalty(
        holders,
        warnings,
    )

    penalty += _lp_penalty(
        lp_safety,
        warnings,
    )

    penalty += _tax_penalty(
        tax_analysis,
        warnings,
    )

    penalty += _ownership_penalty(
        ownership,
        warnings,
    )

    penalty += _trade_safety_penalty(
        trade_safety,
        warnings,
    )

    penalty += _simulation_penalty(
        trade_simulation,
        warnings,
    )

    penalty += _honeypot_penalty(
        honeypot,
        warnings,
    )

    penalty += _swap_execution_penalty(
        swap_simulation,
        warnings,
    )

    penalty += _proxy_penalty(
        proxy,
        implementation,
        warnings,
    )

    # =====================================================
    # SCORE
    # =====================================================

    penalty = max(
        0,
        min(
            int(
                penalty
            ),
            100,
        )
    )

    score = 100 - penalty

    score = max(
        0,
        min(
            int(
                score
            ),
            100,
        )
    )

    # =====================================================
    # RISK
    # =====================================================

    if score >= 80:

        risk = "LOW"

    elif score >= 55:

        risk = "MEDIUM"

    else:

        risk = "HIGH"

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
    # RETURN RESULT
    # =====================================================

    return {
        "score": score,
        "risk": risk,
        "warnings": warnings,
        "positive_signals": positives,
    }

# =========================================================
# PROXY PENALTY
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
        "detected"
    ):

        return 0

    proxy_type = proxy.get(
        "type",
        "UNKNOWN",
    )

    implementation_address = proxy.get(
        "implementation"
    )

    _add_unique(
        warnings,
        f"Token uses an {proxy_type} proxy.",
    )

    if implementation_address:

        _add_unique(
            warnings,
            f"Proxy implementation: {implementation_address}",
        )

    # Verified implementation = smaller complexity
    # penalty than an unverified implementation.
    if implementation.get(
        "verified"
    ) is True:

        return 2

    return 5


# =========================================================
# COMPATIBILITY
# =========================================================

def analyze(
    *args,
    **kwargs
):

    return calculate_overall_risk(
        *args,
        **kwargs
    )


def get_overall_risk(
    *args,
    **kwargs
):

    return calculate_overall_risk(
        *args,
        **kwargs
    )