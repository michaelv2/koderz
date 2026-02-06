def total_match(lst1, lst2):
    len1 = len(''.join(lst1))
    len2 = len(''.join(lst2))
    if len1 <= len2:
        return lst1
    else:
        return lst2