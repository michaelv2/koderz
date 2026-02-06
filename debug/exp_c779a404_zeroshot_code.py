def circular_shift(x, shift):
    x = str(x)
    if shift <= len(x):
        return x[-shift:] + x[:-shift]
    else:
        return x[::-1]