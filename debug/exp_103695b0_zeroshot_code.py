def odd_count(lst):
    def count_odd(s):
        return sum(1 for c in s if int(c) % 2 != 0)

    result = []
    for i, s in enumerate(lst):
        count = count_odd(s)
        sentence = "the number of odd elements {}n the str{}ng {} of the {}nput.".format(count, count, count, count)
        result.append(sentence)
    return result