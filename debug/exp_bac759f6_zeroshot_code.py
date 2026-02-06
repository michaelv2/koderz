import math

def closest_integer(value):
    num = float(value)
    lower = math.floor(num)
    upper = math.ceil(num)
    
    if abs(num - lower) < abs(num - upper):
        return lower
    elif abs(num - lower) > abs(num - upper):
        return upper
    else:
        # Equidistant, round away from zero
        return upper if num > 0 else lower