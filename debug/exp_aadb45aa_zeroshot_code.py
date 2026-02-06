def solve(s):
    # Check if string contains any letters
    has_letters = any(c.isalpha() for c in s)
    
    if has_letters:
        # Swap case of letters, keep non-letters as is
        return ''.join(c.swapcase() if c.isalpha() else c for c in s)
    else:
        # No letters found, reverse the string
        return s[::-1]