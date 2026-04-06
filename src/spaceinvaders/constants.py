"""Game-wide constants and configuration."""

import os

# Screen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colours (retro palette)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
CYAN = (0, 255, 255)
YELLOW = (255, 255, 0)
MAGENTA = (255, 0, 255)
ORANGE = (255, 165, 0)
DARK_GREEN = (0, 180, 0)

# Player
PLAYER_SPEED = 5
PLAYER_WIDTH = 40
PLAYER_HEIGHT = 20
PLAYER_BULLET_SPEED = -7
PLAYER_SHOOT_COOLDOWN = 300  # ms

# Invaders
INVADER_COLS = 11
INVADER_ROWS = 5
INVADER_WIDTH = 30
INVADER_HEIGHT = 20
INVADER_PADDING_X = 15
INVADER_PADDING_Y = 12
INVADER_START_Y = 80
INVADER_DROP = 15
INVADER_BULLET_SPEED = 4
INVADER_SHOOT_CHANCE = 0.002  # per invader per frame

# Barriers
BARRIER_COUNT = 4
BARRIER_BLOCK_SIZE = 6
BARRIER_Y = 470

# Mystery ship
MYSTERY_SPEED = 3
MYSTERY_INTERVAL_MIN = 10000  # ms
MYSTERY_INTERVAL_MAX = 25000

# High scores
HIGHSCORE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "highscores.json"
)
MAX_HIGH_SCORES = 10

# Points by invader row (top to bottom)
ROW_POINTS = [40, 40, 20, 20, 10]
ROW_COLOURS = [MAGENTA, MAGENTA, CYAN, CYAN, GREEN]
MYSTERY_POINTS = [50, 100, 150, 200, 300]
