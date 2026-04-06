"""Main Game class — orchestrates all systems."""

import random
import sys

import pygame

from .constants import (
    BARRIER_BLOCK_SIZE,
    BARRIER_COUNT,
    BARRIER_Y,
    BLACK,
    FPS,
    GREEN,
    INVADER_COLS,
    INVADER_DROP,
    INVADER_HEIGHT,
    INVADER_PADDING_X,
    INVADER_PADDING_Y,
    INVADER_ROWS,
    INVADER_SHOOT_CHANCE,
    INVADER_START_Y,
    INVADER_WIDTH,
    MYSTERY_INTERVAL_MAX,
    MYSTERY_INTERVAL_MIN,
    ROW_COLOURS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from .entities import (
    BARRIER_TEMPLATE,
    BarrierBlock,
    Explosion,
    Invader,
    MysteryShip,
    Player,
)
from .high_scores import add_high_score, is_high_score, load_high_scores, save_high_scores
from .rendering import (
    draw_enter_name,
    draw_game_over,
    draw_high_scores_screen,
    draw_hud,
    draw_player_shape,
    draw_title_screen,
)


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
        self.state = "title"

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
        self.invader_move_interval = 600
        self.mystery_timer = 0
        self.next_mystery = random.randint(MYSTERY_INTERVAL_MIN, MYSTERY_INTERVAL_MAX)
        self.death_timer = 0
        self.create_barriers()
        self.next_wave()
        self.state = "playing"

    def next_wave(self):
        self.wave += 1
        self.invaders.empty()
        self.player_bullets.empty()
        self.invader_bullets.empty()
        self.invader_direction = 1

        base_interval = max(200, 600 - (self.wave - 1) * 40)
        self.invader_move_interval = base_interval
        self.invader_move_timer = 0

        start_x = (SCREEN_WIDTH - (INVADER_COLS * (INVADER_WIDTH + INVADER_PADDING_X))) // 2
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
            step = int(8 + self.wave)
            for inv in self.invaders:
                inv.rect.x += step * self.invader_direction

        count = len(self.invaders)
        if count > 0:
            ratio = count / (INVADER_COLS * INVADER_ROWS)
            self.invader_move_interval = max(
                50, int((max(200, 600 - (self.wave - 1) * 40)) * ratio)
            )

    # -- Collision detection ------------------------------------------------
    def check_collisions(self):
        hits = pygame.sprite.groupcollide(self.invaders, self.player_bullets, True, True)
        for invader in hits:
            self.score += invader.points
            self.explosions.add(
                Explosion(
                    invader.rect.centerx, invader.rect.centery,
                    ROW_COLOURS[invader.row] if invader.row < len(ROW_COLOURS) else GREEN,
                )
            )

        mystery_hits = pygame.sprite.groupcollide(self.mystery_group, self.player_bullets, True, True)
        for ship in mystery_hits:
            self.score += ship.points
            self.explosions.add(Explosion(ship.rect.centerx, ship.rect.centery, (255, 0, 0), 30))

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

        if self.death_timer <= 0:
            player_hit = pygame.sprite.spritecollide(self.player, self.invader_bullets, True)
            if player_hit:
                self.lives -= 1
                self.explosions.add(Explosion(self.player.rect.centerx, self.player.rect.centery, GREEN, 40))
                if self.lives <= 0:
                    self.state = "game_over"
                    self.game_over_timer = pygame.time.get_ticks()
                else:
                    self.death_timer = 1500

        for inv in self.invaders:
            if inv.rect.bottom >= self.player.rect.top:
                self.lives = 0
                self.state = "game_over"
                self.game_over_timer = pygame.time.get_ticks()
                return

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
                                self.score, self.wave, self.high_scores,
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

                if self.death_timer > 0:
                    self.death_timer -= dt

                self.player.update(keys)

                if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.player.can_shoot(now):
                    self.player_bullets.add(self.player.shoot(now))

                self.move_invaders(dt)

                living = self.invaders.sprites()
                for inv in living:
                    if random.random() < INVADER_SHOOT_CHANCE:
                        self.invader_bullets.add(inv.shoot())

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

                if len(self.invaders) == 0 and self.state == "playing":
                    self.next_wave()

            # -- Draw -------------------------------------------------------
            if self.state == "title":
                draw_title_screen(self.screen, self.title_font, self.font, self.small_font)
            elif self.state == "high_scores":
                draw_high_scores_screen(
                    self.screen, self.title_font, self.font, self.small_font, self.high_scores,
                )
            elif self.state in ("playing", "game_over", "enter_name"):
                self.screen.fill(BLACK)
                self.barriers.draw(self.screen)
                self.invaders.draw(self.screen)
                self.player_group.draw(self.screen)
                self.player_bullets.draw(self.screen)
                self.invader_bullets.draw(self.screen)
                self.mystery_group.draw(self.screen)
                self.explosions.draw(self.screen)
                draw_hud(self.screen, self.font, self.score, self.wave, self.lives, draw_player_shape)

                if self.death_timer > 0 and (pygame.time.get_ticks() // 100) % 2 == 0:
                    self.player.image.set_alpha(80)
                else:
                    self.player.image.set_alpha(255)

                if self.state == "game_over":
                    draw_game_over(
                        self.screen, self.title_font, self.font,
                        self.score, self.wave, self.game_over_timer,
                        is_high_score(self.score, self.high_scores),
                    )
                elif self.state == "enter_name":
                    draw_enter_name(self.screen, self.font, self.title_font, self.name_input)

            pygame.display.flip()

        pygame.quit()
        sys.exit()
