import requests

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

url = (
    "https://robinhoodchain.blockscout.com/api/"
    f"?module=contract&action=getabi&address={address}"
)

response = requests.get(url)

print("Status:", response.status_code)
print(response.text)