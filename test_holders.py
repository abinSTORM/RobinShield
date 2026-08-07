from holders import get_holders

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

holders = get_holders(address)

print()

for holder in holders["items"][:5]:

    print(holder["address"]["hash"])

    print(holder["value"])

    print()