from typing import List

def parse_music(music_string: str) -> List[int]:
    tokens = music_string.split()
    durations_map = {'o': 4, 'o|': 2, '.|': 1}
    return [durations_map[token] for token in tokens if token in durations_map]