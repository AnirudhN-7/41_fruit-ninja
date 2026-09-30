import math
import random
import struct

import pygame

from .fruit import Fruit


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BOMB_BLACK = (30, 30, 30)
FRUIT_COLORS = [
    (220, 60, 60),
    (230, 140, 40),
    (230, 200, 40),
    (90, 180, 90),
]

DARK_BLUE = (20, 25, 45)
RED = (220, 60, 60)
YELLOW = (240, 220, 60)


class GameEngine:

    def __init__(self, width, height):

        self.width = width
        self.height = height

        # --------------------------------------------------
        # Fonts
        # --------------------------------------------------

        self.font = pygame.font.SysFont("Arial", 28)
        self.large_font = pygame.font.SysFont("Arial", 52)
        self.medium_font = pygame.font.SysFont("Arial", 34)
        self.small_font = pygame.font.SysFont("Arial", 22)

        # --------------------------------------------------
        # Difficulty settings
        # --------------------------------------------------

        self.difficulties = {
            "Easy": {
                "spawn_interval": 65,
                "bomb_chance": 0.10,
                "speed_scale": 0.9,
            },

            "Medium": {
                "spawn_interval": 55,
                "bomb_chance": 0.15,
                "speed_scale": 1.0,
            },

            "Hard": {
                "spawn_interval": 42,
                "bomb_chance": 0.25,
                "speed_scale": 1.15,
            },
        }

        # --------------------------------------------------
        # Audio
        # --------------------------------------------------

        self.setup_audio()

        # --------------------------------------------------
        # Game state
        # --------------------------------------------------

        self.exit_requested = False

        self.reset("Medium")

    # ======================================================
    # AUDIO
    # ======================================================

    def setup_audio(self):

        self.slice_sound = None
        self.bomb_sound = None
        self.game_over_sound = None

        try:

            if not pygame.mixer.get_init():
                pygame.mixer.init(
                    frequency=44100,
                    size=-16,
                    channels=1
                )

            self.slice_sound = self.create_sound(
                frequency=900,
                duration=0.08,
                volume=0.25
            )

            self.bomb_sound = self.create_sound(
                frequency=120,
                duration=0.25,
                volume=0.40
            )

            self.game_over_sound = self.create_sound(
                frequency=180,
                duration=0.50,
                volume=0.35
            )

        except pygame.error:

            # The game should still work if audio
            # cannot be initialized.

            self.slice_sound = None
            self.bomb_sound = None
            self.game_over_sound = None

    def create_sound(self, frequency, duration, volume):

        sample_rate = 44100
        sample_count = int(
            sample_rate * duration
        )

        audio_data = bytearray()

        for i in range(sample_count):

            time = i / sample_rate

            # Simple fade-out envelope.
            envelope = 1.0 - (i / sample_count)

            wave = math.sin(
                2 * math.pi * frequency * time
            )

            sample = int(
                wave *
                32767 *
                volume *
                envelope
            )

            audio_data.extend(
                struct.pack("<h", sample)
            )

        return pygame.mixer.Sound(
            buffer=bytes(audio_data)
        )

    def play_sound(self, sound):

        if sound is not None:

            try:
                sound.play()

            except pygame.error:
                pass

    # ======================================================
    # RESET / NEW GAME
    # ======================================================

    def reset(self, difficulty):

        self.difficulty = difficulty

        settings = self.difficulties[difficulty]

        self.fruits = []

        self.trail = []

        # Mouse position used for continuous
        # swipe collision detection.
        self.previous_mouse_pos = None

        # Spawn configuration.
        self.spawn_interval = settings["spawn_interval"]
        self.bomb_chance = settings["bomb_chance"]
        self.speed_scale = settings["speed_scale"]

        self._spawn_timer = 0

        self.lives = 3
        self.score = 0

        self.game_over = False
        self.game_over_reason = ""

        self.exit_requested = False

    # ======================================================
    # SPAWNING
    # ======================================================

    def spawn_fruit(self):

        x = random.randint(
            60,
            self.width - 60
        )

        vy = (
            -random.uniform(13, 16)
            * self.speed_scale
        )

        vx = random.uniform(-2, 2)

        gravity = 0.35

        kind = (
            "bomb"
            if random.random() < self.bomb_chance
            else "fruit"
        )

        fruit = Fruit(
            x,
            self.height + 30,
            vx,
            vy,
            gravity,
            kind=kind
        )

        if kind == "bomb":
            fruit.color = BOMB_BLACK
        else:
            fruit.color = random.choice(
                FRUIT_COLORS
            )

        self.fruits.append(fruit)

    # ======================================================
    # EVENT HANDLING
    # ======================================================

    def handle_event(self, event):

        # --------------------------------------------------
        # GAME OVER INPUT
        # --------------------------------------------------

        if self.game_over:

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_1:
                    self.reset("Easy")

                elif event.key == pygame.K_2:
                    self.reset("Medium")

                elif event.key == pygame.K_3:
                    self.reset("Hard")

                elif event.key == pygame.K_ESCAPE:
                    self.exit_requested = True

            return

        # --------------------------------------------------
        # NORMAL GAME INPUT
        # --------------------------------------------------

        if event.type == pygame.MOUSEMOTION:

            self._handle_motion(event.pos)

    # ======================================================
    # MOUSE / BLADE
    # ======================================================

    def _handle_motion(self, pos):

        # If this is the first mouse event,
        # there is no previous point to form a segment.
        if self.previous_mouse_pos is None:

            self.previous_mouse_pos = pos

            self.trail.append(pos)

            return

        start = self.previous_mouse_pos
        end = pos

        # --------------------------------------------------
        # Check every fruit against the complete swipe
        # segment.
        # --------------------------------------------------

        for fruit in self.fruits:

            if fruit.sliced:
                continue

            if fruit.intersects_segment(
                start,
                end
            ):

                self._slice(fruit)

        # --------------------------------------------------
        # Store blade trail
        # --------------------------------------------------

        self.trail.append(pos)

        if len(self.trail) > 15:
            self.trail.pop(0)

        self.previous_mouse_pos = pos

    # ======================================================
    # SLICING
    # ======================================================

    def _slice(self, fruit):

        if fruit.sliced:
            return

        fruit.sliced = True

        # --------------------------------------------------
        # Bomb
        # --------------------------------------------------

        if fruit.kind == "bomb":

            self.play_sound(
                self.bomb_sound
            )

            self.end_game(
                "You sliced a bomb!"
            )

        # --------------------------------------------------
        # Normal fruit
        # --------------------------------------------------

        else:

            self.score += 1

            self.play_sound(
                self.slice_sound
            )

    # ======================================================
    # INPUT
    # ======================================================

    def handle_input(self):
        # Game is mouse-controlled.
        pass

    # ======================================================
    # UPDATE
    # ======================================================

    def update(self):

        if self.game_over:
            return

        # --------------------------------------------------
        # Spawn fruits
        # --------------------------------------------------

        self._spawn_timer += 1

        if self._spawn_timer >= self.spawn_interval:

            self._spawn_timer = 0

            self.spawn_fruit()

        # --------------------------------------------------
        # Update fruits
        # --------------------------------------------------

        still_alive = []

        for fruit in self.fruits:

            fruit.update()

            # Sliced fruit/bomb is removed.
            if fruit.sliced:
                continue

            # --------------------------------------------------
            # Fruit missed
            # --------------------------------------------------

            if fruit.off_screen(self.height):

                if fruit.kind == "fruit":

                    self.lives -= 1

                continue

            still_alive.append(fruit)

        self.fruits = still_alive

        # --------------------------------------------------
        # Game over if no lives remain
        # --------------------------------------------------

        if self.lives <= 0:

            self.end_game(
                "You ran out of lives!"
            )

    # ======================================================
    # GAME OVER
    # ======================================================

    def end_game(self, reason):

        if self.game_over:
            return

        self.game_over = True
        self.game_over_reason = reason

        self.play_sound(
            self.game_over_sound
        )

    # ======================================================
    # RENDER
    # ======================================================

    def render(self, screen):

        # --------------------------------------------------
        # Game Over screen
        # --------------------------------------------------

        if self.game_over:

            screen.fill(BLACK)

            title = self.large_font.render(
                "GAME OVER",
                True,
                RED
            )

            score = self.medium_font.render(
                f"Final Score: {self.score}",
                True,
                WHITE
            )

            reason = self.small_font.render(
                self.game_over_reason,
                True,
                WHITE
            )

            difficulty = self.small_font.render(
                f"Difficulty: {self.difficulty}",
                True,
                WHITE
            )

            replay = self.small_font.render(
                "1: Easy    2: Medium    3: Hard",
                True,
                YELLOW
            )

            exit_text = self.small_font.render(
                "Press ESC to exit",
                True,
                WHITE
            )

            screen.blit(
                title,
                title.get_rect(
                    center=(
                        self.width // 2,
                        150
                    )
                )
            )

            screen.blit(
                score,
                score.get_rect(
                    center=(
                        self.width // 2,
                        230
                    )
                )
            )

            screen.blit(
                reason,
                reason.get_rect(
                    center=(
                        self.width // 2,
                        290
                    )
                )
            )

            screen.blit(
                difficulty,
                difficulty.get_rect(
                    center=(
                        self.width // 2,
                        330
                    )
                )
            )

            screen.blit(
                replay,
                replay.get_rect(
                    center=(
                        self.width // 2,
                        420
                    )
                )
            )

            screen.blit(
                exit_text,
                exit_text.get_rect(
                    center=(
                        self.width // 2,
                        470
                    )
                )
            )

            return

        # --------------------------------------------------
        # Normal game
        # --------------------------------------------------

        screen.fill(DARK_BLUE)

        # --------------------------------------------------
        # Fruits
        # --------------------------------------------------

        for fruit in self.fruits:

            color = getattr(
                fruit,
                "color",
                WHITE
            )

            pygame.draw.circle(
                screen,
                color,
                (
                    int(fruit.x),
                    int(fruit.y)
                ),
                fruit.radius
            )

        # --------------------------------------------------
        # Blade trail
        # --------------------------------------------------

        if len(self.trail) >= 2:

            pygame.draw.lines(
                screen,
                WHITE,
                False,
                self.trail,
                3
            )

        # --------------------------------------------------
        # Score
        # --------------------------------------------------

        score_text = self.font.render(
            f"Score: {self.score}",
            True,
            WHITE
        )

        screen.blit(
            score_text,
            (10, 10)
        )

        # --------------------------------------------------
        # Lives
        # --------------------------------------------------

        lives_text = self.font.render(
            f"Lives: {self.lives}",
            True,
            WHITE
        )

        screen.blit(
            lives_text,
            (
                self.width - 130,
                10
            )
        )

        # --------------------------------------------------
        # Difficulty
        # --------------------------------------------------

        difficulty_text = self.small_font.render(
            f"Difficulty: {self.difficulty}",
            True,
            WHITE
        )

        screen.blit(
            difficulty_text,
            (10, 45)
        )
