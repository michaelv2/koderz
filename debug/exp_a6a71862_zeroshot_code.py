import math

def is_simple_power(x, n):
    # Handle special cases
    if x == 1:
        return True
    
    if n == 1:
        return x == 1
    
    if n == 0:
        return x == 0
    
    if x == 0:
        return False
    
    # For negative numbers, we need to be careful
    if n < 0 and x > 0:
        # If n is negative and x is positive, we need even powers
        # But this is complex, let's use a different approach
        pass
    
    # Calculate the potential exponent using logarithms
    try:
        if n > 0:
            # For positive n, we can use log
            exponent = math.log(x) / math.log(n)
            # Check if exponent is close to an integer
            rounded_exp = round(exponent)
            # Verify by computing n**rounded_exp
            return abs(n ** rounded_exp - x) < 1e-10
        else:
            # For negative n, we need to check both positive and negative powers
            # This is more complex, so let's iterate
            current = 1
            # Check positive powers
            while abs(current) < abs(x):
                current *= n
                if abs(current) == abs(x):
                    return True
            # Check negative powers (if n is not 1 or -1)
            if n != 1 and n != -1:
                current = 1
                while abs(current) > abs(x):
                    current /= n
                    if abs(current) == abs(x):
                        return True
            return False
    except:
        # If logarithm fails, use iterative approach
        pass
    
    # Fallback iterative approach
    if n == 0:
        return x == 0
    
    current = 1
    # Handle the case where n is negative
    if n < 0:
        # For negative base, we need to check alternating signs
        # But let's simplify and just check a reasonable range
        for i in range(100):  # reasonable limit
            if current == x:
                return True
            if abs(current) > abs(x) and current > 0:
                break
            if abs(current) < abs(x) and current < 0:
                break
            current *= n
        return False
    else:
        # Positive base
        for i in range(100):
            if current == x:
                return True
            if current > x and x > 0:
                break
            if current < x and x < 0:
                break
            current *= n
        return False