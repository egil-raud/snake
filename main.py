import pygame
from game import SnakeGame

def main():
    pygame.init()
    game = SnakeGame()
    game.run()

if __name__ == "__main__":
    main()