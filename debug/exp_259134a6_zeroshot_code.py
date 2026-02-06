from typing import List

def filter_by_prefix(strings, prefix):
    """Filter an input list of strings only for ones that start with a given prefix."""
    return [s for s in strings if s.startswith(prefix)]