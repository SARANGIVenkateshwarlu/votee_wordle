import requests
from functools import lru_cache

BASE_URL = "https://wordle.votee.dev:8000"

RESULT_MAP = {
    "absent": 0,
    "present": 1,
    "correct": 2,
}


class WordleAPIError(Exception):
    pass


def _make_request(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        raise WordleAPIError(f"API request failed: {e}")


def guess_daily(guess: str, size: int = 5):
    url = f"{BASE_URL}/daily"
    params = {"guess": guess, "size": size}
    return _parse_response(_make_request(url, params))


def guess_random(guess: str, size: int = 5, seed: int = None):
    url = f"{BASE_URL}/random"
    params = {"guess": guess, "size": size}
    if seed is not None:
        params["seed"] = seed
    return _parse_response(_make_request(url, params))


def guess_word(word: str, guess: str):
    url = f"{BASE_URL}/word/{word}"
    params = {"guess": guess}
    return _parse_response(_make_request(url, params))


def _parse_response(data):
    result = []
    if not isinstance(data, list):
        raise WordleAPIError(f"Unexpected response format: {data}")
    for item in sorted(data, key=lambda x: x.get("slot", 0)):
        result.append(RESULT_MAP.get(item.get("result", "absent"), 0))
    return tuple(result)


def daily_raw(guess: str, size: int = 5):
    url = f"{BASE_URL}/daily"
    return _make_request(url, {"guess": guess, "size": size})


def random_raw(guess: str, size: int = 5, seed: int = None):
    url = f"{BASE_URL}/random"
    params = {"guess": guess, "size": size}
    if seed is not None:
        params["seed"] = seed
    return _make_request(url, params)


def word_raw(word: str, guess: str):
    url = f"{BASE_URL}/word/{word}"
    return _make_request(url, {"guess": guess})
