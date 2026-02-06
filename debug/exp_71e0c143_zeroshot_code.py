def search(lst):
    from collections import Counter
    
    # Count the frequency of each integer in the list
    freq = Counter(lst)
    
    # Iterate through possible values and find the greatest one that meets the condition
    for i in range(max(freq), 0, -1):
        if freq[i] >= i:
            return i
    
    # If no such value exists, return -1
    return -1