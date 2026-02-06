def make_palindrome(string: str) -> str:
    """ Find the shortest palindrome that begins with a supplied string. """
    if not string:
        return string
    
    # Function to check if a string is a palindrome
    def is_palindrome(s: str) -> bool:
        return s == s[::-1]
    
    # Find the longest palindromic suffix
    for i in range(len(string)):
        if is_palindrome(string[i:]):
            # Append the reverse of the non-palindromic prefix to the end
            return string + string[:i][::-1]
    
    # In case no palindromic suffix is found (should not happen with above logic)
    return string + string[::-1]