import pygame
import random
import sqlite3
from shop import Shop


class SnakeGame:
    def __init__(self):
        self.setup_display()
        self.setup_colors()
        self.setup_game()
        self.shop = Shop()

    def setup_display(self):
        self.DIS_WIDTH = 1920
        self.DIS_HEIGHT = 1080
        self.dis = pygame.display.set_mode((self.DIS_WIDTH, self.DIS_HEIGHT))
        pygame.display.set_caption('Змейка v2.0')
        pygame.mouse.set_visible(False)

        self.SNAKE_BLOCK = 30
        self.FONT_SIZE = 20
        self.FONT_STYLE = pygame.font.SysFont("arial", self.FONT_SIZE)

    def setup_colors(self):
        self.BLACK = (0, 0, 0)
        self.RED = (213, 50, 80)
        self.GREEN = (0, 255, 0)
        self.YELLOW = (255, 255, 0)
        self.GRAY_OVERLAY = (50, 50, 50, 150)

    def setup_game(self):
        self.reset_game()
        self.slow_mode = True
        self.setup_database()
        self.golden_apples_eaten = 0
        self.score_multiplier = 1.0
        self.red_apples_eaten = 0
        self.shrink_chance = 0

    def setup_database(self):
        self.conn = sqlite3.connect('saves.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS saves
                         (score REAL)''')
        self.conn.commit()

    def reset_game(self):
        self.snake = [(self.DIS_WIDTH // 2, self.DIS_HEIGHT // 2)]
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
        while True:
            self.food_pos = (
                random.randrange(0, self.DIS_WIDTH - self.SNAKE_BLOCK, self.SNAKE_BLOCK),
                random.randrange(0, self.DIS_HEIGHT - self.SNAKE_BLOCK, self.SNAKE_BLOCK)
            )
            if self.food_pos not in self.snake:
                break

    def generate_safe_point(self):
        if self.red_apples_eaten > 0 and self.red_apples_eaten % 30 == 0 and self.safe_point is None:
            while True:
                self.safe_point = (
                    random.randrange(0, self.DIS_WIDTH - self.SNAKE_BLOCK, self.SNAKE_BLOCK),
                    random.randrange(0, self.DIS_HEIGHT - self.SNAKE_BLOCK, self.SNAKE_BLOCK)
                )
                if self.safe_point not in self.snake and self.safe_point != self.food_pos:
                    return True
        return False

    def save_score(self):
        self.c.execute("INSERT INTO saves VALUES (?)", (self.score,))
        self.conn.commit()
        self.safe_point = None

    def move(self):
        if self.game_over or self.in_shop:
            return

        self.direction = self.next_direction

        head_x, head_y = self.snake[0]

        if self.direction == "UP":
            new_head = (head_x, head_y - self.SNAKE_BLOCK)
        elif self.direction == "DOWN":
            new_head = (head_x, head_y + self.SNAKE_BLOCK)
        elif self.direction == "LEFT":
            new_head = (head_x - self.SNAKE_BLOCK, head_y)
        elif self.direction == "RIGHT":
            new_head = (head_x + self.SNAKE_BLOCK, head_y)

        # Порталы на краях
        if new_head[0] < 0:
            new_head = (self.DIS_WIDTH - self.SNAKE_BLOCK, new_head[1])
        elif new_head[0] >= self.DIS_WIDTH:
            new_head = (0, new_head[1])
        elif new_head[1] < 0:
            new_head = (new_head[0], self.DIS_HEIGHT - self.SNAKE_BLOCK)
        elif new_head[1] >= self.DIS_HEIGHT:
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

            # Применяем эффект предмета
            if random.random() >= self.shrink_chance:
                self.snake.append(self.snake[-1])

            self.generate_food()
            self.generate_safe_point()
        elif self.safe_point and new_head == self.safe_point:
            self.save_score()
            self.golden_apples_eaten += 1
            self.score_multiplier = 1.0 + 0.5 * self.golden_apples_eaten
            self.safe_point = None
        else:
            self.snake.pop()

    def draw_fps_indicator(self):
        size = 15
        x_pos = self.DIS_WIDTH - 40

        if self.slow_mode and not self.game_over:
            pygame.draw.rect(self.dis, self.RED, [x_pos, 20, size, size])

        if not self.slow_mode and not self.game_over:
            if pygame.time.get_ticks() % 1000 < 500:
                pygame.draw.rect(self.dis, self.GREEN, [x_pos, 20, size, size])

    def draw(self):
        self.dis.fill(self.BLACK)
        self.draw_fps_indicator()

        pygame.draw.rect(self.dis, self.RED, [self.food_pos[0], self.food_pos[1], self.SNAKE_BLOCK, self.SNAKE_BLOCK])
        if self.safe_point:
            pygame.draw.rect(self.dis, self.YELLOW,
                             [self.safe_point[0], self.safe_point[1], self.SNAKE_BLOCK, self.SNAKE_BLOCK])

        for segment in self.snake:
            pygame.draw.rect(self.dis, self.GREEN, [segment[0], segment[1], self.SNAKE_BLOCK, self.SNAKE_BLOCK])

        self.show_score()

        if self.slow_mode and not self.game_over:
            self.draw_pause_screen()

        if self.game_over:
            self.draw_game_over()

        if self.in_shop:
            self.shop.draw(self.dis, self.FONT_STYLE, self.DIS_WIDTH, self.DIS_HEIGHT)

        pygame.display.update()

    def show_score(self):
        score_text = self.FONT_STYLE.render(
            f"Очки: {self.score} (x{self.score_multiplier:.1f})",
            True,
            self.GREEN
        )
        self.dis.blit(score_text, [20, 20])

        # Длина змейки
        length_text = self.FONT_STYLE.render(
            f"Длина: {len(self.snake)}",
            True,
            self.GREEN
        )
        self.dis.blit(length_text, [20, 50])

    def draw_pause_screen(self):
        overlay = pygame.Surface((self.DIS_WIDTH, self.DIS_HEIGHT), pygame.SRCALPHA)
        overlay.fill(self.GRAY_OVERLAY)
        self.dis.blit(overlay, (0, 0))

        texts = [
            "SPACE - Продолжить",
            "TAB - Магазин",
            "ESC - Выход"
        ]

        for i, text in enumerate(texts):
            text_surface = self.FONT_STYLE.render(text, True, self.GREEN)
            self.dis.blit(text_surface,
                          [self.DIS_WIDTH // 2 - text_surface.get_width() // 2,
                           self.DIS_HEIGHT - 150 + i * 40])

    def draw_game_over(self):
        overlay = pygame.Surface((self.DIS_WIDTH, self.DIS_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.dis.blit(overlay, (0, 0))

        texts = [
            f"Игра окончена! Очки: {self.score:.1f}",
            "R - рестарт",
            "TAB - магазин",
            "ESC - выход"
        ]
        colors = [self.GREEN, self.GREEN, (255, 215, 0), self.RED]

        for i, (text, color) in enumerate(zip(texts, colors)):
            text_surface = self.FONT_STYLE.render(text, True, color)
            self.dis.blit(text_surface,
                          [self.DIS_WIDTH // 2 - text_surface.get_width() // 2,
                           self.DIS_HEIGHT // 2 - 80 + i * 40])

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if self.in_shop:
                # Передаем все события в магазин, если он открыт
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

        # Обработка непрерывного ввода для змейки (только вне магазина)
        if not self.in_shop and not self.game_over and not self.slow_mode:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w] and self.direction != "DOWN":
                self.next_direction = "UP"
            elif keys[pygame.K_s] and self.direction != "UP":
                self.next_direction = "DOWN"
            elif keys[pygame.K_a] and self.direction != "RIGHT":
                self.next_direction = "LEFT"
            elif keys[pygame.K_d] and self.direction != "LEFT":
                self.next_direction = "RIGHT"

        return True

    def run(self):
        clock = pygame.time.Clock()
        running = True

        while running:
            running = self.handle_events()

            if not self.in_shop:
                self.move()

            self.draw()
            clock.tick(2 if self.slow_mode and not self.game_over else 9)

        pygame.quit()
        self.conn.close()


if __name__ == "__main__":
    game = SnakeGame()
    game.run()