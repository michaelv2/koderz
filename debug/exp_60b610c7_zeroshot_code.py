def odd_count(lst):
    template = "the number of odd elements in the string i of the input."
    result = []
    for s in lst:
        count = sum((ord(ch) - 48) % 2 for ch in s)
        result.append(template.replace('i', str(count)))
    return result