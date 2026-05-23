End-to-end guide: build a Wordle simulator and a strong solving bot
Below is a student-friendly summary of the two transcripts, turned into a practical project guide. It covers:
the basics of Wordle
the information theory behind a good bot
the models and equations
a simple project architecture
what libraries/tools to use
how to simulate games
how to improve the bot
how to measure whether it beats a high score

1. Big idea
The transcripts connect information theory to Wordle.
The key message is:
A good Wordle guess is not just a word with common letters.
A good guess is one that gives the most useful information on average.
That is where entropy comes in.
A strong Wordle bot does two things:
Shrinks the set of possible answers fast
Tries to actually finish the game in few guesses
So the project is really about building:
a Wordle game simulator
a feedback engine
a candidate filtering system
an entropy-based decision model
later, a probability-weighted strategy
and finally, a way to evaluate performance over many games

2. Wordle basics
Rules
In Wordle:
the hidden answer is a 5-letter word
you get 6 guesses
after each guess: 
green = correct letter, correct position
yellow = correct letter, wrong position
gray = letter not in the answer 
with repeated letters, gray handling is subtle
Example
Suppose the answer is:
SHARD
Guess:
CRANE
Feedback:
C = gray
R = yellow
A = green
N = gray
E = gray
Pattern:
⬛ 🟨 🟩 ⬛ ⬛
This pattern tells us a lot:
no C
no N
no E
there is an R, but not in position 2
A is in position 3
That lets us remove many impossible words.

3. What the project should do
You want an end-to-end project that can:
Run Wordle games
Let a human play, or let a bot play
Compute feedback patterns
Track candidate words
Choose guesses intelligently
Simulate thousands of games
Compare strategies
Try to beat a target average score / high score

4. Core information theory ideas
The first transcript introduces the theory in general. The second applies it to Wordle.

4.1 Information content
If something unlikely happens, it gives more information.
The standard formula is:

Where:
= probability of event 
= information in bits
Simple examples
Example A
If an event has probability :

So that event gives 1 bit.
Example B
If an event has probability :

So it gives 2 bits.
Example C
If an event has probability :

So it gives 3 bits.
Intuition
Each extra bit means you cut the possibilities roughly in half one more time.

4.2 Entropy
Entropy is the expected information.
For a discrete random variable :

This tells you how much information you expect to gain before seeing the actual outcome.
In Wordle
For a guess like SLATE, there are many possible color patterns.
Each pattern has some probability.
Entropy of that guess = average information from those possible patterns.
So:
high entropy guess = usually very informative
low entropy guess = usually not very informative

4.3 Why logs matter
Logs are useful because information adds.
If one observation gives 2 bits and another gives 3 bits, together you get:

This mirrors probability multiplication.
That makes entropy natural for decision-making.

5. Why entropy helps in Wordle
Suppose you guess a word. That guess can produce one of many feedback patterns.
Each pattern partitions the possible answer set into a smaller group.
A good guess creates a pattern distribution that is:
spread out
not dominated by one huge boring outcome
That means the guess is good at separating possible answers.
Example intuition
If one guess usually gives:
1 giant bucket of 500 words
a few tiny buckets
that is not great.
But if another guess splits words into many more balanced buckets, that is better.
Because after seeing the feedback, you are much closer to the answer.

6. The main Wordle modeling idea
For each possible guess:
compare it against every possible answer
compute the resulting pattern
count how many answers produce each pattern
convert counts to probabilities
compute entropy
Then choose the guess with the highest entropy.

7. Project stages
A good student project can be built in stages.

Stage 1: Basic Wordle engine
Build the game itself.
You need:
a list of valid guesses
a list of possible answers
a function to score a guess against an answer
a game loop
Data files
Use:
allowed_guesses.txt
possible_answers.txt
You can also start with one merged list.

Stage 2: Candidate filtering
After each guess, keep only words that match the same feedback pattern.
Function idea
If your guess is CRANE and feedback is ⬛🟨🟩⬛⬛, then every candidate answer must produce that exact same pattern when scored against CRANE.
This is the key filter operation.

Stage 3: Entropy-based guesser
For each allowed guess:
evaluate all candidate answers
build pattern histogram
compute entropy
choose highest entropy word
This is the first real bot.

Stage 4: Weighted answer probabilities
Not all words are equally likely as answers.
For example:
SHARD feels plausible
AAHED does not
So instead of uniform probabilities, assign a prior probability to each word.
Then entropy is computed with those weighted probabilities.
This makes the bot more realistic.

