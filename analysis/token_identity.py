"""On-chain token identity reporting and optional trusted-name comparison."""

import difflib
import unicodedata

from web3 import Web3

from config import RPC_URL


IDENTITY_ABI = [
    {"inputs": [], "name": "name", "outputs": [{"type": "string"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "symbol", "outputs": [{"type": "string"}], "stateMutability": "view", "type": "function"},
]

MUTABLE_METADATA_FUNCTIONS = {
    "setname", "settokenname", "updatename", "changename",
    "setsymbol", "settokensymbol", "updatesymbol", "changesymbol",
    "setmetadata", "updatemetadata",
}

# Common visual lookalikes. This is a review aid, not a complete Unicode
# confusables implementation and must never be treated as proof of fraud.
_CONFUSABLES = str.maketrans({
    "а": "a", "А": "a", "е": "e", "Е": "e", "о": "o", "О": "o",
    "р": "p", "Р": "p", "с": "c", "С": "c", "х": "x", "Х": "x",
    "у": "y", "У": "y", "і": "i", "І": "i", "ј": "j", "Ј": "j",
    "Α": "a", "Β": "b", "Ε": "e", "Ζ": "z", "Η": "h", "Ι": "i",
    "Κ": "k", "Μ": "m", "Ν": "n", "Ο": "o", "Ρ": "p", "Τ": "t",
    "Υ": "y", "Χ": "x", "ο": "o", "ρ": "p", "ν": "v", "ι": "i",
})


def _normalized(value):
    value = unicodedata.normalize("NFKC", str(value or "")).translate(_CONFUSABLES).casefold()
    return "".join(char for char in value if char.isalnum())


def _read_string(contract, function_name):
    try:
        value = getattr(contract.functions, function_name)().call()
        if isinstance(value, bytes):
            value = value.decode("utf-8", errors="replace").rstrip("\x00")
        return str(value)
    except Exception:
        return None


def _compare(actual, expected):
    if expected is None:
        return {"status": "NOT_CHECKED", "expected": None, "similarity": None}
    actual_norm = _normalized(actual)
    expected_norm = _normalized(expected)
    if not actual_norm:
        return {"status": "INCONCLUSIVE", "expected": expected, "similarity": None}
    if actual_norm == expected_norm:
        status = "MATCH" if str(actual) == str(expected) else "UNICODE_VARIANT_REVIEW"
        similarity = 1.0
    else:
        similarity = difflib.SequenceMatcher(None, actual_norm, expected_norm).ratio()
        status = "LOOKALIKE_REVIEW" if similarity >= 0.80 else "MISMATCH"
    return {"status": status, "expected": expected, "similarity": round(similarity, 4)}


def analyze_token_identity(address, abi=None, expected_name=None, expected_symbol=None, proxy=None):
    result = {
        "address": address,
        "name": None,
        "symbol": None,
        "name_comparison": _compare(None, expected_name),
        "symbol_comparison": _compare(None, expected_symbol),
        "metadata_mutability": {"functions": [], "proxy_upgradeable": False, "status": "UNKNOWN"},
        "warnings": [],
        "signals": [],
        "reference_source": "caller-supplied expected values" if expected_name is not None or expected_symbol is not None else None,
    }

    try:
        w3 = Web3(Web3.HTTPProvider(RPC_URL))
        if not w3.is_connected():
            raise ConnectionError("Token identity RPC unavailable.")
        contract = w3.eth.contract(address=Web3.to_checksum_address(address), abi=IDENTITY_ABI)
        result["name"] = _read_string(contract, "name")
        result["symbol"] = _read_string(contract, "symbol")
    except Exception as exc:
        result["warnings"].append(f"On-chain name/symbol could not be read: {exc}")

    result["name_comparison"] = _compare(result["name"], expected_name)
    result["symbol_comparison"] = _compare(result["symbol"], expected_symbol)

    if expected_name is None and expected_symbol is None:
        result["warnings"].append(
            "No trusted expected name or symbol was supplied; impersonation cannot be confirmed from the token's own metadata alone."
        )
    for field in ("name", "symbol"):
        value = result.get(field)
        if value and any(ord(char) > 127 for char in value):
            result["signals"].append(f"Token {field} contains non-ASCII characters; check for intentional or lookalike Unicode.")
    for field in ("name_comparison", "symbol_comparison"):
        comparison = result[field]
        if comparison["status"] in ("MISMATCH", "LOOKALIKE_REVIEW", "UNICODE_VARIANT_REVIEW"):
            result["warnings"].append(
                f"On-chain {field.removesuffix('_comparison')} differs from the caller-supplied expected identity ({comparison['status']}); this is a review signal, not proof of impersonation."
            )

    functions = {
        item.get("name", "").replace("_", "").lower()
        for item in (abi or [])
        if isinstance(item, dict) and item.get("type") == "function"
    }
    mutable = sorted(name for name in functions if name in MUTABLE_METADATA_FUNCTIONS)
    proxy_data = proxy if isinstance(proxy, dict) else {}
    upgradeable = proxy_data.get("upgradeable") is True
    result["metadata_mutability"] = {
        "functions": mutable,
        "proxy_upgradeable": upgradeable,
        "status": "POSSIBLE" if mutable or upgradeable else "NO_RECOGNIZED_MUTATOR",
    }
    if mutable or upgradeable:
        result["warnings"].append(
            "Recognized metadata setter or upgradeable proxy detected; name/symbol may be changeable. Custom mechanisms may not be recognized."
        )
    return result
