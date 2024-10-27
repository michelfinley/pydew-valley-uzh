from collections.abc import Iterable

import pygame

from src.camera import Camera
from src.enums import Layer

from src.settings import RENDER_CHUNK_W, RENDER_CHUNK_H
from src.sprites.base import Sprite
from src.sprites.chunk_system.sprite_manager import SpriteChunk, SpriteLayer, \
    SpriteManager


class RenderChunk(SpriteChunk):
    def add(self, sprite: Sprite):
        super().add(sprite)
        sprite.add_to_render_chunk(self)

    def remove(self, *sprites: Sprite):
        super().remove(*sprites)
        for sprite in sprites:
            sprite.remove_from_render_chunk()

    def update(self, dt: float):
        for sprite in self:
            sprite.update(dt)

        super().update()

    def update_blocked(self, dt: float):
        for sprite in self:
            getattr(sprite, "update_blocked", sprite.update)(dt)  # noqa


class RenderLayer(SpriteLayer):
    def draw(self, surface: pygame.Surface, camera: Camera, center: tuple[float, float]):
        sprites = []
        center_chunk = int(center[0] / RENDER_CHUNK_W), int(center[1] / RENDER_CHUNK_H)
        for i in range(center_chunk[0] - 1, center_chunk[0] + 2):
            for j in range(center_chunk[1] - 1, center_chunk[1] + 2):
                for sprite in self.get_chunk((i, j)):
                    sprites.append(sprite)
        sprites.sort(key=lambda spr: spr.hitbox_rect.bottom)

        for sprite in sprites:
            sprite.draw(surface, camera.apply(sprite), camera)

    def update_blocked(self, dt: float):
        for sprite in self:
            getattr(sprite, "update_blocked", sprite.update)(dt)  # noqa

    def on_sprite_exit_chunk(self, sprite: Sprite):
        sprite.render_chunk.remove(sprite)
        self.get_sprite_chunk(sprite).add(sprite)  # TODO: add_persistent


class AllSprites(SpriteManager):
    _containers: dict[Layer, RenderLayer]

    display_surface: pygame.Surface

    def __init__(self):
        self.display_surface = pygame.display.get_surface()
        self._containers = {i: RenderLayer((RENDER_CHUNK_W, RENDER_CHUNK_H), RenderChunk) for i in Layer}

    def add(self, *sprites: Sprite | Iterable[Sprite]):
        for sprite in sprites:
            try:
                self._containers[sprite.z].add(sprite)
            except AttributeError:
                self.add(*sprite)

    def add_persistent(self, *sprites: Sprite):
        for sprite in sprites:
            self._containers[sprite.z].add_persistent(sprite)

    def remove(self, *sprites: Sprite):
        for sprite in sprites:
            if sprite.render_chunk:
                sprite.render_chunk.remove(sprite)

    def update(self, dt: float):
        super().update(dt)

    def update_blocked(self, dt: float):
        for sprite in self:
            sprite.update_blocked(dt)

    def draw(self, camera: Camera, center: tuple[float, float]):
        for layer in self.all_containers():
            layer.draw(self.display_surface, camera, center)

    def change_layer(self, sprite: Sprite, z: Layer, add_persistent: bool = False):
        if sprite.render_chunk:
            sprite.render_chunk.remove(sprite)

        if z in self._containers:
            if add_persistent:
                self.add_persistent(sprite)
            else:
                self.add(sprite)

        sprite._z = z
