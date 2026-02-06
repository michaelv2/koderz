def iscube(a):
    n = abs(a)
    left, right = 0, max(1, n)
    while left <= right:
        mid = (left + right) // 2
        cube = mid * mid * mid
        if cube == n:
            return True
        if cube < n:
            left = mid + 1
        else:
            right = mid - 1
    return False