def add_elements(arr, k):
    s = 0
    for x in arr[:k]:
        if abs(x) <= 99:
            s += x
    return s