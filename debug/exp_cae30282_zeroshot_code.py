def digitSum(s):
    """Sum ASCII codes of uppercase ASCII letters in the string."""
    return sum(ord(ch) for ch in s if 'A' <= ch <= 'Z')