from typing import List

def parse_music(music_string: str) -> List[int]:
    # Define a mapping from note representations to their beat values
    note_to_beats = {
        'o': 4,
        'o|': 2,
        '.|': 1
    }
    
    # Split the input string into individual notes
    notes = music_string.split()
    
    # Convert each note to its corresponding beat value using the mapping
    beats = [note_to_beats[note] for note in notes]
    
    return beats