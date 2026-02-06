1. Problem analysis
- Core challenge: From an input list of integers, select only the integers that represent single digits 1 through 9, sort those selected values in increasing numeric order, then reverse that sorted sequence to produce a descending order, and finally replace each digit with its English name ("One" through "Nine") preserving multiplicity.
- Constraints: Input is a list (possibly empty) of integers; values outside 1..9 (including negatives, zero, and numbers >9) must be ignored; result is an ordered list of strings; if there are no valid digits, return an empty list.

2. Implementation specification
- Function signature: by_length(arr)
- Input: arr — list of integers.
- Output: list of strings.
- Behavior:
  - Filter arr to keep only integers in the inclusive range 1..9.
  - Sort the filtered integers in ascending order, then reverse that order (i.e., produce descending order).
  - Map each integer in the resulting sequence to its corresponding name:
    1 -> "One", 2 -> "Two", 3 -> "Three", 4 -> "Four", 5 -> "Five", 6 -> "Six", 7 -> "Seven", 8 -> "Eight", 9 -> "Nine".
  - Return the list of mapped names in the final order.