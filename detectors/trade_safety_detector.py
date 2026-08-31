def _normalize_functions(functions):
    """
    Convert different function representations into a clean
    set of function names.

    Supported inputs:
    - ["balanceOf", "transfer"]
    - [{"name": "balanceOf"}]
    - [{"function": "balanceOf(address)"}]
    - [{"function": "balanceOf"}]
    """

    names = set()

    if not functions:
        return names

    if isinstance(functions, dict):
        functions = functions.values()

    if not isinstance(
        functions,
        (list, tuple, set),
    ):
        return names

    for item in functions:

        if isinstance(item, str):

            name = item.strip()

            if name:
                names.add(name)

            continue

        if not isinstance(item, dict):
            continue

        name = (
            item.get("name")
            or item.get("function")
            or item.get("selector")
        )

        if not name:
            continue

        name = str(name).strip()

        if name:
            names.add(name)

    return names


def _base_function_name(name):
    """
    Convert:

        balanceOf(address)

    into:

        balanceOf
    """

    return str(
        name
    ).split(
        "(",
        1,
    )[0].strip()


def _contains_any(name, terms):
    """
    Case-insensitive substring matching.
    """

    lowered = str(
        name
    ).lower()

    return any(
        str(term).lower() in lowered
        for term in terms
    )


def _find_functions(
    function_names,
    terms,
):
    """
    Return sorted function names matching any supplied term.
    """

    return sorted(
        {
            name
            for name in function_names
            if _contains_any(
                name,
                terms,
            )
        }
    )


