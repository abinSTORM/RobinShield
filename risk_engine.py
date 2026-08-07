def calculate_score(report):

    score = 0

    for item in report:

        check = item["check"]
        status = item["status"]

        if check == "Mint Function" and status == "PASS":
            score += 25

        elif check == "Ownership" and status == "PASS":
            score += 20

        elif check == "Blacklist" and status == "PASS":
            score += 25

        elif check == "Tax Functions" and status == "PASS":
            score += 10

        elif check == "Tax Functions" and status == "INFO":
            score += 5

    return score


def get_risk(score):

    if score >= 90:
        return "LOW"

    elif score >= 70:
        return "MEDIUM"

    return "HIGH"