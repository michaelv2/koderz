1. Problem analysis
- Core challenge: Count how many sentences in the input string S start with the exact word "I". Sentences are separated by the delimiters '.', '?' and '!'. Sentences may have leading/trailing whitespace and the final sentence may lack a trailing delimiter. The check for the first word is case-sensitive (only "I" counts).

2. Implementation specification
- Function signature: is_bored(S: str) -> int
- Behavior: Parse S into sentences using '.', '?' and '!' as sentence delimiters (treating the trailing fragment after the last delimiter as a sentence). For each sentence, trim leading whitespace, extract the first whitespace-delimited word, and if that word is exactly "I", count it. Return the total count as an integer.