def histogram(test):
    words = test.split()
    freq_dict = {}
    for word in words:
        if word in freq_dict:
            freq_dict[word] += 1
        else:
            freq_dict[word] = 1
    max_freq = max(freq_dict.values(), default=0)
    result_dict = {}
    for word, freq in freq_dict.items():
        if freq == max_freq:
            result_dict[word] = freq
    return result_dict