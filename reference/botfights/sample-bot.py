import os

OPTIMAL_FIRST_WORD = "salet"

g_wordlist = None
g_answerlist = None


def get_wordlist():
    global g_wordlist
    if None is g_wordlist:
        g_wordlist = []
        with open('wordlist.txt') as f:
            for line in f:
                g_wordlist.append(line.strip())
    return g_wordlist


def get_answerlist():
    global g_answerlist
    if None is g_answerlist:
        g_answerlist = []
        path = os.path.join(os.path.dirname(__file__), '..', 'wordle_answers.txt')
        with open(path) as f:
            for line in f:
                g_answerlist.append(line.strip())
    return g_answerlist


def matches(target, guess, feedback):
    target_chars = list(target)
    for i in range(5):
        if feedback[i] == '3':
            if target_chars[i] != guess[i]:
                return False
            target_chars[i] = ' '
    for i in range(5):
        if guess[i] == target_chars[i] and feedback[i] != '3':
            return False
    for i in range(5):
        if feedback[i] == '2':
            if guess[i] not in target_chars:
                return False
            idx = target_chars.index(guess[i])
            target_chars[idx] = ' '
    for i in range(5):
        if feedback[i] == '1' and guess[i] in target_chars:
            return False
    return True


def play(state):
    possible = get_wordlist()
    pairs = state.split(',')
    if len(pairs) == 1:
        return OPTIMAL_FIRST_WORD

    for pair in pairs:
        guess, feedback = pair.split(':')
        possible = list(filter(lambda x: matches(x, guess, feedback), possible))
        possible = list(set(possible) - {guess})

    if len(possible) == 1:
        return possible[0]

    words_to_search = get_answerlist() if len(possible) > 100 else get_wordlist()

    min_score = float('inf')
    chosen_word = ""
    for word_to_guess in words_to_search:
        temp_map = {}
        for pa in possible:
            e = get_evaluation(pa, word_to_guess)
            if e not in temp_map:
                temp_map[e] = [pa]
            else:
                temp_map[e].append(pa)

        score = sum(len(v) * len(v) for v in temp_map.values())
        if score < min_score:
            min_score = score
            chosen_word = word_to_guess
            if score == len(possible):
                break

    return chosen_word


def get_evaluation(answer, word):
    output = [0, 0, 0, 0, 0]
    chars = list(answer)

    for i in range(5):
        if word[i] == chars[i]:
            output[i] = 2
            chars[i] = ' '

    for i in range(5):
        if output[i] == 0:
            char = word[i]
            if char in chars:
                output[i] = 1
                chars[chars.index(char)] = ' '

    return tuple(output)
