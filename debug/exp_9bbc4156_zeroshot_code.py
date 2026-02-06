def hex_key(num: str) -> int:
    prime_digits = {'2', '3', '5', '7', 'B', 'D'}
    if not num:
        return 0
    return sum(1 for ch in num if ch in prime_digits)