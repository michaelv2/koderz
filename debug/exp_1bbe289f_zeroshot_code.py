def triples_sum_to_zero(l: list):
    """
    Return True if there exist three distinct elements in l that sum to zero.
    """
    n = len(l)
    if n < 3:
        return False

    nums = sorted(l)
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        left, right = i + 1, n - 1
        while left < right:
            s = nums[i] + nums[left] + nums[right]
            if s == 0:
                return True
            if s < 0:
                left += 1
            else:
                right -= 1
    return False