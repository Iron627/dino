import copy
import math
import random
import neat
import pygame


WIDTH, HEIGHT = 854, 480
GROUND_Y = 410
FPS = 60
draw = 1
best_play = 0
POPULATION_SIZE = 50
PTERODACTYL_START_SCORE = 500
MIN_OBSTACLE_GAP = 230

BLACK = (0, 0, 0)
WHITE = (245, 245, 245)
GREEN = (0, 220, 80)
RED = (230, 60, 45)
GRAY = (80, 80, 80)
DARK_GRAY = (40, 40, 40)


class Dino:
    def __init__(self):
        self.neuron = neat.NEAT(10,3)
        self.color = (
            random.randint(60, 255),
            random.randint(60, 255),
            random.randint(60, 255),
        )
        self.is_ducking = False
        self.rect = pygame.Rect(60, GROUND_Y - 50, 48, 50)
        self.velocity_y = 0
        self.on_ground = True
        self.alive = True
        self.fitness = 0

    def jump(self):
        if self.on_ground and not self.is_ducking:
            self.velocity_y = -18
            self.on_ground = False
    def update(self):
        self.velocity_y += 1
        self.rect.y += self.velocity_y

        if self.rect.bottom >= GROUND_Y:
            self.rect.bottom = GROUND_Y
            self.velocity_y = 0
            self.on_ground = True
        if self.on_ground:
            target_height = 30 if self.is_ducking else 50
            self.rect.height = target_height
            self.rect.bottom = GROUND_Y
            

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)

    def get_inputs(self, game):
        obstacles = sorted(
            [o for o in (game.cacti + game.pterodactyls) if o.rect.right >= self.rect.left],
            key=lambda obstacle: obstacle.rect.x,
        )

        next_obstacle = obstacles[0] if obstacles else None
        second_obstacle = obstacles[1] if len(obstacles) > 1 else None

        if next_obstacle is None:
            next_distance = WIDTH
            next_width = 0
            next_height = 0
            next_y = GROUND_Y
            is_pterodactyl = 0.0
        else:
            next_distance = max(0, next_obstacle.rect.x - self.rect.x)
            next_width = next_obstacle.rect.width
            next_height = next_obstacle.rect.height
            next_y = next_obstacle.rect.y
            is_pterodactyl = 1.0 if isinstance(next_obstacle, Pterodactyl) else 0.0

        if second_obstacle is None:
            second_distance = WIDTH
        else:
            second_distance = max(0, second_obstacle.rect.x - self.rect.x)

        dino_ground_distance = GROUND_Y - self.rect.bottom
        velocity_y = max(-20, min(20, self.velocity_y))

        return [
            dino_ground_distance / HEIGHT,
            velocity_y / 20,
            1.0 if self.is_ducking else 0.0,
            min(1.0, next_distance / WIDTH),
            next_width / WIDTH,
            next_height / HEIGHT,
            next_y / HEIGHT,
            is_pterodactyl,
            min(1.0, second_distance / WIDTH),
            min(1.0, game.speed / 20),
        ]


class Cactus:
    def __init__(self):
        width = random.choice([22, 44, 66])
        height = random.choice([38, 50, 62])
        self.rect = pygame.Rect(WIDTH, GROUND_Y - height, width, height)

    def update(self, speed):
        self.rect.x -= speed

    def draw(self, screen):
        pygame.draw.rect(screen, RED, self.rect)
class Pterodactyl(Cactus):
    def __init__(self):
        width = 46
        height = 30
        y_pos = GROUND_Y - 60
        self.rect = pygame.Rect(WIDTH, y_pos, width, height)

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 165, 0), self.rect)

