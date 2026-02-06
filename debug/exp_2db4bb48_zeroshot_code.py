def solve(N):
    """Given a positive integer N, return the total sum of its digits in binary as a string."""
    s = sum(int(d) for d in str(N))
    return bin(s)[2:]