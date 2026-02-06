from two integers, round it away from zero.
from two integers, the one you should return is the one that is the

def closest_integer(value):
    num = float(value)
    
    # Get the integer part and fractional part
    if num >= 0:
        # For positive numbers, if fractional part is 0.5, round up
        if num - int(num) == 0.5:
            return int(num) + 1
        else:
            return round(num)
    else:
        # For negative numbers, if fractional part is 0.5, round down (away from zero)
        if num - int(num) == -0.5:
            return int(num) - 1
        else:
            return round(num)