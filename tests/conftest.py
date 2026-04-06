"""Shared fixtures for all tests."""

import os
import sys

import pygame
import pytest

# Ensure src is on the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Initialize pygame with a dummy video driver so tests run headless
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


@pytest.fixture(autouse=True, scope="session")
def _init_pygame():
    pygame.init()
    pygame.display.set_mode((1, 1))
    yield
    pygame.quit()
