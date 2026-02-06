def words_string(s):
    # Replace commas with spaces to normalize separators
    s = s.replace(',', ' ')
    # Split by spaces and filter out empty strings
    words = [word for word in s.split() if word]
    return words