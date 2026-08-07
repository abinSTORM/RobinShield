import json
import os

CACHE_DIR = "cache"


def ensure_cache_folder():

    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)


def get_cache_path(address):

    ensure_cache_folder()

    return os.path.join(CACHE_DIR, f"{address.lower()}.json")


def save_cache(address, data):

    path = get_cache_path(address)

    with open(path, "w") as file:
        json.dump(data, file, indent=4)


def load_cache(address):

    path = get_cache_path(address)

    if not os.path.exists(path):
        return None

    with open(path, "r") as file:
        return json.load(file)