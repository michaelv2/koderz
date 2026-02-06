def match_parens(lst):
    diff1 = lst[0].count('(') - lst[0].count(')')
    diff2 = lst[1].count('(') - lst[1].count(')')
    return 'Yes' if abs(diff1 + diff2) % 2 == 0 and diff1 + diff2 >= 0 else 'No'