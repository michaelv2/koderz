from two integers, round it away from zero.
from two integers, the one you should return is the one that is the

def closest_integer(value):
    num = float(value)
    
    # Handle rounding away from zero
    if num >= 0:
        return int(num + 0.5)
    else:
        return int(num - 0.5)