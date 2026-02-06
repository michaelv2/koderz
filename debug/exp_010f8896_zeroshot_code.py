def strange_sort_list(lst):
    lst.sort()  # Sort the list
    result = []  # Initialize an empty list for the result
    while lst:  # While there are elements left in the list
        result.append(lst.pop(0))  # Pop and append the first element
        if lst:  # If there are still elements left
            result.append(lst.pop())  # Pop and append the last element
    return result  # Return the resulting list