def analyze_trade_safety(
    functions,
    tax_analysis=None,
):
    """
    Static trade-safety analysis.

    This does NOT execute a buy or sell.

    It analyzes ABI / function information for mechanisms
    that may affect trading.

    tax_analysis may be the result returned by
    engines.tax_analysis.analyze_tax().

    Tax-related function names alone are NOT automatically
    considered medium risk. Actual measured tax information
    is used when available.
    """

    normalized = _normalize_functions(
        functions
    )

    # ==================================================
    # ABI / FUNCTION INFORMATION UNAVAILABLE
    # ==================================================

    if not normalized:

        return {
            "status": "UNKNOWN",
            "risk": "LOW",
            "confidence": "LOW",
            "warnings": [
                "Token function information could not be "
                "determined from the available analysis."
            ],
            "signals": [
                "Trade-safety analysis requires ABI or "
                "bytecode-derived function information."
            ],
        }

    # ==================================================
    # NORMALIZE FUNCTION NAMES
    # ==================================================

    function_names = {
        _base_function_name(name)
        for name in normalized
    }

    warnings = []
    signals = []

    # ==================================================
    # BLACKLIST / BLOCKLIST
    # ==================================================

    blacklist_terms = [
        "blacklist",
        "isblacklisted",
        "blacklisted",
        "addblacklist",
        "removeblacklist",
        "blocked",
        "isblocked",
        "blockaddress",
        "denylist",
        "denied",
    ]

    blacklist_found = _find_functions(
        function_names,
        blacklist_terms,
    )

    if blacklist_found:

        warnings.append(
            "Blacklist/blocking functionality detected: "
            + ", ".join(
                blacklist_found
            )
        )

    # ==================================================
    # WHITELIST / ALLOWLIST
    # ==================================================

    whitelist_terms = [
        "whitelist",
        "iswhitelisted",
        "addwhitelist",
        "removewhitelist",
        "allowlist",
        "isallowlisted",
    ]

    whitelist_found = _find_functions(
        function_names,
        whitelist_terms,
    )

    if whitelist_found:

        warnings.append(
            "Whitelist/allowlist functionality detected: "
            + ", ".join(
                whitelist_found
            )
        )

    # ==================================================
    # TRADING CONTROLS
    # ==================================================

    trading_terms = [
        "tradingenabled",
        "enabletrading",
        "disabletrading",
        "tradingopen",
        "tradingactive",
        "tradingstatus",
        "tradingstate",
        "opentrading",
        "closetrading",
        "settrading",
        "settradingenabled",
    ]

    trading_found = _find_functions(
        function_names,
        trading_terms,
    )

    if trading_found:

        warnings.append(
            "Trading control functionality detected: "
            + ", ".join(
                trading_found
            )
        )

    # ==================================================
    # MAX TX / MAX WALLET / TRANSFER LIMITS
    # ==================================================

    limit_terms = [
        "maxtx",
        "maxtransaction",
        "maxwallet",
        "maxhold",
        "maxholding",
        "transactionlimit",
        "walletlimit",
        "maxbuy",
        "maxsell",
        "maxtransfer",
        "maximumtx",
        "maximumwallet",
        "setmaxtx",
        "setmaxwallet",
        "setmaxtransaction",
    ]

    limit_found = _find_functions(
        function_names,
        limit_terms,
    )

    if limit_found:

        warnings.append(
            "Transaction/wallet limit functionality "
            "detected: "
            + ", ".join(
                limit_found
            )
        )

    # ==================================================
    # COOLDOWN / TRANSFER DELAY
    # ==================================================

    cooldown_terms = [
        "cooldown",
        "transferdelay",
        "delayenabled",
        "cooldownenabled",
        "cooldownactive",
        "setcooldown",
    ]

    cooldown_found = _find_functions(
        function_names,
        cooldown_terms,
    )

    if cooldown_found:

        warnings.append(
            "Cooldown/transfer-delay functionality "
            "detected: "
            + ", ".join(
                cooldown_found
            )
        )

    # ==================================================
    # PAUSE / TRANSFER STOP CONTROLS
    # ==================================================

    pause_terms = [
        "pause",
        "unpause",
        "paused",
        "setpaused",
        "pausecontract",
        "pausetrading",
        "pausetransfers",
        "disabletransfers",
        "enabletransfers",
    ]

    pause_found = _find_functions(
        function_names,
        pause_terms,
    )

    if pause_found:

        warnings.append(
            "Pause/transfer control functionality "
            "detected: "
            + ", ".join(
                pause_found
            )
        )

    # ==================================================
    # TAX / FEE FUNCTIONS
    # ==================================================

    tax_terms = [
        "tax",
        "fee",
        "buytax",
        "selltax",
        "taxrate",
        "feerate",
        "buyfee",
        "sellfee",
        "marketingfee",
        "liquidityfee",
        "developmentfee",
        "devfee",
    ]

    tax_found = _find_functions(
        function_names,
        tax_terms,
    )

    if tax_found:

        signals.append(
            "Tax/fee-related functions detected: "
            + ", ".join(
                tax_found
            )
        )

    # ==================================================
    # DYNAMIC TAX / FEE SETTERS
    # ==================================================

    tax_setter_terms = [
        "settax",
        "setfee",
        "updatetax",
        "updatefee",
        "changetax",
        "changefee",
        "setbuytax",
        "setselltax",
        "settaxrate",
        "setfeerate",
        "setbuyfee",
        "setsellfee",
        "setmarketingfee",
        "setliquidityfee",
    ]

    tax_setter_found = _find_functions(
        function_names,
        tax_setter_terms,
    )

    if tax_setter_found:

        warnings.append(
            "Tax/fee values may be dynamically changed: "
            + ", ".join(
                tax_setter_found
            )
        )

    # ==================================================
    # FEE / LIMIT EXEMPTION CONTROLS
    # ==================================================

    exemption_terms = [
        "excludedfromfees",
        "excludefromfees",
        "isfeeexempt",
        "setfeeexempt",
        "excludedfromlimits",
        "excludefromlimits",
        "setexcludedfromlimits",
        "isexcluded",
        "feeexempt",
    ]

    exemption_found = _find_functions(
        function_names,
        exemption_terms,
    )

    if exemption_found:

        signals.append(
            "Fee/limit exemption functionality detected: "
            + ", ".join(
                exemption_found
            )
        )

    # ==================================================
    # MEASURED TAX ANALYSIS
    # ==================================================

    measured_tax_risk = None
    measured_buy_tax = None
    measured_sell_tax = None
    measured_general_tax = None

    if isinstance(
        tax_analysis,
        dict,
    ):

        measured_tax_risk = tax_analysis.get(
            "risk"
        )

        measured_buy_tax = tax_analysis.get(
            "buy_tax"
        )

        measured_sell_tax = tax_analysis.get(
            "sell_tax"
        )

        measured_general_tax = tax_analysis.get(
            "tax"
        )

        if measured_general_tax is None:

            measured_general_tax = tax_analysis.get(
                "general_tax"
            )

        if (
            measured_buy_tax is not None
            or measured_sell_tax is not None
            or measured_general_tax is not None
        ):

            values = []

            for value in [
                measured_buy_tax,
                measured_sell_tax,
                measured_general_tax,
            ]:

                if value is None:
                    continue

                try:

                    values.append(
                        float(value)
                    )

                except (
                    TypeError,
                    ValueError,
                ):

                    continue

            if values:

                maximum_tax = max(
                    values
                )

                signals.append(
                    "Measured maximum detected tax: "
                    f"{maximum_tax:.2f}%."
                )

                if maximum_tax <= 5:

                    signals.append(
                        "Measured tax level is relatively "
                        "low."
                    )

                elif maximum_tax <= 15:

                    warnings.append(
                        "Measured tax level is moderately "
                        "high."
                    )

                elif maximum_tax <= 30:

                    warnings.append(
                        "Measured tax level is high."
                    )

                else:

                    warnings.append(
                        "Measured tax level is extremely "
                        "high."
                    )

    # ==================================================
    # RESTRICTION COUNT
    # ==================================================

    severe_restriction_count = (
        len(blacklist_found)
        + len(trading_found)
        + len(pause_found)
    )

    general_restriction_count = (
        severe_restriction_count
        + len(whitelist_found)
        + len(limit_found)
        + len(cooldown_found)
    )

    # ==================================================
    # TAX RISK
    # ==================================================

    tax_risk_level = "LOW"

    measured_values = []

    for value in [
        measured_buy_tax,
        measured_sell_tax,
        measured_general_tax,
    ]:

        if value is None:
            continue

        try:

            measured_values.append(
                float(value)
            )

        except (
            TypeError,
            ValueError,
        ):

            pass

    if measured_values:

        maximum_tax = max(
            measured_values
        )

        if maximum_tax > 30:

            tax_risk_level = "HIGH"

        elif maximum_tax > 15:

            tax_risk_level = "MEDIUM"

        elif maximum_tax > 5:

            tax_risk_level = "MEDIUM"

    elif measured_tax_risk:

        normalized_tax_risk = str(
            measured_tax_risk
        ).upper()

        if normalized_tax_risk in [
            "HIGH",
            "CRITICAL",
        ]:

            tax_risk_level = "HIGH"

        elif normalized_tax_risk == "MEDIUM":

            tax_risk_level = "MEDIUM"

    # ==================================================
    # FINAL CLASSIFICATION
    # ==================================================

    if (
        blacklist_found
        and (
            trading_found
            or pause_found
        )
    ):

        status = "WARNING"
        risk = "HIGH"

        warnings.append(
            "Blacklist functionality combined with "
            "trading or transfer controls was detected."
        )

    elif severe_restriction_count >= 2:

        status = "WARNING"
        risk = "HIGH"

        warnings.append(
            "Multiple strong mechanisms capable of "
            "restricting trading were detected."
        )

    elif general_restriction_count >= 3:

        status = "WARNING"
        risk = "HIGH"

        warnings.append(
            "Multiple mechanisms capable of restricting "
            "trading behavior were detected."
        )

    elif tax_risk_level == "HIGH":

        status = "WARNING"
        risk = "HIGH"

    elif tax_setter_found:

        status = "WARNING"
        risk = "MEDIUM"

    elif general_restriction_count >= 1:

        status = "WARNING"
        risk = "MEDIUM"

    elif tax_risk_level == "MEDIUM":

        status = "WARNING"
        risk = "MEDIUM"

    else:

        status = "PASS"
        risk = "LOW"

        signals.append(
            "No major blacklist, trading restriction, "
            "pause, transaction-limit, wallet-limit, or "
            "cooldown mechanisms were detected."
        )

        if tax_found and not tax_setter_found:

            signals.append(
                "Tax-related functions were detected, but "
                "no recognized dynamic tax-setting function "
                "was found."
            )

    # ==================================================
    # CONFIDENCE
    # ==================================================

    confidence = "MEDIUM"

    if (
        blacklist_found
        or trading_found
        or limit_found
        or pause_found
        or cooldown_found
    ):

        confidence = "HIGH"

    if tax_analysis:

        confidence = "HIGH"

    # ==================================================
    # RESULT
    # ==================================================

    return {
        "status": status,
        "risk": risk,
        "confidence": confidence,
        "warnings": warnings,
        "signals": signals,
    }