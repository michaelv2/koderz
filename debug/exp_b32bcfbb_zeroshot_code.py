Problem analysis:
- Input is a string containing only the characters '<' and '>'.
- The core challenge is to determine whether the brackets are balanced and properly ordered: every '<' must be matched by a later '>' and no '>' may appear without a corresponding unmatched preceding '<'.

Implementation specification:
- Function signature: correct_bracketing(brackets: str) -> bool
- Return True if and only if the sequence of brackets is balanced (every opening '<' has a corresponding closing '>' in the correct order) and False otherwise.