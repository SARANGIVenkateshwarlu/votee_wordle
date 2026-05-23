import streamlit as st
import random
from solver import WordleSolver, evaluate
from words import get_wordle_answers, get_wordle_guesses

st.set_page_config(page_title="Wordle", page_icon="🟩", layout="centered")

# ── Classic Wordle Dark Theme CSS ──

CSS = """
<style>
/* Reset & global */
.stApp { background: #121213; }
.main .block-container { max-width: 500px; padding-top: 0.5rem; }
header[data-testid="stHeader"] { background: #121213; }
div[data-testid="stToolbar"] { display: none; }
div[data-testid="stDecoration"] { display: none; }
section[data-testid="stSidebar"] { display: none; }

/* Remove Streamlit chrome */
#MainMenu, footer, .stDeployButton { visibility: hidden; }

/* Input styling */
input[type="text"] {
    background: #121213 !important; color: white !important;
    border: 2px solid #3a3a3c !important; border-radius: 4px !important;
    text-align: center !important; font-size: 20px !important; letter-spacing: 4px !important;
    text-transform: uppercase !important; caret-color: white !important;
}
input[type="text"]:focus { border-color: #565758 !important; box-shadow: none !important; }

/* Buttons */
button[kind] {
    background: #818384 !important; color: white !important;
    border: none !important; border-radius: 4px !important;
    font-weight: bold !important; font-size: 14px !important;
}
button[kind]:hover { background: #565758 !important; }

/* Select box */
div[data-baseweb="select"] > div {
    background: #121213 !important; border: 2px solid #3a3a3c !important; border-radius: 4px !important;
    color: white !important;
}
div[data-baseweb="select"] span { color: white !important; }
ul[role="listbox"] { background: #121213 !important; }
ul[role="listbox"] li { color: white !important; }
ul[role="listbox"] li:hover { background: #3a3a3c !important; }

/* Messages */
div[data-testid="stSuccess"] { background: #538d4e22 !important; border: 1px solid #538d4e !important; border-radius: 8px !important; }
div[data-testid="stSuccess"] p { color: #6aaa64 !important; font-weight: bold !important; }
div[data-testid="stWarning"] { background: #b59f3b22 !important; border: 1px solid #b59f3b !important; border-radius: 8px !important; }
div[data-testid="stInfo"] { background: #3a3a3c44 !important; border: 1px solid #3a3a3c !important; border-radius: 8px !important; }

/* ── Title ── */
.wordle-title {
    font-family: 'Georgia', 'Times New Roman', serif;
    font-size: 36px; font-weight: bold; text-align: center;
    letter-spacing: 4px; color: white; margin: 0; padding: 8px 0;
    border-bottom: 1px solid #3a3a3c; margin-bottom: 12px;
}

/* ── Game Board ── */
.board { display: flex; flex-direction: column; align-items: center; gap: 5px; }
.row { display: flex; gap: 5px; }
.tile {
    width: 58px; height: 58px; border: 2px solid #3a3a3c;
    display: flex; align-items: center; justify-content: center;
    font-size: 30px; font-weight: bold; text-transform: uppercase;
    color: white; user-select: none;
    transition: transform 0.5s ease, background 0.3s ease, border-color 0.3s ease;
}
.tile.filled    { border-color: #565758; animation: pop 0.1s ease; }
.tile.absent    { background: #3a3a3c; border-color: #3a3a3c; animation: flip 0.5s ease; }
.tile.present   { background: #b59f3b; border-color: #b59f3b; animation: flip 0.5s ease; }
.tile.correct   { background: #538d4e; border-color: #538d4e; animation: flip 0.5s ease; }
.tile.empty     { background: #121213; border-color: #3a3a3c; }
.tile.has-letter { border-color: #565758; }
.tile.reveal-0 { animation-delay: 0s; }
.tile.reveal-1 { animation-delay: 0.3s; }
.tile.reveal-2 { animation-delay: 0.6s; }
.tile.reveal-3 { animation-delay: 0.9s; }
.tile.reveal-4 { animation-delay: 1.2s; }

@keyframes flip {
    0%   { transform: rotateX(0deg); }
    50%  { transform: rotateX(90deg); }
    100% { transform: rotateX(0deg); }
}
@keyframes pop {
    0%   { transform: scale(1); }
    50%  { transform: scale(1.1); }
    100% { transform: scale(1); }
}
@keyframes bounce {
    0%,100% { transform: translateY(0); }
    50%     { transform: translateY(-8px); }
}
.win-cell { display: inline-block; animation: bounce 0.6s ease; }
.win-cell:nth-child(1) { animation-delay: 0s; }
.win-cell:nth-child(2) { animation-delay: 0.1s; }
.win-cell:nth-child(3) { animation-delay: 0.2s; }
.win-cell:nth-child(4) { animation-delay: 0.3s; }
.win-cell:nth-child(5) { animation-delay: 0.4s; }

/* ── Keyboard ── */
.keyboard { margin-top: 16px; }
.kb-row { display: flex; gap: 4px; justify-content: center; margin: 4px 0; }
.key {
    min-width: 32px; height: 52px; border-radius: 4px; border: none;
    display: flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: bold; text-transform: uppercase;
    cursor: default; padding: 0 4px;
    transition: background 0.2s;
    color: white; background: #818384;
}
.key.wide { min-width: 48px; font-size: 11px; }
.key.absent  { background: #3a3a3c; }
.key.present { background: #b59f3b; }
.key.correct { background: #538d4e; }
.key.unused  { background: #818384; }

/* ── Stats ── */
.stats-container { display: flex; gap: 8px; justify-content: center; }
.stat-box {
    background: #1e1e1f; border-radius: 8px; padding: 12px 18px;
    text-align: center; min-width: 70px;
}
.stat-num  { font-size: 28px; font-weight: bold; color: white; }
.stat-lbl  { font-size: 11px; color: #818384; margin-top: 2px; text-transform: uppercase; letter-spacing: 1px; }

/* ── Distribution bars ── */
.dist-row { display: flex; align-items: center; gap: 6px; margin: 3px 0; }
.dist-label { width: 20px; text-align: right; color: #818384; font-size: 13px; }
.dist-bar-outer { flex: 1; background: #3a3a3c; height: 20px; border-radius: 3px; overflow: hidden; }
.dist-bar-inner {
    background: #538d4e; height: 100%; border-radius: 3px;
    padding-right: 6px; display: flex; align-items: center; justify-content: flex-end;
    font-size: 12px; color: white; font-weight: bold; min-width: 0;
    transition: width 0.5s ease;
}
.dist-bar-inner.today { background: #b59f3b; }

/* ── Hr & spacing ── */
hr { border-color: #3a3a3c; margin: 16px 0; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── Config ──

KEYBOARD_ROWS = [
    ["q","w","e","r","t","y","u","i","o","p"],
    ["a","s","d","f","g","h","j","k","l"],
    ["enter","z","x","c","v","b","n","m","⌫"],
]
RESULT_CLASS = {2: "correct", 1: "present", 0: "absent"}


def render_row(word, feedback=None, reveal_delay=False):
    cells = []
    for i in range(5):
        ch = word[i] if i < len(word) else ""
        cls = "tile"
        delay_class = f" reveal-{i}" if reveal_delay and feedback else ""
        if feedback is not None:
            cls += f" {RESULT_CLASS[feedback[i]]}{delay_class}"
            label = ''.join(
                f'<span class="win-cell">{c.upper()}</span>' if feedback == (2,2,2,2,2) else c.upper()
                for c in word
            )
            ch_html = label if i == 0 else (f'<span class="win-cell">{ch.upper()}</span>' if feedback == (2,2,2,2,2) and i < 5 else ch.upper())
        elif ch:
            cls += " filled"
            ch_html = ch.upper()
        else:
            cls += " empty"
            ch_html = ""
        if feedback and feedback == (2,2,2,2,2):
            cells.append(f'<div class="{cls}"><span class="win-cell">{ch.upper()}</span></div>')
        else:
            cells.append(f'<div class="{cls}">{ch.upper() if ch else ""}</div>')
    return f'<div class="row">{"".join(cells)}</div>'


def render_keyboard(letter_states):
    html = '<div class="keyboard">'
    for row in KEYBOARD_ROWS:
        html += '<div class="kb-row">'
        for letter in row:
            wide = ' wide' if letter in ("enter","⌫") else ''
            cls = "key" + wide
            if letter in letter_states:
                cls += f" {letter_states[letter]}"
            else:
                cls += " unused"
            lbl = letter.upper() if letter not in ("enter","⌫") else ("↵" if letter == "enter" else "")
            html += f'<div class="{cls}">{lbl}</div>'
        html += '</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_stats(games, wins, total_guesses, dist):
    rate = f"{wins/games*100:.0f}" if games > 0 else "0"
    avg = f"{total_guesses/wins:.1f}" if wins > 0 else "0"
    st.markdown(f"""
    <div class="stats-container">
      <div class="stat-box"><div class="stat-num">{games}</div><div class="stat-lbl">Played</div></div>
      <div class="stat-box"><div class="stat-num">{rate}%</div><div class="stat-lbl">Win %</div></div>
      <div class="stat-box"><div class="stat-num">{wins}</div><div class="stat-lbl">Streak</div></div>
      <div class="stat-box"><div class="stat-num">{avg}</div><div class="stat-lbl">Avg</div></div>
    </div>
    """, unsafe_allow_html=True)

    if dist:
        st.markdown('<p style="color:#818384;font-size:13px;text-align:center;margin-top:16px;">GUESS DISTRIBUTION</p>', unsafe_allow_html=True)
        max_count = max(dist.values())
        for turn in range(1, 7):
            count = dist.get(turn, 0)
            pct = int(count / max_count * 100) if max_count > 0 else 0
            is_last = (turn == st.session_state.get("last_win_turns", 0))
            extra = " today" if is_last else ""
            st.markdown(f"""
            <div class="dist-row">
              <span class="dist-label">{turn}</span>
              <div class="dist-bar-outer">
                <div class="dist-bar-inner{extra}" style="width:{pct}%;">{count if count > 0 else ''}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)


