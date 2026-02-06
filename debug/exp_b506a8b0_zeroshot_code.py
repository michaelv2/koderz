def sort_array(arr):
    """
    Sort integers by number of ones in their binary representation (ascending).
    For ties, sort by numeric value (ascending).
    """
    return sorted(arr, key=lambda x: (bin(x).count('1'), x))