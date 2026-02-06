def exchange(lst1, lst2):
    total_evens = sum(1 for x in lst1 + lst2 if x % 2 == 0)
    return "YES" if total_evens >= len(lst1) else "NO"