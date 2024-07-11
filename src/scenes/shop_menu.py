import pygame

from src.GUI.base_classes import GeneralMenu
from src.enums import GameState


class ShopMenu(GeneralMenu):
    def __init__(self, player, switch_screen):
        options = ['wood', 'apple', 'hoe', 'water', 'corn', 'tomato', 'seed']
        background = pygame.image.load('images/menu_background/bg.png')
        title = 'Shop'
        size = (400, 400)
        super().__init__(title, options, switch_screen, size, background)

    def button_action(self, text):
        self.switch_screen(GameState.PAUSE)
