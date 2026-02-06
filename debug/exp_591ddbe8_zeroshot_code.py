def search(lst):
    freq = {}
    for x in lst:
        freq[x] = freq.get(x, 0) + 1
    ans = -1
    for val, cnt in freq.items():
        if val > 0 and cnt >= val and val > ans:
            ans = val
    return ans