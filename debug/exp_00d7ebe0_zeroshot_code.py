def order_by_points(nums):
    return sorted(nums, key=lambda n: sum(int(d) for d in str(abs(n))))