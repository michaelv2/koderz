from two integers, round it away from zero.
from two integers, the one you should return is the one that is the

def closest_integer(value):
    value = float(value)
    if value >= 0:
        return int(value + 0.5)
    else:
        return int(value - 0.5)