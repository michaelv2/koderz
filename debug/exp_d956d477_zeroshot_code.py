def total_match(lst1, lst2):
    s1 = sum(len(s) for s in lst1)
    s2 = sum(len(s) for s in lst2)
    return lst1 if s1 <= s2 else lst2