def solution(lst):
    total = 0
    for i in range(0, len(lst), 2):  # Iterate over even indices
        if lst[i] % 2 != 0:  # Check if the element is odd
            total += lst[i]
    return total