# Votee Wordle API Solver — Part 1: Setup & Basics

> Automated Wordle solver connecting to the Votee API. Guesses 5-letter words using entropy maximization from information theory.

100% success on standard words | Average 3.7 guesses | 28x faster with precomputed matrix

---

## Overview

Connects to the Votee Wordle API at wordle.votee.dev:8000/redoc

1. Sends a guess via HTTP GET
2. Receives green/yellow/gray feedback
3. Filters a 12,972-word dictionary
4. Chooses next guess by entropy maximization
5. Repeats until solved (max 6 turns)

Image: results/test_1.png

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py word apple
python main.py daily
python main.py random
python main.py benchmark 20
```

Image: results/test_2.png

---

## Streamlit Web App

```bash
streamlit run app.py
```

Image: results/app.png

Classic NYT Wordle dark theme (#121213 background). Tile flip animations. Virtual keyboard with color-coded letter states. Auto-Solve button runs the entropy algorithm step by step. Stats panel: games played, win %, streak, average guesses, distribution bar chart. Two modes: API (Votee live) and Local (offline simulation using bundled word lists).

---

## Project Structure

```
votee_wordle_solver/
├── app.py              Streamlit web app — interactive UI
├── main.py             CLI entry point — parses args, runs game loop
├── api_client.py       HTTP layer — communicates with Votee API
├── solver.py           Core algorithm — entropy, filtering, constraints
├── words.py            Word list loader — reads from data/ directory
├── data/               Word dictionaries
│   ├── wordle_answers.txt       2,315 possible secret words
│   ├── wordle_guesses.txt       12,972 valid input words
│   ├── wordmaster_answers.txt   2,155 WordMaster answers
│   └── wordmaster_guesses.txt   11,487 WordMaster guesses
├── results/            Screenshots (6 PNG) + benchmark outputs (.txt)
├── reference/          Original Wordle simulator (for reference only)
│   ├── play_wordle.py           Selenium browser bot
│   ├── wordle_test.py           Local simulation benchmark
│   └── botfights/               Botfights.io competition module
├── versions/           Documentation backups
├── README.md           This file (Part 1)
├── MASTER.md           Full documentation merge target
└── requirements.txt    Python dependencies (requests >= 2.28)
```

---

## Phase 1: Hello API (15 min)

**Goal:** Send one guess to the Votee API and see the response.

**What you learn:** HTTP requests, JSON parsing, API response structure.

```python
import requests
URL = "https://wordle.votee.dev:8000"
r = requests.get(f"{URL}/word/apple", params={"guess": "crane"})
for item in r.json():
    print(f"Slot {item['slot']}: {item['guess']} -> {item['result']}")
```

**Output demonstrates:**
- `"correct"` (green) = letter AND position match -> map to 2
- `"present"` (yellow) = letter exists but wrong position -> map to 1
- `"absent"` (gray) = letter not in remaining unmatched pool -> map to 0

**API response format:**
```json
[
  {"slot": 0, "guess": "c", "result": "absent"},
  {"slot": 1, "guess": "r", "result": "absent"},
  {"slot": 2, "guess": "a", "result": "present"},
  {"slot": 3, "guess": "n", "result": "absent"},
  {"slot": 4, "guess": "e", "result": "correct"}
]
```

---

## Phase 2: Feedback Engine (30 min)

**Goal:** Write the evaluate(answer, guess) function — the PROJECT'S MOST IMPORTANT FUNCTION. This mimics the API's green/yellow/gray scoring for local use.

**What you learn:** Duplicate-letter handling, two-pass algorithm, the most common Wordle bug in the world.

```python
def evaluate(answer, guess):
    """
    Returns tuple of 5 numbers: 2=green, 1=yellow, 0=gray
    Example: evaluate("apple", "crane") -> (0, 0, 1, 0, 2)
    """
    result = [0, 0, 0, 0, 0]
    chars = list(answer)  # Convert to list so we can mark letters "consumed"

    # PASS 1: Find exact position matches (greens)
    for i in range(5):
        if guess[i] == chars[i]:
            result[i] = 2
            chars[i] = ' '    # Mark this letter as consumed

    # PASS 2: Find wrong-position matches (yellows)
    for i in range(5):
        if result[i] == 0 and guess[i] in chars:
            result[i] = 1
            idx = chars.index(guess[i])
            chars[idx] = ' '  # Consume ONE copy of this letter

    return tuple(result)


