from typing import List

def parse_music(music_string: str) -> List[int]:
    """Parse ASCII music notation into a list of beat durations.
    'o'  -> 4 beats (whole note)
    'o|' -> 2 beats (half note)
    '.|' -> 1 beat  (quarter note)
    Tokens are separated by whitespace.
    """
    mapping = {'o': 4, 'o|': 2, '.|': 1}
    if not music_string:
        return []
    result: List[int] = []
    for token in music_string.split():
        if token in mapping:
            result.append(mapping[token])
        else:
            raise ValueError(f"Invalid token: {token!r}")
    return result