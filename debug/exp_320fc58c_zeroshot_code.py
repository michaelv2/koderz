def sort_even(l: list):
    # Extract all the even indexed elements
    evens = [l[i] for i in range(0, len(l), 2)]
    # Sort the even indexed elements
    evens.sort()
    # Replace the even indexed elements in the original list with the sorted ones
    for i in range(len(evens)):
        l[i*2] = evens[i]
    return l