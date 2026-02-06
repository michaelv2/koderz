def modp(n: int, p: int) -> int:
    if n == 0:
        return 1 % p
    else:
        result = 2 % p
        for _ in range(1, n):
            result = (result * result) % p
        return result