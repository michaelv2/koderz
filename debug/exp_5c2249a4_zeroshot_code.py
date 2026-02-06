def add(lst):
    return sum(v for i, v in enumerate(lst) if i % 2 == 1 and v % 2 == 0)