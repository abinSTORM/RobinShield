from holders import get_holders
from holders import get_top_holders_percentage
from scanner import get_token_info

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

holders = get_holders(address)

token = get_token_info(address)

percentage = get_top_holders_percentage(
    holders,
    token["supply"] * (10 ** token["decimals"]),
    10
)

print("Top 10 Wallets")
print(percentage)