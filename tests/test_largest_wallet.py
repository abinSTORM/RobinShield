from analysis.holders import (
    get_holders,
    get_largest_wallet,
    calculate_wallet_percentage,
)

from core.scanner import get_token_info

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

holders = get_holders(address)

wallet = get_largest_wallet(holders)

token = get_token_info(address)

percentage = calculate_wallet_percentage(
    wallet["value"],
    token["supply"] * (10 ** token["decimals"])
)

print("Largest Wallet")
print(wallet["address"]["hash"])
print()

print("Percentage")
print(percentage)