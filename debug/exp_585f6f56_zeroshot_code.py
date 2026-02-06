def triples_sum_to_zero(l: list):
    """
    triples_sum_to_zero takes a list of integers as an input.
    it returns True if there are three distinct elements in the list that
    sum to zero, and False otherwise.
    """
    n = len(l)
    if n < 3:
        return False
    a = sorted(l)
    for i in range(n - 2):
        # If current value > 0, further sums will be > 0
        if a[i] > 0:
            break
        left, right = i + 1, n - 1
        while left < right:
            s = a[i] + a[left] + a[right]
            if s == 0:
                return True
            elif s < 0:
                left += 1
            else:
                right -= 1
    return False