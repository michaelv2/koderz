def specialFilter(nums):
    def is_odd_digit(n):
        return n in [1, 3, 5, 7, 9]
    
    count = 0
    for num in nums:
        if num > 10 and is_odd_digit(abs(num) % 10) and is_odd_digit(int(str(abs(num))[0])):
            count += 1
            
    return count