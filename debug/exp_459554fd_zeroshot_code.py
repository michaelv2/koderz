def search(lst):
    from collections import Counter
    
    freq = Counter(lst)
    result = -1
    
    for num, count in freq.items():
        if num > 0 and count >= num:
            result = max(result, num)
    
    return result