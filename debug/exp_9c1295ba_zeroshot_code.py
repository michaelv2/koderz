from typing import List

def parse_music(music_string: str) -> List[int]:
    """Parse a string of space-separated musical tokens into their beat durations.
    Tokens:
      'o'   -> 4 beats
      'o|'  -> 2 beats
      '.|'  -> 1 beat
    Returns a list of integers representing the duration of each token, in order.
    """
    if not music_string:
        return []
    tokens = music_string.split()
    durations: List[int] = []
    for tok in tokens:
        if tok == 'o':
            durations.append(4)
        elif tok == 'o|':
            durations.append(2)
        elif tok == '.|':
            durations.append(1)
        else:
            raise ValueError(f"Invalid token: {tok!r}")
    return durations