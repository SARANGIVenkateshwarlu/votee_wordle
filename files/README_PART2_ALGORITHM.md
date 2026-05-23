# Votee Wordle API Solver — Part 2: Algorithm & Strategy

> Entropy maximization, game loop, API integration, Streamlit app, performance cache.

---

## Phase 5: Entropy Algorithm (1 hour)

**Goal:** Use information theory to pick the mathematically optimal guess. Choose the word that splits remaining answers into the most BALANCED groups.

```python
def encode(p):
    """Convert (0,1,2,0,1) to integer 0-242 using base-3"""
    return sum(x * (3**i) for i, x in enumerate(p))

def entropy(guess, candidates):
    """Score = sum of squared bucket sizes. LOWER is BETTER."""
    buckets = {}
    for w in candidates:
        p = encode(evaluate(w, guess))
        buckets[p] = buckets.get(p, 0) + 1
    return sum(c**2 for c in buckets.values())
```

**Math intuition:**
- 5 groups of 20 words: `5 x (20^2) = 5 x 400 = 2,000` (GOOD — balanced)
- 1 group of 90 + 5 of 2: `8100 + 5 x 4 = 8,120` (BAD — unbalanced)

**Equivalent to maximizing Shannon entropy** `H = -sum(p_i * log2(p_i))` but computationally cheaper — no floating-point logarithms, just integer arithmetic.

![Solver in Action](results/test_3.png)

**In the real project (solver.py):**
```python
class WordleSolver:
    def choose_guess(self, turn):
        if turn == 1:
            return "salet"              # optimal first word

        if self.candidates_remaining <= 3:
            return self._candidates[0]   # endgame: guess directly

        # Compute entropy for every possible guess
        for guess in self.guess_list:
            buckets = compute_buckets(guess, candidates)
            score = sum(v**2 for v in buckets.values())
            if score < best_score:
                best_score = score
                best_guess = guess
        return best_guess
```

---

## Phase 6: Game Loop (30 min)

**Goal:** Wire everything into a complete self-contained game.

```python
def play(answer, words):
    candidates = list(words)
    for turn in range(1, 7):              # max 6 guesses
        if turn == 1:
            guess = "salet"
        elif len(candidates) <= 2:
            guess = candidates[0]          # endgame
        else:
            guess = pick_best_entropy(candidates)

        fb = evaluate(answer, guess)
        if fb == (2,2,2,2,2):
            return turn                    # solved!

        candidates = [w for w in candidates
                      if evaluate(w, guess) == fb]
    return 6  # failed
```

**Inside main.py:**
```python
def play_api_game(api_func, solver, **kwargs):
    solver.reset()
    for turn in range(1, 7):
        guess = solver.choose_guess(turn)
        feedback = api_func(guess, **kwargs)
        solved = solver.update(guess, feedback)
        if solved:
            return {"solved": True, "turns": turn}
        answer = solver.get_answer_guess()
        if answer:                         # narrowed to 1
            feedback = api_func(answer, **kwargs)
            if feedback == (2,2,2,2,2):
                return {"solved": True, "turns": turn + 1}
    return {"solved": False, "turns": 6}
```

---

## Phase 7: Connect to Real Votee API (30 min)

**Goal:** Swap local `evaluate()` with live API calls. The API is just a remote version of evaluate() — the rest of your code stays unchanged.

```python
MAP = {"correct": 2, "present": 1, "absent": 0}

def api_word(word, guess):
    """Guess against a specific known word"""
    r = requests.get(f"https://wordle.votee.dev:8000/word/{word}",
                     params={"guess": guess})
    return tuple(MAP[x["result"]] for x in r.json())

def api_random(guess, seed):
    """Guess against a seeded random word — SEED IS CRITICAL"""
    r = requests.get(f"https://wordle.votee.dev:8000/random",
                     params={"guess": guess, "seed": seed})
    return tuple(MAP[x["result"]] for x in r.json())

def api_daily(guess):
    """Guess against today's daily puzzle"""
    r = requests.get(f"https://wordle.votee.dev:8000/daily",
                     params={"guess": guess})
    return tuple(MAP[x["result"]] for x in r.json())
```

**Critical:** Always pass `seed=` to `/random` — without it, a NEW random word is chosen EACH TURN, breaking the game.

---

## Phase 8: Streamlit Web App (45 min)

**Goal:** Beautiful interactive UI anyone can use.

```bash
pip install streamlit
streamlit run app.py
```

![Streamlit App](results/app.png)

