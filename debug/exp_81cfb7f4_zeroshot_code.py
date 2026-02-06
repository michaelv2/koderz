1. Problem analysis
- Core challenge: From a sentence made of words separated by spaces, identify which words have lengths that are prime numbers and preserve their original order.
- Constraints: 1 <= len(sentence) <= 100; sentence contains only letters and spaces; words are separated by spaces.

2. Implementation specification
- Function name and signature: words_in_sentence(sentence)
- Input: a single string sentence.
- Behavior: Construct a new string consisting of the words from sentence whose character counts (lengths) are prime numbers, keeping the original order.
- Output: Return the selected words joined by single spaces. If no words meet the criterion, return an empty string.