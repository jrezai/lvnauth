"""
Copyright 2023-2025 Jobin Rezai

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

from typing import NamedTuple


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
    number_of_frames: int


class Rest(NamedTuple):
    number_of_frames: int


class WaitForAnimation(NamedTuple):
    sprite_type: str
    general_alias: str
    animation_type: str


class WaitForAnimationFadeScreen(NamedTuple):
    fade_screen: str


class SceneWithFade(NamedTuple):
    hex_color: str
    fade_in_speed: int
    fade_out_speed: int
    fade_hold_for_frame_count: int
    chapter_name: str
    scene_name: str


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
    number_of_frames: int
    
    
class SpriteTextDelayPunc(NamedTuple):
    sprite_type: str
    general_alias: str
    previous_letter: str
    number_of_frames: int
    

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


class MouseEventRunScriptNoArguments(NamedTuple):
    sprite_name: str
    reusable_script_name: str
    
    
class MouseEventRunScriptWithArguments(NamedTuple):
    sprite_name: str
    reusable_script_name: str
    arguments: str


class Flip(NamedTuple):
    general_alias: str


class FontTextFadeSpeed(NamedTuple):
    fade_speed: int


class FontTextDelay(NamedTuple):
    number_of_seconds: float

    
class FontTextDelayPunc(NamedTuple):
    previous_letter: str
    number_of_milliseconds: float


class FontStartPosition(NamedTuple):
    start_position: int
    
    
class FontIntroAnimation(NamedTuple):
    animation_type: str


class FontOutroAnimation(NamedTuple):
    animation_type: str


class AfterWithArguments(NamedTuple):
    frames_elapse: int
    reusable_script_name: str
    arguments: str

    
class AfterWithoutArguments(NamedTuple):
    frames_elapse: int
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


class MovementSpeed(NamedTuple):
    sprite_name: str
    x: int
    x_direction: str
    y: int
    y_direction: str


class MovementDelay(NamedTuple):
    sprite_name: str
    x: int
    y: int


class MovementStopRunScript(NamedTuple):
    sprite_name: str
    reusable_script_name: str

    
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


class FadeUntilValue(NamedTuple):
    sprite_name: str
    fade_value: float


class FadeCurrentValue(NamedTuple):
    sprite_name: str
    current_fade_value: int


class FadeSpeed(NamedTuple):
    sprite_name: str
    fade_speed: float
    fade_direction: str  # "fade in" or "fade out"


class FadeStopRunScript(NamedTuple):
    sprite_name: str
    reusable_script_name: str


class FadeDelay(NamedTuple):
    sprite_name: str

    # The number of frames to skip by
    fade_delay: int


class ScaleDelay(NamedTuple):
    sprite_name: str

    # The number of frames to skip by
    scale_delay: int


class ScaleBy(NamedTuple):
    sprite_name: str
    scale_by: float
    scale_rotation: str


class ScaleUntil(NamedTuple):
    sprite_name: str
    scale_until: float


class ScaleCurrentValue(NamedTuple):
    sprite_name: str
    scale_current_value: float


class ScaleStopRunScript(NamedTuple):
    sprite_name: str
    reusable_script_name: str


class RotateCurrentValue(NamedTuple):
    sprite_name: str
    rotate_current_value: float


class RotateSpeed(NamedTuple):
    sprite_name: str
    rotate_speed: float
    rotate_direction: str


class RotateStopRunScript(NamedTuple):
    sprite_name: str
    reusable_script_name: str


class RotateUntil(NamedTuple):
    sprite_name: str
    rotate_until: str  # str because the word 'forever' can be used.


class RotateDelay(NamedTuple):
    sprite_name: str

    # The number of frames to skip when rotating a sprite.
    rotate_delay: int
