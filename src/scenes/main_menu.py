import pygame

from src.GUI.base_classes import GeneralMenu
from src.enums import GameState


class MainMenu(GeneralMenu):
    def __init__(self, switch_screen):
        options = ['Play', 'Quit']
        background = pygame.image.load('images/menu_background/bg.png')
        title = 'Main Menu'
        size = (400, 400)
        super().__init__(title, options, switch_screen, size, background)

    def button_action(self, text):
        if text == 'Play':
            self.switch_screen(GameState.LEVEL)
        if text == 'Quit':
            self.quit_game()

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.quit_game()
            if event.key == pygame.K_RETURN:
                self.switch_screen(GameState.LEVEL)
