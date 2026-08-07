from analysis.verifier import get_contract_info

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

info = get_contract_info(address)

print(info.keys())