Stage 5: Endgame / expected score strategy
Pure entropy is not always best near the end.
Sometimes a guess gives slightly less information but has a high chance of being the actual answer now.
So you need a score-aware strategy.
A common idea:
combine: 
probability the guess itself is the answer
expected remaining uncertainty after the guess
expected number of guesses left
This improves average score.

Stage 6: Simulation and benchmarking
Run your bot over all answers, or many random answers.
Measure:
average guesses
wins / losses
percentage solved in 3
percentage solved in 4
worst-case performance
This tells you whether your bot beats your target.

8. Wordle feedback logic: very important
This is the trickiest implementation detail.
Correct rule for repeated letters
You cannot just mark yellow whenever a guessed letter appears somewhere in the answer.
You must handle counts carefully.
Correct algorithm
Given guess and answer:
Pass 1: mark greens
For each position :
if guess[i] == answer[i] 
mark green
remove that letter from availability
Pass 2: mark yellows
For each non-green guessed letter:
if that letter still exists in remaining unmatched answer letters 
mark yellow
consume one copy
else 
mark gray
Example
Answer: APPLE
Guess: ALLEY
A = green
L = yellow? only if unmatched L exists
repeated letters matter
This is essential, otherwise your filtering logic will be wrong.

9. Main equations for the project

9.1 Information of a pattern
If a pattern occurs with probability , then:


9.2 Entropy of a guess
If a guess can produce patterns , then:

This is the expected information from that guess.

9.3 Uniform candidate probability
If there are candidate answers and each is equally likely:


9.4 Weighted candidate probability
If each answer has weight , then:

with:

Then compute entropy using this weighted .

9.5 Remaining uncertainty
If current answer distribution is , then uncertainty is:

If uniform over candidates:

Example:
2 equally likely words → 1 bit
4 equally likely words → 2 bits
16 equally likely words → 4 bits

9.6 Mutual information idea
Conceptually, a guess is good when it reduces uncertainty about the answer.
You can think of the guess feedback as revealing information about the hidden word.
While you may not explicitly compute mutual information in code, entropy reduction is basically the practical version of that idea in this setting.

10. Simple examples

Example 1: information from one clue
Suppose 32 candidate words remain.
You learn a clue that cuts that to 8.
That means probability of the observed event is:

So information gained:

You gained 2 bits.

Example 2: entropy of a simple guess
Suppose a guess can produce 4 patterns with probabilities:
1/2
1/4
1/8
1/8
Then entropy is:




Example 3: uncertainty from candidates
If 64 equally likely answers remain:

That means your uncertainty is equivalent to 6 yes/no questions.

11. Recommended project architecture
Use modules like this:
text
wordle_project/
│
├── data/
│   ├── allowed_guesses.txt
│   └── possible_answers.txt
│
├── src/
│   ├── game.py
│   ├── scoring.py
│   ├── filter.py
│   ├── entropy.py
│   ├── priors.py
│   ├── bot.py
│   ├── simulate.py
│   └── utils.py
│
├── notebooks/
│   └── analysis.ipynb
│
├── tests/
│   ├── test_scoring.py
│   └── test_filter.py
│
└── README.md

12. Suggested libraries
Best choice: Python
Python is the easiest language for this project.
Core libraries
Python standard library 
math
collections
itertools
random
statistics
json
time
Useful external libraries
numpy
for fast arrays and vectorized operations
pandas
for tables and experiment tracking
matplotlib or seaborn
for visualizing entropy distributions, score histograms
tqdm
for progress bars during simulations
scipy
optional, for fitting functions/regression
jupyter
for exploration and visualization
Optional speedups
numba
if simulations get slow
joblib or Python multiprocessing
for parallel simulation

13. Step-by-step implementation plan

Step 1: Load words
Create functions:
load_allowed_words()
load_answer_words()
Store words as lowercase strings.

Step 2: Implement pattern scoring
Create:
python
get_pattern(guess, answer) -> tuple[int, int, int, int, int]
Where:
0 = gray
1 = yellow
2 = green
Example:
python
get_pattern("crane", "shard")
# maybe returns (0,1,2,0,0)
Use the correct two-pass repeated-letter logic.

Step 3: Filter candidate answers
Create:
python
filter_candidates(candidates, guess, pattern)
Keep only words for which:
python
get_pattern(guess, word) == pattern

Step 4: Compute entropy for one guess
For a guess:
compare against all candidate answers
count pattern frequencies
convert to probabilities
compute entropy
Pseudo-code:
python
def entropy_of_guess(guess, candidates):
    counts = Counter()
    for answer in candidates:
        p = get_pattern(guess, answer)
        counts[p] += 1

    total = len(candidates)
    H = 0.0
    for count in counts.values():
        prob = count / total
        H -= prob * math.log2(prob)
    return H

