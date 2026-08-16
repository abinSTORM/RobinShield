def calculate_score(report):

    score = 100

    for item in report:

        check = item.get(
            "check",
            ""
        )

        status = item.get(
            "status",
            "UNKNOWN"
        )

        confidence = item.get(
            "confidence",
            "LOW"
        )

        # ==================================================
        # CONTRACT VERIFICATION
        # ==================================================

        if check == "Contract Verification":

            if status == "FAIL":

                score -= 25

        # ==================================================
        # BYTECODE ANALYSIS
        # ==================================================

        elif check == "Bytecode Analysis":

            if status == "FAIL":

                score -= 30

        # ==================================================
        # MINT
        # ==================================================

        elif check == "Mint Function":

            if status == "FAIL":

                score -= 30

        # ==================================================
        # BLACKLIST
        # ==================================================

        elif check == "Blacklist":

            if status == "FAIL":

                score -= 25

        # ==================================================
        # TAX
        # ==================================================

        elif check == "Tax Functions":

            if status == "INFO":

                score -= 5

        elif (
            check == "Tax Functions"
            and status == "FAIL"
        ):

            score -= 20

        # ==================================================
        # OWNERSHIP
        # ==================================================

        elif check == "Ownership":

            if status == "INFO":

                # We detected ownership functionality,
                # but cannot determine whether ownership
                # is currently renounced.
                score -= 5

            elif status == "FAIL":

                score -= 15

        # ==================================================
        # PAUSE
        # ==================================================

        elif check == "Pause Functions":

            if status == "INFO":

                score -= 5

            elif status == "FAIL":

                score -= 15

    score = max(
        0,
        min(score, 100)
    )

    return score


def get_risk(score):

    if score >= 80:

        return "LOW"

    elif score >= 55:

        return "MEDIUM"

    return "HIGH"