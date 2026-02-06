def sort_array(arr):
    """
    Sort array by number of ones in binary representation (ascending).
    For ties, sort by decimal value (ascending).
    """
    return sorted(arr, key=lambda x: (bin(x).count("1"), x))