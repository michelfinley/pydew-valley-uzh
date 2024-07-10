import pygame
from pygame import Vector2
from pygame.mouse import get_pos as mouse_pos


class Button:
    def __init__(self, text, font, rect, offset):
        self.font = font
        self.text = text
        self.rect = rect
        self.offset = Vector2(offset)
        self.color = 'White'
        self.hover_active = False

        self.display_surface = None

    def mouse_hover(self):
        return self.rect.collidepoint(mouse_pos()-self.offset)

    # draw
    def draw_text(self):
        text_surf = self.font.render(self.text, False, 'Black')
        text_rect = text_surf.get_frect(center=self.rect.center)
        self.display_surface.blit(text_surf, text_rect)

    def draw_hover(self):
        if self.mouse_hover():
            self.hover_active = True
            pygame.draw.rect(self.display_surface, 'Black', self.rect, 4, 4)
        else:
            self.hover_active = False

    def draw(self, surface):
        self.display_surface = surface
        pygame.draw.rect(self.display_surface, self.color, self.rect, 0, 4)
        self.draw_text()
        self.draw_hover()


class Slider:
    def __init__(self, rect, min_value, max_value, init_value, sounds, offset):
        # main setup
        self.surface = None
        self.rect = rect
        self.offset = Vector2(offset)

        # values
        self.min_value = min_value
        self.max_value = max_value
        self.value = init_value

        # sounds
        self.sounds = sounds
        self.font = pygame.font.Font('font/LycheeSoda.ttf', 30)

        # knob
        self.knob_radius = 10
        self.drag_active = False

    def get_value(self):
        return self.value

    # events
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(mouse_pos() - self.offset):
                self.drag_active = True

        if event.type == pygame.MOUSEBUTTONUP:
            self.drag_active = False

        if event.type == pygame.MOUSEMOTION and self.drag_active:
            self.value = self.min_value + (self.max_value - self.min_value) * (mouse_pos()[0] - self.offset.x - self.rect.left) / (self.rect.width - 10)
            self.value = max(self.min_value, min(self.max_value, self.value))
            self.update_volume()

    def update_volume(self):
        self.sounds['music'].set_volume(min((self.value / 1000), 0.4))
        for key in self.sounds:
            if key != 'music':
                self.sounds[key].set_volume((self.value / 100))

    # draw
    def draw_value(self):
        text_surf = self.font.render(str(int(self.value)), False, 'Black')
        text_rect = text_surf.get_frect(midtop=(self.rect.centerx, self.rect.bottom + 10))
        self.surface.blit(text_surf, text_rect)

    def draw_knob(self):
        knob_x = self.rect.left + (self.rect.width - 10) * (self.value - self.min_value) / (self.max_value - self.min_value)
        pygame.draw.circle(self.surface, (232, 207, 166), (int(knob_x), self.rect.centery), self.knob_radius)

    def draw_rect(self):
        pygame.draw.rect(self.surface, (220, 185, 138), self.rect, 0, 4)
        pygame.draw.rect(self.surface, (243, 229, 194), self.rect.inflate(-4, -4), 0, 4)

    def draw(self, surface):
        self.surface = surface
        self.draw_rect()
        self.draw_knob()
        self.draw_value()
