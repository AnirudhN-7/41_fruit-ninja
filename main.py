import pygame

from game.game_engine import GameEngine


# --------------------------------------------------
# Initialize pygame
# --------------------------------------------------

pygame.init()


# --------------------------------------------------
# Screen dimensions
# --------------------------------------------------

WIDTH, HEIGHT = 700, 600

SCREEN = pygame.display.set_mode(
    (WIDTH, HEIGHT)
)

pygame.display.set_caption(
    "Fruit Slice - Pygame Version"
)


# --------------------------------------------------
# Clock
# --------------------------------------------------

clock = pygame.time.Clock()

FPS = 60


# --------------------------------------------------
# Game engine
# --------------------------------------------------

engine = GameEngine(
    WIDTH,
    HEIGHT
)


# --------------------------------------------------
# Main game loop
# --------------------------------------------------

def main():

    running = True

    while running:

        for event in pygame.event.get():

            # Window close
            if event.type == pygame.QUIT:
                running = False

            else:
                engine.handle_event(event)

        # --------------------------------------------------
        # Check for ESC from Game Over screen
        # --------------------------------------------------

        if engine.exit_requested:
            running = False
            continue

        # --------------------------------------------------
        # Normal game processing
        # --------------------------------------------------

        engine.handle_input()

        engine.update()

        engine.render(SCREEN)

        pygame.display.flip()

        clock.tick(FPS)

    pygame.quit()


# --------------------------------------------------
# Start program
# --------------------------------------------------

if __name__ == "__main__":
    main()
