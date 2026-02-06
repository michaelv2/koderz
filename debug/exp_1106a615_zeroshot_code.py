def solve(s):
    has_letters = any(c.isalpha() for c in s)
    if not has_letters:
        return s[::-1]
    
    result = []
    for char in s:
        if char.isalpha():
            result.append(char.swapcase())
        else:
            result.append(char)
    
    return ''.join(result)