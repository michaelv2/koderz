Problem analysis:
- Core challenge: reorder only the elements at even indices (0, 2, 4, ...) while leaving elements at odd indices unchanged.
- Constraints: input is a list; elements at even indices are comparable and can be sorted; output should be a list of the same length.

Implementation specification:
- Function signature: sort_even(l: list) -> list
- Behavior: collect values from even indices of l, sort them in non-decreasing (ascending) order, and place them back into the even index positions of a new list. Values at odd indices must be identical to those in the input list and remain at the same indices. Return the resulting list.