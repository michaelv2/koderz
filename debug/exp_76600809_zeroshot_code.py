Problem analysis:
- Core challenge: Given two groups of n cars moving in opposite directions on an infinite straight road at identical speeds, determine how many distinct opposite-direction collisions occur.
- Constraints: n is an integer (assumed non-negative).

Implementation specification:
- Function signature: car_race_collision(n: int) -> int
- Behavior: Return the total number of collisions as an integer.
- Return value: n * n (the number of distinct collisions between the n left-to-right cars and the n right-to-left cars).