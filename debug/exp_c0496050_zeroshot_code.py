def odd_count(lst):
    result = []
    for string in lst:
        odd_count = sum(1 for digit in string if int(digit) % 2 == 1)
        template = "the number of odd elements {}n the str{}ng {} of the {}nput."
        result.append(template.format(odd_count, odd_count, odd_count, odd_count))
    return result