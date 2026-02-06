def even_odd_count(num):
    """Given an integer. return a tuple that has the number of even and odd digits respectively.
    
    Example:
        even_odd_count(-12) ==> (1, 1)
        even_odd_count(123) ==> (1, 2)
    """
    s = str(abs(num))
    even = sum(1 for ch in s if int(ch) % 2 == 0)
    odd = len(s) - even
    return (even, odd)