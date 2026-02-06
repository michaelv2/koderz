def decimal_to_binary(decimal):
    if not isinstance(decimal, int):
        raise TypeError("decimal must be an int")
    if decimal < 0:
        raise ValueError("decimal must be non-negative")
    return "db" + bin(decimal)[2:] + "db"