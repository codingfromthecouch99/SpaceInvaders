"""Pixel art helpers and screen drawing functions."""

import pygame

from .constants import (
    BLACK,
    CYAN,
    GREEN,
    INVADER_HEIGHT,
    INVADER_WIDTH,
    MAGENTA,
    ORANGE,
    RED,
    ROW_COLOURS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
    YELLOW,
)


def draw_player_shape(surface, colour, rect):
    """Draw a classic cannon/ship shape."""
    x, y, w, h = rect
    pygame.draw.rect(surface, colour, (x, y + h // 2, w, h // 2))
    pygame.draw.rect(surface, colour, (x + w // 2 - 3, y, 6, h // 2))
    pygame.draw.rect(surface, colour, (x + 4, y + h // 3, w - 8, h // 3))


def create_invader_surface(row, width, height):
    """Create a simple pixel-art invader surface based on row type."""
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    colour = ROW_COLOURS[row] if row < len(ROW_COLOURS) else GREEN
    cx, cy = width // 2, height // 2

    if row <= 1:
        pygame.draw.rect(surf, colour, (cx - 4, 2, 8, 6))
        pygame.draw.rect(surf, colour, (cx - 8, 5, 16, 8))
        pygame.draw.rect(surf, colour, (cx - 10, 10, 4, 6))
        pygame.draw.rect(surf, colour, (cx + 6, 10, 4, 6))
        pygame.draw.rect(surf, colour, (cx - 6, 13, 4, 4))
        pygame.draw.rect(surf, colour, (cx + 2, 13, 4, 4))
    elif row <= 3:
        pygame.draw.rect(surf, colour, (cx - 6, 2, 12, 6))
        pygame.draw.rect(surf, colour, (cx - 10, 5, 20, 8))
        pygame.draw.rect(surf, colour, (cx - 12, 8, 4, 6))
        pygame.draw.rect(surf, colour, (cx + 8, 8, 4, 6))
        pygame.draw.rect(surf, colour, (cx - 8, 13, 6, 4))
        pygame.draw.rect(surf, colour, (cx + 2, 13, 6, 4))
    else:
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


def draw_hud(screen, font, score, wave, lives, draw_player_fn):
    """Draw the in-game heads-up display."""
    score_surf = font.render(f"SCORE {score:>06}", True, WHITE)
    screen.blit(score_surf, (10, 10))

    wave_surf = font.render(f"WAVE {wave}", True, WHITE)
    screen.blit(wave_surf, (SCREEN_WIDTH // 2 - wave_surf.get_width() // 2, 10))

    for i in range(lives):
        x = SCREEN_WIDTH - 30 - i * 35
        draw_player_fn(screen, GREEN, (x, 8, 25, 14))

    pygame.draw.line(screen, GREEN, (0, SCREEN_HEIGHT - 20), (SCREEN_WIDTH, SCREEN_HEIGHT - 20))


def draw_title_screen(screen, title_font, font, small_font):
    """Draw the title/start screen."""
    screen.fill(BLACK)
    title = title_font.render("SPACE INVADERS", True, GREEN)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))

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
        screen.blit(surf, (SCREEN_WIDTH // 2 - 80, y))
        label = small_font.render(text, True, colour)
        screen.blit(label, (SCREEN_WIDTH // 2 - 30, y + 4))
        y += 45

    prompt = font.render("PRESS ENTER TO PLAY", True, WHITE)
    if (pygame.time.get_ticks() // 500) % 2 == 0:
        screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 460))

    hs_prompt = small_font.render("H - HIGH SCORES", True, YELLOW)
    screen.blit(hs_prompt, (SCREEN_WIDTH // 2 - hs_prompt.get_width() // 2, 520))


def draw_game_over(screen, title_font, font, score, wave, game_over_timer, is_high_score):
    """Draw the game-over overlay."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150))
    screen.blit(overlay, (0, 0))

    go_text = title_font.render("GAME OVER", True, RED)
    screen.blit(go_text, (SCREEN_WIDTH // 2 - go_text.get_width() // 2, 200))

    score_text = font.render(f"FINAL SCORE: {score}", True, WHITE)
    screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 290))

    wave_text = font.render(f"WAVE REACHED: {wave}", True, WHITE)
    screen.blit(wave_text, (SCREEN_WIDTH // 2 - wave_text.get_width() // 2, 330))

    if pygame.time.get_ticks() - game_over_timer > 1500:
        if is_high_score:
            prompt = font.render("NEW HIGH SCORE! ENTER NAME:", True, YELLOW)
            screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 400))
        else:
            prompt = font.render("PRESS ENTER TO CONTINUE", True, WHITE)
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 400))


def draw_enter_name(screen, font, title_font, name_input):
    """Draw the name-entry overlay."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))

    prompt = font.render("ENTER YOUR NAME:", True, YELLOW)
    screen.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 250))

    name_text = title_font.render(name_input + "_", True, GREEN)
    screen.blit(name_text, (SCREEN_WIDTH // 2 - name_text.get_width() // 2, 310))


def draw_high_scores_screen(screen, title_font, font, small_font, high_scores):
    """Draw the high-scores table screen."""
    screen.fill(BLACK)
    title = title_font.render("HIGH SCORES", True, YELLOW)
    screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

    if not high_scores:
        empty = font.render("NO SCORES YET", True, WHITE)
        screen.blit(empty, (SCREEN_WIDTH // 2 - empty.get_width() // 2, 200))
    else:
        y = 130
        header = small_font.render(
            f"{'RANK':<6}{'NAME':<15}{'SCORE':>8}{'WAVE':>8}", True, CYAN
        )
        screen.blit(header, (SCREEN_WIDTH // 2 - header.get_width() // 2, y))
        y += 30
        pygame.draw.line(
            screen, CYAN,
            (SCREEN_WIDTH // 2 - 150, y),
            (SCREEN_WIDTH // 2 + 150, y),
        )
        y += 10
        for i, entry in enumerate(high_scores):
            colour = YELLOW if i == 0 else WHITE
            line = small_font.render(
                f" {i + 1:<5}{entry['name']:<15}{entry['score']:>8}{entry.get('wave', '-'):>8}",
                True, colour,
            )
            screen.blit(line, (SCREEN_WIDTH // 2 - line.get_width() // 2, y))
            y += 28

    back = small_font.render("PRESS ENTER TO GO BACK", True, WHITE)
    if (pygame.time.get_ticks() // 500) % 2 == 0:
        screen.blit(back, (SCREEN_WIDTH // 2 - back.get_width() // 2, 540))
