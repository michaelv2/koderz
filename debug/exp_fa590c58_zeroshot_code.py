def is_prime(n):
    """Check if n is prime."""
    if n <= 1:
        return False
    elif n == 2:
        return True
    else:
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True

def intersection(interval1, interval2):
    """Find the intersection of two intervals and check if its length is prime."""
    start = max(interval1[0], interval2[0])
    end = min(interval1[1], interval2[1])
    
    # If there's no intersection
    if start > end:
        return "NO"
    
    # The length of the intersection is the difference between the ends and the max start, plus 1
    length = end - start + 1
    
    return "YES" if is_prime(length) else "NO"