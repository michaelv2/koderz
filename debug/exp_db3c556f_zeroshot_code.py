Problem analysis:
- Input: a single positive integer n.
- Core requirement: produce n numbers forming the pile levels. The first level has n stones; each next level is the next number of the same parity (odd → next odd, even → next even).
- Constraint: n > 0.

Implementation specification:
- Function name and signature: make_a_pile(n)
- Return value: a list of n integers where the element at index i equals the number of stones on level (i+1). Specifically, the list starts with n and each subsequent element increases by 2, producing n values in total.