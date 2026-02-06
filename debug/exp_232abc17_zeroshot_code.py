def circular_shift(x, shift):
    """Circular shift the digits of the integer x, shift the digits right by shift
    and return the result as a string.
    If shift > number of digits, return digits reversed.
    """
    s = str(x)
    n = len(s)
    
    # If shift > number of digits, return reversed
    if shift > n:
        return s[::-1]
    
    # Normalize shift to be within the length
    shift = shift % n
    
    # Circular right shift: take last 'shift' characters and move to front
    if shift == 0:
        return s
    
    return s[-shift:] + s[:-shift]