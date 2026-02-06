Problem analysis
- Core challenge: Identify numbers that are both Fibonacci numbers and prime numbers, and return the n-th such number in ascending order.
- Constraints: Input is a single integer n (1-based index). The function should return an integer representing the n-th prime Fibonacci number.

Implementation specification
- Function name and signature: prime_fib(n: int) -> int
- Behavior: Compute and return the n-th Fibonacci number that is prime. The sequence is 1-based (prime_fib(1) == 2).
- Return type: int
- Assumptions: n >= 1 and the function should produce the exact n-th prime Fibonacci number as an integer.