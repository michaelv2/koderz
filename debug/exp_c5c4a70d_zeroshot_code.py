def decimal_to_binary(decimal):
    if int(decimal) == 0:
        return "db0db"
    negative = int(decimal) < 0
    n = abs(int(decimal))
    bits = bin(n)[2:]
    if negative:
        bits = "-" + bits
    return "db" + bits + "db"