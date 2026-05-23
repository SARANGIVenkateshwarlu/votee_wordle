import os

_dir = os.path.dirname(os.path.abspath(__file__))
_data_dir = os.path.join(_dir, "data")


def _read_words(filename):
    words = []
    path = os.path.join(_data_dir, filename)
    with open(path, "r") as f:
        for line in f:
            words.append(line.strip())
    return words


def get_wordle_guesses():
    return _read_words("wordle_guesses.txt")


def get_wordle_answers():
    return _read_words("wordle_answers.txt")


def get_wordmaster_guesses():
    return _read_words("wordmaster_guesses.txt")


def get_wordmaster_answers():
    return _read_words("wordmaster_answers.txt")
