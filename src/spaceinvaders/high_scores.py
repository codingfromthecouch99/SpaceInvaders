"""High score persistence and logic — pure functions (no pygame dependency)."""

import json
import os

from .constants import HIGHSCORE_FILE, MAX_HIGH_SCORES


def load_high_scores(path=None):
    path = path or HIGHSCORE_FILE
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []


def save_high_scores(scores, path=None):
    path = path or HIGHSCORE_FILE
    with open(path, "w") as f:
        json.dump(scores, f, indent=2)


def is_high_score(score, scores):
    return len(scores) < MAX_HIGH_SCORES or score > scores[-1]["score"]


def add_high_score(name, score, wave, scores):
    scores = scores.copy()
    scores.append({"name": name, "score": score, "wave": wave})
    scores.sort(key=lambda s: s["score"], reverse=True)
    return scores[:MAX_HIGH_SCORES]
