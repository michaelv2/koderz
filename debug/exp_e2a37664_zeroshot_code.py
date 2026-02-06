def move_one_ball(arr):
    if len(arr) <= 1:
        return True
    
    # Count the number of positions where arr[i] > arr[i+1]
    break_count = 0
    break_index = -1
    
    for i in range(len(arr) - 1):
        if arr[i] > arr[i + 1]:
            break_count += 1
            break_index = i
    
    # If no breaks, array is already sorted
    if break_count == 0:
        return True
    
    # If exactly one break, check if last element <= first element
    # This ensures that when we rotate, the end connects properly to the beginning
    if break_count == 1:
        return arr[-1] <= arr[0]
    
    # If more than one break, it's impossible
    return False