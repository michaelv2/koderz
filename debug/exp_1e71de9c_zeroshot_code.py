def solve(N):
    if N < 0:
        N = -N
    total = sum(int(d) for d in str(N))
    return bin(total)[2:]