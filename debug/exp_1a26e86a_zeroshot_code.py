def circular_shift(x, shift):
    x = str(x) # Convert the integer to string for easy manipulation
    if shift > len(x): 
        return x[::-1] # If shift is greater than number of digits, reverse the digits
    else:
        return x[-shift:] + x[:-shift] # Otherwise, perform the circular shift