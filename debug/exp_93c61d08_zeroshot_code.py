def intersection(interval1, interval2):
    def is_prime(n):
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        for i in range(3, int(n**0.5) + 1, 2):
            if n % i == 0:
                return False
        return True
    
    start1, end1 = interval1
    start2, end2 = interval2
    
    # Find intersection
    intersection_start = max(start1, start2)
    intersection_end = min(end1, end2)
    
    # Check if there's an intersection
    if intersection_start > intersection_end:
        return "NO"
    
    # Calculate length of intersection
    length = intersection_end - intersection_start
    
    # Check if length is prime
    if is_prime(length):
        return "YES"
    else:
        return "NO"