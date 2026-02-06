def monotonic(l: list) -> bool:
    if not l:
        return True  # An empty list is considered monotonically increasing/decreasing
    
    increasing = decreasing = True
    
    for i in range(1, len(l)):
        if l[i] > l[i - 1]:
            decreasing = False
        elif l[i] < l[i - 1]:
            increasing = False
    
    return increasing or decreasing