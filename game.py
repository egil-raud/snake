import pygame
import random
from shop import Shop
from constants import DIS_WIDTH, DIS_HEIGHT, SNAKE_BLOCK, FONT_SIZE, BLACK, RED, GREEN, YELLOW, GRAY_OVERLAY, GOLD
from database import DatabaseManager


class SnakeGame:
    def __init__(self):
        self.db = DatabaseManager()
        self.setup_display()
        self.setup_game()
        self.shop = Shop()

    def setup_display(self):
        self.dis = pygame.display.set_mode((DIS_WIDTH, DIS_HEIGHT))
        pygame.display.set_caption('Змейка v2.4')
        pygame.mouse.set_visible(False)
        self.FONT_STYLE = pygame.font.SysFont("arial", FONT_SIZE)

    def setup_game(self):
        self.reset_game()
        self.slow_mode = True
        self.golden_apples_eaten = 0
        self.score_multiplier = 1.0
        self.red_apples_eaten = 0
        self.load_effects()

    def load_effects(self):
        self.shrink_chance = 0
        self.db.c.execute("SELECT id, effect FROM purchased_items")
        for item_id, effect in self.db.c.fetchall():
            if item_id == 1 and effect == "shrink_chance":
                self.shrink_chance = 0.2

    def reset_game(self):
        self.snake = [(DIS_WIDTH // 2, DIS_HEIGHT // 2)]
        self.direction = "RIGHT"
        self.next_direction = "RIGHT"
        self.score = 0
        self.game_over = False
        self.in_shop = False
        self.generate_food()
        self.safe_point = None
        self.golden_apples_eaten = 0
        self.score_multiplier = 1.0
        self.red_apples_eaten = 0
        self.shrink_chance = 0

    def generate_food(self):
        snake_set = set(self.snake)
        while True:
            food_pos = (
                random.randrange(0, DIS_WIDTH - SNAKE_BLOCK, SNAKE_BLOCK),
                random.randrange(0, DIS_HEIGHT - SNAKE_BLOCK, SNAKE_BLOCK)
            )
            if food_pos not in snake_set:
                self.food_pos = food_pos
                break

    def generate_safe_point(self):
        if self.red_apples_eaten > 0 and self.red_apples_eaten % 30 == 0 and self.safe_point is None:
            snake_set = set(self.snake)
            while True:
                safe_point = (
                    random.randrange(0, DIS_WIDTH - SNAKE_BLOCK, SNAKE_BLOCK),
                    random.randrange(0, DIS_HEIGHT - SNAKE_BLOCK, SNAKE_BLOCK)
                )
                if safe_point not in snake_set and safe_point != self.food_pos:
                    self.safe_point = safe_point
                    return True
        return False

    def save_score(self):
        self.db.save_score(self.score)
        self.safe_point = None

    def move(self):
        if self.game_over or self.in_shop:
            return

        self.direction = self.next_direction
        head_x, head_y = self.snake[0]

        if self.direction == "UP":
            new_head = (head_x, head_y - SNAKE_BLOCK)
        elif self.direction == "DOWN":
            new_head = (head_x, head_y + SNAKE_BLOCK)
        elif self.direction == "LEFT":
            new_head = (head_x - SNAKE_BLOCK, head_y)
        elif self.direction == "RIGHT":
            new_head = (head_x + SNAKE_BLOCK, head_y)

        # Порталы на краях
        if new_head[0] < 0:
            new_head = (DIS_WIDTH - SNAKE_BLOCK, new_head[1])
        elif new_head[0] >= DIS_WIDTH:
            new_head = (0, new_head[1])
        elif new_head[1] < 0:
            new_head = (new_head[0], DIS_HEIGHT - SNAKE_BLOCK)
        elif new_head[1] >= DIS_HEIGHT:
            new_head = (new_head[0], 0)

        if new_head in self.snake:
            self.game_over = True
            return

        self.snake.insert(0, new_head)

        # Проверка съедения
        if new_head == self.food_pos:
            self.score += self.score_multiplier
            self.score = round(self.score, 1)
            self.red_apples_eaten += 1
            self.generate_food()
            self.generate_safe_point()
            if random.random() < self.shrink_chance:
                self.snake.pop()  # Сжатие с вероятностью
        elif self.safe_point and new_head == self.safe_point:
            self.save_score()
            self.golden_apples_eaten += 1
            self.score_multiplier = 1.0 + 0.5 * self.golden_apples_eaten
            self.safe_point = None
            self.snake.pop()
        else:
            self.snake.pop()

    def draw_fps_indicator(self):
        size = 15
        x_pos = DIS_WIDTH - 40
        if self.slow_mode and not self.game_over:
            pygame.draw.rect(self.dis, RED, [x_pos, 20, size, size])
        elif not self.slow_mode and not self.game_over:
            if pygame.time.get_ticks() % 1000 < 500:
                pygame.draw.rect(self.dis, GREEN, [x_pos, 20, size, size])

    def draw(self):
        self.dis.fill(BLACK)
        self.draw_fps_indicator()
        pygame.draw.rect(self.dis, RED, [self.food_pos[0], self.food_pos[1], SNAKE_BLOCK, SNAKE_BLOCK])
        if self.safe_point:
            pygame.draw.rect(self.dis, YELLOW,
                             [self.safe_point[0], self.safe_point[1], SNAKE_BLOCK, SNAKE_BLOCK])
        for segment in self.snake:
            pygame.draw.rect(self.dis, GREEN, [segment[0], segment[1], SNAKE_BLOCK, SNAKE_BLOCK])
        self.show_score()
        if self.slow_mode and not self.game_over:
            self.draw_pause_screen()
        if self.game_over:
            self.draw_game_over()
        if self.in_shop:
            self.shop.draw(self.dis, self.FONT_STYLE, DIS_WIDTH, DIS_HEIGHT)
        pygame.display.update()

    def show_score(self):
        score_text = self.FONT_STYLE.render(
            f"Очки: {self.score} (x{self.score_multiplier:.1f})",
            True, GREEN
        )
        self.dis.blit(score_text, [20, 20])
        length_text = self.FONT_STYLE.render(
            f"Длина: {len(self.snake)}",
            True, GREEN
        )
        self.dis.blit(length_text, [20, 50])

    def draw_pause_screen(self):
        overlay = pygame.Surface((DIS_WIDTH, DIS_HEIGHT), pygame.SRCALPHA)
        overlay.fill(GRAY_OVERLAY)
        self.dis.blit(overlay, (0, 0))
        texts = ["SPACE - Продолжить", "TAB - Магазин", "ESC - Выход"]
        for i, text in enumerate(texts):
            text_surface = self.FONT_STYLE.render(text, True, GREEN)
            self.dis.blit(text_surface,
                          [DIS_WIDTH // 2 - text_surface.get_width() // 2,
                           DIS_HEIGHT - 150 + i * 40])

    def draw_game_over(self):
        overlay = pygame.Surface((DIS_WIDTH, DIS_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.dis.blit(overlay, (0, 0))
        texts = [
            f"Игра окончена! Очки: {self.score:.1f}",
            "R - рестарт",
            "TAB - магазин",
            "ESC - выход"
        ]
        colors = [GREEN, GREEN, GOLD, RED]
        for i, (text, color) in enumerate(zip(texts, colors)):
            text_surface = self.FONT_STYLE.render(text, True, color)
            self.dis.blit(text_surface,
                          [DIS_WIDTH // 2 - text_surface.get_width() // 2,
                           DIS_HEIGHT // 2 - 80 + i * 40])

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if self.in_shop:
                self.shop.handle_event(event, self)
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_TAB:
                    self.in_shop = True
                    continue
                if event.key == pygame.K_SPACE and not self.game_over:
                    self.slow_mode = not self.slow_mode
                if event.key == pygame.K_r and self.game_over:
                    self.reset_game()
                    self.slow_mode = True
        if not self.in_shop and not self.game_over and not self.slow_mode:
            keys = pygame.key.get_pressed()
            new_direction = self.next_direction
            if keys[pygame.K_w] and self.direction != "DOWN":
                new_direction = "UP"
            elif keys[pygame.K_s] and self.direction != "UP":
                new_direction = "DOWN"
            elif keys[pygame.K_a] and self.direction != "RIGHT":
                new_direction = "LEFT"
            elif keys[pygame.K_d] and self.direction != "LEFT":
                new_direction = "RIGHT"
            self.next_direction = new_direction
        return True

    def run(self):
        clock = pygame.time.Clock()
        running = True
        try:
            while running:
                running = self.handle_events()
                if not self.in_shop and not self.slow_mode and not self.game_over:
                    self.move()
                self.dis.fill(BLACK)  # Очищаем экран перед отрисовкой
                self.draw_fps_indicator()  # Всегда отрисовываем индикатор FPS
                if self.in_shop:
                    self.shop.draw(self.dis, self.FONT_STYLE, DIS_WIDTH, DIS_HEIGHT)
                elif self.slow_mode and not self.game_over:
                    pygame.draw.rect(self.dis, RED, [self.food_pos[0], self.food_pos[1], SNAKE_BLOCK, SNAKE_BLOCK])
                    if self.safe_point:
                        pygame.draw.rect(self.dis, YELLOW,
                                         [self.safe_point[0], self.safe_point[1], SNAKE_BLOCK, SNAKE_BLOCK])
                    for segment in self.snake:
                        pygame.draw.rect(self.dis, GREEN, [segment[0], segment[1], SNAKE_BLOCK, SNAKE_BLOCK])
                    self.show_score()
                    self.draw_pause_screen()
                else:
                    self.draw()
                pygame.display.update()
                clock.tick(9)
        finally:
            self.db.__del__()
            pygame.quit()