**Key Streamlit concepts used in app.py:**

| Concept | What it does in the app |
|---------|------------------------|
| `st.session_state` | Remembers game state (guesses, score, streak) between reruns |
| `st.text_input` | The 5-letter guess input box, centered, uppercase |
| `st.button` | New Game and Auto-Solve triggers |
| `st.columns` | Horizontal layout for 4 stat boxes (played / win% / streak / avg) |
| `st.markdown` + HTML/CSS | Custom Wordle grid with green/yellow/gray tile colors |
| `@keyframes` CSS | Tile flip animation on reveal, bounce animation on win |
| `st.spinner` | Loading indicator while building the 5.4M-entry pattern cache |

**CSS color scheme (matches NYT Wordle exactly):**
- Background: `#121213` (dark)
- Green tile: `#538d4e`
- Yellow tile: `#b59f3b`
- Gray tile: `#3a3a3c`
- Keyboard unused: `#818384`

---

## Phase 9: Precompute Pattern Matrix (30 min)

**Goal:** 28x speed improvement by caching ALL evaluations once at startup.

Build a 2,316 x 2,315 = **5.4 MILLION** pattern matrix (~15 seconds startup). Then O(1) lookups for all subsequent turns.

```python
class WordleSolver:
    def build_cache(self):
        na = len(self.answer_list)     # 2,315
        ng = len(self.guess_list)      # 2,316
        self._matrix = [[0] * na for _ in range(ng)]
        for gi, guess in enumerate(self.guess_list):
            for ai, answer in enumerate(self.answer_list):
                self._matrix[gi][ai] = encode(evaluate(answer, guess))
        # Now: self._matrix[gi][ai] is O(1) — no string ops needed!
```

| Metric | Before | After |
|--------|--------|-------|
| Per-turn computation | ~850ms | **~30ms** |
| Speed improvement | — | **28x faster** |
| Startup cost | 0 | ~15 seconds (one-time) |

![Benchmark Results](results/test_4.png)

---

## Quick Reference: Files & Functions

| Concept | File | Function / Class |
|---------|------|-----------------|
| API calls | `api_client.py` | `guess_word()`, `guess_random()`, `guess_daily()` |
| Feedback evaluation | `solver.py` | `evaluate()` |
| Pattern encoding to int | `solver.py` | `encode()` / `decode()` |
| Candidate filtering | `solver.py` | `WordleSolver.update()` |
| Entropy guess pick | `solver.py` | `WordleSolver.choose_guess()` |
| Pattern matrix cache | `solver.py` | `WordleSolver.build_cache()` |
| Game loop orchestration | `main.py` | `play_api_game()` |
| Web UI | `app.py` | `submit_guess()`, `auto_solve()` |
| Word list loading | `words.py` | `get_wordle_answers()`, `get_wordle_guesses()` |

---

## Common Mistakes & Fixes

| Mistake | Why | Fix |
|---------|-----|-----|
| Duplicate letters wrong | Single-pass evaluation | Two-pass: greens first, then yellows |
| `range(5)` not `range(6)` | Forgetting Wordle gives 6 tries | Always use `range(6)` |
| `fb == [2,2,2,2,2]` never True | Python: tuple != list | Use `fb == (2,2,2,2,2)` |
| API call crashes silently | No error handling | Wrap in `try/except` |
| Guessing same word twice | No tracking | Maintain a `set()` of guessed words |
| Entropy against wrong set | Scoring vs full list, not remaining | Score against FILTERED candidates |
| Slow solver | Computing patterns per turn | Precompute once (Phase 9) |
| Random word changes per turn | No seed on /random | Always pass `seed=` parameter |

---

## Learning Timeline (~5 hours total)

| Phase | Time | Milestone |
|-------|------|-----------|
| 1 — Hello API | 15 min | First API call returns JSON |
| 2 — Feedback Engine | 30 min | evaluate() passes all test cases |
| 3 — Word List + Filter | 30 min | Narrows 2,315 candidates to ~100 |
| 4 — Letter Frequency | 45 min | Solver wins >50% of games |
| 5 — Entropy Algorithm | 1 hr | Solver wins >95% of games |
| 6 — Game Loop | 30 min | Complete self-contained game |
| 7 — Real Votee API | 30 min | Works against live API |
| 8 — Streamlit App | 45 min | Beautiful playable web UI |
| 9 — Performance Cache | 30 min | 28x speed improvement |
| **TOTAL** | **~5 hrs** | **Professional-grade Wordle solver** |
