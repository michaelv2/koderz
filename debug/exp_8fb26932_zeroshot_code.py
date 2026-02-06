def solve(s):
    # Check if string contains any letters
    has_letters = any(c.isalpha() for c in s)
    
    if not has_letters:
        # If no letters, reverse the string
        return s[::-1]
    else:
        # If has letters, reverse case of each letter
        result = []
        for c in s:
            if c.isalpha():
                # Reverse case: lower to upper, upper to lower
                if c.islower():
                    result.append(c.upper())
                else:
                    result.append(c.lower())
            else:
                # Keep non-letters as they are
                result.append(c)
        return ''.join(result)