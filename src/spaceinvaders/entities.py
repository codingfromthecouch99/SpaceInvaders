"""Game sprites: Player, Invader, Bullet, MysteryShip, Explosion, BarrierBlock."""

import random

import pygame

from .constants import (
    BARRIER_BLOCK_SIZE,
    BLACK,
    DARK_GREEN,
    GREEN,
    INVADER_BULLET_SPEED,
    INVADER_HEIGHT,
    INVADER_WIDTH,
    MYSTERY_POINTS,
    MYSTERY_SPEED,
    PLAYER_BULLET_SPEED,
    PLAYER_HEIGHT,
    PLAYER_SHOOT_COOLDOWN,
    PLAYER_SPEED,
    PLAYER_WIDTH,
    ROW_COLOURS,
    ROW_POINTS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
    YELLOW,
)
from .rendering import create_invader_surface, create_mystery_surface, draw_player_shape


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT), pygame.SRCALPHA)
        draw_player_shape(self.image, GREEN, (0, 0, PLAYER_WIDTH, PLAYER_HEIGHT))
        self.rect = self.image.get_rect(midbottom=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        self.last_shot = 0

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x = max(0, self.rect.x - PLAYER_SPEED)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x = min(SCREEN_WIDTH - self.rect.width, self.rect.x + PLAYER_SPEED)

    def can_shoot(self, now):
        return now - self.last_shot >= PLAYER_SHOOT_COOLDOWN

    def shoot(self, now):
        self.last_shot = now
        return Bullet(self.rect.centerx, self.rect.top, PLAYER_BULLET_SPEED, is_player=True)


class Invader(pygame.sprite.Sprite):
    def __init__(self, row, col, x, y):
        super().__init__()
        self.row = row
        self.col = col
        self.image = create_invader_surface(row, INVADER_WIDTH, INVADER_HEIGHT)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.points = ROW_POINTS[row] if row < len(ROW_POINTS) else 10

    def shoot(self):
        return Bullet(self.rect.centerx, self.rect.bottom, INVADER_BULLET_SPEED, is_player=False)


class MysteryShip(pygame.sprite.Sprite):
    def __init__(self, direction):
        super().__init__()
        self.image = create_mystery_surface()
        self.direction = direction
        if direction == 1:
            self.rect = self.image.get_rect(midright=(0, 40))
        else:
            self.rect = self.image.get_rect(midleft=(SCREEN_WIDTH, 40))
        self.speed = MYSTERY_SPEED * direction
        self.points = random.choice(MYSTERY_POINTS)

    def update(self):
        self.rect.x += self.speed
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speed, is_player=True):
        super().__init__()
        self.is_player = is_player
        w, h = (3, 10) if is_player else (3, 12)
        self.image = pygame.Surface((w, h))
        self.image.fill(WHITE if is_player else YELLOW)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = speed

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()


class Explosion(pygame.sprite.Sprite):
    """Brief flash when something is destroyed."""

    def __init__(self, x, y, colour=WHITE, size=20):
        super().__init__()
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        self.colour = colour
        self.size = size
        self.timer = 0
        self.duration = 200  # ms
        self.rect = self.image.get_rect(center=(x, y))
        self._draw_frame(0)

    def _draw_frame(self, progress):
        self.image.fill((0, 0, 0, 0))
        alpha = max(0, 255 - int(255 * progress))
        c = (*self.colour[:3], alpha)
        r = int(self.size / 2 * (0.5 + 0.5 * progress))
        pygame.draw.circle(self.image, c, (self.size // 2, self.size // 2), r, 2)

    def update(self, dt):
        self.timer += dt
        progress = self.timer / self.duration
        if progress >= 1:
            self.kill()
        else:
            self._draw_frame(progress)


class BarrierBlock(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((BARRIER_BLOCK_SIZE, BARRIER_BLOCK_SIZE))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.health = 3

    def hit(self):
        self.health -= 1
        if self.health == 2:
            self.image.fill(DARK_GREEN)
        elif self.health == 1:
            self.image.fill((0, 100, 0))
            for _ in range(4):
                px = random.randint(0, BARRIER_BLOCK_SIZE - 1)
                py = random.randint(0, BARRIER_BLOCK_SIZE - 1)
                self.image.set_at((px, py), BLACK)
        else:
            self.kill()


def create_barrier_template():
    """Return a list of (row, col) offsets for a barrier shape."""
    shape = [
        "  XXXXXXXX  ",
        " XXXXXXXXXX ",
        "XXXXXXXXXXXX",
        "XXXXXXXXXXXX",
        "XXXXXXXXXXXX",
        "XXXXXXXXXXXX",
        "XXX      XXX",
        "XX        XX",
    ]
    blocks = []
    for r, line in enumerate(shape):
        for c, ch in enumerate(line):
            if ch == "X":
                blocks.append((r, c))
    return blocks


BARRIER_TEMPLATE = create_barrier_template()