class Game:
    def __init__(self):
        pygame.init()
        self.population = neat.Population(
            Dino,
            POPULATION_SIZE,
            genome_saver=neat.save_best_genome,
        )
        self.dinos = self.population.agents
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Dino")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.button_font = pygame.font.Font(None, 28)
        self.best_score = 0
        self.manual_save_status = "No completed generation yet"
        self.best_play_status = ""
        self.manual_save_button = pygame.Rect(WIDTH - 250, 20, 230, 42)
        self.training_state = None
        self.initialized = False
        self.reset()

    def reset(self, record_completed=True):
        if best_play:
            self.dinos = [Dino()]
            self.reset_world()
            self.load_best_genome(self.dinos[0])
            return

        if not self.initialized:
            self.reset_world()
            self.initialized = True
            return

        score_achieved = self.display_score()
        self.population.evolve(score_achieved, record_completed=record_completed)
        self.dinos = self.population.agents
        self.manual_save_status = (
            f"Ready: gen {self.population.latest_completed_generation}, score {self.population.latest_completed_score}"
            if self.population.latest_completed_top_genome is not None and record_completed else self.manual_save_status
        )
        self.reset_world()

    def reset_world(self):
        self.cacti = []
        self.pterodactyls = []
        self.score = 0
        self.speed = 7
        self.cactus_spawn_timer = 80
        self.pterodactyl_spawn_timer = 120
        self.game_over = False

    def save_training_state(self):
        self.training_state = {
            "cacti": copy.deepcopy(self.cacti),
            "pterodactyls": copy.deepcopy(self.pterodactyls),
            "score": self.score,
            "speed": self.speed,
            "cactus_spawn_timer": self.cactus_spawn_timer,
            "pterodactyl_spawn_timer": self.pterodactyl_spawn_timer,
            "game_over": self.game_over,
            "best_score": self.best_score,
            "population": copy.deepcopy(self.population),
            "manual_save_status": self.manual_save_status,
        }

    def restore_training_state(self):
        if self.training_state is None:
            self.reset(record_completed=False)
            return

        self.cacti = self.training_state["cacti"]
        self.pterodactyls = self.training_state["pterodactyls"]
        self.score = self.training_state["score"]
        self.speed = self.training_state["speed"]
        self.cactus_spawn_timer = self.training_state["cactus_spawn_timer"]
        self.pterodactyl_spawn_timer = self.training_state["pterodactyl_spawn_timer"]
        self.game_over = self.training_state["game_over"]
        self.best_score = self.training_state["best_score"]
        self.population = self.training_state["population"]
        self.dinos = self.population.agents
        self.manual_save_status = self.training_state["manual_save_status"]
        self.training_state = None

    def toggle_best_play(self):
        global best_play
        if best_play:
            best_play = False
            self.restore_training_state()
            return

        self.save_training_state()
        best_play = True
        self.reset(record_completed=False)

    def save_manual_genome(self):
        if self.population.latest_completed_top_genome is None:
            self.manual_save_status = "No completed generation yet"
            return

        saved = neat.save_manual_genome(
            self.population.latest_completed_top_genome,
            self.population.latest_completed_generation,
            self.population.latest_completed_score,
        )
        if not saved:
            self.manual_save_status = f"Already saved gen {self.population.latest_completed_generation}"
            return

        self.manual_save_status = f"Saved gen {self.population.latest_completed_generation}"

    def load_best_genome(self, dino):
        global best_play
        try:
            dino.neuron.genome = neat.load_best_genome()
            self.best_play_status = "Best genome loaded"
        except FileNotFoundError:
            self.best_play_status = "No best genome found"
            best_play = False
            self.restore_training_state()

    def dino_outputs(self, dino):
        inputs = dino.get_inputs(self)
        values = {}
        for i, value in enumerate(inputs):
            values[i] = value
        values[dino.neuron.bias_id] = 1

        for node in dino.neuron.topological_sort():
            if dino.neuron.nodes[node] in ["bias", "input"]:
                continue
            total = 0
            for connection in dino.neuron.connections:
                if connection["out"] == node and connection["enabled"]:
                    total += values.get(connection["in"], 0) * connection["weight"]
            values[node] = math.tanh(total)

        return [values.get(output_id, 0) for output_id in dino.neuron.output_ids]

    def update_dino_action(self, dino):
        outputs = self.dino_outputs(dino)
        action = outputs.index(max(outputs))
        dino.is_ducking = action == 2 and dino.on_ground
        if action == 1:
            dino.jump()

    def update(self):
        if self.game_over:
            return

        alive_dinos = [dino for dino in self.dinos if dino.alive]

        for dino in alive_dinos:
            self.update_dino_action(dino)
            dino.update()
            dino.fitness += 1

        self.cactus_spawn_timer -= 1

        if self.display_score() >= PTERODACTYL_START_SCORE:
            self.pterodactyl_spawn_timer -= 1

        if self.cactus_spawn_timer <= 0 and self.has_spawn_gap():
            self.cacti.append(Cactus())
            self.cactus_spawn_timer = self.spawn_delay(55, 100)

        if self.pterodactyl_spawn_timer <= 0 and self.has_spawn_gap():
            self.pterodactyls.append(Pterodactyl())
            self.pterodactyl_spawn_timer = self.spawn_delay(120, 180)

        for cactus in self.cacti:
            cactus.update(self.speed)

            for dino in alive_dinos:
                if dino.alive and dino.rect.colliderect(cactus.rect):
                    dino.alive = False

        for pterodactyl in self.pterodactyls:
            pterodactyl.update(self.speed + 4)

            for dino in alive_dinos:
                if dino.alive and dino.rect.colliderect(pterodactyl.rect):
                    dino.alive = False

        self.cacti = [cactus for cactus in self.cacti if cactus.rect.right > 0]
        self.pterodactyls = [pterodactyl for pterodactyl in self.pterodactyls if pterodactyl.rect.right > 0]
        self.score += 1
        self.best_score = max(self.best_score, self.display_score())
        self.speed = 7 + self.score // 600

        self.population.update_best_fitness()
        self.game_over = not any(dino.alive for dino in self.dinos)
        if self.game_over:
            self.reset()

    def display_score(self):
        return self.score // 10

    def spawn_delay(self, low, high):
        speed_bonus = (self.speed - 7) * 4
        low = max(18, low - speed_bonus)
        high = max(low + 10, high - speed_bonus)
        return random.randint(low, high)

    def has_spawn_gap(self):
        obstacles = self.cacti + self.pterodactyls
        if not obstacles:
            return True

        newest_obstacle = max(obstacles, key=lambda obstacle: obstacle.rect.x)
        return newest_obstacle.rect.x < WIDTH - MIN_OBSTACLE_GAP

    def draw(self):
        self.screen.fill(BLACK)
        pygame.draw.line(self.screen, WHITE, (0, GROUND_Y), (WIDTH, GROUND_Y), 2)

        if draw:
            for cactus in self.cacti:
                cactus.draw(self.screen)

            for pterodactyl in self.pterodactyls:
                pterodactyl.draw(self.screen)

            for dino in self.dinos:
                if dino.alive:
                    dino.draw(self.screen)

        draw_text(self.screen, self.font, f"Score: {self.display_score()}", 20, 20)
        draw_text(self.screen, self.font, f"Speed: {self.speed}", 20, 55)

        if best_play:
            draw_text(self.screen, self.font, "BEST GENOME PLAY", 20, 90)
            draw_text(self.screen, self.button_font, self.best_play_status, 20, 125)
        else:
            alive_count = sum(dino.alive for dino in self.dinos)
            labels = [
                f"Alive: {alive_count} Generation: {self.population.generation}",
                f"Best Score: {self.best_score}",
                f"Average Score: {self.population.average_score():.2f}",
                f"Best Fitness: {self.population.best_fitness}",
                "",
            ]
            for i, label in enumerate(labels):
                draw_text(self.screen, self.font, label, 20, 90 + i * 35)
            self.draw_manual_save_button()

        pygame.display.flip()

    def draw_manual_save_button(self):
        button_color = GRAY if self.population.latest_completed_top_genome else DARK_GRAY
        pygame.draw.rect(self.screen, button_color, self.manual_save_button, border_radius=8)
        pygame.draw.rect(self.screen, WHITE, self.manual_save_button, 2, border_radius=8)

        label = self.button_font.render("Save Top Dino", True, WHITE)
        label_rect = label.get_rect(center=self.manual_save_button.center)
        self.screen.blit(label, label_rect)

        status = self.button_font.render(self.manual_save_status, True, WHITE)
        self.screen.blit(status, (self.manual_save_button.x, self.manual_save_button.bottom + 8))

    def run(self):
        while True:
            self.events()
            if not self.game_over:
                self.update()
            self.draw()
            if FPS > 0:
                self.clock.tick(FPS)

    def events(self):
        global FPS, draw, best_play
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not best_play:
                if self.manual_save_button.collidepoint(event.pos):
                    self.save_manual_genome()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                if event.key == pygame.K_c:
                    FPS = 0 if FPS else 60
                if event.key == pygame.K_d:
                    draw = not draw
                if event.key == pygame.K_b:
                    self.toggle_best_play()

    def quit(self):
        pygame.quit()
        raise SystemExit


def draw_text(screen, font, text, x, y):
    image = font.render(text, True, WHITE)
    screen.blit(image, (x, y))


def main():
    Game().run()


if __name__ == "__main__":
    main()
