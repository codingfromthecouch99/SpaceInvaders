"""Integration tests for Game — state transitions, wave management, collisions."""

import pygame
import pytest

from spaceinvaders.constants import (
    INVADER_COLS,
    INVADER_ROWS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from spaceinvaders.entities import Bullet, Invader
from spaceinvaders.game import Game


@pytest.fixture
def game():
    g = Game()
    return g


class TestGameStateTransitions:
    def test_initial_state_is_title(self, game):
        assert game.state == "title"

    def test_start_game_transitions_to_playing(self, game):
        game.start_game()
        assert game.state == "playing"

    def test_start_game_resets_score(self, game):
        game.start_game()
        assert game.score == 0
        assert game.lives == 3
        assert game.wave == 1


class TestWaveManagement:
    def test_first_wave_creates_invaders(self, game):
        game.start_game()
        assert len(game.invaders) == INVADER_COLS * INVADER_ROWS

    def test_next_wave_increments_counter(self, game):
        game.start_game()
        assert game.wave == 1
        game.next_wave()
        assert game.wave == 2

    def test_next_wave_repopulates_invaders(self, game):
        game.start_game()
        game.invaders.empty()
        assert len(game.invaders) == 0
        game.next_wave()
        assert len(game.invaders) == INVADER_COLS * INVADER_ROWS

    def test_wave_speed_increases(self, game):
        game.start_game()
        interval_w1 = game.invader_move_interval
        game.next_wave()
        interval_w2 = game.invader_move_interval
        assert interval_w2 <= interval_w1


class TestBarriers:
    def test_barriers_created(self, game):
        game.start_game()
        assert len(game.barriers) > 0

    def test_barriers_positioned_below_invaders(self, game):
        game.start_game()
        for block in game.barriers:
            assert block.rect.y >= 400  # barriers are at y=470+


class TestCollisions:
    def test_player_bullet_kills_invader(self, game):
        game.start_game()
        invader = game.invaders.sprites()[0]
        bullet = Bullet(
            invader.rect.centerx, invader.rect.centery,
            -7, is_player=True,
        )
        game.player_bullets.add(bullet)
        initial_count = len(game.invaders)
        game.check_collisions()
        assert len(game.invaders) == initial_count - 1

    def test_killing_invader_awards_points(self, game):
        game.start_game()
        invader = game.invaders.sprites()[0]
        expected_points = invader.points
        bullet = Bullet(
            invader.rect.centerx, invader.rect.centery,
            -7, is_player=True,
        )
        game.player_bullets.add(bullet)
        game.check_collisions()
        assert game.score == expected_points

    def test_invader_bullet_hits_player(self, game):
        game.start_game()
        bullet = Bullet(
            game.player.rect.centerx, game.player.rect.centery,
            4, is_player=False,
        )
        game.invader_bullets.add(bullet)
        game.check_collisions()
        assert game.lives == 2

    def test_player_death_triggers_game_over_at_zero_lives(self, game):
        game.start_game()
        game.lives = 1
        bullet = Bullet(
            game.player.rect.centerx, game.player.rect.centery,
            4, is_player=False,
        )
        game.invader_bullets.add(bullet)
        game.check_collisions()
        assert game.state == "game_over"

    def test_invaders_reaching_player_triggers_game_over(self, game):
        game.start_game()
        for inv in game.invaders:
            inv.rect.y = game.player.rect.top
        game.check_collisions()
        assert game.state == "game_over"

    def test_death_timer_grants_invulnerability(self, game):
        game.start_game()
        game.death_timer = 1000  # invulnerable
        bullet = Bullet(
            game.player.rect.centerx, game.player.rect.centery,
            4, is_player=False,
        )
        game.invader_bullets.add(bullet)
        game.check_collisions()
        assert game.lives == 3  # no damage taken


class TestInvaderMovement:
    def test_invaders_move_after_interval(self, game):
        game.start_game()
        inv = game.invaders.sprites()[0]
        start_x = inv.rect.x
        game.move_invaders(game.invader_move_interval + 1)
        assert inv.rect.x != start_x

    def test_invaders_do_not_move_before_interval(self, game):
        game.start_game()
        inv = game.invaders.sprites()[0]
        start_x = inv.rect.x
        game.move_invaders(1)
        assert inv.rect.x == start_x

    def test_invaders_drop_and_reverse_at_edge(self, game):
        game.start_game()
        # Push all invaders to the right edge
        for inv in game.invaders:
            inv.rect.x = SCREEN_WIDTH - 5
        start_y = game.invaders.sprites()[0].rect.y
        game.move_invaders(game.invader_move_interval + 1)
        assert game.invader_direction == -1
        assert game.invaders.sprites()[0].rect.y > start_y
