"""
Copyright 2023 Jobin Rezai

This file is part of LVNAuth.

LVNAuth is free software: you can redistribute it and/or modify it under the terms of
the GNU General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version.

LVNAuth is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along with
LVNAuth. If not, see <https://www.gnu.org/licenses/>.
"""

import pygame
from shared_components import Passer, ManualUpdate
from typing import NamedTuple, Tuple, List
from enum import Enum, auto


class RotateType(Enum):
    CLOCKWISE = auto()
    COUNTERCLOCKWISE = auto()


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


class FadeDelayMain:
    def __init__(self, fade_delay: FadeDelay):
        self.fade_delay = fade_delay
        self.frames_skipped_so_far = 0


class ScaleDelay(NamedTuple):
    sprite_name: str

    # The number of frames to skip by
    scale_delay: int


class ScaleDelayMain:
    def __init__(self, scale_delay: ScaleDelay):
        self.scale_delay = scale_delay
        self.frames_skipped_so_far = 0


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


class RotateDelayMain:
    def __init__(self, rotate_delay: RotateDelay):
        self.rotate_delay = rotate_delay
        self.frames_skipped_so_far = 0


class SpriteAnimationType(Enum):
    FADE = auto()
    SCALE = auto()
    MOVE = auto()
    ROTATE = auto()


class FadeType(Enum):
    FADE_IN = auto()
    FADE_OUT = auto()


class ScaleType(Enum):
    SCALE_UP = auto()
    SCALE_DOWN = auto()



class StartOrStop(Enum):
    START = auto()
    STOP = auto()


class MovementStops(Enum):
    """
    The side of the rectangle that is going to be checked to see
    if it has reached the destination co-ordinates or not.
    """
    RIGHT = auto()
    LEFT = auto()
    TOP = auto()
    BOTTOM = auto()


class ImagePositionX(Enum):
    START_OF_DISPLAY = auto()
    END_OF_DISPLAY = auto()
    BEFORE_START_OF_DISPLAY = auto()
    AFTER_END_OF_DISPLAY = auto()


class ImagePositionY(Enum):
    TOP_OF_DISPLAY = auto()
    ABOVE_TOP_OF_DISPLAY = auto()
    BOTTOM_OF_DISPLAY = auto()
    BELOW_BOTTOM_OF_DISPLAY = auto()


def str_to_position_type(position: str):
    """
    Take a string position name and return the Enum version of it.

    Example: "start of display" will return ImagePositionX.START_OF_DISPLAY
    :param position: str
    :return: ImagePositionX or ImagePositionY
    """
    matches = {"start of display": ImagePositionX.START_OF_DISPLAY,
               "end of display": ImagePositionX.END_OF_DISPLAY,
               "before start of display": ImagePositionX.BEFORE_START_OF_DISPLAY,
               "after end of display": ImagePositionX.AFTER_END_OF_DISPLAY,
               "top of display": ImagePositionY.TOP_OF_DISPLAY,
               "above top of display": ImagePositionY.ABOVE_TOP_OF_DISPLAY,
               "bottom of display": ImagePositionY.BOTTOM_OF_DISPLAY,
               "below bottom of display": ImagePositionY.BELOW_BOTTOM_OF_DISPLAY}

    return matches.get(position)


def rect_section_to_type(rect_section: str) -> MovementStops:
    """
    Convert a string section, such as 'top' to MovementStops.TOP
    :param rect_section: str such as left, top, right, left
    :return: MovementStops class object.
    """
    matches = {"left": MovementStops.LEFT,
               "right": MovementStops.RIGHT,
               "top": MovementStops.TOP,
               "bottom": MovementStops.BOTTOM}

    section = matches.get(rect_section)

    return section



