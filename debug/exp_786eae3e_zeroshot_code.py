1. Problem analysis
- Core challenge: Transform an input list of integers into a list of English names for digits 1 through 9, using only the integers in the input that fall in the inclusive range 1..9, preserving multiplicity but ordering them so that the largest valid digits come first.
- Constraints: Input may contain any integers (negative, zero, >9); those outside 1..9 are ignored. An empty input or an input with no valid digits yields an empty list. Output elements are strings drawn from the set {"One","Two","Three","Four","Five","Six","Seven","Eight","Nine"}.

2. Implementation specification
- Function signature: def by_length(arr)
  - Parameter: arr — list of integers.
  - Return: list of strings.
- Behavior (declarative):
  - Consider only elements x in arr such that 1 <= x <= 9.
  - Order those considered elements so that larger digits appear before smaller digits (i.e., descending numeric order), while keeping duplicate occurrences.
  - Map each resulting digit to its corresponding English name:
    1 -> "One", 2 -> "Two", 3 -> "Three", 4 -> "Four", 5 -> "Five", 6 -> "Six", 7 -> "Seven", 8 -> "Eight", 9 -> "Nine".
  - Return the list of mapped names.