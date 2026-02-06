def sort_array(array):
    # Create a copy of the given array
    arr = array[:]

    # Check if the sum of the first and last elements is odd or even
    if (arr[0] + arr[-1]) % 2 == 0:
        # Sort in descending order if the sum is even
        arr.sort(reverse=True)
    else:
        # Sort in ascending order if the sum is odd
        arr.sort()

    return arr