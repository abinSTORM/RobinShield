from core.abi import get_abi


def has_function(abi, function_name):
    """
    Return True if the ABI contains the requested function.
    """

    if not isinstance(abi, list):
        return False

    for item in abi:

        if not isinstance(item, dict):
            continue

        if item.get("type") != "function":
            continue

        if item.get("name") == function_name:
            return True

    return False