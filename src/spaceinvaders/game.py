"""Main game loop — thin orchestrator wiring engine and renderer."""

import sys

import pygame

from .constants import FPS
from .engine import GameEngine
from .rendering import Renderer


class Game:
    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        self.engine = GameEngine()
        self.renderer = Renderer()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)
            now = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    result = self.engine.handle_keydown(event.key, event.unicode, now)
                    if result == "quit":
                        running = False

            keys = pygame.key.get_pressed()
            self.engine.update(dt, now, keys)
            self.renderer.draw(self.engine)

        pygame.quit()
        sys.exit()
