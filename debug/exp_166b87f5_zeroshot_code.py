def order_by_points(nums):
    def sum_digits(n):
        return sum(int(d) for d in str(abs(n)))
    return [val for _, val in sorted(enumerate(nums), key=lambda iv: (sum_digits(iv[1]), iv[0]))]