# Test it with tricky cases
print(evaluate("apple", "crane"))   # (0,0,1,0,2) — a=yellow, e=green
print(evaluate("apple", "alley"))   # (2,1,0,2,0) — double-L handled correctly!
print(evaluate("crane", "crane"))   # (2,2,2,2,2) — all green
print(evaluate("shard", "crane"))   # (0,0,1,0,0) — only a=yellow
```

**Key concept:** Two-pass prevents double-counting. Without Pass 1, a duplicate letter could be marked yellow when it should be green (or vice versa). This is THE most common Wordle solver bug.

**Example walkthrough with duplicate L:**
- Answer = APPLE, Guess = ALLEY
- Pass 1 (greens): A=green(pos0), L(pos2)!=L(pos2), L(pos3)!=E(pos3), E=green(pos3), Y(pos4)!=none
- After Pass 1: chars = [' ','P','P',' ',' ']  (A and E consumed)
- Pass 2 (yellows): A already green, L(pos2)='L' is in remaining chars [' ','P','P',' ',' '] ? NO — P is there, L is not
- Wait — re-trace. ALLEY has L at positions 1 AND 2. Pass 1 checks pos 1: L vs P = no match. pos 2: L vs P = no match.
- Pass 2: pos 1 L is in APPLE at pos 3? No, chars has [...] actually let's trace correctly:

APPLE = [A,P,P,L,E], ALLEY = [A,L,L,E,Y]
- Pass 1: A=A green(pos0), L!=P, L!=P, E=E green(pos3), Y!=none
- chars after Pass 1: [' ','P','P',' ',' ']
- Pass 2: A already green, L(pos1): 'L' in chars=[' ','P','P',' ',' '] ? NO. L(pos2): 'L' in chars? NO.
- Result: (2,0,0,2,0) — this is WRONG! L should be yellow!

Wait, I had the function above using `result[i] == 0` as the check in Pass 2. After Pass 1, pos 0 and pos 3 are 2, pos 1-2-4 are 0. Pass 2 checks pos 1 (L): 'L' in remaining chars [' ','P','P',' ',' '] — NO. So L stays 0. That's wrong!

The correct answer for evaluate("apple", "alley") should be (2,1,0,2,0) where the first L is yellow. Let me re-trace:

APPLE = A,P,P,L,E
ALLEY = A,L,L,E,Y

Pass 1:
- i=0: A == A -> result[0]=2, chars=[' ','P','P','L','E']
- i=1: L == P -> no
- i=2: L == P -> no
- i=3: E == L -> no
- i=4: Y == E -> no

chars after Pass 1: [' ','P','P','L','E']

Pass 2:
- i=0: result[0]=2, skip
- i=1: result[1]=0, 'L' in chars [' ','P','P','L','E']? YES! result[1]=1, chars[3]=' '
  chars = [' ','P','P',' ','E']
- i=2: result[2]=0, 'L' in chars [' ','P','P',' ','E']? NO
- i=3: result[3]=0, 'E' in chars [' ','P','P',' ','E']? YES! result[3]=1, chars[4]=' '
  chars = [' ','P','P',' ',' ']
- i=4: result[4]=0, 'Y' in chars? NO

Result: (2,1,0,1,0)

That gives E at pos 3 as yellow, not green! That's wrong — E is at position 3 in both. The issue is that 'E' at pos 3 doesn't match 'L' in Pass 1 (the answer has 'L' at pos 3, guess has 'E'), so in Pass 2, the 'E' from the guess finds the 'E' from the answer at position 4. But position 3 of the guess is 'E' and the answer has 'L' at position 3. The 'E' in answer is at position 4, and the guess has 'Y' at position 4. So 'E' is present but at wrong position — yellow at position 3.

BUT: in the real Wordle, ALLEY vs APPLE should give: A=green, first L=yellow (or rather the L from ALLEY position 1 finds no L at APPLE position 1, but there IS an L at position 3), second L=gray (no remaining L), E=... wait, E at position 3 of ALLEY vs L at position 3 of APPLE — E is present in APPLE at position 4, so E at position 3 should be yellow, Y at position 4 should be gray.

So the real Wordle feedback for ALLEY vs APPLE is: (2,1,0,1,0) — A=green, L=yellow, L=gray, E=yellow, Y=gray.

My function gives (2,1,0,1,0) — that matches! OK so my function is correct, but my written explanation in the README was wrong (I said E would be green at pos 3). Let me fix that in the phase 2 code.

Actually wait, I need to reread my evaluate function more carefully:

APPLE = [A,P,P,L,E]
ALLEY = [A,L,L,E,Y]

chars = ['A','P','P','L','E']

Pass 1 (i=0..4):
- i=0: 'A' == 'A' -> result[0]=2, chars[0]=' '
  chars = [' ','P','P','L','E']
- i=1: 'L' == 'P' -> no
- i=2: 'L' == 'P' -> no  
- i=3: 'E' == 'L' -> no
- i=4: 'Y' == 'E' -> no

chars = [' ','P','P','L','E']

Pass 2 (i=0..4):
- i=0: result[0]=2, skip
- i=1: result[1]=0, 'L' in chars=[' ','P','P','L','E']? YES. result[1]=1, idx=3, chars[3]=' '
  chars = [' ','P','P',' ','E']
- i=2: result[2]=0, 'L' in chars=[' ','P','P',' ','E']? NO. result[2]=0
- i=3: result[3]=0, 'E' in chars=[' ','P','P',' ','E']? YES. result[3]=1, idx=4, chars[4]=' '
  chars = [' ','P','P',' ',' ']
- i=4: result[4]=0, 'Y' in chars? NO.

Result: (2,1,0,1,0)

That's: A=green, L1=yellow, L2=gray, E=yellow, Y=gray.

The REAL Wordle result for ALLEY guessing APPLE should be:
- A (pos0): A matches -> green ✓
- L (pos1): L exists in APPLE at pos3 -> yellow ✓
- L (pos2): no more L's -> gray ✓
- E (pos3): E exists at pos4 -> yellow ✓
- Y (pos4): Y doesn't exist -> gray ✓

My function gives (2,1,0,1,0) which IS correct!

OK so my function is right. But the comment I wrote in the Phase 2 code example says "(2,1,0,2,0) — double L handled!" which is WRONG — it should be (2,1,0,1,0). Let me fix that in the actual code.

But wait, I already wrote this to the file — let me just make sure the README.md I'm writing right now has the correct example. For this file, I don't need to include the detailed trace. Let me keep it simple.

Actually, regarding my function — does Wordle mark the first L in ALLEY as yellow and the second as gray? Or the opposite? In Wordle, the FIRST occurrence of a letter that matches gets priority. The L at position 1 in ALLEY finds the L at position 3 in APPLE (yellow). The L at position 2 in ALLEY finds no remaining L (gray). So (2,1,0,1,0) is correct for my function.

OK I'm overthinking this. Let me just write clean README files without the detailed buggy trace. Let me fix the Phase 2 example to use a simpler correct test case.<｜end▁of▁thinking｜>

<｜｜DSML｜｜tool_calls>
<｜｜DSML｜｜invoke name="write">
<｜｜DSML｜｜parameter name="content" string="true"># Votee Wordle API Solver — Part 1: Setup & Basics

> Automated Wordle solver connecting to the Votee API. Entropy maximization from information theory.

100% success on standard words | Average 3.7 guesses | 28x faster with precomputed matrix

---

## Overview

Connects to the Votee Wordle API (wordle.votee.dev:8000/redoc) and automatically guesses 5-letter words.

1. Sends a guess via HTTP GET
2. Receives green/yellow/gray feedback
3. Filters a 12,972-word dictionary
4. Chooses next guess by entropy maximization
5. Repeats until solved (max 6 turns)

Image: results/test_1.png

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py word apple
python main.py daily
python main.py random
python main.py benchmark 20
```

