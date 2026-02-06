from typing import List

Problem analysis:
- Input: a single integer n.
- Core challenge: represent n as a multiset of prime factors so that the product of the returned integers equals n.
- Constraints: work for n >= 1. For n == 1 there are no prime factors (product of empty list equals 1). For n < 1 the function should signal invalid input.

Implementation specification:
- Function name and signature: factorize(n: int) -> List[int].
- Behavior:
  - If n < 1, raise a ValueError.
  - If n == 1, return an empty list [].
  - Otherwise return a list of prime factors (integers > 1) in non-decreasing order (smallest to largest), including repeated entries according to multiplicity, such that the product of the list equals n.
- Return type: List[int].