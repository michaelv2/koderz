def move_one_ball(arr):
    if not arr:
        return True
    
    N = len(arr)
    sorted_arr = sorted(arr)
    
    for i in range(N):
        shifted_arr = arr[-i:] + arr[:-i]
        if shifted_arr == sorted_arr:
            return True
    
    return False