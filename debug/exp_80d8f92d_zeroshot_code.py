def count_nums(arr):
    def sum_of_digits(num):
        if num < 0:
            digits = [-int(str(num)[1])] + [int(d) for d in str(num)[2:]]
        else:
            digits = [int(d) for d in str(num)]
        return sum(digits)
    
    count = 0
    for num in arr:
        if sum_of_digits(num) > 0:
            count += 1
    return count