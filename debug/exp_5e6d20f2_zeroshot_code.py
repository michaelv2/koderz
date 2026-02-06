def triples_sum_to_zero(l: list):
    """
    triples_sum_to_zero takes a list of integers as an input.
    it returns True if there are three distinct elements in the list that
    sum to zero, and False otherwise.
    """
    n = len(l)
    if n < 3:
        return False
    nums = sorted(l)
    for i in range(n - 2):
        a = nums[i]
        left, right = i + 1, n - 1
        while left < right:
            s = a + nums[left] + nums[right]
            if s == 0:
                return True
            if s < 0:
                left += 1
            else:
                right -= 1
    return False