class SpriteObject:

    def __init__(self,
                 name: str,
                 image: pygame.Surface,
                 general_alias: str):
        self.name = name
        self.general_alias = general_alias
        self.image = image
        self.rect = self.image.get_rect()

        self.original_image = image.copy()
        self.original_rect = self.original_image.get_rect()

        # Flags that will be checked in the .update() method
        # of this sprite, so we'll know to show or hide the sprite
        # the next time .update() is checked.
        self.pending_show = False
        self.pending_hide = False

        # So if the sprite gets replaced with another 'emotion', then
        # we'll know whether to flip the replacement sprite or not.
        self.flipped_horizontally = False
        self.flipped_vertically = False

        # Key: MovementStops enum (ie: TOP)
        # Value: int value (pixel position)
        self.stop_movement_conditions = {}

        # Will be based on the MovementStopRunScript class.
        self.movement_stop_run_script = None

        # Will be based on the MovementSpeed class.
        self.movement_speed: story_reader.MovementSpeed
        self.movement_speed = None

        # Will be based on the MovementDelay class.
        self.movement_delay = None

        # Used for skipping frames to simulate a movement delay.
        self.delay_frame_counter_x = 0
        self.delay_frame_counter_y = 0

        # The number of frames to skip for these animations

        # Will be based on the FadeDelayMain class
        self.fade_delay_main = None

        # Will be based on the ScaleDelayMain class
        self.scale_delay_main = None

        # Will be based on the RotateDelayMain class
        self.rotate_delay_main = None

        # Initialize
        self.is_moving = False
        self.is_fading = False
        self.is_scaling = False
        self.is_rotating = False

        # If any object has this flag set, the story script will not
        # continue to be read until the flag below has been set to False (for *all* sprite objects).
        self.wait_for_movement = False

        # Will be based on the FadeUntilValue class
        self.fade_until = None

        # Will be based on the FadeCurrentValue class
        self.current_fade_value = None

        # Will be based on the FadeStopRunScript class
        self.fade_stop_run_script = None

        # Will be based on the FadeSpeed class
        self.fade_speed = None

        # Will be based on the ScaleBy class
        self.scale_by = None

        # Will be based on the ScaleUntil class
        self.scale_until = None

        # Based on the ScaleCurrentValue class
        # Initialize the sprite to a scale of 1.0, which means regular size.
        # We initialize the sprite to 1.0 here so if scaling is used
        # without '<scale_current_value>', it will default to a regular size.
        self.scale_current_value = \
            ScaleCurrentValue(sprite_name=None,
                              scale_current_value=1.0)

        # Will be based on the ScaleStopRunScript class
        self.scale_stop_run_script = None

        # Will be based on the RotateCurrentValue class
        self.rotate_current_value = None

        # Will be based on the RotateSpeed class
        self.rotate_speed = None

        # Will be based on the RotateUntil class
        self.rotate_until = None

        # Will be based on the RotateStopRunScript class
        self.rotate_stop_run_script = None

        # self.sudden_fade_change = False
        self.sudden_scale_change = False
        self.sudden_rotate_change = False

        self.visible = False

    def start_fading(self):
        """
        Set the flag to indicate that fading animations should occur for this sprite.
        :return:
        """
        self.is_fading = True

    def stop_fading(self):
        """
        Reset the flag to indicate that fading animations should not occur for this sprite.
        :return:
        """
        self.is_fading = False

    def start_moving(self):
        """
        Set the flag to indicate that movement animations should occur for this sprite.
        :return:
        """
        self.is_moving = True

    def stop_moving(self):
        """
        Reset the flag to indicate that movement animations should not occur for this sprite.
        :return:
        """
        self.is_moving = False

    def stop_scaling(self):
        """
        Reset the flag to indicate that scaling animations should not occur for this sprite.
        :return:
        """
        self.is_scaling = False

    def start_scaling(self):
        """
        Set the flag to indicate that scaling animations should occur for this sprite.
        :return:
        """
        self.is_scaling = True

    def stop_rotating(self):
        """
        Reset the flag to indicate that rotating animations should not occur for this sprite.
        :return:
        """
        self.is_rotating = False

    def start_rotating(self):
        """
        Set the flag to indicate that rotating animations should occur for this sprite.
        :return:
        """
        self.is_rotating = True

    def _show(self) -> pygame.Rect | None:
        """
        Set the visibility flag to True, to indicate to the renderer that
        this sprite should be drawn on the screen. Return the rect
        of where this sprite currently is.

        This method is meant to be run from self.start_show() and not directly.
        """

        # We only use this flag each time a show is requested on
        # a sprite from a script, so we can reset it now.
        self.pending_show = False

        # Is this sprite already visible? return
        if self.visible:
            return

        self.visible = True

        return self.rect

    def _hide(self) -> pygame.Rect | None:
        """
        Set the visibility flag to False, to indicate to the renderer that
        this sprite should no longer be drawn on the screen. Return the rect
        of where this sprite currently is.

        This method is meant to be run from self.start_hide() and not directly.
        """

        # We only use this flag each time a hide is requested on
        # a sprite from a script, so we can reset it now.
        self.pending_hide = False

        # Is this sprite already invisible? return
        if not self.visible:
            return

        self.visible = False

        return self.rect

    def start_hide(self):
        """
        Set a boolean indicator flag which will be checked in this sprite's
        .update() method.

        We'll check this flag so we'll know to update the screen with this
        sprite's rect, because it will newly be set to become invisible.
        """
        self.pending_hide = True


        # In case a different method was called to show this
        # sprite in the same frame we're on.

        # For example: situations where <..hide> and <..show> one after another,
        # we can't have both show and hide pending.
        self.pending_show = False

    def start_show(self):
        """
        Set a boolean indicator flag which will be checked in this sprite's
        .update() method.

        We'll check this flag so we'll know to update the screen with this
        sprite's rect, because it will newly be set to become visible.
        """
        self.pending_show = True


        # In case a different method was called to hide this
        # sprite in the same frame we're on.

        # For example: situations where <..hide> and <..show> one after another,
        # we can't have both show and hide pending.
        self.pending_hide = False

    def movement_add_stop(self,
                          rect_area: MovementStops,
                          reaches_where: int | ImagePositionX | ImagePositionY):
        """
        Add a condition to stop a movement animation.

        There can be multiple stop conditions added by calling this method multiple times.

        :param rect_area: the part of the rect that we're concerned about when considering to stop an animation.
                          For example: MovementStops.TOP means when the 'top' of the rectangle reaches....

        :param reaches_where: the destination that the rect_area has to reach to satisfy this stop condition.
                              For example: 300 (for 300 pixels) or you can specify ImagePositionX or ImagePositionY,
                              such as ImagePositionY.TOP_OF_DISPLAY

                              If ImagePositionX or ImagePositionY is specified, they will automatically
                              be converted to a pixel coordinate in this method.
        :return: None
        """

        # # rect_area is allowed to be None, but only if reaches_where is ImagePositionX or ImagePositionY (no int).
        # if rect_area is None:
        if isinstance(reaches_where, ImagePositionX) \
                or isinstance(reaches_where, ImagePositionY):

            # rect_area is None and reaches_Where is ImagePositionX or ImagePositionY, so
            # get the pixel location of reaches_where and set the rect_area side automatically.
            rect_area, reaches_where = self._position_to_int(reaches_where)

        self.stop_movement_conditions[rect_area] = reaches_where

    def _position_to_int(self, image_position_x_or_y) -> Tuple[MovementStops, int]:
        """
        Convert an instance of ImagePositionX or ImagePositionY to a tuple (MovementStops, pixel coordinate)

        Purpose: this method is used to know where a sprite should stop. For example, if the given
                 argument is: ImagePositionX.BEFORE_START_OF_DISPLAY, then we'll know that the
                 rect's .left needs to be before the screen (so the sprite is not shown on the screen).

        :param image_position_x_or_y: instance of ImagePositionX or ImagePositionY
        :return: Tuple (example: MovementStops.LEFT, 0)
        """

        if isinstance(image_position_x_or_y, ImagePositionX):
            if image_position_x_or_y == ImagePositionX.BEFORE_START_OF_DISPLAY:
                # Start to the left, before the screen, the same amount as the width of the image.
                return MovementStops.LEFT, 0 - self.rect.width

            elif image_position_x_or_y == ImagePositionX.START_OF_DISPLAY:
                # Regular, start X at 0
                return MovementStops.LEFT, 0

            elif image_position_x_or_y == ImagePositionX.END_OF_DISPLAY:
                # Start at the right of the screen, but show the full image
                return MovementStops.RIGHT, Passer.active_story.screen_size[0]

            elif image_position_x_or_y == ImagePositionX.AFTER_END_OF_DISPLAY:
                # Start at the right of the screen, just after the image, causing it to be beyond the screen
                return MovementStops.LEFT, Passer.active_story.screen_size[0]

        elif isinstance(image_position_x_or_y, ImagePositionY):
            if image_position_x_or_y == ImagePositionY.ABOVE_TOP_OF_DISPLAY:
                # Start above the top of the window, before the screen, so the image is hidden.
                # self.rect.bottom = 0
                return MovementStops.TOP, 0 - self.rect.height

            elif image_position_x_or_y == ImagePositionY.TOP_OF_DISPLAY:
                # Start at the top of the display, showing the image
                return MovementStops.TOP, 0

            elif image_position_x_or_y == ImagePositionY.BOTTOM_OF_DISPLAY:
                # Start at the bottom of the display, with the image 'sitting at the bottom', showing the image.
                return MovementStops.BOTTOM, Passer.active_story.screen_size[1]

            elif image_position_x_or_y == ImagePositionY.BELOW_BOTTOM_OF_DISPLAY:
                # Start below the end of the screen, causing the image to be hidden.
                return MovementStops.TOP, Passer.active_story.screen_size[1]

    def set_center(self, center_x: int, center_y: int):
        """
        Change the .rect's center to the new pixel location specified in the argument.

        Used by command: <..set_center: >
        Example: <character_set_center: rave, 153, 45>

        Arguments:
        - center_x: (int) the x pixel position that we need to set this
        sprite's center to.

        - center_y: (int) the x pixel position that we need to set this
        sprite's center to.

        :return: None
        """

        # Make sure we have a center value.
        if center_x is None or center_y is None:
            return

        # If the sprite is visible, it means we're probably moving it
        # to a new center location, so get the old(current) position
        # and the new center position so we can combine it into one rect
        # for an update.
        if self.visible:

            # Record the rect before we move it.
            rect_before_moving = self.rect.copy()

        else:
            # The sprite is not even visible yet, so there is no 'before' rect.
            rect_before_moving = None


        # Make sure we have int arguments
        try:
            check_int_x = int(center_x)
            check_int_y = int(center_y)
        except ValueError:
            check_int_x = None
            check_int_y = None

        if check_int_x is None or check_int_y is None:
            return

        self.rect.center = (check_int_x, check_int_y)

        # For updating the change on the screen.
        if rect_before_moving:
            # Combine before/after rects to do one update.
            combined_rect = rect_before_moving.union(self.rect)
        else:
            # There is no 'before' rect
            # because the rect isn't currently visible.
            combined_rect = self.rect

        # Queue the combined rect for a manual screen update.
        # Regular animations (such as <character_start_moving: rave>)
        # are updated automatically, but since this is a manual animation,
        # we need to queue it for updating here.
        ManualUpdate.queue_for_update(combined_rect)

    def flip_match_with(self, other_sprite):
        """
        Match the flip settings of this sprite with another sprite object.

        Purpose: when a sprite is swapped out with another sprite, the
        sprite that is being swapped-in will get the same flip settings
        as the sprite that is being swapped-out.

        Arguments:

        - other_sprite: the SpriteObject to match the flip settings with.
        """

        # What kind of flips have occurred so far
        flip_horizontal = False
        flip_vertical = False

        # Do the horizontal flips match?
        if self.flipped_horizontally != other_sprite.flipped_horizontally:
            # The horizontal flips don't match, so horizontally-flip this sprite later in this method.
            flip_horizontal = True

        # Do the vertical flips match?
        if self.flipped_vertically != other_sprite.flipped_vertically:
            # The vertical flips don't match, so vertically-flip this sprite later in this method.
            flip_vertical = True

        # Flip this sprite if needed.
        self.flip(horizontal=flip_horizontal,
                  vertical=flip_vertical)

    def flip(self, horizontal: bool, vertical: bool):
        """
        Flip both the image surface and the original image surface.

        :param horizontal: if True, set the horizontal property to the opposite value.
        :param vertical: if True set the vertical property to the opposite value.
        :return: None
        """

        if horizontal:
            # Toggle horizontal value
            self.flipped_horizontally = not self.flipped_horizontally

        if vertical:
            # Toggle vertical value
            self.flipped_vertically = not self.flipped_vertically

        if all([horizontal, vertical]):
            self.image = pygame.transform.flip(self.image, True, True)
            self.original_image = pygame.transform.flip(self.original_image, True, True)
        elif horizontal:
            self.image = pygame.transform.flip(self.image, True, False)
            self.original_image = pygame.transform.flip(self.original_image, True, False)
        elif vertical:
            self.image = pygame.transform.flip(self.image, False, True)
            self.original_image = pygame.transform.flip(self.original_image, False, True)
        else:
            # No flips have occurred, so there is no need to request a screen-update.
            return

        # Queue the combined rect for a manual screen update.
        # Regular animations (such as <character_start_moving: rave>)
        # are updated automatically, but since this is a manual animation,
        # we need to queue it for updating here.
        ManualUpdate.queue_for_update(self.rect)

    def set_position_x(self,
                       position_type: ImagePositionX = None,
                       position_absolute_x: int = None):
        """
        Change the .rect to the new location specified in the argument.

        Used by command: <..set_position_x: >
        Example: <character_set_position_x: rave, end of display>

        Arguments:
        - position_type: from the class ImagePositionX

        - position_absolute_x: when position_type is not specified, an
        absolute int value can be specified (no words, just int value)

        :return: None
        """

        # Make sure we have a value for at least one argument.
        if position_type is None and position_absolute_x is None:
            return

            # If the sprite is visible, it means we're probably moving it
        # to a new center location, so get the old(current) position
        # and the new position so we can combine it into one rect
        # for an update.
        if self.visible:

            # Record the rect before we move it.
            rect_before_moving = self.rect.copy()

        else:
            # The sprite is not even visible yet, so there is no 'before' rect.
            rect_before_moving = None

        if position_absolute_x is not None:
            self.rect.left = position_absolute_x

        elif position_type == ImagePositionX.BEFORE_START_OF_DISPLAY:
            # Start to the left, before the screen, the same amount as the width of the image.
            self.rect.left = 0 - self.rect.width

        elif position_type == ImagePositionX.START_OF_DISPLAY:
            # Regular, start X at 0
            self.rect.left = 0

        elif position_type == ImagePositionX.END_OF_DISPLAY:
            # Start at the right of the screen, but show the full image
            self.rect.right = Passer.active_story.screen_size[0]

        elif position_type == ImagePositionX.AFTER_END_OF_DISPLAY:
            # Start at the right of the screen, just after the image, causing it to be beyond the screen
            self.rect.left = Passer.active_story.screen_size[0]


        # For updating the change on the screen.
        if rect_before_moving:
            # Combine before/after rects to do one update.
            combined_rect = rect_before_moving.union(self.rect)
        else:
            # There is no 'before' rect
            # because the rect isn't currently visible.
            combined_rect = self.rect

        # Queue the combined rect for a manual screen update.
        # Regular animations (such as <character_start_moving: rave>)
        # are updated automatically, but since this is a manual animation,
        # we need to queue it for updating here.
        ManualUpdate.queue_for_update(combined_rect)

    def set_position_y(self,
                       position_type: ImagePositionY = None,
                       position_absolute_y: int = None):
        """
        Change the .rect to the new location specified in the argument.

        Used by command: <..set_position_y: >
        Example: <character_set_position_y: rave_normal, bottom of display>

        Arguments:
        - position_type: from the class ImagePositionY

        - position_absolute_y: when position_type is not specified, an
        absolute int value can be specified (no words, just int value)

        :return: None
        """

        # Make sure we have a value for at least one argument.
        if position_type is None and position_absolute_y is None:
            return

        # If the sprite is visible, it means we're probably moving it
        # to a new center location, so get the old(current) position
        # and the new position so we can combine it into one rect
        # for an update.
        if self.visible:

            # Record the rect before we move it.
            rect_before_moving = self.rect.copy()

        else:
            # The sprite is not even visible yet, so there is no 'before' rect.
            rect_before_moving = None


        if position_absolute_y is not None:
            self.rect.top = position_absolute_y

        elif position_type == ImagePositionY.ABOVE_TOP_OF_DISPLAY:
            # Start above the top of the window, before the screen, so the image is hidden.
            # self.rect.bottom = 0
            self.rect.top = 0 - self.rect.height

        elif position_type == ImagePositionY.TOP_OF_DISPLAY:
            # Start at the top of the display, showing the image
            self.rect.top = 0

        elif position_type == ImagePositionY.BOTTOM_OF_DISPLAY:
            # Start at the bottom of the display, with the image 'sitting at the bottom', showing the image.
            self.rect.bottom = Passer.active_story.screen_size[1]

        elif position_type == ImagePositionY.BELOW_BOTTOM_OF_DISPLAY:
            # Start below the end of the screen, causing the image to be hidden.
            self.rect.top = Passer.active_story.screen_size[1]

        # For updating the change on the screen.
        if rect_before_moving:
            # Combine before/after rects to do one update.
            combined_rect = rect_before_moving.union(self.rect)
        else:
            # There is no 'before' rect
            # because the rect isn't currently visible.
            combined_rect = self.rect

        # Queue the combined rect for a manual screen update.
        # Regular animations (such as <character_start_moving: rave>)
        # are updated automatically, but since this is a manual animation,
        # we need to queue it for updating here.
        ManualUpdate.queue_for_update(combined_rect)

    def update(self):
        """
        Animate/move the sprite here.
        :return: updated rect or None if no changes occurred to this sprite.
        """

        # The list of update rects for all the animation updates.
        update_list = []

        # Should we show or hide this sprite? If so,
        # get the rect so we can update the screen
        # with its rect.

        if self.pending_show:
            # We're going to start showing this sprite.

            # Get the rect of where this sprite should show
            # so we can update the screen to make the sprite appear.
            show_rect = self._show()
            if show_rect:
                update_list.append(show_rect)

        elif self.pending_hide:
            # We're going to hide this sprite.

            # Return the rect of where this sprite is
            # so we can update the screen so the sprite no longer appears.
            return self._hide()


        # If this sprite is not visible, there is no point
        # in animating it.
        if not self.visible:
            return

        # Note: it's important to do the fading animation last because otherwise
        # the faded image will get overwritten with the original image in the other animations.
        update_rect_scaling = self._animate_scaling()
        update_rect_movement = self._animate_movement()
        update_rect_rotate = self._animate_rotation()
        update_rect_fade = self._animate_fading()

        # if isinstance(self, DialogSprite):
        # print("It's a dialog")
        # update_rect_movement = self.get_screen_coordinates(
        # update_rect_movement)


        # Only add a rect if it's not None.
        for rect in (update_rect_scaling, update_rect_movement, update_rect_fade, update_rect_rotate):
            if rect:
                update_list.append(rect)

        if not update_list:
            return

        # Create one rect from all the updated rects in this sprite.
        one_rect = update_list[0].unionall(update_list)

        return one_rect

    def _animate_rotation(self):
        """
        Rotate the sprite (if required).
        :return: updated rect or None if no rotation occurs.
        """

        # Did the rotation value change without an animation?
        # If so, rotate the sprite and return the new rect.
        if self.sudden_rotate_change:
            self.sudden_rotate_change = False
            return self._scale_or_rotate_sprite()

        # Not rotating the sprite or no rotation speed set? Return.
        if not self.is_rotating or not self.rotate_speed:
            return

        # Initialize for below
        skip_rotate = False

        # Should we skip rotating this sprite in this frame,
        # due to a rotate delay?
        if self.rotate_delay_main:
            if self.rotate_delay_main.frames_skipped_so_far >= self.rotate_delay_main.rotate_delay.rotate_delay:
                # Don't skip this frame for the rotate effect,
                # it has been delayed enough times already.
                self.rotate_delay_main.frames_skipped_so_far = 0
            else:
                # Don't rotate in this frame and increment skipped counter
                self.rotate_delay_main.frames_skipped_so_far += 1
                skip_rotate = True

        if not skip_rotate:

            # Are we rotating clockwise (negative value) or counter-clockwise? (positive value)
            # We need to know so we can determine when to stop the rotating (if a stop has been set).
            if self.rotate_speed.rotate_speed > 0:
                rotate_type = RotateType.COUNTERCLOCKWISE
            elif self.rotate_speed.rotate_speed < 0:
                rotate_type = RotateType.CLOCKWISE
            else:
                return

            # Initialize
            reached_destination_rotate = False

            # Has the sprite reached the destination rotate value?
            if rotate_type == RotateType.COUNTERCLOCKWISE:

                # if rotate_until is None, it means rotate continuously.
                if self.rotate_until and self.rotate_current_value.rotate_current_value >= self.rotate_until.rotate_until:
                    # Stop the rotation
                    self.stop_rotating()
                    reached_destination_rotate = True
                else:
                    # Rotate counterclockwise
                    new_rotate_value = self.rotate_current_value.rotate_current_value + self.rotate_speed.rotate_speed

                    if new_rotate_value >= 360:
                        new_rotate_value = 0

                    self.rotate_current_value = self.rotate_current_value._replace \
                        (rotate_current_value=new_rotate_value)

            # if rotate_until is None, it means rotate continuously.
            elif rotate_type == RotateType.CLOCKWISE:

                if self.rotate_until and self.rotate_current_value.rotate_current_value <= self.rotate_until.rotate_until:
                    # Stop the rotation
                    self.stop_rotating()
                    reached_destination_rotate = True
                else:
                    # Rotate clockwise
                    new_rotate_value = self.rotate_current_value.rotate_current_value + self.rotate_speed.rotate_speed

                    if new_rotate_value < 0:
                        new_rotate_value = 360

                    self.rotate_current_value = self.rotate_current_value._replace \
                        (rotate_current_value=new_rotate_value)

            # Have we reached a destination rotation which caused the rotating to stop?
            if reached_destination_rotate:
                # Yes, the rotation has now stopped because we've reached a specific rotation value.

                # Should we run a specific script now that the rotating animation
                # has stopped for this sprite?
                if self.rotate_stop_run_script.reusable_script_name:

                    # Get the name of the script we need to run now.
                    reusable_script_name = self.rotate_stop_run_script.reusable_script_name

                    # Clear the variable that holds information about which script we need to run
                    # because we're about to load that specified script below.
                    # If we don't clear this variable, it will run the specified script again
                    # once the sprite stops rotating next time.
                    self.rotate_stop_run_script = None

                    # Run the script that is supposed to run now that this sprite has stopped rotating.
                    Passer.active_story.reader.spawn_new_background_reader(reusable_script_name=reusable_script_name)

                return

        # Skipping the animation in this frame due to a delay?
        # Don't apply the current value of the animation effect
        # if it's the *only* active animation.
        if skip_rotate:
            if self._is_only_active_animation(animation_type=SpriteAnimationType.ROTATE):
                # Don't apply this animation in this frame,
                # because it's the only animation and it's currently
                # on a delayed pause.
                return

        rect = self._scale_or_rotate_sprite()
        return rect

    def _animate_scaling(self):
        """
        Scale the sprite (if required).
        :return: updated rect or None if no scaling occurs.
        """

        # Did the scale value change without an animation?
        # If so, scale the sprite and return the new rect.
        if self.sudden_scale_change:
            self.sudden_scale_change = False
            return self._scale_or_rotate_sprite()

        # Not scaling the sprite or no scale speed set
        # or no scale_until set? Return.
        if not all((self.is_scaling, self.scale_by, self.scale_until)):
            return

        # Initialize for below
        skip_scale = False

        # Should we skip scaling this sprite in this frame, due to a scale delay?
        if self.scale_delay_main:
            if self.scale_delay_main.frames_skipped_so_far >= self.scale_delay_main.scale_delay.scale_delay:
                # Don't skip this frame for the scale effect,
                # it has been delayed enough times already.
                self.scale_delay_main.frames_skipped_so_far = 0
            else:
                # Don't scale in this frame and increment skipped counter
                self.scale_delay_main.frames_skipped_so_far += 1
                skip_scale = True

        if not skip_scale:

            # Are we scaling up or scaling down?
            # We need to know so we can determine when to stop the scaling (if a stop has been set).
            if self.scale_by.scale_by > 0:
                scale_type = ScaleType.SCALE_UP
            elif self.scale_by.scale_by < 0:
                scale_type = ScaleType.SCALE_DOWN
            else:
                return

            # Initialize
            reached_destination_scale = False

            # Has the sprite reached the destination scale value?
            if scale_type == ScaleType.SCALE_UP:
                if self.scale_current_value.scale_current_value >= self.scale_until.scale_until:
                    # Stop the scaling
                    self.stop_scaling()
                    reached_destination_scale = True
                else:
                    # Increment scaling
                    new_scale_value = self.scale_current_value.scale_current_value + self.scale_by.scale_by

                    self.scale_current_value = self.scale_current_value._replace(scale_current_value=new_scale_value)

            elif scale_type == ScaleType.SCALE_DOWN:
                if self.scale_current_value.scale_current_value <= self.scale_until.scale_until:
                    # Stop the scaling
                    self.stop_scaling()
                    reached_destination_scale = True
                else:
                    # Decrease scaling
                    new_scale_value = self.scale_current_value.scale_current_value + self.scale_by.scale_by
                    if new_scale_value <= 0:
                        new_scale_value = 0

                    self.scale_current_value = self.scale_current_value._replace(scale_current_value=new_scale_value)

            # Have we reached a destination scaling which caused the scaling to stop?
            if reached_destination_scale:
                # Yes, the scaling has now stopped because we've reached a specific scaling value.

                # Should we run a specific script now that the scaling animation
                # has stopped for this sprite?
                if self.scale_stop_run_script and \
                        self.scale_stop_run_script.reusable_script_name:

                    # Get the name of the script we need to run now.
                    reusable_script_name = self.scale_stop_run_script.reusable_script_name

                    # Clear the variable that holds information about which script we need to run
                    # because we're about to load that specified script below.
                    # If we don't clear this variable, it will run the specified script again
                    # once the sprite stops scaling next time.
                    self.scale_stop_run_script = None

                    # Run the script that is supposed to run now that this sprite has stopped scaling.
                    Passer.active_story.reader.spawn_new_background_reader(reusable_script_name=reusable_script_name)

                return

        # Skipping the animation in this frame due to a delay?
        # Don't apply the current value of the animation effect
        # if it's the *only* active animation.
        if skip_scale:
            if self._is_only_active_animation(animation_type=SpriteAnimationType.SCALE):
                # Don't apply this animation in this frame,
                # because it's the only animation and it's currently
                # on a delayed pause.
                return

        rect = self._scale_or_rotate_sprite()

        return rect

    def _scale_or_rotate_sprite(self) -> pygame.Rect:
        """
        Scale and/or rotate the sprite and then return a rect
        that covers the old rect and the new rect combined into one rect.
        :return: rect
        """

        # So we can combine the old rect with the new rect
        old_rect = self.rect.copy()

        if self.scale_current_value:
            current_scale = self.scale_current_value.scale_current_value
        else:
            # Original size
            current_scale = 1

        if self.rotate_current_value:
            current_rotate = self.rotate_current_value.rotate_current_value
        else:
            # Original angle
            current_rotate = 0


        # Scale and/or rotate the image, which is based on the original image.
        self.image = pygame.transform.rotozoom(self.original_image, current_rotate, current_scale)

        # Get the new rect of the rotated or scaled image
        self.rect = self.image.get_rect(center=self.rect.center)

        combined_rect = old_rect.union(self.rect)

        return combined_rect

    def _is_only_active_animation(self, animation_type: SpriteAnimationType):
        """
        Check if the supplied animation-type is the only active animation
        for this sprite or not.

        Example: if a rotation animation is the *only* active animation for this
        sprite, and the animation_type (argument) is SpriteAnimationType.ROTATE,
        then this method will return True.

        Purpose of this method: when a delay is used on an animation (such as
        rotation or scale), we ideally shouldn't update the sprite on
        the screen when no animation is occuring during the delays/pauses.
        However, it's only safe to skip updating a sprite animation if there
        is one animation. If there are multiple animations enabled for this
        sprite, we need to constantly update the sprite on each frame.
        We use this method to know whether the sprite has only one kind of
        animation or not.

        Return: bool (True if there is only one animation for the given type
        or False if there are multiple animations on this sprite.)
        """
        animations = {animation_type.ROTATE: self.is_rotating,
                      animation_type.SCALE: self.is_scaling,
                      animation_type.FADE: self.is_fading}

        # Only keep active animations in the dictionary
        animations = {k: v for (k, v) in animations.items()
                      if v}

        if len(animations) == 1:
            is_enabled = animations.get(animation_type, False)
            return is_enabled

        return False

    def _animate_fading(self):
        """
        Fade the sprite (if required), but only if we know how far to fade the sprite.
        :return: updated rect or None if no fading occurs.
        """

        ## Did a sudden fade value change occur without an animation? (direct command)
        ## Then fade the sprite and return the rect of the sprite so it can be updated on the screen.
        # if self.sudden_fade_change:
        # self.sudden_fade_change = False
        # self._fade_sprite()
        # return self.rect

        # Not fading the sprite? Return.
        if not self.is_fading:
            return

            # If there is no fade_until value, but the fade
        # value is not fully opaque, then apply the fade,
        # even though we're not fading to a fade-destination.
        if not self.fade_until and self.current_fade_value is not None:
            if self.current_fade_value.current_fade_value < 255:
                self._fade_sprite()
                return

        # At this point, we need to know whether to fade out or fade in.
        # If that hasn't been decided (fade_speed), return
        if not self.fade_speed:
            return

        # Initialize for below
        skip_fade = False

        # Should we skip fading this sprite in this frame, due to a fade delay?
        if self.fade_delay_main:
            if self.fade_delay_main.frames_skipped_so_far >= self.fade_delay_main.fade_delay.fade_delay:
                # Don't skip this frame for the fade effect,
                # it has been delayed enough times already.
                self.fade_delay_main.frames_skipped_so_far = 0
            else:
                # Don't fade in this frame and increment skipped counter
                self.fade_delay_main.frames_skipped_so_far += 1
                skip_fade = True

        if not skip_fade:

            # Are we fading-in or fading-out? We need to know so that we can
            # determine when to stop the fade.
            if self.fade_speed.fade_direction == "fade in":  # > 0:
                fade_type = FadeType.FADE_IN
            elif self.fade_speed.fade_direction == "fade out":  # < 0:
                fade_type = FadeType.FADE_OUT
            else:
                return

            # Initialize
            reached_destination_fade = False

            # Has the sprite reached the destination fade value?
            if fade_type == FadeType.FADE_IN:
                if self.current_fade_value.current_fade_value >= self.fade_until.fade_value:

                    # Stop the fade, only if the opacity is full at 255
                    if self.current_fade_value.current_fade_value >= 255:
                        self.stop_fading()

                    # If the final fade value is less than 255, then
                    # we won't stop the fade (even though the fade has
                    # reached its destination value), because if we stop
                    # the fade animation, then in the next frame,
                    # the sprite will have full opacity.

                    reached_destination_fade = True
                else:
                    # Increment fade
                    new_fade_value = self.current_fade_value.current_fade_value + self.fade_speed.fade_speed
                    if new_fade_value > 255:
                        new_fade_value = 255

                    self.current_fade_value = self.current_fade_value._replace(current_fade_value=new_fade_value)

            elif fade_type == FadeType.FADE_OUT:
                if self.current_fade_value.current_fade_value <= self.fade_until.fade_value:

                    # We've reached the destination fade out value.
                    # Set a flag so we can check if a reusable script needs to run
                    reached_destination_fade = True

                    # We're not going to stop the fade, even though the fade
                    # has reached its fade-value destination,
                    # because if we stop the fade animation, then in the next frame,
                    # the sprite will have full opacity.

                else:
                    # Decrease fade
                    new_fade_value = self.current_fade_value.current_fade_value + self.fade_speed.fade_speed
                    if new_fade_value < 0:
                        new_fade_value = 0

                    self.current_fade_value = self.current_fade_value._replace(current_fade_value=new_fade_value)

            # Have we reached a destination fade which caused the fade to stop?
            if reached_destination_fade:
                # Yes, the fade has now stopped because we've reached a specific fade value.

                # Reset the fade_until value
                self.fade_until = None

                # Should we run a specific script now that the fade animation
                # has stopped for this sprite?
                if self.fade_stop_run_script and self.fade_stop_run_script.reusable_script_name:

                    # Get the name of the script we need to run now.
                    reusable_script_name = self.fade_stop_run_script.reusable_script_name

                    # Clear the variable that holds information about which script we need to run
                    # because we're about to load that specified script below.
                    # If we don't clear this variable, it will run the specified script again
                    # once the sprite stops fading next time.
                    self.fade_stop_run_script = None

                    # Run the script that is supposed to run now that this sprite has stopped fading.
                    Passer.active_story.reader.spawn_new_background_reader(reusable_script_name=reusable_script_name)

                # Apply the fade effect one last time for the destination fade amount
                # that we're in. Without this, the destination fade amount
                # won't get blitted.
                self._fade_sprite()

                return

        # Skipping the animation in this frame due to a delay?
        # Don't apply the current value of the animation effect
        # if it's the *only* active animation.
        if skip_fade:
            if self._is_only_active_animation(animation_type=SpriteAnimationType.FADE):
                # Don't apply this animation in this frame,
                # because it's the only animation and it's currently
                # on a delayed pause.
                return

        # We're haven't skipped fading in this frame, so apply
        # the fade and return the updated rect.
        self._fade_sprite()
        return self.rect


    def _fade_sprite(self):
        """
        Fade the sprite to the current fade value.

        If the sprite is being scaled (as an animation) or being rotated (as an animation),
        don't copy the original image, because then the scaling and/or rotation changes won't show.
        :return: None
        """

        if not self.is_scaling and not self.is_rotating:
            self.image = self.original_image.copy()

        self.image.fill((255, 255, 255, self.current_fade_value.current_fade_value), None, pygame.BLEND_RGBA_MULT)

    def _animate_movement(self):
        """
        Move the sprite (if required) and obey any delay rules for the movement.

        :return: updated rect or None if no movement occurs.
        """

        # Not moving the sprite or no instructions on speed? Return.
        if not self.is_moving or not self.movement_speed:
            return

        if self.stop_movement_conditions:

            satisfied_stop_keys = []

            # Have we reached the movement stop position for this sprite?
            for side, pixel_coordinate in self.stop_movement_conditions.items():
                # side is the side of the sprite we need to check for stops.
                # pixel_coordinate is the stop coordinate.

                # Check the left side of the sprite?
                if side == MovementStops.LEFT:

                    # How we check for a stop depends on the
                    # direction the sprite is moving.
                    if self.movement_speed.x_direction == "left":
                        # The sprite is moving left

                        if self.rect.left <= pixel_coordinate:
                            satisfied_stop_keys.append(side)

                    elif self.movement_speed.x_direction == "right":
                        # The sprite is moving right

                        if self.rect.left >= pixel_coordinate:
                            satisfied_stop_keys.append(side)

                            # Check the right side of the sprite for stops?
                elif side == MovementStops.RIGHT:

                    # How we check for a stop depends on the
                    # direction the sprite is moving.
                    if self.movement_speed.x_direction == "right":
                        # The sprite is moving right

                        if self.rect.right >= pixel_coordinate:
                            satisfied_stop_keys.append(side)

                    elif self.movement_speed.x_direction == "left":
                        # The sprite is moving left

                        if self.rect.right <= pixel_coordinate:
                            satisfied_stop_keys.append(side)

                            # Check the top of the sprite for a stop?
                elif side == MovementStops.TOP:

                    # How we check for a stop depends on the
                    # direction the sprite is moving.

                    if self.movement_speed.y_direction == "up":
                        # The sprite is moving up

                        if self.rect.top <= pixel_coordinate:
                            satisfied_stop_keys.append(side)

                    if self.movement_speed.y_direction == "down":
                        # The sprite is moving down

                        if self.rect.top >= pixel_coordinate:
                            satisfied_stop_keys.append(side)

                            # Check the bottom of the sprite for a stop?
                elif side == MovementStops.BOTTOM:

                    # How we check for a stop depends on the
                    # direction the sprite is moving.

                    if self.movement_speed.y_direction == "down":
                        # The sprite is moving down

                        if self.rect.bottom >= pixel_coordinate:
                            satisfied_stop_keys.append(side)

                    elif self.movement_speed.y_direction == "up":
                        # The sprite is moving up

                        if self.rect.bottom <= pixel_coordinate:
                            satisfied_stop_keys.append(side)

            if satisfied_stop_keys:
                # Remove movement stop positions that have already been satisfied.
                for key in satisfied_stop_keys:
                    del self.stop_movement_conditions[key]

                # No more stop conditions? Stop the movement of this sprite.
                if not self.stop_movement_conditions:
                    self.stop_moving()

                    # Should we run a specific reusable script now that the movement has stopped?
                    # (this is if 'character_after_movement_stop' has been used on this sprite).
                    if self.movement_stop_run_script:

                        # Get the name of the script we need to run now.
                        reusable_script_name = self.movement_stop_run_script.reusable_script_name

                        # At this point, we know the reusable script name we need to run, now that this
                        # sprite has stopped moving.
                        # So clear the variable that holds information about which script we need to run
                        # because we're about to load that specified script below.
                        # If we don't clear this variable, it will run the specified script again
                        # once the sprite stops moving next time.
                        self.movement_stop_run_script = None

                        # Run the script that is supposed to run now that this sprite has stopped moving.
                        Passer.active_story.reader.spawn_new_background_reader \
                            (reusable_script_name=reusable_script_name)

                    return

        # For now, we'll assume we will be moving both x and y
        proceed_move_x = True
        proceed_move_y = True

        # Should we delay/skip the movement of this sprite?
        if self.movement_delay:
            # Yes, we need to consider the delay of x or y or both.

            # Are we delaying the movement of x?
            if self.movement_delay.x > 0:
                # Yes, consider delaying the movement of x

                # Increment delay counter so we can keep track of how many frames we've skipped so far.
                self.delay_frame_counter_x += 1

                # Have we skipped the movement of x enough times?
                if self.delay_frame_counter_x < self.movement_delay.x:
                    # We haven't skipped enough times.
                    proceed_move_x = False
                else:
                    # We've skipped enough times, to reset the delay counter.
                    # At this point, we will proceed with moving x.
                    self.delay_frame_counter_x = 0

            # Are we delaying the movement of y?
            if self.movement_delay.y > 0:
                # Yes, consider delaying the movement of y

                # Increment delay counter so we can keep track of how many frames we've skipped so far.
                self.delay_frame_counter_y += 1

                # Have we skipped the movement of y enough times?
                if self.delay_frame_counter_y < self.movement_delay.y:
                    # We haven't skipped enough times.
                    proceed_move_y = False
                else:
                    # We've skipped enough times, to reset the delay counter.
                    # At this point, we will proceed with moving y.
                    self.delay_frame_counter_y = 0

        # Keep track of where the sprite is before we move it
        # so that we can create an update rect later on.
        old_rect = self.rect.copy()

        # Initialize
        moved = False

        if proceed_move_x:
            self.rect.move_ip(self.movement_speed.x, 0)
            moved = True

        if proceed_move_y:
            self.rect.move_ip(0, self.movement_speed.y)
            moved = True

        # Have we moved the sprite?
        if moved:
            # Create a union rect that combines the old rect position and the new position.
            update_rect = old_rect.union(self.rect)
            return update_rect


