from typing import List

def parse_music(music_string: str) -> List[int]:
    """ Input to this function is a string representing musical notes in a special ASCII format.
    Your task is to parse this string and return list of integers corresponding to how many beats does each
    not last.

    Here is a legend:
    'o'  - whole note, lasts four beats
    'o|' - half note, lasts two beats
    '.|' - quater note, lasts one beat

    >>> parse_music('o o| .| o| o| .| .| .| .| o o')
    [4, 2, 1, 2, 2, 1, 1, 1, 1, 4, 4]
    """
    
    # Create a dictionary to map notes to their corresponding beat lengths
    note_lengths = {'o': 4, 'o|': 2, '.|': 1}
    
    # Split the input string into individual notes and strip any leading/trailing whitespace
    notes = music_string.split()
    
    # Use a list comprehension to map each note to its corresponding beat length
    return [note_lengths[note] for note in notes]