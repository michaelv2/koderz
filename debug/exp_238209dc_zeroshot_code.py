def move_one_ball(arr):
    if not arr:
        return True
    n = len(arr)
    desc = 0
    for i in range(n):
        if arr[i] > arr[(i + 1) % n]:
            desc += 1
            if desc > 1:
                return False
    return True