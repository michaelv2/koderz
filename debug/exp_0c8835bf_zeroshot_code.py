def move_one_ball(arr):
    if not arr:
        return True
    
    n = len(arr)
    count_breaks = 0
    
    for i in range(n):
        if arr[i] > arr[(i + 1) % n]:
            count_breaks += 1
            if count_breaks > 1:
                return False
    
    return True