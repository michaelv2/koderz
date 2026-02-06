def solve(N):
    return bin(sum(int(c) for c in str(N)))[2:]