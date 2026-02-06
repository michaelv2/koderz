1. Problem analysis
- Core challenge: Given a string representing a hexadecimal number, count how many characters correspond to hexadecimal digits whose numeric values are prime.
- Constraints: Input is a string (possibly empty) containing only valid hex characters 0-9 and A-F (uppercase). No need to validate input. Primes of interest among single hex digits are the values 2, 3, 5, 7, 11 (B), and 13 (D).

2. Implementation specification
- Function signature: def hex_key(num: str) -> int
- Behavior: Examine each character in the input string and count characters that are one of: '2','3','5','7','B','D'.
- Return value: Integer count of such prime-valued hex digits. For an empty input string, return 0.