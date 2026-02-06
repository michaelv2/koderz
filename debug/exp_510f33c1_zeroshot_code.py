def odd_count(lst):
    template = "the number of odd elements in the string i of the input."
    result = []
    for s in lst:
        cnt = sum(1 for ch in s if ch in "13579")
        result.append(template.replace('i', str(cnt)))
    return result