Problem analysis:
- Core challenge: Compute the average of the inclusive integer range from n to m, round that average to the nearest integer, and return its binary representation as a string.
- Constraints: n and m are positive integers. If n > m the function must indicate invalid input by returning -1.

Implementation specification:
- Function signature: rounded_avg(n, m)
- If n > m, return -1 (integer).
- Otherwise, compute the average of all integers from n through m inclusive, round the average to the nearest integer (use standard nearest rounding; ties round to the nearest even integer), convert that rounded integer to a binary string with the "0b" prefix, and return that string.