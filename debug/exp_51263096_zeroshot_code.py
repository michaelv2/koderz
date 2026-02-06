def monotonic(l: list):
    if len(l) <= 1:
        return True
    
    increasing = None
    
    for i in range(1, len(l)):
        if l[i] > l[i-1]:
            if increasing is False:
                return False
            increasing = True
        elif l[i] < l[i-1]:
            if increasing is True:
                return False
            increasing = False
        # If l[i] == l[i-1], we continue without changing the trend
    
    return True