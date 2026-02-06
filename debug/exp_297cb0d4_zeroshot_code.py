def by_length(arr):
    # Mapping from numbers to their word representations
    num_to_word = {
        1: "One",
        2: "Two", 
        3: "Three",
        4: "Four",
        5: "Five",
        6: "Six",
        7: "Seven",
        8: "Eight",
        9: "Nine"
    }
    
    # Filter numbers between 1 and 9 inclusive
    filtered_arr = [num for num in arr if 1 <= num <= 9]
    
    # Sort the filtered array
    filtered_arr.sort()
    
    # Reverse the sorted array
    filtered_arr.reverse()
    
    # Replace each number with its word representation
    result = [num_to_word[num] for num in filtered_arr]
    
    return result