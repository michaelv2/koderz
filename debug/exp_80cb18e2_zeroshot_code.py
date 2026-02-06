def count_nums(arr):
    def digit_sum(n):
        s = str(n)
        if s[0] == '-':
            return -int(s[1]) + sum(int(d) for d in s[2:])
        else:
            return sum(int(d) for d in s)
    
    count = 0
    for num in arr:
        if digit_sum(num) > 0:
            count += 1
    return count