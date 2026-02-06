def by_length(arr):
    # Mapping of digits to their English names
    digit_names = {
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
    
    # Filter to keep only integers between 1 and 9 inclusive
    filtered = [x for x in arr if isinstance(x, int) and 1 <= x <= 9]
    
    # Sort the filtered array
    filtered.sort()
    
    # Reverse the sorted array
    filtered.reverse()
    
    # Map each digit to its name
    result = [digit_names[x] for x in filtered]
    
    return result