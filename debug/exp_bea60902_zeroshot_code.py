from typing import List

def parse_music(music_string: str) -> List[int]:
    notes = music_string.split()
    beats = []
    
    for note in notes:
        if 'o' in note:
            beats.append(4)
        elif '|' in note:
            beats.append(2)
        else:
            beats.append(1)
            
    return beats