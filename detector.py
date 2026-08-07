def detect_functions(functions, names):

    result = {}

    for name in names:

        result[name] = name in functions

    return result