def total_match(lst1, lst2):
    total1 = sum(len(s) for s in lst1)
    total2 = sum(len(s) for s in lst2)
    return lst1 if total1 <= total2 else lst2