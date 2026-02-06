def search(lst):
    # Create a dictionary to store the frequency of each number
    freq_dict = {}
    for num in lst:
        if num not in freq_dict:
            freq_dict[num] = 1
        else:
            freq_dict[num] += 1
    
    # Sort the dictionary by key in descending order
    sorted_freq = dict(sorted(freq_dict.items(), reverse=True))
    
    # Check each number starting from the largest
    for num, freq in sorted_freq.items():
        if num <= freq:
            return num
    
    # If no such a value exist, return -1
    return -1