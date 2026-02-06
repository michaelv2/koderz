from typing import List

def parse_music(music_string: str) -> List[int]:
    """Parse a string representing musical notes into their durations in beats.
    - 'o'   -> 4 beats
    - 'o|'  -> 2 beats
    - '.|'  -> 1 beat
    Tokens are separated by whitespace.
    """
    if not music_string:
        return []
    durations = {'o': 4, 'o|': 2, '.|': 1}
    result: List[int] = []
    for token in music_string.split():
        if token in durations:
            result.append(durations[token])
        else:
            raise ValueError(f"Invalid token: {token}")
    return result