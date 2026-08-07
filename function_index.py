def build_function_index(abi):

    functions = set()

    if abi is None:
        return functions

    for item in abi:

        if item.get("type") == "function":
            functions.add(item["name"])

    return functions