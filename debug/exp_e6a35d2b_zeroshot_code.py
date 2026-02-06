Problem analysis:
- Core challenge: select the k largest elements from the input list (respecting duplicates) and return them as a sorted list.
- Constraints: 1 <= len(arr) <= 1000, elements in [-1000, 1000], and 0 <= k <= len(arr).

Implementation specification:
- Function name and signature: maximum(arr, k)
- Inputs: arr (list of int), k (int)
- Behavior: return a list of length k containing the k largest elements from arr (including duplicates as they appear in value), sorted in non-decreasing (ascending) order.
- Edge behavior: if k == 0 return an empty list; assume k is between 0 and len(arr).