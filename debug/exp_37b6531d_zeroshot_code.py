def odd_count(lst):
    base = "the number of odd elements in the string i of the input."
    result = []
    for s in lst:
        count = sum(1 for ch in s if ch in '13579')
        result.append(base.replace('i', str(count)))
    return result