Problem analysis
- Core challenge: Sort a list of integers by the number of '1' bits in their binary representation (ascending). When two values have the same count of '1' bits, order them by their decimal value (ascending).
- Constraints: Input is a list of integers. The function must return a list of the same integers sorted according to the rules above.

Implementation specification
- Function signature: sort_array(arr)
- Input: arr — list of integers.
- Output: a new list containing the same integers from arr, sorted first by the count of '1' bits in each integer's binary representation (with the binary representation taken in the usual way for the integer's non-negative magnitude), and secondarily by numeric value (ascending) when counts are equal. The original list must not be modified.