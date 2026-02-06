def move_one_ball(arr):
    """Return True if the array can be rotated (via right shifts) to a non-decreasing order."""
    n = len(arr)
    if n <= 1:
        return True

    drops = 0
    for i in range(n - 1):
        if arr[i] > arr[i + 1]:
            drops += 1
            if drops > 1:
                return False

    # Check the wrap-around pair (last -> first)
    if arr[-1] > arr[0]:
        drops += 1

    return drops <= 1