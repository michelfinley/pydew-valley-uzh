import pygame

from src.settings import OVERLAY_POSITIONS
from src.support import import_font


class FPS:
    def __init__(self, clock: pygame.time.Clock):
        # setup
        self.display_surface = pygame.display.get_surface()
        self.clock = clock

        # dimensions
        self.left = 20
        self.top = 20

        width, height = 180, 112
        self.font = import_font(40, "font/LycheeSoda.ttf")
        self.small_font = import_font(28, "font/LycheeSoda.ttf")

        self.rect = pygame.Rect(self.left, self.top, width, height)

        self.rect.bottomright = OVERLAY_POSITIONS["FPS"]

        self.fps_sample = {}
        self.dt_sample = []
        self.ctime = 0
        self.avg_fps = 0
        self.min_fps = 0
        self.max_fps = 0

    def update(self, dt: float):
        self.ctime += dt
        self.dt_sample.append(dt)

        # update avg fps 10 times per second
        if (
            int(self.ctime * 10) / 10 != int((self.ctime - dt) * 10) / 10
            or self.ctime < 0.1
        ) and len(self.dt_sample) > 0:
            self.avg_fps = 1 / (sum(self.dt_sample) / len(self.dt_sample))
            self.fps_sample[round(self.ctime, 3)] = round(self.avg_fps, 3)

            self.max_fps = 1 / min(self.dt_sample)
            self.min_fps = 1 / max(self.dt_sample)

        # only keep samples from the last 5 seconds
        if len(self.dt_sample) >= 5 / (sum(self.dt_sample) / len(self.dt_sample)):
            self.dt_sample.pop(0)

    def display(self):
        # rects and surfs
        pad_y = 2

        label_surf = self.font.render("FPS:", False, "Black")
        label_rect = label_surf.get_frect(
            bottomleft=(self.rect.left + 20, self.rect.bottom - pad_y)
        )

        fps_surf = self.font.render(f"{self.avg_fps:5.1f}", False, "Black")
        fps_rect = fps_surf.get_frect(
            bottomright=(self.rect.right - 20, self.rect.bottom - pad_y)
        )

        min_label_surf = self.small_font.render("MIN:", False, "Black")
        min_label_rect = min_label_surf.get_frect(
            bottomleft=(self.rect.left + 20, self.rect.bottom - pad_y - 40)
        )

        min_fps_surf = self.small_font.render(f"{self.min_fps:.1f}", False, "Black")
        min_fps_rect = min_fps_surf.get_frect(
            bottomright=(self.rect.right - 20, self.rect.bottom - pad_y - 40)
        )

        max_label_surf = self.small_font.render("MAX:", False, "Black")
        max_label_rect = max_label_surf.get_frect(
            bottomleft=(self.rect.left + 20, self.rect.bottom - pad_y - 64)
        )

        max_fps_surf = self.small_font.render(f"{self.max_fps:.1f}", False, "Black")
        max_fps_rect = max_fps_surf.get_frect(
            bottomright=(self.rect.right - 20, self.rect.bottom - pad_y - 64)
        )

        # display
        pygame.draw.rect(self.display_surface, "White", self.rect, 0, 4)
        pygame.draw.rect(self.display_surface, "Black", self.rect, 4, 4)
        self.display_surface.blit(label_surf, label_rect)
        self.display_surface.blit(fps_surf, fps_rect)
        self.display_surface.blit(min_label_surf, min_label_rect)
        self.display_surface.blit(min_fps_surf, min_fps_rect)
        self.display_surface.blit(max_label_surf, max_label_rect)
        self.display_surface.blit(max_fps_surf, max_fps_rect)
