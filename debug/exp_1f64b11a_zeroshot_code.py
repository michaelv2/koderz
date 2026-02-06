def circular_shift(x, shift):
    x_str = str(x)
    num_digits = len(x_str)
    
    if shift >= num_digits:
        return x_str[::-1]
    
    # Calculate the effective shift
    shift = shift % num_digits
    
    # Perform the circular shift
    return x_str[-shift:] + x_str[:-shift]