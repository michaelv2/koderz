def exchange(lst1, lst2):
    """Determine if it's possible to exchange elements between lst1 and lst2
    so that lst1 contains only even numbers. Return "YES" or "NO"."""
    m = len(lst1)
    evens = sum(1 for x in lst1 + lst2 if x % 2 == 0)
    return "YES" if evens >= m else "NO"