"""Unit tests for high score logic — pure functions, no pygame needed."""

import json
import os
import tempfile

import pytest

from spaceinvaders.high_scores import add_high_score, is_high_score, load_high_scores, save_high_scores


class TestIsHighScore:
    def test_empty_list_qualifies(self):
        assert is_high_score(0, []) is True

    def test_below_max_entries_qualifies(self):
        scores = [{"name": "A", "score": 100, "wave": 1}]
        assert is_high_score(50, scores) is True

    def test_higher_than_last_qualifies(self):
        scores = [{"name": f"P{i}", "score": 100 - i * 10, "wave": 1} for i in range(10)]
        assert is_high_score(15, scores) is True  # beats last (10)

    def test_lower_than_last_does_not_qualify(self):
        scores = [{"name": f"P{i}", "score": 100 - i * 5, "wave": 1} for i in range(10)]
        assert is_high_score(1, scores) is False


class TestAddHighScore:
    def test_adds_and_sorts(self):
        scores = [{"name": "A", "score": 100, "wave": 2}]
        result = add_high_score("B", 200, 3, scores)
        assert result[0]["name"] == "B"
        assert result[0]["score"] == 200
        assert result[1]["name"] == "A"

    def test_does_not_mutate_original(self):
        original = [{"name": "A", "score": 100, "wave": 1}]
        add_high_score("B", 200, 2, original)
        assert len(original) == 1

    def test_caps_at_max(self):
        scores = [{"name": f"P{i}", "score": 1000 - i * 10, "wave": 1} for i in range(10)]
        result = add_high_score("NEW", 5000, 5, scores)
        assert len(result) == 10
        assert result[0]["name"] == "NEW"

    def test_low_score_dropped_when_full(self):
        scores = [{"name": f"P{i}", "score": 1000 - i * 10, "wave": 1} for i in range(10)]
        last_name = scores[-1]["name"]
        result = add_high_score("NEW", 5000, 5, scores)
        names = [s["name"] for s in result]
        assert last_name not in names


class TestPersistence:
    def test_save_and_load_round_trip(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            scores = [{"name": "ACE", "score": 999, "wave": 3}]
            save_high_scores(scores, path)
            loaded = load_high_scores(path)
            assert loaded == scores
        finally:
            os.unlink(path)

    def test_load_missing_file_returns_empty(self):
        assert load_high_scores("/nonexistent/path.json") == []

    def test_load_corrupt_file_returns_empty(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{corrupt")
            path = f.name
        try:
            assert load_high_scores(path) == []
        finally:
            os.unlink(path)
