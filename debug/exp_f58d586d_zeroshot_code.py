def by_length(arr):
    nums = ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    
    # Filter out numbers not in the range 1-9
    arr = [num for num in arr if 1 <= num <= 9]
    
    # Sort the array and reverse it
    arr.sort()
    arr.reverse()
    
    # Replace each digit with its corresponding name
    return [nums[num] for num in arr]