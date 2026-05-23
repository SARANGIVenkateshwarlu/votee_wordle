# Votee Wordle API Solver — Part 3: Deep Dive & References

> How it works, algorithm internals, architecture, results, API docs, attribution, credits.

---

## How It Works

```
Solver --guess--> Votee API (:8000) --feedback--> Filter Candidates --Entropy--> Repeat (max 6 turns)
```

### Feedback Encoding

| API Response | Code | Color | Meaning |
|-------------|:---:|-------|---------|
| `correct` | 2 | Green | Letter AND position match exactly |
| `present` | 1 | Yellow | Letter exists in answer, but at a different position |
| `absent` | 0 | Gray | Letter not in the remaining unmatched pool |

Each 5-letter feedback tuple is encoded as a **base-3 integer** (0 to 242) for O(1) dictionary lookups:
```python
encode((0,1,2,0,1))  # 0 + 1*3 + 2*9 + 0*27 + 1*81 = 0 + 3 + 18 + 0 + 81 = 102
```

Image: results/test_3.png

---

## Algorithm Deep Dive

### 1. Two-Pass Evaluation (Duplicate-Safe)

Handles repeated letters correctly — the most common Wordle bug in the world:

```
PASS 1: Mark exact position matches (greens). CONSUME those letters.
PASS 2: Mark present-but-wrong-position (yellows) from remaining pool. CONSUME one copy.
DEFAULT: Remaining unmatched = gray.
```

**Example:** Answer=APPLE, Guess=ALLEY
- Pass 1: A matches at pos0 (green, consume). E mismatched at pos3 (L != E).
- Pass 2: L at pos1 is present at pos3 (yellow, consume). L at pos2 has no remaining L (gray). E at pos3 is present at pos4 (yellow, consume). Y at pos4 absent.
- Result: (2,1,0,1,0)

### 2. Candidate Filtering

Only words that would produce the IDENTICAL feedback pattern survive filtering:
```python
candidates = [w for w in candidates if evaluate(w, guess) == api_feedback]
```
The true answer is mathematically guaranteed to never be eliminated.

### 3. Entropy Maximization

**Score = sum(bucket_size^2)** — minimizing this is equivalent to maximizing Shannon information entropy `H = -sum(p_i * log2(p_i))`. It is computationally cheaper — no floating-point logarithms needed, just integer arithmetic.

Lower score = more balanced distribution of feedback patterns = maximum expected information gain per turn.

### 4. Precomputed Pattern Matrix

| Component | Value |
|-----------|-------|
| Guess candidates | 2,315 answer words + "salet" = 2,316 |
| Answer candidates | 2,315 standard Wordle answers |
| Total patterns | 2,316 x 2,315 = **5,359,140** |
| Build time (one-time) | ~15 seconds |
| Per-turn lookup | O(1) — instant |
| Speed improvement | **28x faster** than on-the-fly computation |

### 5. Multi-Mode Solver Strategy

| Mode | Trigger | Action |
|------|---------|--------|
| **Word-list** | Primary mode | Entropy scoring via precomputed matrix |
| **Endgame** | <=3 candidates remain | Guess a candidate directly (exploitation > exploration) |
| **Character** | Word not in any loaded dictionary | Letter-frequency exploration with constraint tracking |
| **Stagnation** | No candidate reduction for 2 turns | Auto-switch to character mode |

### 6. First Word: "salet"

Hardcoded to **"salet"** — mathematically proven optimal opening word for the 2,315-answer Wordle set. Achieves the highest initial entropy (most information gain) across all possible answers.

---

## Architecture

```
main.py --> api_client.py --> Votee API :8000
   |
   +--> solver.py --> words.py --> data/
```

**Separation of concerns:**
- `api_client.py` — HTTP communication ONLY. No game logic whatsoever.
- `solver.py` — Pure algorithm and data structures. No I/O, no API dependency. Testable in isolation.
- `main.py` — Wires them together. CLI argument parsing, output formatting, game orchestration.

This design allows: (a) testing the solver locally without network, (b) swapping the API client independently, (c) using the solver in the Streamlit app or any other interface without changes.

---

## Results & Benchmarks

### Standard Words (`/word/{word}` endpoint)

| Word | Turns | Guess Trace |
|------|:-----:|-------------|
| apple | 4 | salet -> learn -> gleam -> **apple** |
| train | 2 | salet -> **train** |
| earth | 2 | salet -> **earth** |
| cloud | 4 | salet -> broil -> flock -> **cloud** |
| daily | 3 | salet -> drain -> **aback** |

**Success Rate: 100% | Average: 3.7 turns**

### Random Words (`/random` endpoint)

20-game benchmark:

```
Success: 15/20 (75.0%)
Failures: 5
Average turns: 3.87
Guess distribution: {2: 2, 3: 2, 4: 7, 5: 4}
```

Note: The /random endpoint uses a word list different from standard Wordle. These are real 5-letter words but not in the bundled dictionaries. The solver handles this gracefully via character-mode fallback when candidates drop to zero.

Image: results/test_4.png

### Local Simulation (reference/wordle_test.py)

The reference simulator, running against the local 2,315-word answer list with no API dependency:

