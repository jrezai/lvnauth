"""
Copyright 2023-2026 Jobin Rezai

This file is part of LVNAuth.

LVNAuth is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

LVNAuth is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with LVNAuth.  If not, see <https://www.gnu.org/licenses/>.
"""

"""
Change logs

- (Jobin Rezai - July 12, 2025) - Added RemoteWithGet class.
"""

from typing import NamedTuple, List
from dataclasses import dataclass, fields, field, InitVar
from enum import Enum


def get_dataclass_field_names(class_blueprint) -> List:
    """
    Return a list of field names in a dataclass.
    Get the public names, not the _private names. Reason: if a dataclass
    is using a getter/setter, getting the field names the regular way will
    give us the private names starting with an underscore. This function
    removes the underscore from the field names.
    
    Example: ['alias', 'arguments']
    """
    field_names = []
    
    # Enumerate the dataclass fields
    for field in fields(class_blueprint):
        
        # Get the name of the dataclass
        # Example: 'arguments'
        name = field.name
        
        # If the name starts with an underscore, strip it for the 
        # 'public' version
        # Example: _count becomes count
        if name.startswith('_'):
            name = name[1:]
            
        field_names.append(name)
        
    return field_names



class DialogRectangleDefinition(NamedTuple):
    width: int
    height: int
    animation_speed: float
    intro_animation: str
    outro_animation: str
    anchor: str
    bg_color_hex: str
    padding_x: int
    padding_y: int
    opacity: int
    rounded_corners: str
    reusable_on_intro_starting: str
    reusable_on_intro_finished: str
    reusable_on_outro_starting: str
    reusable_on_outro_finished: str
    reusable_on_halt: str
    reusable_on_unhalt: str
    border_color_hex: str
    border_opacity: int
    border_width: int


class VariableSet(NamedTuple):
    variable_name: str
    variable_value: str


class Continue(NamedTuple):
    adjust_y: int


class HaltAuto(NamedTuple):
    number_of_seconds: float



class CenterSprite(NamedTuple):
    sprite_name: str
    x: int
    y: int


class Rest(NamedTuple):
    number_of_seconds: float


class WaitForAnimation(NamedTuple):
    sprite_type: str
    general_alias: str
    animation_type: str


class WaitForAnimationEntireScreen(NamedTuple):
    screen_animation_type: str


class SceneWithFade(NamedTuple):
    hex_color: str
    fade_in_speed: int
    fade_out_speed: int
    fade_hold_seconds: int
    chapter_name: str
    scene_name: str
    
    
    
@dataclass
class SequencePlay:
    """
    Used by <sequence_play>
    Example:
    <sequence_play: 3>
    <sequence_play: repeat>
    """
    sequence_name: str
    
    # We have this as a string instead of an int because we need to
    # read the word 'repeat'
    number_of_times: str
    

@dataclass
class SequenceCreate:
    """
    Used by <sequence_create> and <sequence_delay>
    Example uses:
    <sequence_create: sequence name, character, 0.1, theo_1, theo_2, theo_3>
    <sequence_delay: sequence name, character, 0.5, theo_1, theo_2>
    """
    sequence_name: str
    _sprite_type: str
    delay: float
    arguments: str
    
    @property
    def sprite_type(self) -> str:
        return self._sprite_type
    
    @sprite_type.setter
    def sprite_type(self, value: str):
        """
        Only specific sprite type values are allowed.
        """
        # Store the value in lowercase so it'll work with dictionary lookups.
        if value:
            value = value.lower()
            
        if value not in ("character", "object", "dialog sprite"):
            self._sprite_type = None
        else:
            self._sprite_type = value
            

@dataclass
class SequenceStop:
    sequence_name: str
    
    
@dataclass
class CameraMovement:
    target_x: int
    target_y: int
    zoom: float
    _duration_seconds: float
    smoothing_style: str
    
    @property
    def duration_seconds(self) -> float:
        return self._duration_seconds
    
    @duration_seconds.setter
    def duration_seconds(self, value: float):
        """
        Enforce clamping to between 0.01 and 100.
        """
        self._duration_seconds = max(0.01, min(value, 100.0))
    
    def __post_init__(self):
        # Make sure the smoothing style is lowercase
        self.smoothing_style = self.smoothing_style.lower()
    
    
    
class CameraShake(NamedTuple):
    intensity: float
    duration_seconds: float
    
    
class CameraStopChoice(Enum):
    
    # We don't use 'auto' here because when editing the command via 
    # the context menu, we instantiate the CameraStopWhere class using 
    # one of the strings below, so the enum values below need to accept
    # those string values.
    AT_CURRENT_SPOT = "current spot"
    JUMP_TO_END = "jump to end"
    
    # So none of the radio buttons gets selected when editing
    # when it's an unknown argument.
    UNKNOWN = "unknown"
    
    
@dataclass
class CameraStopWhere:
    # "jump to end" or "current spot"
    arguments: str
    
    def __post_init__(self):
        # Make sure the given argument is always lowercase,
        # because they're keywords: "jump to end" or "current spot"
        self.arguments = self.arguments.lower()
    

class ConditionDefinition(NamedTuple):
    value1: str
    operator: str
    value2: str
    condition_name: str
    
    
# <case> has an optional condition_name argument.
# This class is used when no condition_name has been specified when editing.
class ConditionDefinitionNoConditionName(NamedTuple):
    value1: str
    operator: str
    value2: str


class PlayAudio(NamedTuple):
    audio_name: str
    
    
# Used by <play_music> when wanting to loop the music.
class PlayAudioLoop(NamedTuple):
    audio_name: str
    loop: str


