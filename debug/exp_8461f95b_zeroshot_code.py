def exchange(lst1, lst2):
    # If there are any odd numbers in lst1, check if we have an even number in lst2 to swap with it
    for num in lst1:
        if num % 2 != 0:
            if not any(num_lst2 % 2 == 0 for num_lst2 in lst2):
                return "NO"
    return "YES"