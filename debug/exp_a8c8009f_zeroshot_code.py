def even_odd_palindrome(n):
    """
    Return a tuple (num_even_palindromes, num_odd_palindromes) for integers
    in the inclusive range [1, n].
    """
    evens = 0
    odds = 0
    for i in range(1, n + 1):
        s = str(i)
        if s == s[::-1]:
            if i % 2 == 0:
                evens += 1
            else:
                odds += 1
    return (evens, odds)