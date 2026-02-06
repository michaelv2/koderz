def flip_case(string: str) -> str:
    result = ""
    for char in string:
        if char.isupper():
            result += char.lower()
        elif char.islower():
            result += char.upper()
        else:
            result += char
    return result