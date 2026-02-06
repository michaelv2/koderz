def exchange(lst1, lst2):
    # Separate odd and even numbers from both lists
    lst1_odd = [num for num in lst1 if num % 2 != 0]
    lst2_even = [num for num in lst2 if num % 2 == 0]

    # Check if there are enough even numbers in lst2 to replace all the odd numbers in lst1
    return "YES" if len(lst2_even) >= len(lst1_odd) else "NO"