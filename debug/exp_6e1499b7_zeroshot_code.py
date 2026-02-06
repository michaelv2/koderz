def by_length(arr):
    digit_names = ["One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]
    
    # Filter out numbers that are not between 1 and 9
    filtered_arr = [num for num in arr if 1 <= num <= 9]
    
    # Sort the filtered array
    sorted_arr = sorted(filtered_arr)
    
    # Reverse the sorted array
    reversed_arr = sorted_arr[::-1]
    
    # Replace each digit by its corresponding name
    result = [digit_names[num - 1] for num in reversed_arr]
    
    return result