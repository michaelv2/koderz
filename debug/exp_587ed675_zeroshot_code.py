def exchange(lst1, lst2):
    # Count the number of odd elements in lst1
    odd_count = sum(1 for x in lst1 if x % 2 != 0)
    
    # Count the number of even elements in lst2
    even_count = sum(1 for x in lst2 if x % 2 == 0)
    
    # Check if there are enough even elements in lst2 to replace all odd elements in lst1
    if even_count >= odd_count:
        return "YES"
    else:
        return "NO"