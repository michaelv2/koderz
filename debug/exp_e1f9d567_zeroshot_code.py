def search(lst):
    # Count frequency of each element
    freq = {}
    for num in lst:
        freq[num] = freq.get(num, 0) + 1
    
    # Find candidates where frequency >= value
    candidates = []
    for num, count in freq.items():
        if count >= num:
            candidates.append(num)
    
    # Return the greatest candidate, or -1 if none exist
    return max(candidates) if candidates else -1