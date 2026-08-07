import requests

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

url = f"https://robinhoodchain.blockscout.com/api/v2/tokens/{address}/holders"

response = requests.get(url)

print(response.status_code)
print(response.text)