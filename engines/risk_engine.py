def _get_security_items(report):
    """
    Extract security checks from either:

    1. A list of checks
    2. A dictionary returned by security_scan()
    """

    if isinstance(report, list):
        return report

    if isinstance(report, dict):

        security = report.get(
            "security",
            []
        )

        if isinstance(security, list):
            return security

    return []


def calculate_score(report):
    """
    Calculate CONTRACT SECURITY score.

    100 = lowest detected contract risk
    0   = highest detected contract risk

    This engine only evaluates contract-security checks.
    It does NOT evaluate liquidity, holders, honeypot,
    trade simulation, or market conditions.
    """

    items = _get_security_items(report)

    # Start from safest score.
    score = 100

    for item in items:

        if not isinstance(item, dict):
            continue

        check = str(
            item.get(
                "check",
                ""
            )
        ).strip()

        status = str(
            item.get(
                "status",
                "UNKNOWN"
            )
        ).upper()

        # ==================================================
        # CONTRACT VERIFICATION
        # ==================================================

        if check == "Contract Verification":

            if status == "FAIL":

                # Unverified source reduces transparency
                # and confidence, but does not prove
                # malicious behavior.
                score -= 10

            elif status == "WARNING":

                score -= 5

        # ==================================================
        # BYTECODE ANALYSIS
        # ==================================================

        elif check == "Bytecode Analysis":

            if status == "FAIL":

                score -= 30

            elif status == "WARNING":

                score -= 15

        # ==================================================
        # MINT FUNCTION
        # ==================================================

        elif check == "Mint Function":

            if status == "FAIL":

                score -= 30

            elif status == "WARNING":

                score -= 15

            elif status == "INFO":

                score -= 5

        # ==================================================
        # BLACKLIST
        # ==================================================

        elif check == "Blacklist":

            if status == "FAIL":

                score -= 30

            elif status == "WARNING":

                score -= 15

            elif status == "INFO":

                score -= 5

        # ==================================================
        # TAX FUNCTIONS
        # ==================================================

        elif check == "Tax Functions":

            if status == "FAIL":

                score -= 20

            elif status == "WARNING":

                score -= 10

            elif status == "INFO":

                # Tax functions existing alone is not
                # automatically dangerous. Actual tax
                # percentage is handled separately by
                # tax_analysis.py.
                score -= 2

        # ==================================================
        # OWNERSHIP
        # ==================================================

        elif check == "Ownership":

            if status == "FAIL":

                score -= 20

            elif status == "WARNING":

                score -= 10

            elif status == "INFO":

                # Ownership functions existing is normal.
                # Do not heavily punish the score.
                score -= 2

        # ==================================================
        # PAUSE FUNCTIONS
        # ==================================================

        elif check == "Pause Functions":

            if status == "FAIL":

                score -= 20

            elif status == "WARNING":

                score -= 10

            elif status == "INFO":

                score -= 3

        # ==================================================
        # TRADING CONTROLS
        # ==================================================

        elif check == "Trading Controls":

            if status == "FAIL":

                score -= 30

            elif status == "WARNING":

                score -= 15

            elif status == "INFO":

                score -= 5

        # ==================================================
        # UNKNOWN SECURITY CHECKS
        # ==================================================

        else:

            if status == "FAIL":

                score -= 10

            elif status == "WARNING":

                score -= 5

    # ======================================================
    # LIMIT SCORE
    # ======================================================

    score = max(
        0,
        min(
            int(score),
            100
        )
    )

    return score


def get_risk(score):
    """
    Convert CONTRACT SECURITY score to risk level.

    Higher score = lower detected contract risk.
    """

    try:

        score = int(score)

    except (
        TypeError,
        ValueError
    ):

        return "HIGH"

    # ======================================================
    # RISK LEVELS
    # ======================================================

    if score >= 85:

        return "LOW"

    elif score >= 60:

        return "MEDIUM"

    return "HIGH"