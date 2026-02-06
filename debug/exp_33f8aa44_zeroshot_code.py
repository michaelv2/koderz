def odd_count(lst):
    """Given a list of strings of digits, return transformed sentences where each
    'i' in the template is replaced by the count of odd digits in that string."""
    template = "the number of odd elements in the string i of the input."
    result = []
    for s in lst:
        count = sum(1 for ch in s if ch in "13579")
        result.append(template.replace('i', str(count)))
    return result