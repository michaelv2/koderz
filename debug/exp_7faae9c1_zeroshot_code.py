def search(lst):
    count = {}
    max_val = -1

    for num in lst:
        if num in count:
            count[num] += 1
        else:
            count[num] = 1

        if count[num] >= num and num > max_val:
            max_val = num

    return max_val