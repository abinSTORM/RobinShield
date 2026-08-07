from abi import get_abi

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

abi = get_abi(address)

print(type(abi))

print(len(abi))

print()

for item in abi[:10]:

    print(item["type"], item.get("name"))