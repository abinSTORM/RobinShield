from core.lp import get_pair
from engines.liquidity_engine import analyze_liquidity

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

pair = get_pair(address)

result = analyze_liquidity(pair)

print(result)