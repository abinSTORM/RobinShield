from core.abi import get_abi
from core.abi_analyzer import has_function

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

abi = get_abi(address)

functions = [
    "mint",
    "owner",
    "transferOwnership",
    "renounceOwnership",
    "buyTaxRate",
    "sellTaxRate",
]

for function in functions:

    print(function, "->", has_function(abi, function))