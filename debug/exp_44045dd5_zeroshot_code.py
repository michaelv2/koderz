def is_prime(n):
    """Helper function to check if a number is prime."""
    if n <= 1:
        return False
    elif n == 2:
        return True
    else:
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True

def prime_length(string):
    """Function to check if the length of a string is a prime number."""
    return is_prime(len(string))