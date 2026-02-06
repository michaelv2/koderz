def is_palindrome(n):
    return str(n) == str(n)[::-1]

def even_odd_palindrome(n):
    palindromes = [i for i in range(1, n+1) if is_palindrome(i)]
    evens = len([num for num in palindromes if num % 2 == 0])
    odds = len(palindromes) - evens
    return (evens, odds)