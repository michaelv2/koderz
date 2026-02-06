def odd_count(lst):
    result = []
    for s in lst:
        odd_count = sum(1 for char in s if char in '13579')
        output_string = f"the number of odd elements {odd_count}n the str{odd_count}ng {odd_count} of the {odd_count}nput."
        result.append(output_string)
    return result