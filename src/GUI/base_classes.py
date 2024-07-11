import sys

import pygame

from src.enums import GameState
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from src.GUI.components import Button


# -------  Menu ------- #


class GeneralMenu:
    def __init__(self, title, options, switch_screen, size, background=None):
        # general setup
        self.display_surface = pygame.display.get_surface()
        self.buttons_surface = pygame.Surface(size)
        self.buttons_surface.set_colorkey('green')
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 30)
        self.background = pygame.transform.scale(background, (SCREEN_WIDTH, SCREEN_HEIGHT)) if background else None
        self.title = title

        # rect
        self.size = size
        self.rect = None
        self.rect_setup()

        # buttons
        self.options = options
        self.buttons = []
        self.button_setup()

        # switch
        self.switch_screen = switch_screen

    # setup
    def rect_setup(self):
        self.rect = pygame.Rect((0, 0), self.size)
        self.rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

    def button_setup(self):
        button_width = 400
        button_height = 50
        space = 10
        generic_button_rect = pygame.Rect((0,0), (button_width, button_height))
        for item in self.options:
            button = Button(item, self.font, generic_button_rect, self.rect.topleft)
            self.buttons.append(button)
            generic_button_rect = generic_button_rect.move(0, button_height + space)

    # events
    def event_loop(self):
        self.mouse_hover()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            self.click(event)
            self.handle_events(event)

    def handle_events(self, event):
        pass

    def click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for button in self.buttons:
                if button.hover_active:
                    self.button_action(button.text)
                    pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    def mouse_hover(self):
        for button in self.buttons:
            if button.hover_active:
                pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
                return
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

    def button_action(self, text):
        if text == 'Play':
            self.switch_screen(GameState.LEVEL)
        if text == 'Quit':
            self.quit_game()

    def quit_game(self):
        pygame.quit()
        sys.exit()

    # draw
    def draw_title(self):
        text_surf = self.font.render(self.title, False, 'Black')
        text_rect = text_surf.get_frect(midtop=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 20))

        bg_rect = pygame.Rect((0, 0), (200, 50))
        bg_rect.center = text_rect.center

        pygame.draw.rect(self.display_surface, 'White', bg_rect, 0, 4)
        self.display_surface.blit(text_surf, text_rect)

    def draw_background(self):
        if self.background:
            self.display_surface.blit(self.background, (0, 0))

    def draw_buttons(self):
        self.buttons_surface.fill('green')
        for button in self.buttons:
            button.draw(self.buttons_surface)
        self.display_surface.blit(self.buttons_surface, self.rect.topleft)

    def draw(self):
        self.draw_background()
        self.draw_title()
        self.draw_buttons()

    # update
    def update(self, dt):
        self.event_loop()
        self.draw()


# ------- Description Box ------- #


class Description:
    def __init__(self, pos):
        # surface
        self.display_surface = pygame.display.get_surface()
        self.description_surface = None
        self.description_slider_surface = None

        # rect
        self.rect = pygame.Rect(pos, (600, 400))
        self.setup()

        # font
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 30)

    # setup
    def setup(self):
        # description
        self.description_rect = pygame.Rect(0, 0, 600, 400)
        self.description_rect.topright = self.rect.topright
        self.description_surface = pygame.Surface(self.description_rect.size)
        self.description_surface.set_colorkey('green')

        # slider
        self.description_slider_surface = pygame.Surface((600, 500))
        self.description_slider_rect = self.description_surface.get_rect()
        self.description_slider_surface.set_colorkey('green')

    # events
    def handle_events(self, event):
        self.mouse_wheel(event)

    def mouse_wheel(self, event):
        if event.type == pygame.MOUSEWHEEL:
            speed = 10
            self.description_slider_rect.y += event.y * speed
            self.description_slider_rect.y = min(0, self.description_slider_rect.y)
            self.description_slider_rect.y = max(self.description_surface.height - self.description_slider_surface.height, self.description_slider_rect.y)

    # draw
    def make_surface_transparent(self):
        self.description_surface.fill('green')
        self.description_slider_surface.fill('green')

    def draw_slider_bar(self):
        height1 = self.description_slider_surface.get_height()
        height2 = self.description_surface.get_height()
        Y1 = self.description_slider_rect.top

        coeff = height2 / height1
        slider_height = coeff * height2

        slide_bar_rect = pygame.Rect(0, 0, 10, slider_height)
        slide_bar_rect.right = self.description_rect.right - 2
        slide_bar_rect.top = self.description_rect.top - Y1 * coeff

        pygame.draw.rect(self.display_surface, 'grey', slide_bar_rect, 0, 4)

    def draw(self):
        pygame.draw.rect(self.display_surface, 'White', self.rect, 0, 4)
        self.make_surface_transparent()
        self.draw_slider_bar()
