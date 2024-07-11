import pygame
from pygame import Vector2
from pygame.mouse import get_pressed as mouse_buttons, get_pos as mouse_pos

from src.support import save_data, load_data
from src.GUI.base_classes import Description
from src.GUI.components import Slider


class KeySetup:
    def __init__(self, key_name, key_value, pos, symbol_image):
        self.key_name = key_name
        self.key_symbol = None
        self.key_value = key_value
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 30)
        self.offset = Vector2()

        # rect
        self.pos = pos
        self.rect = pygame.Rect(pos, (300, 50))

        # symbol
        self.symbol_image = symbol_image
        self.symbol_image = pygame.transform.scale(self.symbol_image, (40, 40))
        self.symbol_image_rect = self.symbol_image.get_rect(midright=self.rect.midright - Vector2(10, 0))


    def hover(self, offset):
        self.offset = Vector2(offset)
        return self.rect.collidepoint(mouse_pos() - self.offset)


    # draw
    def draw_key_name(self, surface):
        text_surf = self.font.render(self.key_name, False, 'Black')
        text_rect = text_surf.get_frect(midleft=(self.rect.left + 10, self.rect.centery))
        pygame.draw.rect(surface, 'White', text_rect.inflate(10, 10), 0, 4)
        surface.blit(text_surf, text_rect)

    def draw_symbol(self, surface):
        text_surf = self.font.render(self.key_symbol, False, 'White')
        text_rect = text_surf.get_frect(center=self.symbol_image_rect.center)
        surface.blit(self.symbol_image, self.symbol_image_rect)
        surface.blit(text_surf, text_rect)

    def draw(self, surface):
        pygame.draw.rect(surface, 'grey', self.rect, 0, 4)
        self.draw_key_name(surface)
        self.draw_symbol(surface)


class KeybindsDescription(Description):
    def __init__(self, pos):
        super().__init__(pos)
        self.keybinds = {}
        self.keys_group = []
        self.selection_key = None
        self.key_setup = None     # TODO: change name

        # setup
        self.import_data()
        self.create_keybinds()


    # setup
    def create_keybinds(self):
        index = 0
        for key_name, value in self.keybinds.items():
            key_value = value
            symbol = self.value_to_unicode(key_value)

            path = self.get_path(key_value)
            image = pygame.image.load(path)
            image = pygame.transform.scale(image, (40, 40))

            pos = (10, 10 + 60 * index)
            key_setup = KeySetup(key_name, key_value, pos, image)
            key_setup.key_symbol = symbol
            self.keys_group.append(key_setup)
            index += 1

    def save_data(self):
        data = {}
        for key in self.keys_group:
            data[key.key_name] = key.key_value
        save_data(data, 'keybinds.json')

    def import_data(self):
        self.keybinds = {
            "Up": pygame.K_UP,
            "Down": pygame.K_DOWN,
            "Left": pygame.K_LEFT,
            "Right": pygame.K_RIGHT,
            "Use": pygame.K_SPACE,
            "Cycle Tools": pygame.K_TAB,
            "Cycle Seeds": pygame.K_LSHIFT,
            "Plant Current Seed": pygame.K_RETURN,
        }

        try:
            self.keybinds = load_data('keybinds.json')
        except FileNotFoundError:
            pass


    # events
    def handle_events(self, event):
        super().handle_events(event)
        self.select_keySetup(event)
        self.set_key(event)

    # keybinds
    def select_keySetup(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and mouse_buttons()[0]:
            for key in self.keys_group:
                offset = Vector2(self.description_slider_rect.topleft) + self.description_rect.topleft
                if key.hover(offset):
                    self.key_setup = key
                    return
            self.key_setup = None

    def set_key(self, event):
        if self.key_setup:
            if event.type == pygame.KEYDOWN:
                symbol = event.unicode.upper()
                path = self.get_path(event.key)
                image = pygame.image.load(path)
                image = pygame.transform.scale(image, (40, 40))

                self.key_setup.key_symbol = symbol if self.is_generic(symbol) else None
                self.key_setup.symbol_image = image
                self.key_setup.key_value = event.key
                self.key_setup = None

    def is_generic(self, symbol):
        return symbol in "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()_+-=[]{}|;':,.<>/?"

    def get_path(self, keydown):
        if keydown == None:
            return "images/keys/generic.svg"

        special_keys = {
            pygame.K_SPACE: "images/keys/space.svg",
            pygame.K_LCTRL: "images/keys/lctrl.png",
            pygame.K_LEFT: "images/keys/left.png",
            pygame.K_UP: "images/keys/up.svg",
            pygame.K_DOWN: "images/keys/down.svg",
            pygame.K_RIGHT: "images/keys/right.svg"
        }

        if keydown in special_keys:
            return special_keys[keydown]

        return "images/keys/generic.svg"

    def value_to_unicode(self, value):
        if value == None:
            return None
        if value in range(48, 58):
            return str(value - 48)
        if value in range(97, 123):
            return chr(value - 32)
        return None


    # draw
    def draw_selected_key_indicator(self):
        if self.key_setup:
            pygame.draw.rect(self.description_slider_surface, 'red', self.key_setup.rect, 4, 4)

    def draw_keybinds(self):
        for key in self.keys_group:
            key.draw(self.description_slider_surface)

        self.draw_selected_key_indicator()
        self.description_surface.blit(self.description_slider_surface, self.description_slider_rect)
        self.display_surface.blit(self.description_surface, self.description_rect.topleft)

    def draw(self):
        super().draw()
        self.draw_keybinds()


class VolumeDescription(Description):
    def __init__(self, pos, sounds):
        super().__init__(pos)
        self.sounds = sounds

        # setup
        self.create_slider()
        self.import_data()

    # setup
    def create_slider(self):
        slider_rect = pygame.Rect((30, 30), (200, 10))
        self.slider = Slider(slider_rect, 0, 100, 50, self.sounds, self.rect.topleft)

    def save_data(self):
        data = self.slider.get_value()
        save_data(int(data), 'volume.json')

    def import_data(self):
        try:
            self.slider.value = load_data('volume.json')
        except FileNotFoundError:
            pass


    # events
    def handle_events(self, event):
        super().handle_events(event)
        self.slider.handle_event(event)

    # draw
    def draw_slider(self):
        self.slider.draw(self.description_slider_surface)
        self.description_surface.blit(self.description_slider_surface, self.description_slider_rect.topleft)
        self.display_surface.blit(self.description_surface, self.description_rect.topleft)

    def draw(self):
        super().draw()
        self.draw_slider()
