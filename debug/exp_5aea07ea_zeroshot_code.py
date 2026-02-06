from typing import List, Optional

def longest(strings):
    if not strings:
        return None
    else:
        max_length = -1
        longest_string = ""
        for string in strings:
            if len(string) > max_length:
                max_length = len(string)
                longest_string = string
        return longest_string