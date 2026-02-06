Problem analysis:
- Input: a list l.
- Core challenge: reorder only the elements at even indices (0-based) so that those positions contain the even-indexed values from l sorted in non-decreasing order, while values at odd indices remain exactly as in the original list.
- Output: a list of the same length as l with even-index positions replaced by the sorted even-index values and odd-index positions unchanged.

Implementation specification:
- Collect values from l at indices i where i % 2 == 0.
- Sort that collection in non-decreasing order.
- Create and return a new list that is identical to l except that at each even index i, the element is taken sequentially from the sorted collection (first sorted value goes to index 0, next to index 2, etc.).