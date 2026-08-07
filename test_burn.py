from holders import get_holders
from holders import is_burn_wallet

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

holders = get_holders(address)

found = False

for holder in holders["items"]:

    if is_burn_wallet(holder):
        print("🔥 Burn Wallet Found")
        print(holder["address"]["hash"])
        print(holder["value"])
        found = True

if not found:
    print("No burn wallet found.")