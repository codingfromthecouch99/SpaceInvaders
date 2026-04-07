"""Integration tests for GameEngine — state transitions, wave management, collisions."""

import pygame
import pytest

from spaceinvaders.constants import (
    INVADER_COLS,
    INVADER_ROWS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from spaceinvaders.entities import Bullet, Invader
from spaceinvaders.engine import GameEngine


@pytest.fixture
def engine():
    return GameEngine()


class TestGameStateTransitions:
    def test_initial_state_is_title(self, engine):
        assert engine.state == "title"

    def test_start_game_transitions_to_playing(self, engine):
        engine.start_game()
        assert engine.state == "playing"

    def test_start_game_resets_score(self, engine):
        engine.start_game()
        assert engine.score == 0
        assert engine.lives == 3
        assert engine.wave == 1

    def test_enter_key_starts_game(self, engine):
        engine.handle_keydown(pygame.K_RETURN, "\r", 1000)
        assert engine.state == "playing"

    def test_h_key_opens_high_scores(self, engine):
        engine.handle_keydown(pygame.K_h, "h", 1000)
        assert engine.state == "high_scores"

    def test_escape_from_high_scores_returns_to_title(self, engine):
        engine.state = "high_scores"
        engine.handle_keydown(pygame.K_ESCAPE, "", 1000)
        assert engine.state == "title"

    def test_escape_from_playing_returns_to_title(self, engine):
        engine.start_game()
        engine.handle_keydown(pygame.K_ESCAPE, "", 1000)
        assert engine.state == "title"

    def test_escape_from_title_signals_quit(self, engine):
        result = engine.handle_keydown(pygame.K_ESCAPE, "", 1000)
        assert result == "quit"


class TestWaveManagement:
    def test_first_wave_creates_invaders(self, engine):
        engine.start_game()
        assert len(engine.invaders) == INVADER_COLS * INVADER_ROWS

    def test_next_wave_increments_counter(self, engine):
        engine.start_game()
        assert engine.wave == 1
        engine.next_wave()
        assert engine.wave == 2

    def test_next_wave_repopulates_invaders(self, engine):
        engine.start_game()
        engine.invaders.empty()
        assert len(engine.invaders) == 0
        engine.next_wave()
        assert len(engine.invaders) == INVADER_COLS * INVADER_ROWS

    def test_wave_speed_increases(self, engine):
        engine.start_game()
        interval_w1 = engine.invader_move_interval
        engine.next_wave()
        interval_w2 = engine.invader_move_interval
        assert interval_w2 <= interval_w1


class TestBarriers:
    def test_barriers_created(self, engine):
        engine.start_game()
        assert len(engine.barriers) > 0

    def test_barriers_positioned_below_invaders(self, engine):
        engine.start_game()
        for block in engine.barriers:
            assert block.rect.y >= 400


class TestCollisions:
    def test_player_bullet_kills_invader(self, engine):
        engine.start_game()
        invader = engine.invaders.sprites()[0]
        bullet = Bullet(
            invader.rect.centerx, invader.rect.centery,
            -7, is_player=True,
        )
        engine.player_bullets.add(bullet)
        initial_count = len(engine.invaders)
        engine.check_collisions()
        assert len(engine.invaders) == initial_count - 1

    def test_killing_invader_awards_points(self, engine):
        engine.start_game()
        invader = engine.invaders.sprites()[0]
        expected_points = invader.points
        bullet = Bullet(
            invader.rect.centerx, invader.rect.centery,
            -7, is_player=True,
        )
        engine.player_bullets.add(bullet)
        engine.check_collisions()
        assert engine.score == expected_points

    def test_invader_bullet_hits_player(self, engine):
        engine.start_game()
        bullet = Bullet(
            engine.player.rect.centerx, engine.player.rect.centery,
            4, is_player=False,
        )
        engine.invader_bullets.add(bullet)
        engine.check_collisions()
        assert engine.lives == 2

    def test_player_death_triggers_game_over_at_zero_lives(self, engine):
        engine.start_game()
        engine.lives = 1
        bullet = Bullet(
            engine.player.rect.centerx, engine.player.rect.centery,
            4, is_player=False,
        )
        engine.invader_bullets.add(bullet)
        engine.check_collisions()
        assert engine.state == "game_over"

    def test_invaders_reaching_player_triggers_game_over(self, engine):
        engine.start_game()
        for inv in engine.invaders:
            inv.rect.y = engine.player.rect.top
        engine.check_collisions()
        assert engine.state == "game_over"

    def test_death_timer_grants_invulnerability(self, engine):
        engine.start_game()
        engine.death_timer = 1000
        bullet = Bullet(
            engine.player.rect.centerx, engine.player.rect.centery,
            4, is_player=False,
        )
        engine.invader_bullets.add(bullet)
        engine.check_collisions()
        assert engine.lives == 3


class TestInvaderMovement:
    def test_invaders_move_after_interval(self, engine):
        engine.start_game()
        inv = engine.invaders.sprites()[0]
        start_x = inv.rect.x
        engine.move_invaders(engine.invader_move_interval + 1)
        assert inv.rect.x != start_x

    def test_invaders_do_not_move_before_interval(self, engine):
        engine.start_game()
        inv = engine.invaders.sprites()[0]
        start_x = inv.rect.x
        engine.move_invaders(1)
        assert inv.rect.x == start_x

    def test_invaders_drop_and_reverse_at_edge(self, engine):
        engine.start_game()
        for inv in engine.invaders:
            inv.rect.x = SCREEN_WIDTH - 5
        start_y = engine.invaders.sprites()[0].rect.y
        engine.move_invaders(engine.invader_move_interval + 1)
        assert engine.invader_direction == -1
        assert engine.invaders.sprites()[0].rect.y > start_y


class TestNameEntry:
    def test_typing_name(self, engine):
        engine.start_game()
        engine.state = "enter_name"
        engine.name_input = ""
        engine.handle_keydown(pygame.K_a, "a", 1000)
        engine.handle_keydown(pygame.K_c, "c", 1000)
        engine.handle_keydown(pygame.K_e, "e", 1000)
        assert engine.name_input == "ace"

    def test_backspace_deletes(self, engine):
        engine.start_game()
        engine.state = "enter_name"
        engine.name_input = "ab"
        engine.handle_keydown(pygame.K_BACKSPACE, "", 1000)
        assert engine.name_input == "a"

    def test_name_max_length(self, engine):
        engine.start_game()
        engine.state = "enter_name"
        engine.name_input = "1234567890"
        engine.handle_keydown(pygame.K_a, "a", 1000)
        assert len(engine.name_input) == 10  # not 11
