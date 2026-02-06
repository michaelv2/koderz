def search(lst):
    from collections import Counter
    
    # Count the frequency of each integer in the list
    freq = Counter(lst)
    
    # Initialize the result as -1 (in case no such integer is found)
    result = -1
    
    # Iterate through the frequency dictionary
    for num, count in freq.items():
        # Check if the frequency is greater than or equal to the number itself
        if count >= num:
            # Update the result with the maximum value that satisfies the condition
            result = max(result, num)
    
    return result