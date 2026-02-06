Problem analysis
- Input: a string s.
- Core task: compute the total of ASCII codes for characters that are uppercase letters.
- Constraints: ignore all characters that are not uppercase letters; empty string -> return 0.

Implementation specification
- Function: digitSum(s)
- Parameter: s (str)
- Return value: an int equal to the sum of ASCII codes (ord values) of each character in s that is an uppercase letter ('A' through 'Z'); if none, return 0.