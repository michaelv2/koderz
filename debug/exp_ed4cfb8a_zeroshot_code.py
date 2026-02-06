def add(lst):
    total = 0
    for i in range(len(lst)):
        if i % 2 != 0 and lst[i] % 2 == 0:
            total += lst[i]
    return total