Step 5: Choose best guess
python
def best_guess(allowed_guesses, candidates):
    best_word = None
    best_entropy = -1
    for guess in allowed_guesses:
        H = entropy_of_guess(guess, candidates)
        if H > best_entropy:
            best_entropy = H
            best_word = guess
    return best_word, best_entropy

Step 6: Play one full game automatically
python
def play_game(answer, allowed_guesses, answer_words):
    candidates = answer_words[:]
    guesses = []

    for turn in range(1, 7):
        guess, H = best_guess(allowed_guesses, candidates)
        pattern = get_pattern(guess, answer)
        guesses.append((guess, pattern, H))

        if guess == answer:
            return guesses

        candidates = filter_candidates(candidates, guess, pattern)

    return guesses

Step 7: Simulate many games
Loop through all answer words.
Track:
average turns
failures
score distribution

14. Improving beyond uniform entropy
The transcript explains that using all candidate words equally is okay, but not ideal.
Because some words are much more plausible than others.

14.1 Add priors
Assign each word a score based on frequency.
Possible sources:
word frequency lists
subtitle frequency data
wordfreq package
curated word lists
Then normalize probabilities:

This becomes your prior over answers.

14.2 Weighted entropy
Instead of raw counts, sum answer probabilities into each pattern bucket.
Pseudo-code:
python
def weighted_entropy_of_guess(guess, candidates, probs):
    pattern_mass = defaultdict(float)
    for answer in candidates:
        pattern = get_pattern(guess, answer)
        pattern_mass[pattern] += probs[answer]

    H = 0.0
    for p in pattern_mass.values():
        if p > 0:
            H -= p * math.log2(p)
    return H

14.3 Why this helps
Suppose 10 weird rare words and 2 common words all match a clue.
Uniform treatment says 12 possibilities.
But realistic treatment says maybe only 2 are serious answers.
Entropy over the weighted distribution captures that.

15. Better decision rule near the end
Pure entropy can be wasteful in endgame.
Example:
Guess A gives slightly more expected information
Guess B is itself very likely to be the answer
If guess B has a 60% chance to win immediately, it may be better.
So define a heuristic score.

One simple heuristic
For each guess:

Where:
are tunable
This is easy and often works fairly well.

Better idea: expected remaining guesses
Estimate:

Then choose the guess minimizing:

The transcript describes approximating this from remaining uncertainty.
For example:
current uncertainty: 
expected information from guess: 
expected uncertainty after guess: 
Then fit a function:

And choose the guess minimizing:

This is more advanced, but quite good.

16. How to estimate that function 
The transcript suggests:
run many games with a simpler bot
record: 
uncertainty at each step
number of guesses remaining from that step
fit a curve/regression
Then use that fitted function as an estimate.
Example methods
linear regression
polynomial regression
piecewise fit
simple lookup table by bins
For a student project, a lookup table is enough.

17. Metrics to track
If your goal is to “beat high score”, define what that means.
Possible definitions
A. Lower average guesses
Best metric for bots.

B. Maximize solves in 3
Track:
% solved in 1
% solved in 2
% solved in 3
% solved in 4
% solved in 5
% solved in 6
% failed
C. Minimize worst case
How many guesses does the hardest answer require?
D. Human challenge mode
If building a playable simulation, define “high score” as:
most consecutive wins
lowest average over last 30 games
highest percent solved in 3 or less

18. Good project experiments
Here are strong experiments for a report.

Experiment 1
Compare opening guesses:
SLATE
CRANE
SOARE
TARES
WEARY
Measure first-guess entropy.

Experiment 2
Uniform vs weighted prior
Compare:
average score
solves in 3
losses

Experiment 3
Entropy-only vs score-aware strategy
Compare whether score-aware improves endgame.

Experiment 4
Guess from answer list only vs full allowed-guess list
Sometimes best information words are not likely answers.
See how much that helps.

Experiment 5
One-step vs two-step lookahead
More compute, maybe better score.

19. Practical coding tips
Efficiency matters
Computing entropy for every guess against every answer can be expensive.
If:
13,000 guesses
2,300 candidate answers
that is a lot of pattern computations.
Speed tricks
Precompute pattern matrix
For every guess-answer pair, store the pattern once
Cache results
Very helpful
Use integer encoding for patterns
Example base-3 code:

Since each slot is 0/1/2, there are possible patterns
Restrict candidate guess set in late stages
optional

20. Suggested pattern encoding
Each feedback pattern is length 5 with values in .
Encode as a number from 0 to 242.
Example:
python
def encode_pattern(pattern):
    code = 0
    mul = 1
    for x in pattern:
        code += x * mul
        mul *= 3
    return code
This is faster than tuples for large simulations.

21. User interface ideas
You asked for a simulation game project, so here are options.
Option A: terminal app
Simplest.
Features:
user enters answer or random answer chosen
user can guess
bot can suggest best next guess
shows candidate count and entropy
Option B: notebook dashboard
Good for learning and plots.
Option C: web app
Use:
Python Flask or FastAPI backend
HTML/CSS/JavaScript frontend
Features:
playable Wordle
“hint” button from bot
“autoplay” mode
stats dashboard

22. Suggested end-to-end workflow for students
Phase 1: learn the game
implement Wordle rules
test with examples
Phase 2: build a basic solver
filter candidate words
choose random candidate
Phase 3: add entropy
compute pattern distributions
pick best guess by entropy
Phase 4: simulate many games
compute average score
visualize performance
Phase 5: add priors
use word frequencies
compare results
Phase 6: add score-aware endgame
blend answer probability with entropy
improve average score
Phase 7: optimize
precompute pattern matrix
benchmark speed
Phase 8: polish
create CLI or GUI
write report and plots

23. Example pseudo-code for full bot loop
python
candidates = all_answers
probs = initial_word_probabilities(candidates)

for turn in range(1, 7):
    guess = choose_best_guess(allowed_guesses, candidates, probs)

    pattern = get_pattern(guess, true_answer)

    if guess == true_answer:
        win(turn)
        break

    candidates = [
        w for w in candidates
        if get_pattern(guess, w) == pattern
    ]

    probs = renormalize(probs over candidates)

24. What “theory” should go in your report
If this is for class, your writeup should include these concepts.
Topics to explain
probability
information content
entropy
expected value
pattern distributions in Wordle
candidate filtering
prior distributions
weighted entropy
tradeoff between exploration and exploitation
Short explanation of that tradeoff
exploration = guesses that reveal more information
exploitation = guesses likely to be the answer now
Strong bots balance both.

25. Common mistakes
Incorrect repeated-letter scoring
Assuming all gray means letter absent without count logic
Using only common letters, not actual pattern entropy
Only guessing candidate answers 
sometimes a non-answer guess is more informative
Not separating allowed guesses from likely answers
No benchmarking
Using average candidate count instead of entropy
Ignoring endgame answer probability

26. Nice simple examples to teach students
Example: why common letters alone are not enough
Two guesses may both contain frequent letters, but one may produce more balanced pattern outcomes.
Balanced outcomes = higher entropy = better average reduction.
So frequency helps, but entropy is the real scoring rule.

Example: why rare letters can sometimes be good
A guess with a rare letter like W might sometimes produce a very informative rare event.
But if that event almost never happens, the average information may still be worse.
So we care about expected information, not best-case information.

Example: why endgame needs a different strategy
If there are two likely answers left and one of them is itself guessable, just guessing it may be better than using a “perfect information” probe.
Because the goal is not only to learn; it is to win in fewer turns.

27. Recommended deliverables
If this is a full project, produce:
Code
working Wordle engine
entropy bot
simulation scripts
Report
explanation of entropy
formulas
algorithm steps
results table
comparison graphs
Visuals
histogram of scores
entropy of opening words
candidate count over turns
average performance by strategy
Demo
one playable game
one autoplay bot run
one simulation summary

28. Minimal viable project
If time is short, do this:
Python Wordle engine
Correct feedback scoring
Candidate filtering
Entropy-based bot with uniform distribution
Simulation over answer list
Plot score histogram
That is already a solid project.

29. Stronger advanced project
If you want a better result:
all of the above
weighted answer prior from word frequencies
answer-probability-aware endgame
precomputed pattern matrix
opening-word comparison dashboard
two-step lookahead for top few candidates

30. Final takeaway
The transcripts teach a beautiful central lesson:
Information measures how surprising an observation is
Entropy measures expected information
In Wordle, each guess produces a distribution of feedback patterns
The best guesses tend to maximize the entropy of that distribution
Better bots also model which answers are more likely and balance: 
gaining information
actually finishing the game quickly
So the full project is:
Build a Wordle engine, model uncertainty over answers, use entropy to choose guesses, improve with weighted probabilities and score-aware decisions, then simulate many games to evaluate performance.