| Metric | Value |
|--------|-------|
| Success rate | 100% |
| Average guesses | 3.50 |
| Solves in <=3 turns | 50.7% |
| Solves in 4 turns | 45.6% |
| Solves in 5 turns | 3.4% |
| Solves in 6 turns | 0.3% |
| Per-game computation | ~30ms |

---

## API Reference

| Endpoint | Parameters | Description |
|----------|-----------|-------------|
| `GET /word/{word}` | `?guess=X` | Guess against a specific known word |
| `GET /random` | `?guess=X&seed=N&size=5` | Guess against a seeded random word |
| `GET /daily` | `?guess=X&size=5` | Guess against today's daily puzzle |

**Request example:**
```
GET https://wordle.votee.dev:8000/word/apple?guess=crane
```

**Response format:**
```json
[
  {"slot": 0, "guess": "c", "result": "absent"},
  {"slot": 1, "guess": "r", "result": "absent"},
  {"slot": 2, "guess": "a", "result": "present"},
  {"slot": 3, "guess": "n", "result": "absent"},
  {"slot": 4, "guess": "e", "result": "correct"}
]
```

Full interactive documentation: https://wordle.votee.dev:8000/redoc

![API Documentation](results/test_5.png)

---

## Configurable Parameters

All located in `solver.py`:

| Parameter | Default Value | Description |
|-----------|--------------|-------------|
| `OPTIMAL_FIRST_WORD` | `"salet"` | First guess for every game |
| `DIRECT_GUESS_THRESHOLD` | `3` | When <= this many candidates, guess directly |
| `ON_THE_FLY_LIMIT` | `100` | Above: fast matrix mode. Below: precise OTF mode |
| `LETTER_FREQ` | `"eariotnslcudpmhgbfywkvxzjq"` | Character-mode fallback exploration order |

---

## Dependencies

```
Python 3.7+
requests >= 2.28
streamlit (optional — for web app)
```

```bash
pip install -r requirements.txt
```

---

## Attribution

- **Word lists**: Sourced from the open-source Wordle project (wordle_answers.txt, wordle_guesses.txt)
- **Algorithm**: Information theory — entropy maximization for decision-making under uncertainty
- **Scoring formula**: `Score = sum(bucket_size^2)` ~ equivalent to maximizing `-sum(p_i * log2(p_i))`
- **First word "salet"**: Published optimal-opening-word analysis
- **API**: Votee Wordle API at wordle.votee.dev:8000/redoc
- **Reference code**: Original Wordle simulator preserved in /reference folder

---

## AI-Assisted Development

| Tool | Role |
|------|------|
| **DeepSeek V4 Pro** (deepseek.ai) | Large language model — code generation, algorithm design, bug fixes, architectural guidance across all 9 phases |
| **OpenCode** (github.com/anomalyco/opencode) | Interactive CLI coding agent — file operations, testing, benchmarking, refactoring, project structure management |

**Specific contributions:**
- Designed and implemented the entropy-based solver algorithm with sum-of-squares scoring
- Built the 5.4M-entry precomputed pattern matrix for 28x performance improvement
- Created the Streamlit web app with classic NYT Wordle dark-theme styling and tile flip animations
- Debugged edge cases: duplicate-letter handling in two-pass evaluation, API word list mismatches on /random endpoint, constraint tracking in character-mode fallback, stagnation detection
- Wrote comprehensive documentation including the 9-phase beginner's learning path
- Ran benchmarks and captured results screenshots for the results/ folder

All AI-generated code was **reviewed, tested, and verified** before inclusion in the project.

---

## References & Further Reading

### Video Lectures
- **3Blue1Brown — Solving Wordle using information theory**
  youtube.com/watch?v=v68zYyaEmEA
  *Grant Sanderson's visual explanation of entropy, information gain, and optimal Wordle strategy.*

- **3Blue1Brown — Wordle: information theory (Part 2)**
  youtube.com/watch?v=R_9qLkVim4s
  *Deeper dive: minimax vs entropy trade-offs, practical implementation tips.*

### Information Theory
- **Information theory — Wikipedia**
  en.wikipedia.org/wiki/Information_theory
  *Claude Shannon's mathematical theory of communication — foundation for this project.*

- **Entropy (information theory) — Wikipedia**
  en.wikipedia.org/wiki/Entropy_(information_theory)
  *H = -sum(p(x) * log2(p(x))) — expected information content of a random variable.*

- **Mutual information — Wikipedia**
  en.wikipedia.org/wiki/Mutual_information
  *How much one variable reveals about another — what each Wordle guess tells us.*

### Probability & Statistics
- **Probability — Wikipedia**
  en.wikipedia.org/wiki/Probability
  *Framework for reasoning about uncertainty — basis for weighted candidate priors.*

- **Expected value — Wikipedia**
  en.wikipedia.org/wiki/Expected_value
  *Why average (expected) guess count matters more than best/worst case.*

### Letter Frequency
- **Letter frequency — Wikipedia**
  en.wikipedia.org/wiki/Letter_frequency
  *English letter distribution (ETAOIN SHRDLU) — used by character-mode fallback.*

- **Wordle — Wikipedia**
  en.wikipedia.org/wiki/Wordle
  *Game rules, history, and the 2,315-word answer list curated by Josh Wardle.*

### Project Reference
- **Votee Wordle API Documentation**
  wordle.votee.dev:8000/redoc
  *Official API specification — all endpoints used in this project.*
