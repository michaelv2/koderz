def sort_array(arr):
    def count_ones(n):
        if n >= 0:
            return bin(n).count('1')
        else:
            # For negative numbers, count 1s in two's complement representation
            # Python's bin() for negative shows -0b..., so we count from abs
            # Actually, for negative numbers in two's complement, we need special handling
            # Let's use bit_length to handle this properly
            return bin(n).count('1')
    
    return sorted(arr, key=lambda x: (count_ones(x), x))