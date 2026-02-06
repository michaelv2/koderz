def solve(s):
    result = []
    has_letter = False
    for char in s:
        if char.isalpha():
            has_letter = True
            if char.islower():
                result.append(char.upper())
            else:
                result.append(char.lower())
        else:
            result.append(char)
    return ''.join(result[::-1]) if not has_letter else ''.join(result)