def sort_array(arr):
    # Separate non-negative and negative numbers
    non_negatives = [x for x in arr if x >= 0]
    negatives = [x for x in arr if x < 0]
    
    # Sort non-negatives by number of ones in binary representation, then by value
    non_negatives_sorted = sorted(non_negatives, key=lambda x: (bin(x).count('1'), x))
    
    # Sort negatives in descending order based on their absolute values
    negatives_sorted = sorted(negatives, key=abs, reverse=True)
    
    # Combine the sorted lists
    return negatives_sorted + non_negatives_sorted