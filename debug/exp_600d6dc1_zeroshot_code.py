def is_prime(n):
    """Helper function to check if a number is prime."""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def words_in_sentence(sentence):
    """Return a string containing words from the original sentence whose lengths are prime numbers."""
    words = sentence.split()
    prime_length_words = [word for word in words if is_prime(len(word))]
    return ' '.join(prime_length_words)