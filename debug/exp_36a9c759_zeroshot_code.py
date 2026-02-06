def will_it_fly(q, w):
    if q != q[::-1]:  # Check if the list is a palindrome
        return False
    elif sum(q) > w:  # Check if the sum of elements is less than or equal to the weight limit
        return False
    else:
        return True