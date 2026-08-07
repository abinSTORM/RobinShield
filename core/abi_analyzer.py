from abi import get_abi


def has_function(abi, function_name):

    if abi is None:
        return False

    for item in abi:

        if item["type"] != "function":
            continue

        if item["name"] == function_name:
            return True

    return False