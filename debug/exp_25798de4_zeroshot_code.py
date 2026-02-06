def median(l):
    l = sorted(l)
    n = len(l)
    m = n - 1
    return (l[m//2] + l[(m+1)//2]) / 2