from holders import get_holders
from scanner import get_token_info
from holders import calculate_top_holder_percentage

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

holders = get_holders(address)

token = get_token_info(address)

percentage = calculate_top_holder_percentage(
    holders,
    token["supply"] * 10**18
)

print(percentage)