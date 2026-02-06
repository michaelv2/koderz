def circular_shift(x, shift):
    """Circular shift the digits of the integer x, shift the digits right by shift
    and return the result as a string.
    If shift > number of digits, return digits reversed.
    """
    str_x = str(x)
    num_digits = len(str_x)
    
    if shift <= num_digits:
        # Perform circular shift
        shift = shift % num_digits  # In case shift is equal to num_digits
        return str_x[-shift:] + str_x[:-shift]
    else:
        # Reverse the digits
        return str_x[::-1]