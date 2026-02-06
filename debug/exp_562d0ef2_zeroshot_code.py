from typing import List

def parse_music(music_string: str) -> List[int]:
    mapping = {'o': 4, 'o|': 2, '.|': 1}
    tokens = music_string.split()
    return [mapping[t] for t in tokens]