from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TypeVar

import pygame

from src.sprites.base import Sprite
from src.timer import Timer


class EmoteBoxBase(Sprite, ABC):
    """
    Base class to create emote boxes
    Attributes:
        emote: List of animation frames
        _current_emote_image: Current animation frame

        pos: Position property of the emote box

        _ani_frame_count: Frame count of one animation cycle
        _ani_cframe: Current frame of the animation
        _ani_frame_length: Time until a new frame of the animation plays in
                           seconds
        _ani_length: Total time the animation will play
        _ani_total_frames: Total frame count of the animation
        ani_finished: Whether the animation has been finished or not
        __on_finish_animation_funcs: List of functions that will be called when
                                     the animation has finished

        timer: Timer triggering the next animation frames
    """

    emote: list[pygame.Surface]
    _current_emote_image = pygame.Surface

    pos: tuple[float, float]

    _ani_frame_count: int
    _ani_cframe: int
    _ani_frame_length: float
    _ani_length: float
    _ani_total_frames: int
    ani_finished: bool
    __on_finish_animation_funcs: list[Callable[[], None]]

    timer: Timer

    @property
    @abstractmethod
    def pos(self):
        pass

    @abstractmethod
    def on_finish_animation(self, func: Callable[[], None]):
        pass

    @abstractmethod
    def _ani_next_frame(self):
        pass

    @abstractmethod
    def update(self, *args, **kwargs):
        pass


EmoteBoxType = TypeVar("EmoteBoxType", bound=EmoteBoxBase)


class EmoteManagerBase(ABC):
    groups: tuple[pygame.sprite.Group, ...]

    emotes: dict[str, list[pygame.Surface]]

    _emote_boxes: dict[int, EmoteBoxType]

    @abstractmethod
    def _check_obj(self, obj: object) -> bool:
        pass

    @abstractmethod
    def show_emote(self, obj: object, emote: str):
        pass

    @abstractmethod
    def update_obj(self, obj: object, pos: tuple[int, int]):
        pass

    @abstractmethod
    def _remove_emote_box(self, obj_id: int):
        pass

    @abstractmethod
    def _clear_emote_boxes(self):
        pass

    @abstractmethod
    def __setitem__(self, obj: object, value: EmoteBoxBase):
        pass

    @abstractmethod
    def __getitem__(self, obj: object):
        pass

    @abstractmethod
    def __delitem__(self, obj: object):
        pass


class EmoteWheelBase(Sprite):
    """
    Base class for the Player's emote selection wheel

    Attributes:
        current_emote_selection: Names of all emotes on the emote wheel.
        Should be a selection of keys from EmoteManagerBase.emotes
    """

    _visible: bool

    _emote_manager: EmoteManagerBase

    _default_emote_selection: list[str]
    _emote_selection_stack: list[list[str]]

    current_emote_selection: list[str]

    emotes_count: int

    _emote_separator_width: int
    _selected_emote_separator_width: int
    _background_alpha: int

    _inner_radius: int
    _outer_radius: int
    _center: float

    _image: pygame.Surface

    pos: tuple[float, float]

    @abstractmethod
    def _setup_emote_selection(self):
        pass

    @property
    @abstractmethod
    def pos(self) -> tuple[float, float]:
        pass

    @property
    @abstractmethod
    def emote_index(self) -> int:
        pass

    @property
    @abstractmethod
    def is_open(self) -> bool:
        pass

    @property
    @abstractmethod
    def current_emote(self):
        pass

    @abstractmethod
    def open(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def toggle(self):
        pass

    @abstractmethod
    def submit(self):
        pass

    @abstractmethod
    def _update_image(self):
        pass

    @abstractmethod
    def _update_emote_selection(self):
        pass

    @abstractmethod
    def push_emote_selection(self, emotes: list[str]):
        pass

    @abstractmethod
    def pop_emote_selection(self):
        pass
