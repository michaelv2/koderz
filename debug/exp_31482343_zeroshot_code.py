def is_sorted(lst):
    if len(lst) <= 1:
        return True
    
    count = {}
    
    for i in range(len(lst)):
        if i > 0 and lst[i] < lst[i - 1]:
            return False
        
        if lst[i] in count:
            count[lst[i]] += 1
        else:
            count[lst[i]] = 1
        
        if count[lst[i]] > 2:
            return False
    
    return True