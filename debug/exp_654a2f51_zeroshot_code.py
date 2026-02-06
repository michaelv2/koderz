from typing import List

def parse_music(music_string: str) -> List[int]:
    tokens = music_string.split()
    beat_map = {'o': 4, 'o|': 2, '.|': 1}
    return [beat_map[t] for t in tokens]