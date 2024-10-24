from abc import ABC
from typing import Any

import pygame

from src.enums import Layer
from src.map_objects import MapObjectType
from src.settings import SCALE_FACTOR


class Sprite(pygame.sprite.Sprite):
    def __init__(
        self,
        pos: tuple[int | float, int | float],
        surf: pygame.Surface,
        groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group = None,
        z: Layer = Layer.MAIN,
        name: str | None = None,
        custom_properties: dict[str, Any] | None = None,
    ):
        self._z = z
        if groups:
            super().__init__(groups)
        else:
            super().__init__()
        self.surf = surf
        self.image = surf
        self.rect = self.image.get_frect(topleft=pos)
        self.name = name
        self.custom_properties: dict[str, Any] = custom_properties or {}
        self.hitbox_rect = self.rect.copy()

    @property
    def z(self):
        return self._z

    def draw(self, display_surface: pygame.Surface, rect: tuple[float, float], camera):
        display_surface.blit(self.image, rect)

    def add(self, *groups: Any):
        for group in groups:
            if not hasattr(group, "_spritegroup") and not isinstance(group, tuple):
                group.add(self)
            else:
                super().add(group)  # noqa


class CollideableSprite(Sprite, ABC):
    hitbox_rect: pygame.FRect


class CollideableMapObject(Sprite):
    def __init__(
        self,
        pos: tuple[int, int],
        object_type: MapObjectType,
        groups: tuple[pygame.sprite.Group, ...] | pygame.sprite.Group = None,
        z=Layer.MAIN,
        name=None,
    ):
        self.object_type = object_type

        surf = pygame.transform.scale_by(self.object_type.image, SCALE_FACTOR)

        super().__init__(pos, surf, groups, z, name)

        self.hitbox_rect = self.object_type.hitbox.move(self.rect.topleft)


class AnimatedSprite(Sprite):
    def __init__(self, pos, frames, groups=None, z=Layer.MAIN):
        self.frames, self.frame_index = frames, 0
        super().__init__(pos, frames[0], groups, z)

    def animate(self, dt):
        self.frame_index += 2 * dt
        self.image = self.frames[int(self.frame_index) % len(self.frames)]

    def update(self, dt):
        self.animate(dt)
