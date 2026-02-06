def odd_count(lst):
    result = []
    for i, s in enumerate(lst):
        count = 0
        for c in s:
            if int(c) % 2 != 0:
                count += 1
        template = "the number of odd elements {}n the str{}ng {} of the {}nput."
        result.append(template.format(count, count, i+1, i+1))
    return result