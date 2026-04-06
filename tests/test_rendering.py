"""Unit tests for rendering helpers."""

import pygame
import pytest

from spaceinvaders.constants import INVADER_HEIGHT, INVADER_WIDTH
from spaceinvaders.rendering import (
    create_invader_surface,
    create_mystery_surface,
    draw_player_shape,
)


class TestDrawPlayerShape:
    def test_does_not_raise(self):
        surf = pygame.Surface((40, 20), pygame.SRCALPHA)
        draw_player_shape(surf, (0, 255, 0), (0, 0, 40, 20))

    def test_pixels_drawn(self):
        """At least some pixels should be non-transparent after drawing."""
        surf = pygame.Surface((40, 20), pygame.SRCALPHA)
        draw_player_shape(surf, (0, 255, 0), (0, 0, 40, 20))
        has_colour = any(
            surf.get_at((x, y)).a > 0
            for x in range(40) for y in range(20)
        )
        assert has_colour


class TestCreateInvaderSurface:
    @pytest.mark.parametrize("row", [0, 1, 2, 3, 4])
    def test_correct_dimensions(self, row):
        surf = create_invader_surface(row, INVADER_WIDTH, INVADER_HEIGHT)
        assert surf.get_width() == INVADER_WIDTH
        assert surf.get_height() == INVADER_HEIGHT

    @pytest.mark.parametrize("row", [0, 2, 4])
    def test_has_non_transparent_pixels(self, row):
        surf = create_invader_surface(row, INVADER_WIDTH, INVADER_HEIGHT)
        has_colour = any(
            surf.get_at((x, y)).a > 0
            for x in range(INVADER_WIDTH) for y in range(INVADER_HEIGHT)
        )
        assert has_colour

    def test_different_rows_look_different(self):
        """Top, middle, bottom rows should produce different sprites."""
        s0 = create_invader_surface(0, INVADER_WIDTH, INVADER_HEIGHT)
        s2 = create_invader_surface(2, INVADER_WIDTH, INVADER_HEIGHT)
        s4 = create_invader_surface(4, INVADER_WIDTH, INVADER_HEIGHT)
        # Compare raw pixel data
        d0 = pygame.image.tobytes(s0, "RGBA")
        d2 = pygame.image.tobytes(s2, "RGBA")
        d4 = pygame.image.tobytes(s4, "RGBA")
        assert d0 != d2
        assert d2 != d4

    def test_out_of_range_row_uses_fallback(self):
        """Rows beyond 4 should still produce a valid surface."""
        surf = create_invader_surface(99, INVADER_WIDTH, INVADER_HEIGHT)
        assert surf.get_width() == INVADER_WIDTH


class TestCreateMysterySurface:
    def test_dimensions(self):
        surf = create_mystery_surface()
        assert surf.get_width() == 40
        assert surf.get_height() == 16

    def test_has_pixels(self):
        surf = create_mystery_surface()
        has_colour = any(
            surf.get_at((x, y)).a > 0
            for x in range(40) for y in range(16)
        )
        assert has_colour