def init_session():
    defaults = {
        "games": 0, "wins": 0, "total_guesses": 0, "distribution": {},
        "last_win_turns": 0,
        "answer": "", "guesses": [], "feedbacks": [], "solved": False,
        "solver_ready": False, "solver": None, "candidates_remaining": 12972,
        "mode": "api", "api_seed": 0, "message": "", "msg_type": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def new_game():
    mode = st.session_state.get("mode", "api")
    st.session_state.guesses = []
    st.session_state.feedbacks = []
    st.session_state.solved = False
    st.session_state.candidates_remaining = 12972
    st.session_state.message = ""
    st.session_state.msg_type = ""
    st.session_state.answer = None

    if mode == "api":
        from api_client import guess_random
        st.session_state.api_seed = random.randint(0, 2_000_000_000)
    else:
        answers = get_wordle_answers()
        st.session_state.answer = random.choice(answers)


def load_solver():
    if not st.session_state.solver_ready:
        with st.spinner("Loading word lists..."):
            answers = get_wordle_answers()
            full = get_wordle_guesses()
            solver = WordleSolver(answer_list=answers, guess_list=answers, full_wordlist=full)
            solver.build_cache()
            st.session_state.solver = solver
            st.session_state.solver_ready = True


def submit_guess(guess):
    guess = guess.lower().strip()
    if len(guess) != 5 or not guess.isalpha():
        st.session_state.message = "Not enough letters"
        st.session_state.msg_type = "warn"
        return
    if guess in st.session_state.guesses:
        st.session_state.message = "Already guessed"
        st.session_state.msg_type = "warn"
        return

    mode = st.session_state.mode
    if mode == "api":
        from api_client import guess_random
        feedback = guess_random(guess, seed=st.session_state.api_seed)
    else:
        feedback = evaluate(st.session_state.answer, guess)

    st.session_state.guesses.append(guess)
    st.session_state.feedbacks.append(feedback)

    if feedback == (2, 2, 2, 2, 2):
        st.session_state.solved = True
        turns = len(st.session_state.guesses)
        _record_win(turns)
    elif len(st.session_state.guesses) >= 6:
        st.session_state.games += 1
        if mode == "local" and st.session_state.answer:
            st.session_state.message = f"The answer was {st.session_state.answer.upper()}"
        else:
            st.session_state.message = "Game Over"
        st.session_state.msg_type = "warn"


def auto_solve():
    load_solver()
    solver = st.session_state.solver
    solver.reset()
    mode = st.session_state.mode
    if mode == "api":
        from api_client import guess_random
        seed = st.session_state.api_seed

    for turn in range(1, 7):
        guess = solver.choose_guess(turn)
        st.session_state.guesses.append(guess)

        if mode == "api":
            feedback = guess_random(guess, seed=seed)
        else:
            feedback = evaluate(st.session_state.answer, guess)

        st.session_state.feedbacks.append(feedback)
        solver.update(guess, feedback)
        st.session_state.candidates_remaining = solver.candidates_remaining

        if feedback == (2, 2, 2, 2, 2):
            st.session_state.solved = True
            _record_win(turn)
            return

    st.session_state.games += 1
    if mode == "local" and st.session_state.answer:
        st.session_state.message = f"The answer was {st.session_state.answer.upper()}"
    else:
        st.session_state.message = "Better luck next time"
    st.session_state.msg_type = "warn"


def _record_win(turns):
    st.session_state.solved = True
    st.session_state.games += 1
    st.session_state.wins += 1
    st.session_state.total_guesses += turns
    st.session_state.distribution[turns] = st.session_state.distribution.get(turns, 0) + 1
    st.session_state.last_win_turns = turns
    emoji = {1: "🤯", 2: "🔥", 3: "✨", 4: "👍", 5: "😅", 6: "😰"}.get(turns, "✅")
    st.session_state.message = f"{emoji} Solved in {turns}!"
    st.session_state.msg_type = "success"


def get_letter_states():
    states = {}
    for guess, fb in zip(st.session_state.guesses, st.session_state.feedbacks):
        for i, ch in enumerate(guess):
            score = fb[i]
            cls = RESULT_CLASS[score]
            current = states.get(ch)
            if current is None:
                states[ch] = cls
            elif current == "absent" and cls in ("present", "correct"):
                states[ch] = cls
            elif current == "present" and cls == "correct":
                states[ch] = cls
    return states


# ── UI ──

init_session()

# Title
st.markdown('<div class="wordle-title">WORDLE</div>', unsafe_allow_html=True)

# Controls bar
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    mode = st.selectbox("Mode", ["api", "local"], key="mode_select", label_visibility="collapsed")
    if mode != st.session_state.mode:
        st.session_state.mode = mode
with c2:
    if st.button("🔄 New", use_container_width=True, key="new_btn"):
        new_game()
        st.rerun()
with c3:
    guess = st.text_input(
        "guess", max_chars=5, placeholder="Type a 5-letter word",
        label_visibility="collapsed", key="guess_input",
        disabled=st.session_state.solved or len(st.session_state.guesses) >= 6,
    )

# Handle guess input
if guess and len(guess) == 5 and guess != st.session_state.get("_last_input"):
    st.session_state._last_input = guess
    if not st.session_state.solved and len(st.session_state.guesses) < 6:
        submit_guess(guess)
        st.rerun()

# Message
if st.session_state.message:
    if st.session_state.msg_type == "success":
        st.success(st.session_state.message)
    elif st.session_state.msg_type == "warn":
        st.warning(st.session_state.message)

# Game board
rows_html = []
for row_idx in range(6):
    if row_idx < len(st.session_state.guesses):
        rows_html.append(render_row(st.session_state.guesses[row_idx], st.session_state.feedbacks[row_idx]))
    elif row_idx == len(st.session_state.guesses) and not st.session_state.solved:
        current = st.session_state.get("_last_input", "") if len(st.session_state.guesses) < 6 else ""
        rows_html.append(render_row(current))
    else:
        rows_html.append(render_row(""))

st.markdown(f'<div class="board">{"".join(rows_html)}</div>', unsafe_allow_html=True)

# Keyboard
render_keyboard(get_letter_states())

# Auto-solve button
can_auto = not st.session_state.solved and len(st.session_state.guesses) < 6
if can_auto and len(st.session_state.guesses) == 0:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🤖 Auto-Solve with Entropy Bot", use_container_width=True):
        auto_solve()
        st.rerun()

# Stats
st.markdown("<hr>", unsafe_allow_html=True)
render_stats(
    st.session_state.games,
    st.session_state.wins,
    st.session_state.total_guesses,
    st.session_state.distribution,
)

# Solver details expander
if st.session_state.solver_ready and st.session_state.guesses:
    with st.expander("🔍 Solver Trace", expanded=False):
        for i, (g, fb) in enumerate(zip(st.session_state.guesses, st.session_state.feedbacks)):
            p = "".join("🟩" if f == 2 else "🟨" if f == 1 else "⬛" for f in fb)
            st.markdown(f"**Turn {i+1}:** `{g.upper()}` {p}")
        st.caption(f"Candidates after last guess: {st.session_state.candidates_remaining}")
