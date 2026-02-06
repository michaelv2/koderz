def order_by_points(nums):
    def sum_digits(n):
        return sum(int(d) for d in str(abs(n)))
    
    nums = [(i, n, sum_digits(n)) for i, n in enumerate(nums)]
    nums.sort(key=lambda x: (x[2], x[0]))
    return [n[1] for n in nums]