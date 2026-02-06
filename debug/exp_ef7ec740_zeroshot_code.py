def add_elements(arr, k):
    """
    Given a non-empty array of integers arr and an integer k, return
    the sum of the elements with at most two digits from the first k elements of arr.
    """
    return sum(num for num in arr[:k] if abs(num) < 100)