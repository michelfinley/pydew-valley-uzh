from collections.abc import Generator, Callable

import pygame

from src.camera import Camera
from src.enums import Layer
from src.settings import CHUNK_W, CHUNK_H
from src.sprites.base import Sprite, MovingSprite
from src.utils import DefaultCallableDict


class PersistentSpriteGroup(pygame.sprite.Group):
    _persistent_sprites: list[pygame.sprite.Sprite]

    def __init__(self, *sprites):
        """
        This Group subclass allows certain Sprites to be added as persistent
        Sprites, which will not be removed when calling Group.empty.
        When needing to remove all Sprites, including persistent Sprites, you
        should call PersistentSpriteGroup.empty_persistent.
        """
        super().__init__(*sprites)
        self._persistent_sprites = []

    def add_persistent(self, *sprites: pygame.sprite.Sprite):
        """
        Add a persistent Sprite. This Sprite will not be removed
        from the Group when Group.empty is called.
        """
        super().add(*sprites)
        self._persistent_sprites.extend(sprites)

    def empty(self):
        super().empty()
        self.add(*self._persistent_sprites)

    def empty_persistent(self):
        """
        Remove all sprites, including persistent Sprites.
        """
        super().empty()


# TODO : we could replace this with pygame.sprite.LayeredUpdates, as that
#  is a subclass of pygame.sprite.Group that natively supports layers


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
        sprite.add_to_chunk(self)

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
            sprite.remove_from_chunk()

    def update(self, dt: float):
        for sprite in self:
            sprite.update(dt)

        sprite_list = []
        for sprite in self._moving_sprite_list:
            if not (int(sprite.rect.left / CHUNK_W) == self._pos[0] and
                    int(sprite.rect.top / CHUNK_H) == self._pos[1]):
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

    def sprites(self) -> Generator[Sprite, None, None]:
        for chunk in self.chunks.values():
            for sprite in chunk:
                yield sprite

    def add(self, sprite: Sprite):
        self.get_sprite_chunk(sprite).add(sprite)

    def add_persistent(self, sprite: Sprite):
        self.get_sprite_chunk(sprite).add_persistent(sprite)

    def update(self, dt: float):
        for chunk in self.chunks.values():
            chunk.update(dt)

    def draw(self, surface: pygame.Surface, camera: Camera, center: tuple[float, float]):
        sprites = []
        center_chunk = int(center[0] / CHUNK_W), int(center[1] / CHUNK_H)
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
        for chunk in self.chunks.values():
            chunk.empty()

    def empty_persistent(self):
        for chunk in self.chunks.values():
            chunk.empty_persistent()

    def on_sprite_exit_chunk(self, sprite: Sprite):
        sprite.render_chunk.remove(sprite)
        self.get_sprite_chunk(sprite).add(sprite)  # TODO: add_persistent

    def get_chunk(self, pos: tuple[int, int]):
        return self.chunks[pos]

    def get_sprite_chunk(self, sprite: Sprite):
        pos = int(sprite.rect.left / CHUNK_W), int(sprite.rect.top / CHUNK_H)
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
