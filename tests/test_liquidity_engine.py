from core.lp import get_pair
from engines.liquidity_engine import analyze_liquidity


ADDRESS = "0xa9a2fbff17ad742383a4ca357c437af661dfee70"


pair = get_pair(ADDRESS)

print("Token:", ADDRESS)
print("Pair:", pair)

if pair is None:
    print("No Uniswap V2 WETH pair found.")
else:
    result = analyze_liquidity(pair)
    print(result)
