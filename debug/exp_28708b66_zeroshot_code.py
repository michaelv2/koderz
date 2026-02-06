import math

def sum_squares(lst):
    total = 0
    for num in lst:
        rounded = math.ceil(num)
        total += rounded ** 2
    return total