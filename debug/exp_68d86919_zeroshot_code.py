def search(lst):
    freq = {}
    for num in lst:
        if num not in freq:
            freq[num] = 1
        else:
            freq[num] += 1
    
    max_val = -1
    for key, value in freq.items():
        if key > max_val and value >= key:
            max_val = key
            
    return max_val