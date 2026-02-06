def words_in_sentence(sentence):
    def is_prime(n: int) -> bool:
        if n < 2:
            return False
        if n % 2 == 0:
            return n == 2
        i = 3
        while i * i <= n:
            if n % i == 0:
                return False
            i += 2
        return True

    words = sentence.split()
    return " ".join([w for w in words if is_prime(len(w))])