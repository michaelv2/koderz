def add(lst):
    total = 0
    for i in range(1, len(lst), 2):  # Start from index 1 and step by 2 to get odd indices
        if lst[i] % 2 == 0:  # Check if the element is even
            total += lst[i]
    return total