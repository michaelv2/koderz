def move_one_ball(arr):
    if not arr:
        return True
    drops = 0
    for i in range(len(arr) - 1):
        if arr[i] > arr[i + 1]:
            drops += 1
            if drops > 1:
                return False
    if drops == 0:
        return True
    return arr[-1] <= arr[0]