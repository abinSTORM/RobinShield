from web3 import Web3

from config import RPC_URL


# =========================================================
# KNOWN FUNCTION SELECTORS
# =========================================================

KNOWN_SELECTORS = {
    # ERC20
    "a9059cbb": "transfer(address,uint256)",
    "23b872dd": "transferFrom(address,address,uint256)",
    "095ea7b3": "approve(address,uint256)",
    "70a08231": "balanceOf(address)",
    "18160ddd": "totalSupply()",

    # Ownership
    "8da5cb5b": "owner()",
    "715018a6": "renounceOwnership()",
    "f2fde38b": "transferOwnership(address)",

    # Common mint/burn
    "40c10f19": "mint(address,uint256)",
    "a0712d68": "mint(uint256)",
    "42966c68": "burn(uint256)",
    "9dc29fac": "burn(address,uint256)",

    # Common blacklist
    "f9f92be4": "blacklist(address)",
    "e4997dc5": "unblacklist(address)",
    "44337ea1": "isBlacklisted(address)",

    # Pause
    "8456cb59": "pause()",
    "3f4ba83a": "unpause()",
    "5c975abb": "paused()",

    # Common trading controls
    "8a0c6b4b": "enableTrading()",
    "c9567bf9": "swapBack()",

    # Common tax functions
    "d8aed145": "setTax(uint256)",
}


# =========================================================
# WEB3
# =========================================================

def get_web3():

    w3 = Web3(
        Web3.HTTPProvider(RPC_URL)
    )

    if not w3.is_connected():
        raise ConnectionError(
            "Unable to connect to Robinhood Chain RPC."
        )

    return w3


# =========================================================
# BYTECODE
# =========================================================

def get_bytecode(address):

    w3 = get_web3()

    address = Web3.to_checksum_address(
        address
    )

    code = w3.eth.get_code(
        address
    )

    if not code:
        return None

    if code == b"\x00":
        return None

    return code


# =========================================================
# SELECTOR EXTRACTION
# =========================================================

def extract_selectors(bytecode):

    if not bytecode:
        return []

    data = bytes(bytecode)

    selectors = set()

    # PUSH4 opcode = 0x63
    #
    # Solidity dispatchers commonly contain:
    #
    # 63 <4-byte-selector>
    #
    # This is heuristic analysis only.

    for i in range(
        len(data) - 4
    ):

        if data[i] == 0x63:

            selector = data[
                i + 1:i + 5
            ].hex()

            selectors.add(
                selector
            )

    return sorted(
        selectors
    )


# =========================================================
# BYTECODE ANALYSIS
# =========================================================

def analyze_bytecode(address):

    result = {
        "available": False,
        "bytecode_size": 0,
        "selectors": [],
        "known_functions": [],
        "signals": [],
        "warnings": [],
    }

    try:

        bytecode = get_bytecode(
            address
        )

    except Exception as e:

        result["warnings"].append(
            f"Unable to read contract bytecode: {e}"
        )

        return result

    if not bytecode:

        result["warnings"].append(
            "No deployed contract bytecode was found."
        )

        return result

    result["available"] = True

    result["bytecode_size"] = len(
        bytecode
    )

    selectors = extract_selectors(
        bytecode
    )

    result["selectors"] = selectors

    known_functions = []

    for selector in selectors:

        if selector in KNOWN_SELECTORS:

            known_functions.append(
                KNOWN_SELECTORS[selector]
            )

    result["known_functions"] = sorted(
        set(known_functions)
    )

    # -----------------------------------------------------
    # DANGEROUS / IMPORTANT FUNCTIONS
    # -----------------------------------------------------

    mint_functions = [
        fn
        for fn in known_functions
        if fn.startswith("mint")
    ]

    blacklist_functions = [
        fn
        for fn in known_functions
        if (
            "blacklist" in fn.lower()
            or "unblacklist" in fn.lower()
        )
    ]

    ownership_functions = [
        fn
        for fn in known_functions
        if (
            fn.startswith("owner")
            or fn.startswith("renounceOwnership")
            or fn.startswith("transferOwnership")
        )
    ]

    pause_functions = [
        fn
        for fn in known_functions
        if (
            fn.startswith("pause")
            or fn.startswith("unpause")
        )
    ]

    tax_functions = [
        fn
        for fn in known_functions
        if (
            "tax" in fn.lower()
            or "fee" in fn.lower()
        )
    ]

    # -----------------------------------------------------
    # SIGNALS
    # -----------------------------------------------------

    if mint_functions:

        result["warnings"].append(
            "Potential mint functionality detected "
            "from contract bytecode."
        )

    if blacklist_functions:

        result["warnings"].append(
            "Potential blacklist functionality detected "
            "from contract bytecode."
        )

    if tax_functions:

        result["signals"].append(
            "Tax/fee-related function selectors detected "
            "in contract bytecode."
        )

    if ownership_functions:

        result["signals"].append(
            "Ownership-related function selectors detected."
        )

    if pause_functions:

        result["signals"].append(
            "Pause-related function selectors detected."
        )

    if not known_functions:

        result["signals"].append(
            "No recognized high-level function selectors "
            "were identified in bytecode."
        )

    return result