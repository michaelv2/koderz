def rounded_avg(n, m):
    """You are given two positive integers n and m, and your task is to compute the
    average of the integers from n through m (including n and m). 
    Round the answer to the nearest integer and convert that to binary.
    If n is greater than m, return -1.
    """
    if n > m:
        return -1
    s = n + m
    if s % 2 == 0:
        avg = s // 2
    else:
        lower = s // 2
        # Tie (.5): use round-to-even as Python's round does
        if lower % 2 == 0:
            avg = lower
        else:
            avg = lower + 1
    return bin(avg)