1. Problem analysis
- Core challenge: Determine how many unique characters appear in the input string when letter case is ignored (e.g., 'A' and 'a' count as the same character).
- Constraints: Input is a Python str; function should return an integer count. No assumptions about character set or length beyond typical string usage.

2. Implementation specification
- Function name and signature: count_distinct_characters(string: str) -> int
- Behavior: Treat characters case-insensitively, identify distinct characters present in the entire input string, and return the number of distinct characters as an int. The input string may be empty, in which case the function returns 0.