from analysis.holders import get_holders
from analysis.holders import is_lp_wallet

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

holders = get_holders(address)

for holder in holders["items"][:10]:

    print(holder["address"]["name"])

    print(is_lp_wallet(holder))

    print()