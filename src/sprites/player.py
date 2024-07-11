from typing import Callable

import pygame

from src import settings, savefile
from src.enums import FarmingTool, InventoryResource, ItemToUse
from src.scenes.pause_menu import PauseMenu
from src.scenes.settings_menu import SettingsMenu
from src.settings import SCALE_FACTOR
from src.sprites.entity import Entity

_NONSEED_INVENTORY_DEFAULT_AMOUNT = 20
_SEED_INVENTORY_DEFAULT_AMOUNT = 5
_INV_DEFAULT_AMOUNTS = (
    _NONSEED_INVENTORY_DEFAULT_AMOUNT,
    _SEED_INVENTORY_DEFAULT_AMOUNT
)


class Player(Entity):
    def __init__(
            self,
            game,
            pos: settings.Coordinate,
            frames,
            groups,
            collision_sprites: pygame.sprite.Group,
            apply_tool: Callable,
            interact: Callable,
            sounds: settings.SoundDict,
            font: pygame.font.Font):

        save_data = savefile.load_savefile()
        self.game = game

        super().__init__(
            pos,
            frames,
            groups,
            collision_sprites,
            (44 * SCALE_FACTOR, 40 * SCALE_FACTOR),
            apply_tool
        )

        # movement
        self.speed = 250
        self.blocked = False
        self.paused = False
        self.font = font
        self.interact = interact
        self.sounds = sounds

        # menus
        self.pause_menu = PauseMenu(self.font)
        self.settings_menu = SettingsMenu(self.font, self.sounds)

        self.current_tool = save_data.get("current_tool", FarmingTool.get_first_tool_id())
        self.tool_index = self.current_tool.value - 1

        self.current_seed = save_data.get("current_seed", FarmingTool.get_first_seed_id())
        self.seed_index = self.current_seed.value - FarmingTool.get_first_seed_id().value

        # inventory
        self.inventory = {
            res: save_data["inventory"].get(
                res.as_serialised_string(),
                _SEED_INVENTORY_DEFAULT_AMOUNT if res >= InventoryResource.CORN_SEED else
                _NONSEED_INVENTORY_DEFAULT_AMOUNT
                )
            for res in InventoryResource.__members__.values()
        }
        self.money = save_data.get("money", 200)

        # sounds
        self.sounds = sounds

    def save(self):
        # We compact the inventory first, i.e. remove any default values if they didn't change.
        # This is to save space in the save file.
        compacted_inv = self.inventory.copy()
        key_set = list(compacted_inv.keys())
        for k in key_set:
            # The default amount for each resource differs
            # according to whether said resource is a seed or not
            # (5 units for seeds, 20 units for everything else).
            if self.inventory[k] == _INV_DEFAULT_AMOUNTS[k.is_seed()]:
                del compacted_inv[k]
        savefile.save(self.current_tool, self.current_seed, self.money, compacted_inv)

    def input(self):
        keys = pygame.key.get_pressed()
        recent_keys = pygame.key.get_just_pressed()
        if recent_keys[pygame.K_SPACE] and self.game.dm.showing_dialogue:
            self.game.dm.advance()
            if not self.game.dm.showing_dialogue:
                self.blocked = False
            return
        # movement
        if not self.tool_active and not self.blocked:
            if recent_keys[pygame.K_ESCAPE]:
                self.paused = not self.paused
                self.direction.y = 0
                self.direction.x = 0
                return
            if recent_keys[pygame.K_t]:
                if self.game.dm.showing_dialogue:
                    pass
                else:
                    self.game.dm.open_dialogue("test")
                    self.blocked = True
                return

        if not self.tool_active and not self.blocked and not self.paused:
            self.direction.x = int(
                keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
            self.direction.y = int(
                keys[pygame.K_DOWN]) - int(keys[pygame.K_UP])
            self.direction = (
                self.direction.normalize()
                if self.direction
                else self.direction
            )

            # tool switch
            if recent_keys[pygame.K_q]:
                self.tool_index = (self.tool_index + 1) % FarmingTool.get_tool_count()
                self.current_tool = FarmingTool(self.tool_index + FarmingTool.get_first_tool_id())

            # tool use
            if recent_keys[pygame.K_SPACE]:
                self.tool_active = True
                self.frame_index = 0
                self.direction = pygame.Vector2()
                if self.current_tool.is_swinging_tool():
                    self.sounds['swing'].play()

            # seed switch
            if recent_keys[pygame.K_e]:
                self.seed_index = (self.seed_index + 1) % FarmingTool.get_seed_count()
                self.current_seed = FarmingTool(self.seed_index + FarmingTool.get_first_seed_id())

            # seed used
            if recent_keys[pygame.K_LCTRL]:
                self.use_tool(ItemToUse.SEED)

                # interact
            if recent_keys[pygame.K_RETURN]:
                self.interact(self.rect.center)

    def move(self, dt):
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.collision('vertical')
        self.rect.center = self.hitbox_rect.center
        self.plant_collide_rect.center = self.hitbox_rect.center

    def get_current_tool_string(self):
        return self.available_tools[self.tool_index]

    def get_current_seed_string(self):
        return self.available_seeds[self.seed_index]

    def add_resource(self, resource, amount=1):
        super().add_resource(resource, amount)
        self.sounds['success'].play()

    def update(self, dt):
        self.input()
        super().update(dt)