class DialogTextSound(NamedTuple):
    audio_name: str
    

class Volume(NamedTuple):
    volume: int


class SpriteText(NamedTuple):
    sprite_type: str
    general_alias: str
    value: str
    
    
class SpriteTextDelay(NamedTuple):
    sprite_type: str
    general_alias: str
    number_of_seconds: int
    
    
class SpriteTextDelayPunc(NamedTuple):
    sprite_type: str
    general_alias: str
    previous_letter: str
    number_of_seconds: int
    

class SpriteFontIntroAnimation(NamedTuple):
    sprite_type: str
    sprite_name: str
    animation_type: str
    
    
class SpriteFontFadeSpeed(NamedTuple):
    sprite_type: str
    sprite_name: str
    fade_speed: int
    
    
class SpriteTextClear(NamedTuple):
    sprite_type: str
    general_alias: str
    
    
    
class SpriteTintRegular(NamedTuple):
    general_alias: str
    speed: int
    dest_tint: int
    
    
class SpriteTintBright(NamedTuple):
    general_alias: str
    speed: int
    dest_tint: int
    bright_keyword: str
    
    
class SpriteTintSolo(NamedTuple):
    general_alias: str


class Flip(NamedTuple):
    general_alias: str


class FontTextFadeSpeed(NamedTuple):
    fade_speed: int


class FontTextDelay(NamedTuple):
    number_of_seconds: float

    
class FontTextDelayPunc(NamedTuple):
    previous_letter: str
    number_of_seconds: float


class FontStartPosition(NamedTuple):
    start_position: int
    
    
class FontIntroAnimation(NamedTuple):
    animation_type: str


class FontOutroAnimation(NamedTuple):
    animation_type: str


class AfterWithArguments(NamedTuple):
    seconds_to_wait: float
    reusable_script_name: str
    arguments: str

    
class AfterWithoutArguments(NamedTuple):
    seconds_to_wait: float
    reusable_script_name: str
    

class AfterCancel(NamedTuple):
    reusable_script_name: str

    
class SceneLoad(NamedTuple):
    chapter_name: str
    scene_name: str


class CallWithArguments(NamedTuple):
    reusable_script_name: str
    arguments: str


class CallWithNoArguments(NamedTuple):
    reusable_script_name: str



class RemoteSave(NamedTuple):
    # Example:
    # <remote_save: favcolor=Blue, favpet=Cat>
    arguments: str
    
    
class RemoteGet(NamedTuple):
    # Remote with a single argument (save key name)
    
    # <remote_get: some key>
    save_key: str



class RemoteGetWithVariable(NamedTuple):
    # Remote with two arguments.
    # A save key and a variable to put the value into.
    
    # <remote_get: some_key, some variable>
    save_key: str
    variable_name: str



class RemoteCallNoArguments(NamedTuple):
    # Example:
    # <remote_call: some custom action name>
    remote_command: str
    
    
    
class RemoteCallWithArguments(NamedTuple):
    # Example:
    # <remote_call: some custom action name, character_name=some name, time=daytime>
    remote_command: str
    arguments: str
    
    

# Sprite classes


class MoveStart(NamedTuple):
    sprite_name: str
    x: int
    x_direction: str
    y: int
    y_direction: str


# Used for multiple commands, such as:
# character_after_fading_stop
# object_after_scaling_stop
# dialog_sprite_after_rotating_stop
# character_after_movement_stop
# character_on_mouse_enter, mouse_leave, mouse_click
class SpriteStopRunScriptNoArguments(NamedTuple):
    sprite_name: str
    reusable_script_name: str
    
    
# Used for multiple commands, such as:
# character_after_fading_stop
# object_after_scaling_stop
# dialog_sprite_after_rotating_stop
# character_after_movement_stop
# character_on_mouse_enter, mouse_leave, mouse_click
class SpriteStopRunScriptWithArguments(NamedTuple):
    sprite_name: str
    reusable_script_name: str
    arguments: str

    
# Used when the 'side to check' is specified (3 arguments)
class MovementStopCondition(NamedTuple):
    sprite_name: str
    side_to_check: str
    stop_location: str
    
    
# Used when the 'side to check' is automatic (2 arguments)
class MovementStopConditionShorter(NamedTuple):
    sprite_name: str
    stop_location: str
    
    
class SpritePosition(NamedTuple):
    sprite_name: str
    
    # Could be a fixed location such as 'start of display' or a pixel position.
    position: str


class SpriteShowHide(NamedTuple):
    sprite_name: str


class SpriteCenter(NamedTuple):
    sprite_name: str
    x: int
    y: int


class SpriteCenterWith(NamedTuple):
    alias_to_move: str
    sprite_type_to_center_with: str
    center_with_alias: str


class SpriteLoad(NamedTuple):
    sprite_name: str
    sprite_general_alias: str


class FadeCurrentValue(NamedTuple):
    sprite_name: str
    current_fade_value: int


    
class FadeStart(NamedTuple):
    sprite_name: str
    fade_speed: float
    fade_until: int



class ScaleStart(NamedTuple):
    sprite_name: str
    scale_speed: float
    scale_until: float


class ScaleCurrentValue(NamedTuple):
    sprite_name: str
    scale_current_value: float


class RotateCurrentValue(NamedTuple):
    sprite_name: str
    rotate_current_value: float
    
    

class RotateStart(NamedTuple):
    sprite_name: str
    rotate_direction: str
    rotate_speed: float
    rotate_until: str  # str because the word 'forever' can be used.
    