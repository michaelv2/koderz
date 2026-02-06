1. Problem analysis
- Core challenge: Parse two integer counts (number of apples and number of oranges) from the input string of the form "<apples> apples and <oranges> oranges" and compute how many mangoes are in the basket given the total number of fruits.
- Constraints: The string contains exactly two non-negative integers (possibly multi-digit); the second argument is an integer total. The function returns an integer equal to total minus the two parsed counts.

2. Implementation specification
- Function name and signature: fruit_distribution(s, n)
- Behavior:
  - Extract the first integer from s as apples and the second integer from s as oranges.
  - Compute mangoes = n - apples - oranges.
  - Return mangoes (an integer).