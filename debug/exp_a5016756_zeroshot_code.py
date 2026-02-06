from typing import List, Optional

def longest(strings: List[str]) -> Optional[str]:
    if not strings:
        return None
    longest_string = strings[0]
    max_length = len(longest_string)
    for string in strings[1:]:
        if len(string) > max_length:
            longest_string = string
            max_length = len(string)
    return longest_string