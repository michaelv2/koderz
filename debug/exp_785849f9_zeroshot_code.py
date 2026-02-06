def exchange(lst1, lst2):
    # Count odd numbers in lst1 that need to be replaced
    odd_count_lst1 = sum(1 for x in lst1 if x % 2 == 1)
    
    # Count even numbers in lst2 that can be used for replacement
    even_count_lst2 = sum(1 for x in lst2 if x % 2 == 0)
    
    # If we have enough even numbers in lst2 to replace all odd numbers in lst1
    if even_count_lst2 >= odd_count_lst1:
        return "YES"
    else:
        return "NO"