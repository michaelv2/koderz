def make_palindrome(string: str) -> str:
    """ Find the shortest palindrome that begins with a supplied string. """
    if not string:
        return string
    
    # Find the longest palindromic suffix
    for i in range(len(string)):
        suffix = string[i:]
        if is_palindrome(suffix):
            # Found longest palindromic suffix starting at position i
            # Prefix is everything before position i
            prefix = string[:i]
            # Append reverse of prefix to the end
            return string + prefix[::-1]
    
    # Should never reach here if is_palindrome works correctly
    return string