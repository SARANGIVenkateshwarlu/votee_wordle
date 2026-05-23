import random
import time
from math import log2
from words import get_wordle_answers

OPTIMAL_FIRST_WORD = "salet"
CANDIDATE_DIRECT_GUESS_THRESHOLD = 3
ANSWER_LIST = list(get_wordle_answers())
ALLOWED_GUESSES = list(set(ANSWER_LIST) | {OPTIMAL_FIRST_WORD})

def encode_pattern(pattern):
    code = 0
    mul = 1
    for x in pattern:
        code += x * mul
        mul *= 3
    return code


def decode_pattern(code):
    p = [0, 0, 0, 0, 0]
    for i in range(5):
        p[i] = code % 3
        code //= 3
    return tuple(p)


def get_evaluation_raw(answer, word):
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


def build_pattern_matrix():
    answer_to_idx = {w: i for i, w in enumerate(ANSWER_LIST)}
    guess_to_idx = {w: i for i, w in enumerate(ALLOWED_GUESSES)}

    matrix = [[0] * len(ANSWER_LIST) for _ in range(len(ALLOWED_GUESSES))]

    for gi, guess in enumerate(ALLOWED_GUESSES):
        for ai, answer in enumerate(ANSWER_LIST):
            pattern = get_evaluation_raw(answer, guess)
            matrix[gi][ai] = encode_pattern(pattern)

    return matrix, answer_to_idx, guess_to_idx


_pattern_matrix = None
_answer_to_idx = None
_guess_to_idx = None


def init_cache():
    global _pattern_matrix, _answer_to_idx, _guess_to_idx
    if _pattern_matrix is None:
        _pattern_matrix, _answer_to_idx, _guess_to_idx = build_pattern_matrix()


def get_cached_evaluation(guess, answer):
    return _pattern_matrix[_guess_to_idx[guess]][_answer_to_idx[answer]]


def compute_bucket_map(guess, candidate_indices):
    gi = _guess_to_idx[guess]
    temp_map = {}
    for ai in candidate_indices:
        pcode = _pattern_matrix[gi][ai]
        if pcode not in temp_map:
            temp_map[pcode] = [ai]
        else:
            temp_map[pcode].append(ai)
    return temp_map


def score_from_buckets(buckets):
    return sum(len(v) * len(v) for v in buckets.values())


def run():
    answer_str = random.choice(ANSWER_LIST)
    answer_idx = _answer_to_idx[answer_str]
    candidate_indices = [i for i in range(len(ANSWER_LIST))]
    candidates_count = len(candidate_indices)

    for guess_number in range(6):
        if guess_number == 0:
            chosen_word = OPTIMAL_FIRST_WORD
            buckets = compute_bucket_map(chosen_word, candidate_indices)
        elif len(candidate_indices) <= CANDIDATE_DIRECT_GUESS_THRESHOLD:
            chosen_word = ANSWER_LIST[candidate_indices[0]]
            buckets = compute_bucket_map(chosen_word, candidate_indices)
        else:
            min_score = float('inf')
            chosen_word = ""
            chosen_buckets = {}

            for gi in range(len(ALLOWED_GUESSES)):
                guess = ALLOWED_GUESSES[gi]
                buckets = compute_bucket_map(guess, candidate_indices)
                score = score_from_buckets(buckets)

                if score < min_score:
                    min_score = score
                    chosen_word = guess
                    chosen_buckets = buckets
                    if score == len(candidate_indices):
                        break

            buckets = chosen_buckets

        actual_pattern_code = get_cached_evaluation(chosen_word, answer_str)
        actual_pattern = decode_pattern(actual_pattern_code)

        if actual_pattern == (2, 2, 2, 2, 2):
            return True, guess_number + 1

        if actual_pattern_code in buckets:
            candidate_indices = buckets[actual_pattern_code]
        else:
            candidate_indices = []

        candidates_count = len(candidate_indices)

        if candidates_count == 1:
            return True, guess_number + 2

        if candidates_count == 0:
            return False, 6

    return False, 6


def get_stats(n):
    successes = 0
    total_guesses = 0
    guess_distribution = {}
    failures = 0
    for i in range(n):
        success, guesses = run()
        if success:
            successes += 1
            total_guesses += guesses
            guess_distribution[guesses] = guess_distribution.get(guesses, 0) + 1
        else:
            failures += 1

    avg_guesses = total_guesses / successes if successes > 0 else 0
    return successes / n, avg_guesses, guess_distribution, failures


def get_time(n):
    t = 0
    for _ in range(n):
        start_time = time.time()
        run()
        t = max(t, time.time() - start_time)
    return t


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    print("Initializing pattern cache...")
    t0 = time.time()
    init_cache()
    print(f"Cache built in {time.time() - t0:.2f}s")
    print(f"Running {n} trials...")
    t0 = time.time()
    rate, avg, dist, failures = get_stats(n)
    elapsed = time.time() - t0
    print(f"Success rate: {rate*100:.2f}%")
    print(f"Failures: {failures}")
    print(f"Average guesses: {avg:.4f}")
    print(f"Guess distribution: {dict(sorted(dist.items()))}")
    print(f"Worst-case time: {get_time(10):.3f}s")
    print(f"Total time for {n} trials: {elapsed:.2f}s ({elapsed/n*1000:.1f}ms/trial)")
