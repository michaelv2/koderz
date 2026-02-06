def count_nums(arr):
    count = 0
    for n in arr:
        s = str(n)
        if s.startswith('-'):
            if len(s) >= 2:
                signed = -int(s[1])
                for ch in s[2:]:
                    signed += int(ch)
            else:
                signed = 0
        else:
            signed = sum(int(ch) for ch in s)
        if signed > 0:
            count += 1
    return count