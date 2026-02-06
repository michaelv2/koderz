def solve(N):
    s = sum(int(c) for c in str(abs(int(N))))
    return bin(s)[2:]