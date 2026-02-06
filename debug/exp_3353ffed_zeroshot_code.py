def move_one_ball(arr):
    n = len(arr)
    if n == 0:
        return True
    diff_arr = [(arr[(i+1)%n] - arr[i]) % n for i in range(n)]
    return all(d == 1 or d == n-1 for d in diff_arr)