from core.abi import get_abi
from core.function_index import build_function_index
from core.detector import detect_functions

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

abi = get_abi(address)

functions = build_function_index(abi)

checks = [
    "mint",
    "owner",
    "transferOwnership",
    "renounceOwnership",
    "buyTaxRate",
    "sellTaxRate"
]

result = detect_functions(functions, checks)

print(result)