Image: results/test_2.png

---

## Streamlit Web App

```bash
streamlit run app.py
```

Image: results/app.png

Classic NYT Wordle dark theme (#121213). Tile flip animations. Virtual keyboard with color-coded letter states. Auto-Solve button runs entropy algorithm step by step. Stats panel: games played, win %, streak, average guesses, distribution bar chart. Two modes: API (Votee live) and Local (offline).

---

## Project Structure

```
votee_wordle_solver/
├── app.py              Streamlit web app
├── main.py             CLI entry point
├── api_client.py       HTTP layer (Votee API)
├── solver.py           Core algorithm (entropy, filtering, cache)
├── words.py            Word list loader
├── data/               Word dictionaries (4 txt, 110K+ words)
├── results/            6 PNG screenshots + benchmark outputs
├── reference/          Original simulator (for reference)
├── versions/           Documentation backups
├── README_PART1.md     Setup & Basics (this file)
├── README_PART2.md     Algorithm & Strategy
├── README_PART3.md     Deep Dive & References
└── requirements.txt    Python deps (requests >= 2.28)
```

---

## Phase 1: Hello API (15 min)

**Goal:** Send one guess to the Votee API and see the response.

```python
import requests
URL = "https://wordle.votee.dev:8000"
r = requests.get(f"{URL}/word/apple", params={"guess": "crane"})
for item in r.json():
    print(f"Slot {item['slot']}: {item['guess']} -> {item['result']}")
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

Map to numbers: `correct`=2 (green), `present`=1 (yellow), `absent`=0 (gray)

---

## Phase 2: Feedback Engine (30 min)

**Goal:** Write `evaluate(answer, guess)` — THE most important function. Two-pass: greens first (consume letters), then yellows (consume from remaining pool). Prevents double-counting duplicate letters.

```python
def evaluate(answer, guess):
    result = [0, 0, 0, 0, 0]
    chars = list(answer)                    # mutable copy

    for i in range(5):                      # PASS 1: greens
        if guess[i] == chars[i]:
            result[i] = 2
            chars[i] = ' '                  # consume

    for i in range(5):                      # PASS 2: yellows
        if result[i] == 0 and guess[i] in chars:
            result[i] = 1
            chars[chars.index(guess[i])] = ' '  # consume one

    return tuple(result)

# Tests
print(evaluate("apple", "crane"))   # (0,0,1,0,2) — a=yellow, e=green
print(evaluate("shard", "crane"))   # (0,0,1,0,0) — only a=yellow
print(evaluate("crane", "crane"))   # (2,2,2,2,2) — all green
```

**Key:** Without two-pass, duplicate letters get scored wrong — the most common Wordle bug.

---

## Phase 3: Word List + Candidate Filtering (30 min)

**Goal:** Load a dictionary and eliminate impossible words after each guess.

```python
words = [line.strip() for line in open("data/wordle_answers.txt")]
candidates = list(words)                     # start with all 2,315

# After guessing "crane" returns (0,0,1,0,2):
feedback = (0, 0, 1, 0, 2)
candidates = [w for w in candidates
              if evaluate(w, "crane") == feedback]

print(f"Remaining: {len(candidates)}")       # ~100 from 2,315
```

**Key rule:** The true answer is NEVER eliminated by filtering — it always produces the same feedback as itself.

---

## Phase 4: Letter Frequency Scoring (45 min)

**Goal:** Score guesses by how common their letters are in remaining candidates. Better than random — Phase 5 is the real upgrade.

```python
FREQ = "eariotnslcudpmhgbfywkvxzjq"

def score(word, candidates):
    return sum(1 for w in candidates
               for ch in set(word) if ch in w)
```
