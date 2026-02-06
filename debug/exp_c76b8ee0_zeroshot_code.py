def exchange(lst1, lst2):
    # Check if there are any odd numbers in lst1
    for num in lst1:
        if num % 2 != 0:
            # If there is an odd number, check if it can be replaced by an even number from lst2
            for i in range(len(lst2)):
                if lst2[i] % 2 == 0:
                    return "YES"
    return "NO"