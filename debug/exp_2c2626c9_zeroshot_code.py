def odd_count(lst):
    result = []
    for i, s in enumerate(lst, 1):
        count = sum(int(c) % 2 for c in s)
        result.append("the number of odd elements {}n the str{}ng {} of the {}nput.".format(count, count, count, count))
    return result