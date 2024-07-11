import pygame
from pygame import Vector2 as vector

from src.GUI.base_classes import GeneralMenu
from src.GUI.descriptions import KeybindsDescription, VolumeDescription
from src.enums import GameState


class SettingsMenu(GeneralMenu):
    def __init__(self, switch_screen, sounds):
        options = ['Keybinds', 'Volume', 'Back']
        background = pygame.image.load('images/menu_background/bg.png')
        title = 'Settings'
        size = (400, 400)
        super().__init__(title, options, switch_screen, size, background)

        # rect
        self.setup()

        # description
        description_pos = self.rect.topright + vector(100, 0)
        self.keybinds_description = KeybindsDescription(description_pos)
        self.volume_description = VolumeDescription(description_pos, sounds)

        self.current_description = self.keybinds_description

    # setup
    def button_action(self, text):
        if text == 'Keybinds':
            self.current_description = self.keybinds_description
        if text == 'Volume':
            self.current_description = self.volume_description
        if text == 'Back':
            self.keybinds_description.save_data()
            self.volume_description.save_data()
            self.switch_screen(GameState.PAUSE)

    def setup(self):
        offset = vector(-350, 0)
        self.rect.topleft += offset
        for button in self.buttons:
            button.offset = vector(self.rect.topleft)

    # events
    def handle_events(self, event):
        self.current_description.handle_events(event)
        self.echap(event)

    def echap(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.switch_screen(GameState.PAUSE)

    # draw
    def draw(self):
        self.draw_background()
        self.draw_title()
        self.draw_buttons()
        self.current_description.draw()
