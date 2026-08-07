from analysis.holders import get_holders
from analysis.holders import get_holder_risk
from core.scanner import get_token_info

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

holders = get_holders(address)

token = get_token_info(address)

risk = get_holder_risk(
    holders,
    token["supply"] * (10 ** token["decimals"])
)

print("Holder Risk")
print("----------------")

print("Level:", risk["level"])
print("Score:", risk["score"])

print()

print("Largest Wallet:", risk["largest_wallet"], "%")
print("Top 5:", risk["top5"], "%")
print("Top 10:", risk["top10"], "%")

print()

print("Reasons:")

for reason in risk["reasons"]:
    print("-", reason)