def count_nums(arr):
    def sum_digits(n):
        return sum(int(i) for i in str(abs(n)))
    
    return len([x for x in arr if sum_digits(x) > 0])