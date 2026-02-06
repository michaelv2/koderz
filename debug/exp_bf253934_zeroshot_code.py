def sort_array(array):
    # Return a sorted copy depending on parity of sum of first and last elements.
    if not array:
        return []
    nums = list(array)
    total = nums[0] + nums[-1]
    if total % 2 == 1:
        nums.sort()
    else:
        nums.sort(reverse=True)
    return nums