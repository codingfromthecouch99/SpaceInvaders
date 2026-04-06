"""Unit tests for game entities."""

import pygame
import pytest

from spaceinvaders.constants import (
    BARRIER_BLOCK_SIZE,
    INVADER_BULLET_SPEED,
    PLAYER_BULLET_SPEED,
    PLAYER_SHOOT_COOLDOWN,
    PLAYER_SPEED,
    PLAYER_WIDTH,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from spaceinvaders.entities import (
    BARRIER_TEMPLATE,
    BarrierBlock,
    Bullet,
    Explosion,
    Invader,
    MysteryShip,
    Player,
    create_barrier_template,
)


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------
class TestPlayer:
    def test_initial_position(self):
        player = Player()
        assert player.rect.centerx == SCREEN_WIDTH // 2
        assert player.rect.bottom == SCREEN_HEIGHT - 30

    def test_move_left(self):
        player = Player()
        start_x = player.rect.x
        keys = {i: False for i in range(512)}
        keys[pygame.K_LEFT] = True

        class KeyProxy:
            def __getitem__(self, key):
                return keys.get(key, False)

        player.update(KeyProxy())
        assert player.rect.x == start_x - PLAYER_SPEED

    def test_move_right(self):
        player = Player()
        start_x = player.rect.x
        keys = {i: False for i in range(512)}
        keys[pygame.K_RIGHT] = True

        class KeyProxy:
            def __getitem__(self, key):
                return keys.get(key, False)

        player.update(KeyProxy())
        assert player.rect.x == start_x + PLAYER_SPEED

    def test_cannot_move_past_left_edge(self):
        player = Player()
        player.rect.x = 0
        keys = {i: False for i in range(512)}
        keys[pygame.K_LEFT] = True

        class KeyProxy:
            def __getitem__(self, key):
                return keys.get(key, False)

        player.update(KeyProxy())
        assert player.rect.x == 0

    def test_cannot_move_past_right_edge(self):
        player = Player()
        player.rect.x = SCREEN_WIDTH - PLAYER_WIDTH
        keys = {i: False for i in range(512)}
        keys[pygame.K_RIGHT] = True

        class KeyProxy:
            def __getitem__(self, key):
                return keys.get(key, False)

        player.update(KeyProxy())
        assert player.rect.x == SCREEN_WIDTH - PLAYER_WIDTH

    def test_shoot_cooldown(self):
        player = Player()
        # First shot: last_shot=0, now=1000 → 1000 >= 300 → True
        assert player.can_shoot(1000) is True
        player.shoot(1000)
        # Too soon: 1100 - 1000 = 100 < 300
        assert player.can_shoot(1100) is False
        # Exactly at cooldown: 1300 - 1000 = 300 >= 300 → True
        assert player.can_shoot(1000 + PLAYER_SHOOT_COOLDOWN) is True

    def test_shoot_returns_bullet(self):
        player = Player()
        bullet = player.shoot(0)
        assert isinstance(bullet, Bullet)
        assert bullet.is_player is True
        assert bullet.speed == PLAYER_BULLET_SPEED


# ---------------------------------------------------------------------------
# Invader
# ---------------------------------------------------------------------------
class TestInvader:
    def test_points_by_row(self):
        inv0 = Invader(0, 0, 100, 100)
        inv2 = Invader(2, 0, 100, 100)
        inv4 = Invader(4, 0, 100, 100)
        assert inv0.points == 40
        assert inv2.points == 20
        assert inv4.points == 10

    def test_out_of_range_row_defaults(self):
        inv = Invader(99, 0, 100, 100)
        assert inv.points == 10

    def test_shoot_returns_enemy_bullet(self):
        inv = Invader(0, 0, 100, 100)
        bullet = inv.shoot()
        assert isinstance(bullet, Bullet)
        assert bullet.is_player is False
        assert bullet.speed == INVADER_BULLET_SPEED


# ---------------------------------------------------------------------------
# Bullet
# ---------------------------------------------------------------------------
class TestBullet:
    def test_player_bullet_moves_up(self):
        bullet = Bullet(100, 300, PLAYER_BULLET_SPEED, is_player=True)
        start_y = bullet.rect.y
        bullet.update()
        assert bullet.rect.y == start_y + PLAYER_BULLET_SPEED

    def test_enemy_bullet_moves_down(self):
        bullet = Bullet(100, 300, INVADER_BULLET_SPEED, is_player=False)
        start_y = bullet.rect.y
        bullet.update()
        assert bullet.rect.y == start_y + INVADER_BULLET_SPEED

    def test_bullet_killed_when_off_screen_top(self):
        group = pygame.sprite.Group()
        bullet = Bullet(100, 0, -10, is_player=True)
        group.add(bullet)
        bullet.rect.bottom = -1
        bullet.update()
        assert not group.has(bullet)

    def test_bullet_killed_when_off_screen_bottom(self):
        group = pygame.sprite.Group()
        bullet = Bullet(100, SCREEN_HEIGHT, 10, is_player=False)
        group.add(bullet)
        bullet.rect.top = SCREEN_HEIGHT + 1
        bullet.update()
        assert not group.has(bullet)


# ---------------------------------------------------------------------------
# MysteryShip
# ---------------------------------------------------------------------------
class TestMysteryShip:
    def test_moves_right(self):
        ship = MysteryShip(1)
        start_x = ship.rect.x
        ship.update()
        assert ship.rect.x > start_x

    def test_moves_left(self):
        ship = MysteryShip(-1)
        start_x = ship.rect.x
        ship.update()
        assert ship.rect.x < start_x

    def test_killed_when_off_screen_right(self):
        group = pygame.sprite.Group()
        ship = MysteryShip(1)
        group.add(ship)
        ship.rect.left = SCREEN_WIDTH + 1
        ship.update()
        assert not group.has(ship)

    def test_killed_when_off_screen_left(self):
        group = pygame.sprite.Group()
        ship = MysteryShip(-1)
        group.add(ship)
        ship.rect.right = -1
        ship.update()
        assert not group.has(ship)


# ---------------------------------------------------------------------------
# Explosion
# ---------------------------------------------------------------------------
class TestExplosion:
    def test_alive_during_duration(self):
        group = pygame.sprite.Group()
        exp = Explosion(100, 100)
        group.add(exp)
        exp.update(100)  # 100ms of 200ms duration
        assert group.has(exp)

    def test_killed_after_duration(self):
        group = pygame.sprite.Group()
        exp = Explosion(100, 100)
        group.add(exp)
        exp.update(250)  # exceeds 200ms
        assert not group.has(exp)


# ---------------------------------------------------------------------------
# BarrierBlock
# ---------------------------------------------------------------------------
class TestBarrierBlock:
    def test_initial_health(self):
        block = BarrierBlock(0, 0)
        assert block.health == 3

    def test_hit_reduces_health(self):
        block = BarrierBlock(0, 0)
        block.hit()
        assert block.health == 2

    def test_destroyed_after_three_hits(self):
        group = pygame.sprite.Group()
        block = BarrierBlock(0, 0)
        group.add(block)
        block.hit()  # 3 -> 2
        block.hit()  # 2 -> 1
        block.hit()  # 1 -> 0, killed
        assert not group.has(block)

    def test_size(self):
        block = BarrierBlock(10, 20)
        assert block.rect.width == BARRIER_BLOCK_SIZE
        assert block.rect.height == BARRIER_BLOCK_SIZE


# ---------------------------------------------------------------------------
# Barrier template
# ---------------------------------------------------------------------------
class TestBarrierTemplate:
    def test_template_not_empty(self):
        assert len(BARRIER_TEMPLATE) > 0

    def test_template_has_arch_gap(self):
        """The bottom rows should have a gap (the arch opening)."""
        bottom_row = max(r for r, c in BARRIER_TEMPLATE)
        bottom_cols = {c for r, c in BARRIER_TEMPLATE if r == bottom_row}
        all_cols = set(range(12))
        assert len(all_cols - bottom_cols) > 0  # gap exists

    def test_idempotent(self):
        assert create_barrier_template() == BARRIER_TEMPLATE
