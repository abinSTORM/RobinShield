from abi import get_abi
from function_index import build_function_index
from blacklist_detector import scan

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

abi = get_abi(address)

functions = build_function_index(abi)

result = scan(functions)

print(result)