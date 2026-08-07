import requests

address = "0xb0BAf0A19Da434DE5d40d91d3264978CC1997777"

url = f"https://robinhoodchain.blockscout.com/api/v2/smart-contracts/{address}"

response = requests.get(url)

print("Status:", response.status_code)

try:
    data = response.json()

    print()

    print(data.keys())

except Exception:

    print(response.text)