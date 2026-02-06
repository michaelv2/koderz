def triples_sum_to_zero(l: list):
    if len(l) < 3:
        return False
    arr = sorted(l)
    n = len(arr)
    for i in range(n - 2):
        a = arr[i]
        left, right = i + 1, n - 1
        while left < right:
            s = a + arr[left] + arr[right]
            if s == 0:
                return True
            if s < 0:
                left += 1
            else:
                right -= 1
    return False