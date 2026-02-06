def iscube(a: int) -> bool:
    if a == 0:
        return True
    n = abs(a)
    hi = 1 << ((n.bit_length() + 2) // 3)  # upper bound for |cube_root(a)|
    lo = -hi
    while lo <= hi:
        mid = (lo + hi) // 2
        cube = mid * mid * mid
        if cube == a:
            return True
        if cube < a:
            lo = mid + 1
        else:
            hi = mid - 1
    return False