class SpriteGroup:

    def __init__(self):
        self.update_rects = []

        # Key: sprite name (str)
        # Value: sprite object (SpriteObject)
        self.sprites = {}

    def add(self, name: str, sprite: SpriteObject):
        if name not in self.sprites:
            self.sprites[name] = sprite

    def remove(self, name: str) -> bool:
        sprite = self.sprites.get(name)
        if not sprite:
            return

        update_rect = sprite.rect
        self.update_rects.append(update_rect)

        del self.sprites[name]

    def hide_all(self):
        """
        Hide all the sprites in this group
        by settings the visibility to False.

        Purpose: when using <background_show>, it needs to hide
        the existing background before showing the new one (like a toggle).

        Also used for hiding all 'name' objects.
        """
        for sprite in self.sprites.values():

            if sprite.visible or sprite.pending_show:
                sprite.start_hide()

    def clear(self):
        """
        Clear all the loaded sprites in this group's dictionary.

        Purpose: this method gets called before a new scene is loaded.
        """
        self.sprites.clear()

    def update(self):
        """
        Loop through all the sprites in this group and run the update() method on each one.
        :return: None
        """
        sprite: SpriteObject
        for sprite in self.sprites.values():

            # Get a regular animation update rect
            # This will be one rect for multiple animations (fade,scale, etc.)
            new_rect = sprite.update()

            if new_rect:
                self.update_rects.append(new_rect)

    def get_updated_rects(self) -> List[pygame.Rect]:
        """
        # Get all the rects for update sprites.

        # The caller of this method will use the list of update rects
        # to update the screen for just rects that have been changed.
        :return: List[pygame.Rect]
        """

        # Get a copy of all the updated rects in this group.
        updated_rects = self.update_rects.copy()

        # Clear for the next animation loop.
        self.update_rects.clear()

        return updated_rects

    def draw(self, surface: pygame.Surface):

        sprite: SpriteObject
        for sprite in self.sprites.values():
            if sprite.visible:
                surface.blit(sprite.image, sprite.rect)


