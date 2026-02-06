def sort_array(arr):
    def bitcount(n):
        try:
            return n.bit_count()
        except AttributeError:
            return bin(n).count('1')
    return sorted(arr, key=lambda x: (bitcount(x), x))