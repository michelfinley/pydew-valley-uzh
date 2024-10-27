from collections.abc import Callable, Generator
from itertools import chain

import pygame

from src.settings import COLLISION_CHUNK_W, COLLISION_CHUNK_H
from src.sprites.base import Sprite, MovingSprite
from src.utils import DefaultCallableDict


class CollisionChunk:
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
        sprite.add_to_collision_chunk(self)

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
            sprite.remove_from_collision_chunk()

    def update(self):
        sprite_list = []
        for sprite in self._moving_sprite_list:
            if not (int(sprite.rect.left / COLLISION_CHUNK_W) == self._pos[0] and
                    int(sprite.rect.top / COLLISION_CHUNK_H) == self._pos[1]):
                sprite_list.append(sprite)

        for sprite in sprite_list:
            self._on_sprite_exit_chunk(sprite)

    def empty(self):
        self.remove(
            *set(self._sprite_list).symmetric_difference(self._persistent_sprite_list)
        )

    def empty_persistent(self):
        self.remove(*self._sprite_list)


class CollisionManager:
    chunks: dict[tuple[int, int], CollisionChunk]

    def __init__(self):
        self.chunks = DefaultCallableDict(
            lambda x: CollisionChunk(x, self.on_sprite_exit_chunk)
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
        return f"<{self.__class__.__name__}({len(self)} sprites)>"

    def all_chunks(self) -> list[CollisionChunk]:
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

    def update(self):
        for chunk in self.all_chunks():
            chunk.update()

    def empty(self):
        for chunk in self.all_chunks():
            chunk.empty()

    def empty_persistent(self):
        for chunk in self.all_chunks():
            chunk.empty_persistent()

    def on_sprite_exit_chunk(self, sprite: Sprite):
        sprite.collision_chunk.remove(sprite)
        self.get_sprite_chunk(sprite).add(sprite)  # TODO: add_persistent

    def get_chunk(self, pos: tuple[int, int]):
        return self.chunks[pos]

    def get_sprite_pos(self, sprite: Sprite):
        pos = int(sprite.hitbox_rect.left / COLLISION_CHUNK_W), int(sprite.hitbox_rect.top / COLLISION_CHUNK_H)
        return pos

    def get_sprite_chunk(self, sprite: Sprite):
        pos = self.get_sprite_pos(sprite)
        return self.get_chunk(pos)

    def check_collision(self, hitbox: pygame.FRect):
        for sprite in self:
            if sprite.hitbox_rect.colliderect(hitbox) and sprite.hitbox_rect != hitbox:
                return True

    def update_sprite(self, sprite: MovingSprite) -> bool:
        """
        :return: Whether the sprite collides with anything
        """
        center_chunk = self.get_sprite_pos(sprite)
        chunks = [self.chunks[i, j] for j in range(center_chunk[1] - 1, center_chunk[1] + 2) for i in range(center_chunk[0] - 1, center_chunk[0] + 2)]

        colliding_rect = None
        for c_sprite in chain(*chunks):
            if c_sprite.hitbox_rect.colliderect(sprite.hitbox_rect) and c_sprite != sprite:
                colliding_rect = c_sprite.hitbox_rect
                distances_rect = colliding_rect

                if isinstance(c_sprite, MovingSprite):
                    # When colliding with another moving sprite, the hitbox to
                    # compare to will also reflect its last-frame's state
                    distances_rect = c_sprite.last_hitbox_rect

                # Compares each point of the last-frame's sprite hitbox to the
                # hitbox the Entity collided with, to check at which
                # direction the collision happened first
                distances = (
                    abs(sprite.last_hitbox_rect.right - distances_rect.left),
                    abs(sprite.last_hitbox_rect.left - distances_rect.right),
                    abs(sprite.last_hitbox_rect.bottom - distances_rect.top),
                    abs(sprite.last_hitbox_rect.top - distances_rect.bottom),
                )

                shortest_distance = min(distances)
                if shortest_distance == distances[0]:
                    sprite.hitbox_rect.right = colliding_rect.left
                elif shortest_distance == distances[1]:
                    sprite.hitbox_rect.left = colliding_rect.right
                elif shortest_distance == distances[2]:
                    sprite.hitbox_rect.bottom = colliding_rect.top
                elif shortest_distance == distances[3]:
                    sprite.hitbox_rect.top = colliding_rect.bottom
        return bool(colliding_rect)
