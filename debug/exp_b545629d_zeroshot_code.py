def order_by_points(nums):
    def sum_digits(n):
        n = abs(n)
        s = 0
        if n == 0:
            return 0
        while n:
            s += n % 10
            n //= 10
        return s
    return sorted(nums, key=lambda x: (sum_digits(x), 0 if x < 0 else 1))