import requests

BASE_URL = "https://robinhoodchain.blockscout.com/api/v2"


def get_holders(address):

    url = f"{BASE_URL}/tokens/{address}/holders"

    response = requests.get(url)

    if response.status_code != 200:
        return None

    return response.json()

def calculate_top_holder_percentage(holders, total_supply):

    if not holders:
        return 0

    top_balance = int(holders["items"][0]["value"])

    percentage = (top_balance / total_supply) * 100

    return round(percentage, 2)

def is_lp_wallet(holder):

    name = holder["address"].get("name")

    if not name:
        return False

    name = name.lower()

    keywords = [
        "uniswap",
        "pair",
        "pool",
        "lp",
        "liquidity"
    ]

    for keyword in keywords:
        if keyword in name:
            return True

    return False

def is_burn_wallet(holder):

    address = holder["address"]["hash"].lower()

    burn_addresses = [
        "0x0000000000000000000000000000000000000000",
        "0x000000000000000000000000000000000000dead",
    ]

    return address in burn_addresses


def should_ignore_holder(holder):

    if is_lp_wallet(holder):
        return True

    if is_burn_wallet(holder):
        return True

    return False


def get_largest_wallet(holders):

    for holder in holders["items"]:

        if should_ignore_holder(holder):
            continue

        return holder

    return None


def calculate_wallet_percentage(balance, total_supply):

    percentage = (int(balance) / total_supply) * 100

    return round(percentage, 2)

def get_top5_percentage(holders, total_supply):

    total_balance = 0

    count = 0

    for holder in holders["items"]:

        if should_ignore_holder(holder):
            continue

        total_balance += int(holder["value"])

        count += 1

        if count == 5:
            break

    percentage = (total_balance / total_supply) * 100

    return round(percentage, 2)

def get_top10_percentage(holders, total_supply):

    total_balance = 0

    count = 0

    for holder in holders["items"]:

        if should_ignore_holder(holder):
            continue

        total_balance += int(holder["value"])

        count += 1

        if count == 10:
            break

    percentage = (total_balance / total_supply) * 100

    return round(percentage, 2)

def get_top_holders_percentage(
    holders,
    total_supply,
    limit,
):

    total_balance = 0

    count = 0

    for holder in holders["items"]:

        if should_ignore_holder(holder):
            continue

        total_balance += int(holder["value"])

        count += 1

        if count == limit:
            break

    percentage = (total_balance / total_supply) * 100

    return round(percentage, 2)

def get_holder_risk(holders, total_supply):

    largest_wallet = get_largest_wallet(holders)

    if largest_wallet is None:
        return {
            "score": 100,
            "level": "HIGH",
            "reason": "No valid holders found."
        }

    largest_percentage = calculate_wallet_percentage(
        largest_wallet["value"],
        total_supply
    )

    top5 = get_top_holders_percentage(
        holders,
        total_supply,
        5
    )

    top10 = get_top_holders_percentage(
        holders,
        total_supply,
        10
    )

    score = 0

    reasons = []

    # Largest wallet
    if largest_percentage > 20:
        score += 40
        reasons.append("Largest wallet owns over 20%")

    elif largest_percentage > 10:
        score += 20
        reasons.append("Largest wallet owns over 10%")

    # Top 5
    if top5 > 50:
        score += 30
        reasons.append("Top 5 wallets own over 50%")

    elif top5 > 30:
        score += 15
        reasons.append("Top 5 wallets own over 30%")

    # Top 10
    if top10 > 70:
        score += 30
        reasons.append("Top 10 wallets own over 70%")

    elif top10 > 50:
        score += 15
        reasons.append("Top 10 wallets own over 50%")

    if score <= 20:
        level = "LOW"

    elif score <= 50:
        level = "MEDIUM"

    else:
        level = "HIGH"

    return {
        "score": score,
        "level": level,
        "largest_wallet": largest_percentage,
        "top5": top5,
        "top10": top10,
        "reasons": reasons
    }