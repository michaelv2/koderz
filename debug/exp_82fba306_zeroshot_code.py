def closest_integer(value):
    num = float(value)
    if num < 0:
        num -= 0.1
    return int(round(num))