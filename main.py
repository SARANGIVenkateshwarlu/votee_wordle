import random
import time
import sys
from solver import WordleSolver
from words import get_wordle_answers, get_wordle_guesses
from api_client import guess_random, guess_daily, guess_word, WordleAPIError


def build_solver():
    answers = get_wordle_answers()
    full_list = get_wordle_guesses()
    solver = WordleSolver(
        answer_list=answers,
        guess_list=answers,
        full_wordlist=full_list,
    )
    elapsed = solver.build_cache()
    return solver, elapsed


def play_api_game(api_func, solver, verbose=True, **api_kwargs):
    solver.reset()

    for turn in range(1, 7):
        guess = solver.choose_guess(turn)

        try:
            feedback = api_func(guess, **api_kwargs)
        except WordleAPIError as e:
            if verbose:
                print(f"  Turn {turn}: API ERROR - {e}")
            return {"solved": False, "turns": turn, "history": solver.history}

        pattern_display = "".join("G" if f == 2 else "Y" if f == 1 else "-" for f in feedback)

        solved = solver.update(guess, feedback)
        if solved:
            if verbose:
                print(f"  Turn {turn}: {guess} -> {pattern_display}  SOLVED!")
            return {"solved": True, "turns": turn, "history": solver.history}

        if verbose:
            print(f"  Turn {turn}: {guess} -> {pattern_display}  ({solver.candidates_remaining} remaining)")

        answer = solver.get_answer_guess()
        if answer:
            if verbose:
                print(f"  Turn {turn + 1}: {answer} -> GGGGG  SOLVED!")
            try:
                feedback = api_func(answer, **api_kwargs)
            except WordleAPIError:
                return {"solved": True, "turns": turn + 1, "history": solver.history + [(answer, None)]}
            solver.update(answer, feedback)
            if feedback == (2, 2, 2, 2, 2):
                return {"solved": True, "turns": turn + 1, "history": solver.history}

    return {"solved": False, "turns": 6, "history": solver.history}


def solve_daily(solver, verbose=True):
    return play_api_game(guess_daily, solver, verbose=verbose)


def solve_random(solver, seed=None, verbose=True):
    if seed is None:
        seed = random.randint(0, 2_000_000_000)
    return play_api_game(lambda g: guess_random(g, seed=seed), solver, verbose=verbose)


def solve_word(solver, word, verbose=True):
    return play_api_game(lambda g: guess_word(word, g), solver, verbose=verbose)


def benchmark(solver, n=10, mode="random", verbose=True):
    successes = 0
    total_turns = 0
    dist = {}
    failures = 0

    if verbose:
        print(f"Benchmark: {n} games ({mode})\n")

    for i in range(n):
        if mode == "random":
            suffix = f"(seed={random.randint(0, 999999)})"
            result = solve_random(solver, verbose=False)
        elif mode == "daily":
            suffix = ""
            result = solve_daily(solver, verbose=False)
        else:
            word = mode
            suffix = f"(word={word})"
            result = solve_word(solver, mode, verbose=False)

        if result["solved"]:
            successes += 1
            t = result["turns"]
            total_turns += t
            dist[t] = dist.get(t, 0) + 1

        if verbose:
            status = f"SOLVED ({result['turns']})" if result["solved"] else "FAILED"
            print(f"  Game {i+1}: {status} {suffix}")

        if not result["solved"]:
            failures += 1

    avg = total_turns / successes if successes > 0 else 0
    rate = successes / n * 100

    if verbose:
        print(f"\n  Success: {successes}/{n} ({rate:.1f}%)")
        print(f"  Failures: {failures}")
        print(f"  Average turns: {avg:.3f}")
        print(f"  Distribution: {dict(sorted(dist.items()))}")

    return {"success_rate": rate / 100, "avg_turns": avg, "distribution": dist, "failures": failures, "total": n}


def main():
    print("Wordle API Solver - Votee")
    print("Building pattern cache...")
    solver, elapsed = build_solver()
    print(f"Cache built in {elapsed:.1f}s\n")

    args = sys.argv[1:]

    if not args:
        print("Usage:")
        print("  python main.py daily              Solve today's puzzle")
        print("  python main.py random             Solve 1 random puzzle")
        print("  python main.py random 10          Benchmark 10 random")
        print("  python main.py word <WORD>        Solve specific word")
        print("  python main.py benchmark 20       Benchmark 20 random")
        return

    cmd = args[0].lower()

    if cmd == "daily":
        print("Solving daily puzzle:")
        result = solve_daily(solver)
        print(f"\n  Result: {'SOLVED' if result['solved'] else 'FAILED'} in {result['turns']} turns")

    elif cmd == "random":
        n = int(args[1]) if len(args) > 1 else 1
        if n == 1:
            print("Solving random puzzle:")
            result = solve_random(solver)
            print(f"\n  Result: {'SOLVED' if result['solved'] else 'FAILED'} in {result['turns']} turns")
        else:
            benchmark(solver, n, mode="random")

    elif cmd == "word":
        if len(args) < 2:
            print("Please provide a word: python main.py word <WORD>")
            return
        word = args[1].lower()
        print(f"Solving '{word}':")
        result = solve_word(solver, word)
        print(f"\n  Result: {'SOLVED' if result['solved'] else 'FAILED'} in {result['turns']} turns")

    elif cmd == "benchmark":
        n = int(args[1]) if len(args) > 1 else 10
        benchmark(solver, n, mode="random")

    else:
        print(f"Unknown command: {cmd}")
        print("Usage: python main.py [daily|random|word|benchmark]")


if __name__ == "__main__":
    main()
