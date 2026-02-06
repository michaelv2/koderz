def total_match(lst1, lst2):
    sum1 = sum(len(s) for s in lst1)
    sum2 = sum(len(s) for s in lst2)
    return lst1 if sum1 <= sum2 else lst2