from core.cache import save_cache
from core.cache import load_cache

address = "0x123456"

data = {
    "name": "GameCoin",
    "holders": 860,
    "risk": "LOW"
}

save_cache(address, data)

loaded = load_cache(address)

print(loaded)