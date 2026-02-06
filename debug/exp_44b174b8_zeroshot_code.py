def odd_count(lst):
    template = "the number of odd elements in the string i of the input."
    result = []
    for s in lst:
        count = sum(1 for ch in s if int(ch) % 2 == 1)
        result.append(template.replace('i', str(count)))
    return result