import random
import sys

import pygame


WIDTH, HEIGHT = 854, 480
GROUND_Y = 410
FPS = 60

BLACK = (0, 0, 0)
WHITE = (245, 245, 245)
GREEN = (0, 220, 80)
RED = (230, 60, 45)


class Dino:
    def __init__(self):
        self.rect = pygame.Rect(60, GROUND_Y - 50, 48, 50)
        self.velocity_y = 0
        self.on_ground = True

    def jump(self):
        if self.on_ground:
            self.velocity_y = -18
            self.on_ground = False

    def update(self):
        self.velocity_y += 1
        self.rect.y += self.velocity_y

        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.velocity_y = 0
            self.on_ground = True

    def draw(self, screen):
        pygame.draw.rect(screen, GREEN, self.rect)


class Cactus:
    def __init__(self):
        width = random.choice([22, 34, 46])
        height = random.choice([38, 50, 62])
        self.rect = pygame.Rect(WIDTH, GROUND_Y - height, width, height)

    def update(self, speed):
        self.rect.x -= speed

    def draw(self, screen):
        pygame.draw.rect(screen, RED, self.rect)


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.dino = Dino()
        self.cacti = []
        self.score = 0
        self.speed = 7
        self.spawn_timer = 80
        self.game_over = False

    def jump_or_restart(self):
        if self.game_over:
            self.reset()
        else:
            self.dino.jump()

    def update(self):
        if self.game_over:
            return

        self.dino.update()
        self.spawn_timer -= 1

        if self.spawn_timer <= 0:
            self.cacti.append(Cactus())
            self.spawn_timer = random.randint(55, 100)

        for cactus in self.cacti:
            cactus.update(self.speed)

            if self.dino.rect.colliderect(cactus.rect):
                self.game_over = True

        self.cacti = [cactus for cactus in self.cacti if cactus.rect.right > 0]
        self.score += 1
        self.speed = 7 + self.score // 600

    def draw(self, screen, font):
        screen.fill(BLACK)
        pygame.draw.line(screen, WHITE, (0, GROUND_Y), (WIDTH, GROUND_Y), 2)
        self.dino.draw(screen)

        for cactus in self.cacti:
            cactus.draw(screen)

        draw_text(screen, font, f"Score: {self.score // 10}", 20, 20)

        if self.game_over:
            draw_text(screen, font, "Game Over - press SPACE", WIDTH // 2 - 160, HEIGHT // 2)


def draw_text(screen, font, text, x, y):
    image = font.render(text, True, WHITE)
    screen.blit(image, (x, y))


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Simple Dino")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)

    game = Game()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    game.jump_or_restart()

        game.update()
        game.draw(screen, font)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
