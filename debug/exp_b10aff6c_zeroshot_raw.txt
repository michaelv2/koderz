1. Problem analysis
- Core challenge: Convert each numeric GPA in the input list to a corresponding letter grade per the given threshold table, preserving input order.
- Constraints: Input is a list of numeric GPA values (floats or ints). Output must be a list of strings, one letter grade per input GPA.

2. Implementation specification
- Function signature: numerical_letter_grade(grades)
- Input: grades — list of numeric GPA values.
- Output: list of strings where each string is the letter grade corresponding to the GPA at the same index, using these mappings:
  - exactly 4.0 -> 'A+'
  - > 3.7 -> 'A'
  - > 3.3 -> 'A-'
  - > 3.0 -> 'B+'
  - > 2.7 -> 'B'
  - > 2.3 -> 'B-'
  - > 2.0 -> 'C+'
  - > 1.7 -> 'C'
  - > 1.3 -> 'C-'
  - > 1.0 -> 'D+'
  - > 0.7 -> 'D'
  - > 0.0 -> 'D-'
  - exactly 0.0 -> 'E'
- Behavior: For each GPA, evaluate the above conditions and assign the first matching letter grade; return the list of assigned grades in the same order as the input.