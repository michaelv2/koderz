def move_one_ball(arr):
    # If the list is empty or has only one element, it's already sorted
    if len(arr) < 2:
        return True
    
    # Find the index of the maximum value in the array
    max_index = arr.index(max(arr))
    
    # Check if the list is already sorted (non-decreasing order)
    if all(arr[i] <= arr[(i+1)%len(arr)] for i in range(len(arr))):
        return True
    
    # If not, perform right shift operations until we get to the maximum value
    while max_index != 0:
        arr = [arr[-1]] + arr[:-1]  # Perform one right shift operation
        max_index -= 1  # Decrease the index of the maximum value
    
    # Check if the list is sorted after performing the operations
    return all(arr[i] <= arr[(i+1)%len(arr)] for i in range(len(arr)))