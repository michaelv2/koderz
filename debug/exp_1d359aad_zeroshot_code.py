def monotonic(l: list):
    if not l:
        return True
    increasing = all(l[i] <= l[i + 1] for i in range(len(l) - 1))
    decreasing = all(l[i] >= l[i + 1] for i in range(len(l) - 1))
    return increasing or decreasing