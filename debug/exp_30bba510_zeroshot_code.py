def make_palindrome(string):
    for i in range(len(string)):
        suffix = string[i:]
        if suffix == suffix[::-1]:
            prefix = string[:i]
            return string + prefix[::-1]
    return string + string[::-1]