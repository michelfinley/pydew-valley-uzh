from collections.abc import Generator

import pygame

from src.camera import Camera
from src.enums import Layer
from src.sprites.base import Sprite


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


class RenderLayer:
    layer: Layer

    _sprite_list: list[Sprite]
    _persistent_sprite_list: list[Sprite]

    def __init__(self, layer: Layer):
        self.layer = layer

        self._sprite_list = []
        self._persistent_sprite_list = []

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
        return f"<{self.__class__.__name__}({len(self)} sprites)>"

    def sprites(self) -> Generator[Sprite, None, None]:
        for sprite in self._sprite_list:
            yield sprite

    def add(self, sprite: Sprite):
        if not sprite in self:
            self._sprite_list.append(sprite)

    def add_persistent(self, sprite: Sprite):
        self.add(sprite)
        if not sprite in self._persistent_sprite_list:
            self._persistent_sprite_list.append(sprite)

    def remove(self, *sprites: Sprite):
        for sprite in sprites:
            if sprite in self:
                self._sprite_list.remove(sprite)

    def update(self, *args, **kwargs):
        for sprite in self:
            sprite.update(*args, **kwargs)

    def draw(self, surface: pygame.Surface, camera: Camera):
        self._sprite_list.sort(key=lambda spr: spr.hitbox_rect.bottom)

        for sprite in self:
            sprite.draw(surface, camera.apply(sprite), camera)

    def update_blocked(self, dt: float):
        for sprite in self:
            getattr(sprite, "update_blocked", sprite.update)(dt)  # noqa

    def empty(self):
        self.remove(*set(self._sprite_list).symmetric_difference(self._persistent_sprite_list))

    def empty_persistent(self):
        self.remove(*self._sprite_list)


class AllSprites:
    display_surface: pygame.Surface
    layers: list[RenderLayer]

    def __init__(self, *sprites):
        self.display_surface = pygame.display.get_surface()
        self.layers = [RenderLayer(i) for i in Layer]

        self.add(*sprites)

    def __bool__(self):
        return next(self.sprites(), False)

    def __contains__(self, sprite: Sprite):
        for layer in self.layers:
            if sprite in layer:
                return True

    def __iter__(self):
        return self.sprites()

    def __len__(self):
        return sum(len(layer) for layer in self.layers)

    def __repr__(self):
        return f"<{self.__class__.__name__}({len(self)} sprites)>"

    def sprites(self) -> Generator[Sprite, None, None]:
        for layer in self.layers:
            for sprite in layer:
                yield sprite

    def add(self, *sprites: Sprite):
        for sprite in sprites:
            self.layers[sprite.z].add(sprite)

    def add_persistent(self, *sprites: Sprite):
        for sprite in sprites:
            self.layers[sprite.z].add_persistent(sprite)

    def remove(self, *sprites: Sprite):
        for sprite in sprites:
            self.layers[sprite.z].remove(sprite)

    def update(self, *args, **kwargs):
        for layer in self.layers:
            layer.update(*args, **kwargs)

    def update_blocked(self, dt: float):
        for sprite in self:
            getattr(sprite, "update_blocked", sprite.update)(dt)  # noqa

    def draw(self, camera: Camera):
        for layer in self.layers:
            layer.draw(self.display_surface, camera)

    def empty(self):
        for layer in self.layers:
            layer.empty()

    def empty_persistent(self):
        for layer in self.layers:
            layer.empty_persistent()
