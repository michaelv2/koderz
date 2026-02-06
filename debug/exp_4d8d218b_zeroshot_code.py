from typing import List

Problem analysis:
- Given a list of numeric values, compute the Mean Absolute Deviation (MAD) around the arithmetic mean: the task is to measure the average absolute difference between each element and the dataset mean. Input is a list of floats (assume at least one element).

Implementation specification:
- Function signature: mean_absolute_deviation(numbers: List[float]) -> float.
- Compute the arithmetic mean of the input numbers.
- For each element, compute the absolute difference from that mean.
- Return the average of those absolute differences as a float.