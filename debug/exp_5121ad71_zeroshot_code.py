def move_one_ball(arr):
    if not arr:
        return True
    
    n = len(arr)
    break_count = 0
    break_index = -1
    
    # Count breaks and find the index where break occurs
    for i in range(n):
        next_index = (i + 1) % n
        if arr[i] > arr[next_index]:
            break_count += 1
            break_index = i
    
    # If no breaks, array is already sorted
    if break_count == 0:
        return True
    
    # If more than one break, impossible to sort with rotations
    if break_count > 1:
        return False
    
    # If exactly one break, check if rotating at that point gives sorted array
    # The rotation point should be break_index + 1
    # Check if array from break_index + 1 to end + array from start to break_index is sorted
    rotated_arr = arr[break_index + 1:] + arr[:break_index + 1]
    
    # Check if rotated array is sorted
    for i in range(len(rotated_arr) - 1):
        if rotated_arr[i] > rotated_arr[i + 1]:
            return False
    
    return True