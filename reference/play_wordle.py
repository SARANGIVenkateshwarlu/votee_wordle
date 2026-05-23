from words import get_wordle_guesses, get_wordle_answers, get_wordmaster_guesses, get_wordmaster_answers
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import keyboard
import numpy as np

OPTIMAL_FIRST_WORD = "salet"
CANDIDATE_DIRECT_GUESS_THRESHOLD = 3

_answer_list = None
_guess_list = None
_answer_to_idx = None
_guess_to_idx = None
_pattern_matrix = None


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


def encode_pattern(pattern):
    code = 0
    mul = 1
    for x in pattern:
        code += x * mul
        mul *= 3
    return code


def build_cache():
    global _answer_list, _guess_list, _answer_to_idx, _guess_to_idx, _pattern_matrix
    if _pattern_matrix is not None:
        return
    _answer_list = list(get_wordle_answers())
    _guess_list = list(set(_answer_list) | {OPTIMAL_FIRST_WORD})
    _answer_to_idx = {w: i for i, w in enumerate(_answer_list)}
    _guess_to_idx = {w: i for i, w in enumerate(_guess_list)}
    _pattern_matrix = [[0] * len(_answer_list) for _ in range(len(_guess_list))]
    for gi, guess in enumerate(_guess_list):
        for ai, answer in enumerate(_answer_list):
            pattern = get_evaluation_raw(answer, guess)
            _pattern_matrix[gi][ai] = encode_pattern(pattern)


def get_cached_eval(guess, answer_str):
    return _pattern_matrix[_guess_to_idx[guess]][_answer_to_idx[answer_str]]


def compute_buckets(guess, candidate_idxs):
    gi = _guess_to_idx[guess]
    buckets = {}
    for ai in candidate_idxs:
        pcode = _pattern_matrix[gi][ai]
        if pcode not in buckets:
            buckets[pcode] = [ai]
        else:
            buckets[pcode].append(ai)
    return buckets


def play(game_rows, browser, possible_guesses, possible_answers, classic_wordle=True):
    global _answer_list, _guess_list
    build_cache()

    if classic_wordle:
        words = possible_answers
    else:
        words = possible_answers

    narrowed_down_list = list(possible_answers)
    candidate_indices = [i for i in range(len(_answer_list))]
    answer_str_to_idx = {w: i for i, w in enumerate(_answer_list)}

    for guess_number in range(6):
        if guess_number == 0:
            chosen_word = OPTIMAL_FIRST_WORD
            buckets = compute_buckets(chosen_word, candidate_indices)
        elif len(candidate_indices) <= CANDIDATE_DIRECT_GUESS_THRESHOLD:
            chosen_word = _answer_list[candidate_indices[0]]
            buckets = compute_buckets(chosen_word, candidate_indices)
        else:
            min_score = float('inf')
            chosen_word = ""
            chosen_buckets = {}

            for guess in words:
                buckets = compute_buckets(guess, candidate_indices)
                score = sum(len(v) * len(v) for v in buckets.values())
                if score < min_score:
                    min_score = score
                    chosen_word = guess
                    chosen_buckets = buckets
                    if score == len(candidate_indices):
                        break

            buckets = chosen_buckets

        enter_guess(chosen_word)
        time.sleep(1)

        if classic_wordle:
            answer_evaluation = get_wordle_evaluation(chosen_word, game_rows[guess_number], browser)
        else:
            answer_evaluation = get_wordmaster_evaluation(chosen_word, game_rows[guess_number], browser)

        if answer_evaluation == (2, 2, 2, 2, 2):
            return [chosen_word]

        pcode = encode_pattern(answer_evaluation)
        if pcode in buckets:
            candidate_indices = buckets[pcode]
        else:
            candidate_indices = []

        narrowed_down_list = [_answer_list[i] for i in candidate_indices] if candidate_indices else []

        if len(candidate_indices) == 1:
            enter_guess(_answer_list[candidate_indices[0]])
            return [chosen_word]

        time.sleep(1)

    return narrowed_down_list


def get_wordle_evaluation(chosen_word, game_row, browser):
    row = browser.execute_script('return arguments[0].shadowRoot', game_row)
    tiles = row.find_elements(By.CSS_SELECTOR, "game-tile")
    evaluation = []
    eval_to_int = {"correct": 2, "present": 1, "absent": 0}
    for tile in tiles:
        evaluation.append(eval_to_int[tile.get_attribute("evaluation")])
    return tuple(evaluation)


def get_wordmaster_evaluation(chosen_word, game_row, browser):
    evaluation = []
    for tile in game_row:
        if 'nm-inset-n-green' in tile.get_attribute("class"):
            evaluation.append(2)
        elif 'nm-inset-yellow-500' in tile.get_attribute("class"):
            evaluation.append(1)
        elif 'nm-inset-n-gray' in tile.get_attribute("class"):
            evaluation.append(0)
    return tuple(evaluation)


def enter_guess(word):
    keyboard.write(word, delay=0.05)
    keyboard.press_and_release('enter')


def run_program():
    start_button = 'esc'
    classic_wordle = False

    browser = webdriver.Chrome(ChromeDriverManager().install())
    if classic_wordle:
        browser.get("https://www.powerlanguage.co.uk/wordle/")
        keyboard.wait(start_button)

        game_app = browser.find_element(By.TAG_NAME, 'game-app')
        board = browser.execute_script("return arguments[0].shadowRoot.getElementById('board')", game_app)
        game_rows = board.find_elements(By.TAG_NAME, 'game-row')

        play(game_rows, browser, get_wordle_guesses(), get_wordle_answers(), classic_wordle)
    else:
        num_games = 100

        browser.get("https://octokatherine.github.io/word-master/")
        keyboard.wait(start_button)

        for _ in range(num_games):
            game_rows = np.array(browser.find_elements(By.TAG_NAME, 'span')).reshape(6, 5)
            play(game_rows, browser, get_wordmaster_guesses(), get_wordmaster_answers(), classic_wordle)

            time.sleep(2)
            keyboard.press('esc')
            time.sleep(2)
            keyboard.release('esc')
            time.sleep(1)
            browser.find_element(By.XPATH, '//button[text()="Play Again"]').click()
            time.sleep(1)
    keyboard.wait(start_button)