class Character(SpriteObject):
    def __init__(self, name, image, general_alias):
        super().__init__(name, image, general_alias)


class DialogSprite(SpriteObject):
    def __init__(self, name, image, general_alias):
        super().__init__(name, image, general_alias)

    def get_screen_coordinates(self, inner_sprite_rect: pygame.Rect) -> Tuple:
        """
        Return the X and Y coordinates of the given dialog sprite,
        relative to the size of the main surface.
        """
        if not all([Passer.active_story.dialog_rectangle_rect, inner_sprite_rect]):
            return

        dialog_x = Passer.active_story.dialog_rectangle_rect.left
        dialog_y = Passer.active_story.dialog_rectangle_rect.top

        new_rect = pygame.Rect(dialog_x + inner_sprite_rect.left,
                               dialog_y + inner_sprite_rect.top,
                               inner_sprite_rect.width,
                               inner_sprite_rect.height)

        return new_rect


class Background(SpriteObject):
    def __init__(self, name, image, general_alias):
        super().__init__(name, image, general_alias)


class Name(SpriteObject):
    def __init__(self, name, image, general_alias):
        super().__init__(name, image, general_alias)


class Groups:
    character_group = SpriteGroup()
    background_group = SpriteGroup()
    object_group = SpriteGroup()
    dialog_group = SpriteGroup()
