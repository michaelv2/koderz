def iscube(a):
    if a == 0:
        return True
    if a > 0:
        lo, hi = 0, a
        while lo <= hi:
            mid = (lo + hi) // 2
            cube = mid * mid * mid
            if cube == a:
                return True
            elif cube < a:
                lo = mid + 1
            else:
                hi = mid - 1
        return False
    else:
        b = -a
        lo, hi = 0, b
        while lo <= hi:
            mid = (lo + hi) // 2
            cube = mid * mid * mid
            if cube == b:
                return True
            elif cube < b:
                lo = mid + 1
            else:
                hi = mid - 1
        return False