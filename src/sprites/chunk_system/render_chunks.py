from typing import Callable, Generator

import pygame

from src.camera import Camera
from src.enums import Layer

from src.settings import RENDER_CHUNK_W, RENDER_CHUNK_H
from src.sprites.base import Sprite, MovingSprite
from src.utils import DefaultCallableDict


class RenderChunk:
    _pos: tuple[int, int]

    _sprite_list: list[Sprite]
    _persistent_sprite_list: list[Sprite]

    _moving_sprite_list: list[Sprite]

    def __init__(self, pos: tuple[int, int], on_sprite_exit_chunk: Callable[[Sprite], None]):
        self._pos = pos

        self._sprite_list = []
        self._persistent_sprite_list = []

        self._moving_sprite_list = []
        self._on_sprite_exit_chunk = on_sprite_exit_chunk

    def __bool__(self):
        return bool(self._sprite_list)

    def __contains__(self, sprite: Sprite):
        if sprite in self._sprite_list:
            return True

    def __iter__(self):
        return self.sprites()

    def __len__(self):
        return len(self._sprite_list)

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._pos} / {len(self)} sprites)>"

    def sprites(self) -> Generator[Sprite, None, None]:
        for sprite in self._sprite_list:
            yield sprite

    def add(self, sprite: Sprite):
        if sprite not in self:
            if isinstance(sprite, MovingSprite):
                self._moving_sprite_list.append(sprite)
            self._sprite_list.append(sprite)
        sprite.add_to_render_chunk(self)

    def add_persistent(self, sprite: Sprite):
        self.add(sprite)
        if sprite not in self._persistent_sprite_list:
            self._persistent_sprite_list.append(sprite)

    def remove(self, *sprites: Sprite):
        for sprite in sprites:
            if sprite in self:
                self._sprite_list.remove(sprite)
            if sprite in self._persistent_sprite_list:
                self._persistent_sprite_list.remove(sprite)
            if sprite in self._moving_sprite_list:
                self._moving_sprite_list.remove(sprite)
            sprite.remove_from_render_chunk()

    def update(self, dt: float):
        for sprite in self:
            sprite.update(dt)

        sprite_list = []
        for sprite in self._moving_sprite_list:
            if not (int(sprite.rect.left / RENDER_CHUNK_W) == self._pos[0] and
                    int(sprite.rect.top / RENDER_CHUNK_H) == self._pos[1]):
                sprite_list.append(sprite)

        for sprite in sprite_list:
            self._on_sprite_exit_chunk(sprite)

    def update_blocked(self, dt: float):
        for sprite in self:
            getattr(sprite, "update_blocked", sprite.update)(dt)  # noqa

    def empty(self):
        self.remove(
            *set(self._sprite_list).symmetric_difference(self._persistent_sprite_list)
        )

    def empty_persistent(self):
        self.remove(*self._sprite_list)


class RenderLayer:
    chunks: dict[tuple[int, int], RenderChunk]

    def __init__(self, layer: Layer):
        self._layer = layer
        self.chunks = DefaultCallableDict(
            lambda x: RenderChunk(x, self.on_sprite_exit_chunk)
        )

    def __bool__(self):
        return next(self.sprites(), False)

    def __contains__(self, sprite: Sprite):
        for chunk in self.chunks.values():
            if sprite in chunk:
                return True

    def __iter__(self):
        return self.sprites()

    def __len__(self):
        return sum(len(chunk) for chunk in self.chunks.values())

    def __repr__(self):
        return f"<{self.__class__.__name__}({self._layer.name} / {len(self)} sprites)>"

    def all_chunks(self) -> list[RenderChunk]:
        # convert to list to allow the dictionary to change in size during iteration
        return list(self.chunks.values())

    def sprites(self) -> Generator[Sprite, None, None]:
        for chunk in self.all_chunks():
            for sprite in chunk:
                yield sprite

    def add(self, sprite: Sprite):
        self.get_sprite_chunk(sprite).add(sprite)

    def add_persistent(self, sprite: Sprite):
        self.get_sprite_chunk(sprite).add_persistent(sprite)

    def update(self, dt: float):
        for chunk in self.all_chunks():
            chunk.update(dt)

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

    def empty(self):
        for chunk in self.all_chunks():
            chunk.empty()

    def empty_persistent(self):
        for chunk in self.all_chunks():
            chunk.empty_persistent()

    def on_sprite_exit_chunk(self, sprite: Sprite):
        sprite.render_chunk.remove(sprite)
        self.get_sprite_chunk(sprite).add(sprite)  # TODO: add_persistent

    def get_chunk(self, pos: tuple[int, int]):
        return self.chunks[pos]

    def get_sprite_chunk(self, sprite: Sprite):
        pos = int(sprite.rect.left / RENDER_CHUNK_W), int(sprite.rect.top / RENDER_CHUNK_H)
        return self.get_chunk(pos)


class AllSprites:
    display_surface: pygame.Surface
    layers: dict[Layer, RenderLayer]

    def __init__(self, *sprites):
        self.display_surface = pygame.display.get_surface()
        self.layers = {i: RenderLayer(i) for i in Layer}

        self.add(*sprites)

    def __bool__(self):
        return next(self.sprites(), False)

    def __contains__(self, sprite: Sprite):
        for layer in self.layers.values():
            if sprite in layer:
                return True

    def __iter__(self):
        return self.sprites()

    def __len__(self):
        return sum(len(layer) for layer in self.layers.values())

    def __repr__(self):
        return f"<{self.__class__.__name__}({len(self)} sprites)>"

    def sprites(self) -> Generator[Sprite, None, None]:
        for layer in self.layers.values():
            for sprite in layer:
                yield sprite

    def add(self, *sprites: Sprite):
        for sprite in sprites:
            try:
                self.layers[sprite.z].add(sprite)
            except AttributeError:
                self.add(*sprite)

    def add_persistent(self, *sprites: Sprite):
        for sprite in sprites:
            self.layers[sprite.z].add_persistent(sprite)

    def remove(self, *sprites: Sprite):
        for sprite in sprites:
            if sprite.render_chunk:
                sprite.render_chunk.remove(sprite)

    def update(self, dt: float):
        for layer in self.layers.values():
            layer.update(dt)

    def update_blocked(self, dt: float):
        for sprite in self:
            sprite.update_blocked(dt)

    def draw(self, camera: Camera, center: tuple[float, float]):
        for layer in self.layers.values():
            layer.draw(self.display_surface, camera, center)

    def empty(self):
        for layer in self.layers.values():
            layer.empty()

    def empty_persistent(self):
        for layer in self.layers.values():
            layer.empty_persistent()

    def change_layer(self, sprite: Sprite, z: Layer, add_persistent: bool = False):
        if sprite.render_chunk:
            sprite.render_chunk.remove(sprite)

        if z in self.layers:
            if add_persistent:
                self.add_persistent(sprite)
            else:
                self.add(sprite)

        sprite._z = z
