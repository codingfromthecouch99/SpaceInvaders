"""
Space Invaders - Retro arcade game built with pygame-ce.
Endless waves, destructible barriers, 3 lives, high score table.
"""

import json
import math
import os
import random
import sys

import pygame

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
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
HIGHSCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "highscores.json")
MAX_HIGH_SCORES = 10

# Points by invader row (top to bottom)
ROW_POINTS = [40, 40, 20, 20, 10]
ROW_COLOURS = [MAGENTA, MAGENTA, CYAN, CYAN, GREEN]
MYSTERY_POINTS = [50, 100, 150, 200, 300]


# ---------------------------------------------------------------------------
# Pixel art helpers  (drawn at runtime, no external assets needed)
# ---------------------------------------------------------------------------
def draw_player_shape(surface, colour, rect):
    """Draw a classic cannon/ship shape."""
    x, y, w, h = rect
    # Base
    pygame.draw.rect(surface, colour, (x, y + h // 2, w, h // 2))
    # Turret
    pygame.draw.rect(surface, colour, (x + w // 2 - 3, y, 6, h // 2))
    # Shoulders
    pygame.draw.rect(surface, colour, (x + 4, y + h // 3, w - 8, h // 3))


def create_invader_surface(row, width, height):
    """Create a simple pixel-art invader surface based on row type."""
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    colour = ROW_COLOURS[row] if row < len(ROW_COLOURS) else GREEN
    cx, cy = width // 2, height // 2

    if row <= 1:
        # Top rows: small squid shape
        pygame.draw.rect(surf, colour, (cx - 4, 2, 8, 6))
        pygame.draw.rect(surf, colour, (cx - 8, 5, 16, 8))
        pygame.draw.rect(surf, colour, (cx - 10, 10, 4, 6))
        pygame.draw.rect(surf, colour, (cx + 6, 10, 4, 6))
        pygame.draw.rect(surf, colour, (cx - 6, 13, 4, 4))
        pygame.draw.rect(surf, colour, (cx + 2, 13, 4, 4))
    elif row <= 3:
        # Middle rows: crab shape
        pygame.draw.rect(surf, colour, (cx - 6, 2, 12, 6))
        pygame.draw.rect(surf, colour, (cx - 10, 5, 20, 8))
        pygame.draw.rect(surf, colour, (cx - 12, 8, 4, 6))
        pygame.draw.rect(surf, colour, (cx + 8, 8, 4, 6))
        pygame.draw.rect(surf, colour, (cx - 8, 13, 6, 4))
        pygame.draw.rect(surf, colour, (cx + 2, 13, 6, 4))
    else:
        # Bottom rows: octopus/grunt shape
        pygame.draw.rect(surf, colour, (cx - 8, 2, 16, 10))
        pygame.draw.rect(surf, colour, (cx - 12, 6, 24, 6))
        pygame.draw.rect(surf, colour, (cx - 10, 12, 4, 5))
        pygame.draw.rect(surf, colour, (cx - 4, 12, 4, 5))
        pygame.draw.rect(surf, colour, (cx + 0, 12, 4, 5))
        pygame.draw.rect(surf, colour, (cx + 6, 12, 4, 5))

    return surf


def create_mystery_surface():
    """Classic saucer shape."""
    w, h = 40, 16
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, RED, (0, 4, w, h - 4))
    pygame.draw.ellipse(surf, ORANGE, (8, 0, w - 16, 10))
    return surf


# ---------------------------------------------------------------------------
# Barrier (destructible)
# ---------------------------------------------------------------------------
def create_barrier_template():
    """Return a list of (row, col) offsets for a barrier shape."""
    # Classic arch shape, ~24x18 in blocks
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
            # Add some damage pixels
            for _ in range(4):
                px = random.randint(0, BARRIER_BLOCK_SIZE - 1)
                py = random.randint(0, BARRIER_BLOCK_SIZE - 1)
                self.image.set_at((px, py), BLACK)
        else:
            self.kill()


# ---------------------------------------------------------------------------
# Sprites
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# High Scores
# ---------------------------------------------------------------------------
def load_high_scores():
    if os.path.exists(HIGHSCORE_FILE):
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return []


def save_high_scores(scores):
    with open(HIGHSCORE_FILE, "w") as f:
        json.dump(scores, f, indent=2)


def is_high_score(score, scores):
    return len(scores) < MAX_HIGH_SCORES or score > scores[-1]["score"]


def add_high_score(name, score, wave, scores):
    scores.append({"name": name, "score": score, "wave": wave})
    scores.sort(key=lambda s: s["score"], reverse=True)
    return scores[:MAX_HIGH_SCORES]


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Space Invaders")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 64)
        self.high_scores = load_high_scores()
        self.state = "title"  # title, playing, game_over, enter_name, high_scores

    # -- Wave / reset helpers -----------------------------------------------
    def start_game(self):
        self.score = 0
        self.lives = 3
        self.wave = 0
        self.player = Player()
        self.player_group = pygame.sprite.GroupSingle(self.player)
        self.player_bullets = pygame.sprite.Group()
        self.invader_bullets = pygame.sprite.Group()
        self.invaders = pygame.sprite.Group()
        self.barriers = pygame.sprite.Group()
        self.mystery_group = pygame.sprite.GroupSingle()
        self.explosions = pygame.sprite.Group()
        self.invader_direction = 1
        self.invader_speed = 1.0
        self.invader_move_timer = 0
        self.invader_move_interval = 600  # ms — gets faster
        self.mystery_timer = 0
        self.next_mystery = random.randint(MYSTERY_INTERVAL_MIN, MYSTERY_INTERVAL_MAX)
        self.death_timer = 0  # brief pause on death
        self.create_barriers()
        self.next_wave()
        self.state = "playing"

    def next_wave(self):
        self.wave += 1
        self.invaders.empty()
        self.player_bullets.empty()
        self.invader_bullets.empty()
        self.invader_direction = 1

        # Speed increases each wave
        base_interval = max(200, 600 - (self.wave - 1) * 40)
        self.invader_move_interval = base_interval
        self.invader_move_timer = 0

        start_x = (SCREEN_WIDTH - (INVADER_COLS * (INVADER_WIDTH + INVADER_PADDING_X))) // 2
        # Push invaders lower on later waves (but cap it)
        extra_y = min((self.wave - 1) * 10, 80)

        for row in range(INVADER_ROWS):
            for col in range(INVADER_COLS):
                x = start_x + col * (INVADER_WIDTH + INVADER_PADDING_X)
                y = INVADER_START_Y + extra_y + row * (INVADER_HEIGHT + INVADER_PADDING_Y)
                self.invaders.add(Invader(row, col, x, y))

    def create_barriers(self):
        self.barriers.empty()
        total_width = BARRIER_COUNT * 12 * BARRIER_BLOCK_SIZE
        gap = (SCREEN_WIDTH - total_width) / (BARRIER_COUNT + 1)

        for i in range(BARRIER_COUNT):
            bx = gap + i * (12 * BARRIER_BLOCK_SIZE + gap)
            for r, c in BARRIER_TEMPLATE:
                x = bx + c * BARRIER_BLOCK_SIZE
                y = BARRIER_Y + r * BARRIER_BLOCK_SIZE
                self.barriers.add(BarrierBlock(x, y))

    # -- Invader movement ---------------------------------------------------
    def move_invaders(self, dt):
        self.invader_move_timer += dt
        if self.invader_move_timer < self.invader_move_interval:
            return

        self.invader_move_timer = 0
        # Check edges
        drop = False
        for inv in self.invaders:
            if self.invader_direction == 1 and inv.rect.right >= SCREEN_WIDTH - 10:
                drop = True
                break
            if self.invader_direction == -1 and inv.rect.left <= 10:
                drop = True
                break

        if drop:
            self.invader_direction *= -1
            for inv in self.invaders:
                inv.rect.y += INVADER_DROP
        else:
            step = int(8 + self.wave)  # pixels per step, increases with wave
            for inv in self.invaders:
                inv.rect.x += step * self.invader_direction

        # Speed up as fewer invaders remain
        count = len(self.invaders)
        if count > 0:
            ratio = count / (INVADER_COLS * INVADER_ROWS)
            self.invader_move_interval = max(
                50, int((max(200, 600 - (self.wave - 1) * 40)) * ratio)
            )

    # -- Collision detection ------------------------------------------------
    def check_collisions(self):
        # Player bullets vs invaders
        hits = pygame.sprite.groupcollide(self.invaders, self.player_bullets, True, True)
        for invader, bullets in hits.items():
            self.score += invader.points
            self.explosions.add(
                Explosion(invader.rect.centerx, invader.rect.centery,
                          ROW_COLOURS[invader.row] if invader.row < len(ROW_COLOURS) else GREEN)
            )

        # Player bullets vs mystery ship
        mystery_hits = pygame.sprite.groupcollide(self.mystery_group, self.player_bullets, True, True)
        for ship, bullets in mystery_hits.items():
            self.score += ship.points
            self.explosions.add(Explosion(ship.rect.centerx, ship.rect.centery, RED, 30))

        # Bullets vs barriers
        for bullet in self.player_bullets:
            hit_blocks = pygame.sprite.spritecollide(bullet, self.barriers, False)
            if hit_blocks:
                bullet.kill()
                hit_blocks[0].hit()

        for bullet in self.invader_bullets:
            hit_blocks = pygame.sprite.spritecollide(bullet, self.barriers, False)
            if hit_blocks:
                bullet.kill()
                hit_blocks[0].hit()

        # Invader bullets vs player
        if self.death_timer <= 0:
            player_hit = pygame.sprite.spritecollide(self.player, self.invader_bullets, True)
            if player_hit:
                self.lives -= 1
                self.explosions.add(
                    Explosion(self.player.rect.centerx, self.player.rect.centery, GREEN, 40)
                )
                if self.lives <= 0:
                    self.state = "game_over"
                    self.game_over_timer = pygame.time.get_ticks()
                else:
                    self.death_timer = 1500  # ms invulnerability

        # Invaders reaching barrier/player level = game over
        for inv in self.invaders:
            if inv.rect.bottom >= self.player.rect.top:
                self.lives = 0
                self.state = "game_over"
                self.game_over_timer = pygame.time.get_ticks()
                return

    # -- Drawing ------------------------------------------------------------
    def draw_hud(self):
        score_surf = self.font.render(f"SCORE {self.score:>06}", True, WHITE)
        self.screen.blit(score_surf, (10, 10))

        wave_surf = self.font.render(f"WAVE {self.wave}", True, WHITE)
        self.screen.blit(wave_surf, (SCREEN_WIDTH // 2 - wave_surf.get_width() // 2, 10))

        # Lives as small ship icons
        for i in range(self.lives):
            x = SCREEN_WIDTH - 30 - i * 35
            draw_player_shape(self.screen, GREEN, (x, 8, 25, 14))

        # Bottom line
        pygame.draw.line(self.screen, GREEN, (0, SCREEN_HEIGHT - 20), (SCREEN_WIDTH, SCREEN_HEIGHT - 20))

    def draw_title_screen(self):
        self.screen.fill(BLACK)
        title = self.title_font.render("SPACE INVADERS", True, GREEN)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))

        # Show invader types and points
        info = [
            ("= 40 PTS", MAGENTA, 0),
            ("= 20 PTS", CYAN, 2),
            ("= 10 PTS", GREEN, 4),
            ("= ??? PTS", RED, -1),
        ]
        y = 240
        for text, colour, row in info:
            if row >= 0:
                surf = create_invader_surface(row, INVADER_WIDTH, INVADER_HEIGHT)
            else:
                surf = create_mystery_surface()
            self.screen.blit(surf, (SCREEN_WIDTH // 2 - 80, y))
            label = self.small_font.render(text, True, colour)
            self.screen.blit(label, (SCREEN_WIDTH // 2 - 30, y + 4))
            y += 45

        prompt = self.font.render("PRESS ENTER TO PLAY", True, WHITE)
        # Blink effect
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 460))

        hs_prompt = self.small_font.render("H - HIGH SCORES", True, YELLOW)
        self.screen.blit(hs_prompt, (SCREEN_WIDTH // 2 - hs_prompt.get_width() // 2, 520))

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        go_text = self.title_font.render("GAME OVER", True, RED)
        self.screen.blit(go_text, (SCREEN_WIDTH // 2 - go_text.get_width() // 2, 200))

        score_text = self.font.render(f"FINAL SCORE: {self.score}", True, WHITE)
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 290))

        wave_text = self.font.render(f"WAVE REACHED: {self.wave}", True, WHITE)
        self.screen.blit(wave_text, (SCREEN_WIDTH // 2 - wave_text.get_width() // 2, 330))

        if pygame.time.get_ticks() - self.game_over_timer > 1500:
            if is_high_score(self.score, self.high_scores):
                prompt = self.font.render("NEW HIGH SCORE! ENTER NAME:", True, YELLOW)
                self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 400))
            else:
                prompt = self.font.render("PRESS ENTER TO CONTINUE", True, WHITE)
                if (pygame.time.get_ticks() // 500) % 2 == 0:
                    self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 400))

    def draw_enter_name(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        prompt = self.font.render("ENTER YOUR NAME:", True, YELLOW)
        self.screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 250))

        name_text = self.title_font.render(self.name_input + "_", True, GREEN)
        self.screen.blit(name_text, (SCREEN_WIDTH // 2 - name_text.get_width() // 2, 310))

    def draw_high_scores_screen(self):
        self.screen.fill(BLACK)
        title = self.title_font.render("HIGH SCORES", True, YELLOW)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        if not self.high_scores:
            empty = self.font.render("NO SCORES YET", True, WHITE)
            self.screen.blit(empty, (SCREEN_WIDTH // 2 - empty.get_width() // 2, 200))
        else:
            y = 130
            header = self.small_font.render(
                f"{'RANK':<6}{'NAME':<15}{'SCORE':>8}{'WAVE':>8}", True, CYAN
            )
            self.screen.blit(header, (SCREEN_WIDTH // 2 - header.get_width() // 2, y))
            y += 30
            pygame.draw.line(self.screen, CYAN,
                             (SCREEN_WIDTH // 2 - 150, y),
                             (SCREEN_WIDTH // 2 + 150, y))
            y += 10
            for i, entry in enumerate(self.high_scores):
                colour = YELLOW if i == 0 else WHITE
                line = self.small_font.render(
                    f" {i + 1:<5}{entry['name']:<15}{entry['score']:>8}{entry.get('wave', '-'):>8}",
                    True, colour
                )
                self.screen.blit(line, (SCREEN_WIDTH // 2 - line.get_width() // 2, y))
                y += 28

        back = self.small_font.render("PRESS ENTER TO GO BACK", True, WHITE)
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            self.screen.blit(back, (SCREEN_WIDTH // 2 - back.get_width() // 2, 540))

    # -- Main loop ----------------------------------------------------------
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)
            now = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    if self.state == "title":
                        if event.key == pygame.K_RETURN:
                            self.start_game()
                        elif event.key == pygame.K_h:
                            self.state = "high_scores"
                        elif event.key == pygame.K_ESCAPE:
                            running = False

                    elif self.state == "playing":
                        if event.key == pygame.K_ESCAPE:
                            self.state = "title"

                    elif self.state == "game_over":
                        if now - self.game_over_timer > 1500:
                            if is_high_score(self.score, self.high_scores):
                                self.state = "enter_name"
                                self.name_input = ""
                            elif event.key == pygame.K_RETURN:
                                self.state = "title"

                    elif self.state == "enter_name":
                        if event.key == pygame.K_RETURN and self.name_input.strip():
                            self.high_scores = add_high_score(
                                self.name_input.strip().upper(),
                                self.score, self.wave, self.high_scores
                            )
                            save_high_scores(self.high_scores)
                            self.state = "high_scores"
                        elif event.key == pygame.K_BACKSPACE:
                            self.name_input = self.name_input[:-1]
                        elif len(self.name_input) < 10 and event.unicode.isprintable() and event.unicode.strip():
                            self.name_input += event.unicode

                    elif self.state == "high_scores":
                        if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                            self.state = "title"

            # -- Update -----------------------------------------------------
            if self.state == "playing":
                keys = pygame.key.get_pressed()

                # Death invulnerability timer
                if self.death_timer > 0:
                    self.death_timer -= dt

                self.player.update(keys)

                # Player shooting
                if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.player.can_shoot(now):
                    self.player_bullets.add(self.player.shoot(now))

                # Invader movement
                self.move_invaders(dt)

                # Invader shooting
                living = self.invaders.sprites()
                for inv in living:
                    if random.random() < INVADER_SHOOT_CHANCE:
                        self.invader_bullets.add(inv.shoot())

                # Mystery ship
                self.mystery_timer += dt
                if self.mystery_timer >= self.next_mystery and not self.mystery_group.sprite:
                    direction = random.choice([-1, 1])
                    self.mystery_group.add(MysteryShip(direction))
                    self.mystery_timer = 0
                    self.next_mystery = random.randint(MYSTERY_INTERVAL_MIN, MYSTERY_INTERVAL_MAX)

                self.player_bullets.update()
                self.invader_bullets.update()
                self.mystery_group.update()
                self.explosions.update(dt)

                self.check_collisions()

                # Wave cleared?
                if len(self.invaders) == 0 and self.state == "playing":
                    self.next_wave()

            # -- Draw -------------------------------------------------------
            if self.state == "title":
                self.draw_title_screen()
            elif self.state == "high_scores":
                self.draw_high_scores_screen()
            elif self.state in ("playing", "game_over", "enter_name"):
                self.screen.fill(BLACK)
                self.barriers.draw(self.screen)
                self.invaders.draw(self.screen)
                self.player_group.draw(self.screen)
                self.player_bullets.draw(self.screen)
                self.invader_bullets.draw(self.screen)
                self.mystery_group.draw(self.screen)
                self.explosions.draw(self.screen)
                self.draw_hud()

                # Player blink during invulnerability
                if self.death_timer > 0 and (pygame.time.get_ticks() // 100) % 2 == 0:
                    self.player.image.set_alpha(80)
                else:
                    self.player.image.set_alpha(255)

                if self.state == "game_over":
                    self.draw_game_over()
                elif self.state == "enter_name":
                    self.draw_enter_name()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()
