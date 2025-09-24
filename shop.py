import pygame
from database import DatabaseManager
from constants import ITEM_SIZE, GRID_COLS, GRID_ROWS, GOLD

class Shop:
    def __init__(self):
        self.db = DatabaseManager()
        self.item_size = ITEM_SIZE
        self.setup_items()
        self.load_purchased_items()
        self.selected_index = 0
        self.grid_cols = GRID_COLS
        self.grid_rows = GRID_ROWS
        self.font = pygame.font.SysFont("arial", 20)
        self.cached_texts = {
            "title": self.font.render("МАГАЗИН", True, GOLD),
            "hint": self.font.render("WASD - выбор, SPACE - купить, TAB - выход", True, (200, 200, 200))
        }

    def load_purchased_items(self):
        purchased_ids = self.db.load_purchased_items()
        for item in self.items:
            if item["id"] in purchased_ids:
                item["purchased"] = True

    def setup_items(self):
        self.items = [
            {
                "id": 1,
                "color": (213, 50, 80),
                "price": 100,
                "name": "Случайное сжатие",
                "description": "20% шанс не увеличиваться\nпри поедании красных яблок",
                "effect": "shrink_chance",
                "purchased": False
            }
        ]
        self.items += [
            {
                "id": i,
                "color": (255, 255, 0),
                "price": 50,
                "name": f"Предмет {i}",
                "description": "Эффект не реализован",
                "purchased": False
            } for i in range(2, 11)
        ]

    def get_total_saves(self):
        return self.db.get_total_saves()

    def handle_event(self, event, game):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                game.in_shop = False
                return True
            if event.key == pygame.K_w and self.selected_index >= self.grid_cols:
                self.selected_index -= self.grid_cols
            elif event.key == pygame.K_s and self.selected_index < len(self.items) - self.grid_cols:
                self.selected_index += self.grid_cols
            elif event.key == pygame.K_a and self.selected_index > 0:
                self.selected_index -= 1
            elif event.key == pygame.K_d and self.selected_index < len(self.items) - 1:
                self.selected_index += 1
            elif event.key == pygame.K_SPACE:
                self.buy_item(game)
        return False

    def buy_item(self, game):
        item = self.items[self.selected_index]
        if item["purchased"]:
            return
        if self.get_total_saves() >= item["price"]:
            self.db.deduct_score(item["price"])
            self.db.purchase_item(item["id"], item.get("effect", ""))
            item["purchased"] = True
            if item["id"] == 1:
                game.shrink_chance = 0.2

    def draw(self, surface, font, width, height):
        self.draw_background(surface, width, height)
        self.draw_title(surface, width)
        self.draw_balance(surface, width)
        self.draw_item_grid(surface, width, height)
        self.draw_item_info(surface, font, width, height)
        self.draw_hint(surface, width, height)

    def draw_background(self, surface, width, height):
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        surface.blit(overlay, (0, 0))

    def draw_title(self, surface, width):
        surface.blit(self.cached_texts["title"], [width // 2 - self.cached_texts["title"].get_width() // 2, 30])

    def draw_balance(self, surface, width):
        balance = self.font.render(f"Баланс: {self.get_total_saves():.1f}", True, (255, 255, 255))
        surface.blit(balance, [width // 2 - balance.get_width() // 2, 70])

    def draw_item_grid(self, surface, width, height):
        grid_width = self.grid_cols * (self.item_size + 20)
        start_x = width // 2 - grid_width // 2
        start_y = 150
        for i, item in enumerate(self.items):
            row = i // self.grid_cols
            col = i % self.grid_cols
            x = start_x + col * (self.item_size + 20)
            y = start_y + row * (self.item_size + 20)
            color = (0, 255, 0) if item["purchased"] else item["color"]
            pygame.draw.rect(surface, color, [x, y, self.item_size, self.item_size])
            if i == self.selected_index:
                pygame.draw.rect(surface, (255, 255, 255), [x - 3, y - 3, self.item_size + 6, self.item_size + 6], 3)
            price_text = self.font.render(str(item["price"]), True, (0, 0, 0))
            surface.blit(price_text, [x + 5, y + 5])

    def draw_item_info(self, surface, font, width, height):
        item = self.items[self.selected_index]
        panel_width = 400
        panel_height = 150
        x = width // 2 - panel_width // 2
        y = height - 220
        pygame.draw.rect(surface, (40, 40, 40), [x, y, panel_width, panel_height])
        pygame.draw.rect(surface, (100, 100, 100), [x, y, panel_width, panel_height], 2)
        name = font.render(item["name"], True, (255, 255, 255))
        price = font.render(f"Цена: {item['price']}", True, (200, 200, 100))
        surface.blit(name, [x + 20, y + 20])
        surface.blit(price, [x + 20, y + 50])
        desc_lines = item["description"].split('\n')
        for i, line in enumerate(desc_lines):
            desc = font.render(line, True, (200, 200, 200))
            surface.blit(desc, [x + 20, y + 80 + i * 30])

    def draw_hint(self, surface, width, height):
        surface.blit(self.cached_texts["hint"], [width // 2 - self.cached_texts["hint"].get_width() // 2, height - 50])