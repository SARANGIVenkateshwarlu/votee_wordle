import time

OPTIMAL_FIRST_WORD = "salet"
DIRECT_GUESS_THRESHOLD = 3
ON_THE_FLY_LIMIT = 100

# English letter frequency in 5-letter words (ETAOIN SHRDLU adapted)
LETTER_FREQ = "eariotnslcudpmhgbfywkvxzjq"


def evaluate(answer, guess):
    output = [0, 0, 0, 0, 0]
    chars = list(answer)
    for i in range(5):
        if guess[i] == chars[i]:
            output[i] = 2
            chars[i] = ' '
    for i in range(5):
        if output[i] == 0:
            c = guess[i]
            if c in chars:
                output[i] = 1
                chars[chars.index(c)] = ' '
    return tuple(output)


def encode(pattern):
    return sum(x * (3 ** i) for i, x in enumerate(pattern))


def decode(code):
    return tuple((code // (3 ** i)) % 3 for i in range(5))


class WordleSolver:

    def __init__(self, answer_list, guess_list=None, full_wordlist=None, first_word=OPTIMAL_FIRST_WORD):
        self.answer_list = list(answer_list)
        self.guess_list = list(guess_list) if guess_list else list(self.answer_list)
        self.full_wordlist = list(full_wordlist) if full_wordlist else list(self.answer_list)
        self.first_word = first_word
        self.threshold = DIRECT_GUESS_THRESHOLD
        self.otf_limit = ON_THE_FLY_LIMIT

        if self.first_word not in self.guess_list:
            self.guess_list.append(self.first_word)
        if self.first_word not in self.full_wordlist:
            self.full_wordlist.append(self.first_word)

        self._guess_idx = {w: i for i, w in enumerate(self.guess_list)}
        self._matrix = None
        self._candidates = None
        self._history = None
        self._guessed = None
        self._char_mode = False
        self._known = None
        self._must_include = None
        self._excluded = None
        self._yellow_at = None
        self._last_candidate_count = None

    def build_cache(self):
        if self._matrix is not None:
            return 0
        t0 = time.time()
        na, ng = len(self.answer_list), len(self.guess_list)
        self._matrix = [[0] * na for _ in range(ng)]
        for gi, guess in enumerate(self.guess_list):
            for ai, answer in enumerate(self.answer_list):
                self._matrix[gi][ai] = encode(evaluate(answer, guess))
        return time.time() - t0

    def reset(self):
        self._candidates = list(self.full_wordlist)
        self._history = []
        self._guessed = set()
        self._char_mode = False
        self._known = [None] * 5
        self._must_include = set()
        self._excluded = set()
        self._yellow_at = [set() for _ in range(5)]
        self._last_candidate_count = len(self._candidates)

    @property
    def candidates_remaining(self):
        return len(self._candidates) if self._candidates is not None else 0

    @property
    def history(self):
        return self._history or []

    # ── word-list mode ──

    def _bucket_score_matrix(self, guess):
        gi = self._guess_idx.get(guess)
        if gi is None:
            return float('inf')
        buckets = {}
        for ai in range(len(self.answer_list)):
            c = self._matrix[gi][ai]
            buckets[c] = buckets.get(c, 0) + 1
        return sum(v ** 2 for v in buckets.values())

    def _bucket_score_otf(self, guess, candidates):
        buckets = {}
        for cand in candidates:
            c = encode(evaluate(cand, guess))
            buckets[c] = buckets.get(c, 0) + 1
        return sum(v ** 2 for v in buckets.values())

    def _is_valid_guess(self, guess):
        for i, ch in enumerate(guess):
            if self._known[i] is not None and self._known[i] != ch:
                return False
        for ch in self._excluded:
            if ch in guess:
                return False
        for req in self._must_include:
            if req not in guess:
                return False
        for i in range(5):
            if guess[i] in self._yellow_at[i]:
                return False
        return True

    def _choose_from_words(self):
        use_otf = self.candidates_remaining <= self.otf_limit
        candidates = self._candidates if use_otf else None

        best = float('inf')
        pick = self.first_word
        pool = [g for g in self.guess_list if g not in self._guessed]
        if not pool:
            pool = list(self.guess_list)

        need_explore = self._known.count(None) >= 3

        for g in pool:
            if need_explore and not self._is_valid_guess(g):
                continue
            score = self._bucket_score_otf(g, candidates) if use_otf else self._bucket_score_matrix(g)
            if score < best:
                best = score
                pick = g
                if best <= 1:
                    break

        if need_explore and best == float('inf'):
            pick = pool[0] if pool else self.first_word

        self._guessed.add(pick)
        return pick

    # ── character exploration mode (fallback) ──

    def _choose_from_chars(self):
        valid = [w for w in self.full_wordlist
                 if w not in self._guessed and self._is_valid_guess(w)]

        if valid:
            if len(valid) <= self.threshold:
                pick = valid[0]
                self._guessed.add(pick)
                return pick

            return self._pick_by_entropy(valid)

        word = self._known[:]
        remaining = list(self._must_include)

        for i, letter in enumerate(self._known):
            if letter and letter in remaining:
                remaining.remove(letter)

        open_slots = [i for i in range(5) if word[i] is None]

        for i in open_slots:
            for ch in list(remaining):
                if ch not in self._yellow_at[i]:
                    word[i] = ch
                    remaining.remove(ch)
                    break

        for i in open_slots:
            if word[i] is not None:
                continue
            for ch in LETTER_FREQ:
                if (ch not in self._excluded and
                    ch not in self._yellow_at[i] and
                    ch not in word):
                    word[i] = ch
                    break

        guess = ''.join(w if w else 'e' for w in word)
        self._guessed.add(guess)
        return guess

    def _pick_by_entropy(self, candidates):
        best = float('inf')
        pick = candidates[0]
        for g in candidates:
            buckets = {}
            for cand in candidates:
                c = encode(evaluate(cand, g))
                buckets[c] = buckets.get(c, 0) + 1
            score = sum(v ** 2 for v in buckets.values())
            if score < best:
                best = score
                pick = g
                if best <= len(candidates):
                    break
        self._guessed.add(pick)
        return pick

    # ── main interface ──

    def choose_guess(self, turn):
        if turn == 1:
            self._guessed.add(self.first_word)
            return self.first_word

        if self._char_mode:
            return self._choose_from_chars()

        # Detect stagnation — switch to char mode if we're stuck
        shrinking = self._last_candidate_count - self.candidates_remaining
        self._last_candidate_count = self.candidates_remaining

        if self.candidates_remaining == 0 or (
            shrinking == 0 and self.candidates_remaining > 3):
            self._char_mode = True
            return self._choose_from_chars()

        if 1 <= self.candidates_remaining <= self.threshold:
            pick = self._candidates[0]
            self._guessed.add(pick)
            return pick

        return self._choose_from_words()

    def _update_constraints(self, guess, feedback):
        matched = list(guess)
        for i, (g, f) in enumerate(zip(guess, feedback)):
            if f == 2:
                self._known[i] = g
                if g in self._must_include:
                    self._must_include.discard(g)
                matched[i] = ' '
            elif f == 1:
                self._must_include.add(g)
                self._yellow_at[i].add(g)
                matched[i] = ' '
            else:
                pass

        # Exclude letters that are used up as gray but not counted elsewhere
        gray_letters = [
            guess[i] for i in range(5) if feedback[i] == 0
        ]
        for ch in set(gray_letters):
            green_count = sum(1 for j in range(5) if feedback[j] == 2 and guess[j] == ch)
            yellow_count = sum(1 for j in range(5) if feedback[j] == 1 and guess[j] == ch)
            known_count = green_count + yellow_count
            if known_count == 0 and ch not in self._known and ch not in self._must_include:
                self._excluded.add(ch)

    def update(self, guess, feedback):
        self._history.append((guess, feedback))
        self._update_constraints(guess, feedback)

        if feedback == (2, 2, 2, 2, 2):
            self._candidates = [guess]
            return True

        if not self._char_mode:
            fb_code = encode(feedback)
            self._candidates = [
                w for w in self._candidates
                if encode(evaluate(w, guess)) == fb_code
            ]

        return False

    def get_answer_guess(self):
        if self._candidates and len(self._candidates) == 1:
            return self._candidates[0]
        if all(self._known):
            return ''.join(self._known)
        return None
