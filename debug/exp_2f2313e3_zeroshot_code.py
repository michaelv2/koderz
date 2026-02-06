def sum_squares(lst):
    total = 0
    for i, x in enumerate(lst):
        if i % 3 == 0:
            total += x ** 2
        elif i % 4 == 0:
            total += x ** 3
        else:
            total += x
    return total