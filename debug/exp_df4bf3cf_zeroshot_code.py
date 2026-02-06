def odd_count(lst):
    base = "the number of odd elements in the string of the input."
    return [base.replace('i', str(sum(1 for ch in s if ch in '13579'))) for s in lst]