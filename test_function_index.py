from abi import get_abi
from function_index import build_function_index

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

abi = get_abi(address)

functions = build_function_index(abi)

print("Total Functions")

print(len(functions))

print()

for function in sorted(functions):

    print(function)