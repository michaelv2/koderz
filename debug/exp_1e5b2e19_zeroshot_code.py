def order_by_points(nums):
    def digit_sum(n):
        return sum(int(digit) for digit in str(abs(n)))

    return [x for _, x in sorted((digit_sum(num), i, num) for i, num in enumerate(nums))]