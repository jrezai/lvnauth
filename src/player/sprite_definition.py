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

import pygame
import font_handler
import command_class as cc
from shared_components import Passer, ManualUpdate, MouseActionsAndCoordinates
from typing import Tuple
from enum import Enum, auto
from datetime import datetime
from animation_speed import AnimationSpeed
from tint_handler import TintHandler, TintStyle



class RotateType(Enum):
    CLOCKWISE = auto()
    COUNTERCLOCKWISE = auto()



class SpriteAnimationType(Enum):
    FADE = auto()
    SCALE = auto()
    MOVE = auto()
    ROTATE = auto()


class FadeType(Enum):
    FADE_IN = auto()
    FADE_OUT = auto()
    FADE_REACHED_DESTINATION = auto()


class ScaleType(Enum):
    SCALE_UP = auto()
    SCALE_DOWN = auto()
    SCALE_REACHED_DESTINATION = auto()


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


# Used for knowing whether a sprite has entered over a sprite
# and if it has, the sprite's mouse flag gets set to HOVERING_OVER_SPRITE
# until it moves away from the sprite. We use this enum to prevent a reusable
# script from running multiple times when the mouse is over a sprite.
class SpriteMouseStatus(Enum):
    AWAY_FROM_SPRITE = auto()
    HOVERING_OVER_SPRITE = auto()



class SpriteObject:

    def __init__(self,
                 name: str,
                 image: pygame.Surface,
                 general_alias: str):
        

        self.name = name
        self.general_alias = general_alias
        self.image = image
        self.rect = self.image.get_rect()
        
        """
        Used for delta movements. A pygame rectangle can only hold
        integer values, so we need to keep track of the 'real' float movement
        positions before telling self.rect about the newly moved int positions.
        In other words, when we increment slightly, int values will be rounded
        to a whole number, but we need float values to keep the accurate
        non-rounded positions while the movement animation is occuring.
        pos_moving_x and pos_moving_y are only used during a movement 
        animation. They are not used anywhere else. Once a movement animation
        stops, these two variables are reset to zero until the next movement.
        Note: these two variables don't even get used for <position_x..> related
        commands. They're *just* for movement animations.
        """
        self.calculated_pos_moving_x:float
        self.calculated_pos_moving_x = 0
        self.calculated_pos_moving_y:float
        self.calculated_pos_moving_y = 0

        # We need a copy of the image before we apply any text to it, 
        # so that we don't blit the same text over and over again.
        # We're going to eventually copy this image to self.original_image
        # in the drawing loop. We will use the rect self.original_rect below.
        self.original_image_before_text = image.copy()

        # This will hold the original image, but may contain text.
        # The actual 100% original is in self.original_image_before_text
        # but this below is the second original which may or may not contain
        # text drawn on it. If there is no text drawn on it, then it will be
        # exactly the same as self.original_image_before_text
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
        self.movement_speed: cc.MovementSpeed
        self.movement_speed = None


        # Initialize
        self.is_moving = False
        self.is_fading = False
        self.is_scaling = False
        self.is_rotating = False

        # The effect amounts that are applied.
        # We use these to determine if we need to apply the effects
        # when there is no gradual animation (sudden effect changes).
        self.applied_fade_value = None
        self.applied_scale_value = None
        self.applied_rotate_value = None
        
        self.tint_handler = TintHandler()

        # If any object has this flag set, the story script will not
        # continue to be read until the flag below has been set to False (for *all* sprite objects).
        self.wait_for_movement = False

        # Will be based on the FadeUntilValue class
        self.fade_until = None

        """
        There are 3 variables for sprite fading.
        
        1) self.calculated_fade_value - This holds the float value of what
        the opacity should be, using the delta/time calculation since the
        last frame, for smooth fade transitioning regardless of the FPS.
        This is only used for time-fade calculations. The int() version of
        this variable's value is put into self.current_fade_value.
        
        2) self.current_fade_value - This holds what the fade value *should*
        be after a calculation, as an integer.
        
        3) self.applied_fade_value - This holds what fade value has actually
        been *applied* to the image. So self.current_fade_value holds what 
        opacity the image should be, and after each frame,
        self.applied_fade_value checks if it's the same value as
        self.current_fade_value, and if it's not, it applies the opacity
        to the original image and updates self.applied_fade_value.
        

        """
        # Will be based on the FadeCurrentValue class
        self.current_fade_value = None
        # For time-accuracy with delta calculations for each frame.
        self.calculated_fade_value:float = 0

        # Will be based on the FadeStopRunScript class
        self.fade_stop_run_script = None

        # Will be based on the FadeSpeed class
        self.fade_speed:cc.FadeSpeed
        self.fade_speed = None

        # Will be based on the ScaleSpeed class
        self.scale_speed: cc.ScaleSpeed
        self.scale_speed = None
        
        # So the animation method knows which direction to scale, up or down.
        self.scale_type: ScaleType
        self.scale_type = None

        # Will be based on the ScaleUntil class
        self.scale_until: cc.ScaleUntil
        self.scale_until = None

        # Based on the ScaleCurrentValue class
        # Initialize the sprite to a scale of 1.0, which means regular size.
        # We initialize the sprite to 1.0 here so if scaling is used
        # without '<scale_current_value>', it will default to a regular size.
        self.scale_current_value = \
            cc.ScaleCurrentValue(sprite_name=None,
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
        # self.sudden_scale_change = False
        # self.sudden_rotate_change = False
        
        # Used for making sure the mouse event reusable scripts
        # are executed only once for each mouse event change.
        # If we didn't have this, a mouse hover event could have run
        # a reusable script each time the mouse moved on a sprite.
        self.mouse_status: SpriteMouseStatus = SpriteMouseStatus.AWAY_FROM_SPRITE
        
        # Names of reusable scripts to run after specific mouse events.
        self.on_mouse_enter_run_script: cc.SpriteStopRunScriptWithArguments = None
        self.on_mouse_leave_run_script: cc.SpriteStopRunScriptWithArguments = None
        self.on_mouse_click_run_script: cc.SpriteStopRunScriptWithArguments = None
        
        # Deals with showing/hiding sprite text
        self.active_font_handler =\
            font_handler.ActiveFontHandler(story=Passer.active_story,
                                           sprite_object=self)        

        self.visible = False

    def clear_text_and_redraw(self):
        """
        Copy the image that doesn't have any text on it
        (self.original_image_before_text) to self.original_image.
        
        Then, update self.image and apply any scale/rotation/fade that it needs,
        because once we copy self.original_image to self.image, it won't
        have any alterations (no rotation,scale,fade), so we need to re-apply
        those to the new image that has no text, if the previous image with
        text had those things applied to it.
        """

        # This sprite has no text? return
        if not self.active_font_handler:
            return
        elif not self.active_font_handler.letters_to_blit:
            return

        # Clear the list that's used for blitting letters.
        self.active_font_handler.clear_letters()

        # Clear the cursor position in case text was shown gradually.
        self.active_font_handler.font_animation.gradual_letter_cursor_position = 0

        # Get the original image that has no text blitted on it.
        # We might need to apply a scale/rotation/fade to it later.
        self.original_image = self.get_original_image_without_text()

        

        ## If self.image wasn't replaced by any of the scale/rotation/fade
        ## method calls here, then replace self.image with the original image now.
        ## This will cause the sprite's display image to change to the version
        ## that doesn't contain text.
        ## if not replaced_display_image:
        #self.image = self.get_original_image_with_text()
        
        self._apply_still_effects()

        ManualUpdate.queue_for_update(self.rect)

    def start_fading(self):
        """
        Set the flag to indicate that fading animations should occur
        for this sprite.
        """
        
        # There has to be a fade_until value for the fade to work.
        # fade_until is used to determine the direction of the fade (fade-in or
        # fade-out).
        if self.fade_until is None:
            return
                
        self.is_fading = True

    def stop_fading(self):
        """
        Reset the flag to indicate that fading animations should not occur for this sprite.
        :return:
        """
        self.is_fading = False
        
        # Now that the fading animation has stopped, we no longer need
        # the float fade value, so reset it for the next fading animation.        
        self.calculated_fade_value = 0

    def start_moving(self):
        """
        Set the flag to indicate that movement animations should occur
        for this sprite.
        
        Return: None
        """
        self.is_moving = True
        
        # Record where the image (surface) currently is so we can use
        # pos_moving_x and pos_moving_y for float movement calculations.
        self.calculated_pos_moving_x = self.rect.x
        self.calculated_pos_moving_y = self.rect.y

    def stop_moving(self):
        """
        Reset the flag to indicate that movement animations should not occur
        for this sprite.
        
        Return: None
        """
        self.is_moving = False
        
        # Now that the movement animation has stopped, we no longer need
        # these two variables, so reset them for the next movement animation.
        self.calculated_pos_moving_x = 0
        self.calculated_pos_moving_y = 0

    def stop_scaling(self):
        """
        Reset the flag to indicate that scaling animations should not occur for this sprite.
        :return:
        """
        self.is_scaling = False
        
        # Reset the scale animation direction.
        self.scale_type = None

    def start_scaling(self):
        """
        Set the flag to indicate that scaling animations should occur
        for this sprite.
        
        Also, determine whether the sprite showed me scale Up or scaled Down.
        We do this by comparing where the scale is now (scale_current_value),
        to where it needs to be (scale_until).
        
        Return: None
        """
        
        # Make sure scale_until is initialized
        if not self.scale_until:
            return
        
        if self.scale_until.scale_until > self.scale_current_value.scale_current_value:
            self.scale_type = ScaleType.SCALE_UP
            
        elif self.scale_until.scale_until < self.scale_current_value.scale_current_value:
            self.scale_type = ScaleType.SCALE_DOWN
            
        else:
            # The scale_until value is the same as the current scale value.
            # No scaling animation is required, so don't continue.
            self.scale_type = None
            return
        
        
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

    def _show(self):
        """
        Set the visibility flag to True, to indicate to the renderer that
        this sprite should be drawn on the screen.

        This method is meant to be run from self.start_show() and not directly.
        """

        # We only use this flag each time a show is requested on
        # a sprite from a script, so we can reset it now.
        self.pending_show = False

        # Is this sprite already visible? return
        if self.visible:
            return

        self.visible = True

    def _hide(self):
        """
        Set the visibility flag to False, to indicate to the renderer that
        this sprite should no longer be drawn on the screen.

        This method is meant to be run from self.start_hide() and not directly.
        """

        # We only use this flag each time a hide is requested on
        # a sprite from a script, so we can reset it now.
        self.pending_hide = False

        # Is this sprite already invisible? return
        if not self.visible:
            return

        self.visible = False

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
            self.original_image_before_text = pygame.transform.flip(self.original_image_before_text, True, True)
        elif horizontal:
            self.image = pygame.transform.flip(self.image, True, False)
            self.original_image = pygame.transform.flip(self.original_image, True, False)
            self.original_image_before_text = pygame.transform.flip(self.original_image_before_text, True, False)
        elif vertical:
            self.image = pygame.transform.flip(self.image, False, True)
            self.original_image = pygame.transform.flip(self.original_image, False, True)
            self.original_image_before_text = pygame.transform.flip(self.original_image_before_text, False, True)
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
        Return: None
        """

        # Should we show or hide this sprite?
        if self.pending_show:
            # We're going to start showing this sprite.
            self._show()

        elif self.pending_hide:
            # We're going to hide this sprite.
            self._hide()
            return

        # If this sprite is not visible, there is no point
        # in animating it.
        if not self.visible:
            return

        # Note: it's important to do the fading animation last because otherwise
        # the faded image will get overwritten with the original image in the other animations.
        self.active_font_handler.draw()
        self._animate_scaling()
        self._animate_movement()
        self._animate_rotation()
        self.tint_handler.animate_tint()
        self._animate_fading()
        
        self._apply_still_effects()
        
        
        self._handle_mouse_events()
        
    def _handle_mouse_events(self):
        """
        Check the following mouse events and if any of the events are
        occurring, check if the current sprite should run a reusable script
        for a specific mouse event.
        
        The events are: on_mouse_enter, on_mouse_leave, on_mouse_click
        """
        
        # Is the mouse pointer inside the current sprite?
        if MouseActionsAndCoordinates.MOUSE_POS:
            if self.rect.collidepoint(MouseActionsAndCoordinates.MOUSE_POS):
                # The mouse pointer is inside the current sprite.
                
                
                # Make the sprite aware that the mouse pointer is on top
                # of the current sprite, if it doesn't already know.
                if self.mouse_status != SpriteMouseStatus.HOVERING_OVER_SPRITE:
                    self.mouse_status = SpriteMouseStatus.HOVERING_OVER_SPRITE
                    
                    # Run on_enter reusable script here
                    if self.on_mouse_enter_run_script:
                        
                        # Try to get the optional arguments (if any) to pass
                        # to the reusable script.
                        arguments =\
                            Passer.active_story.reader.\
                            try_get_arguments_attribute(
                                self.on_mouse_enter_run_script)                        
                    
                        # Run the script that is supposed to run, now that the
                        # mouse pointer is over the sprite.
                        Passer.active_story.reader.\
                            spawn_new_background_reader(
                                reusable_script_name=self.on_mouse_enter_run_script.reusable_script_name, 
                                arguments=arguments)
                    
                # Was a mouse button clicked? Check if we should
                # run a specific reusable script.
                if MouseActionsAndCoordinates.MOUSE_UP:
                    
                    if self.on_mouse_click_run_script:
                        
                        # Try to get the optional arguments (if any) to pass
                        # to the reusable script.
                        arguments =\
                            Passer.active_story.reader.\
                            try_get_arguments_attribute(
                                self.on_mouse_click_run_script)
                    
                        # Run the script that is supposed to run now that this 
                        # sprite has been clicked.
                        Passer.active_story.reader.\
                            spawn_new_background_reader(
                                reusable_script_name=self.on_mouse_click_run_script.reusable_script_name,
                                arguments=arguments)
                        
                    
            else:
                # The mouse pointer is not on top of the current sprite.
                
                # Make sure the sprite aware that the mouse pointer is not
                # on top of the current sprite, if it doesn't already know.
                if self.mouse_status != SpriteMouseStatus.AWAY_FROM_SPRITE:
                    self.mouse_status = SpriteMouseStatus.AWAY_FROM_SPRITE
                    
                    # Run on_leave reusable script here
                    if self.on_mouse_leave_run_script:
                        
                        # Try to get the optional arguments (if any) to pass
                        # to the reusable script.
                        arguments =\
                            Passer.active_story.reader.\
                            try_get_arguments_attribute(
                                self.on_mouse_leave_run_script)
                    
                        # Run the script that is supposed to run now that the
                        # mouse pointer is no longer over the sprite.
                        Passer.active_story.reader.\
                            spawn_new_background_reader(
                                reusable_script_name=self.on_mouse_leave_run_script.reusable_script_name, 
                                arguments=arguments)
        
    def _animate_rotation(self):
        """
        Rotate the sprite (if required).
        Return: None
        """

        ## Did the rotation value change without an animation?
        ## If so, rotate the sprite and return the new rect.
        # if self.sudden_rotate_change:
        # self.sudden_rotate_change = False
        # return self._scale_or_rotate_sprite()

        # Not rotating the sprite or no rotation speed set? Return.
        if not self.is_rotating or not self.rotate_speed:
            return


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
                new_rotate_value =\
                    self.rotate_current_value.rotate_current_value \
                    + self.rotate_speed.rotate_speed \
                    * AnimationSpeed.delta

                if new_rotate_value >= 360:
                    new_rotate_value = 0

                self.rotate_current_value = self.rotate_current_value._replace \
                    (rotate_current_value=new_rotate_value)

        # if rotate_until is None, it means rotate continuously.
        elif rotate_type == RotateType.CLOCKWISE:

            # Conditions for stopping a rotation that's not rotating forever:
            # 1) If a 'rotate_until' value has been specified
            # 2) and the current rotate value is greater than 0 (if we don't have
            # this check, then no rotation will start, because a rotation typically starts at 0 degrees)
            # 3) and if 360 minus the current rotation value has reached the destination angle.
            # The reason we take 360 minus the current rotation value is because pygame
            # starts from 360 and goes down when rotating clockwise, so for example
            # if the current rotation value says 300 degrees, we're really at 60 degrees (360 minus 300).
            # 4) then stop the rotation
            if self.rotate_until and \
               self.rotate_current_value.rotate_current_value > 0 and \
               (360 - self.rotate_current_value.rotate_current_value) >= self.rotate_until.rotate_until:
                
                # Stop the rotation
                self.stop_rotating()
                reached_destination_rotate = True
            else:
                # Rotate clockwise
                new_rotate_value =\
                    self.rotate_current_value.rotate_current_value \
                    + self.rotate_speed.rotate_speed \
                    * AnimationSpeed.delta

                if new_rotate_value < 0:
                    new_rotate_value = 360

                self.rotate_current_value = self.rotate_current_value._replace \
                    (rotate_current_value=new_rotate_value)

        # Have we reached a destination rotation which caused the 
        # rotating to stop?
        if reached_destination_rotate:
            # Yes, the rotation has now stopped because we've reached a 
            # specific rotation value.

            # Should we run a specific script now that the rotating 
            # animation has stopped for this sprite?
            if self.rotate_stop_run_script and \
               self.rotate_stop_run_script.reusable_script_name:

                # Get the name of the script we need to run now.
                reusable_script_name =\
                    self.rotate_stop_run_script.reusable_script_name
                
                # Try to get the arguments value, if there is one.
                arguments =\
                    Passer.active_story.reader.\
                    try_get_arguments_attribute(self.rotate_stop_run_script)

                # Clear the variable that holds information about which 
                # script we need to run because we're about to load that 
                # specified script below.
                
                # If we don't clear this variable, it will run the 
                # specified script again once the sprite stops rotating 
                # next time.
                self.rotate_stop_run_script = None

                # Run the script that is supposed to run now that this 
                # sprite has stopped rotating.
                Passer.active_story.reader.\
                    spawn_new_background_reader(
                        reusable_script_name=reusable_script_name,
                        arguments=arguments)

            return

        ## Skipping the animation in this frame due to a delay?
        ## Don't apply the current value of the animation effect
        ## if it's the *only* active animation.
        #if skip_rotate:
            #if self._is_only_active_animation(animation_type=SpriteAnimationType.ROTATE):
                ## Don't apply this animation in this frame,
                ## because it's the only animation and it's currently
                ## on a delayed pause.
                #return

    def _animate_scaling(self):
        """
        Scale the sprite (if required).
        
        Return: None
        """

        ## Did the scale value change without an animation?
        ## If so, scale the sprite and return the new rect.
        # if self.sudden_scale_change:
        # self.sudden_scale_change = False
        #return self._scale_or_rotate_sprite()

        # Not scaling the sprite or no scale speed set
        # or no scale_until set or no scale type (direction)? Return.
        if not all((self.is_scaling, self.scale_speed,
                    self.scale_until, self.scale_type)):
            return


        # Are we scaling up or scaling down?
        # We need to know so we can determine when to stop the scaling.        
        if self.scale_type == ScaleType.SCALE_UP:
            
            # Has the sprite reached the destination scale while
            # scaling up?
            if self.scale_current_value.scale_current_value >= self.scale_until.scale_until:
                self.scale_type = ScaleType.SCALE_REACHED_DESTINATION
            
        elif self.scale_type == ScaleType.SCALE_DOWN:
            
            # Has the sprite reached the destination scale while 
            # scaling down?
            if self.scale_current_value.scale_current_value <= self.scale_until.scale_until:
                
                # The sprite has reached the destination scale.
                self.scale_type = ScaleType.SCALE_REACHED_DESTINATION

        # Initialize
        reached_destination_scale = False

        # Has the sprite reached the destination scale value?
        if self.scale_type in (ScaleType.SCALE_UP,
                               ScaleType.SCALE_REACHED_DESTINATION):
            
            # We either need to keep scaling-up or we've already reached
            # the final scale-up or scale-down and we need to use this block
            # to stop the scale effect.                
            
            if self.scale_current_value.scale_current_value >= self.scale_until.scale_until:
                # Stop the scaling
                self.stop_scaling()
                reached_destination_scale = True
            else:
                # Increment scaling
                new_scale_value =\
                    self.scale_current_value.scale_current_value \
                    + self.scale_speed.scale_speed \
                    * AnimationSpeed.delta
                
                if new_scale_value >= self.scale_until.scale_until:
                    new_scale_value = self.scale_until.scale_until

                self.scale_current_value =\
                    self.scale_current_value._replace(
                        scale_current_value=new_scale_value)

        elif self.scale_type == ScaleType.SCALE_DOWN:
            
            if self.scale_current_value.scale_current_value <= self.scale_until.scale_until:
                # Stop the scaling
                self.stop_scaling()
                reached_destination_scale = True
            else:
                
                # A positive value will scale up the sprite.
                # A negative value(such as -0.00050) will scale down a 
                # sprite.            
                scale_down_float = -abs(self.scale_speed.scale_speed)                    
                
                # Decrease scaling
                new_scale_value =\
                    self.scale_current_value.scale_current_value \
                    + scale_down_float \
                    * AnimationSpeed.delta
                
                if new_scale_value <= 0:
                    new_scale_value = 0

                self.scale_current_value =\
                    self.scale_current_value._replace(
                        scale_current_value=new_scale_value)

        # Have we reached a destination scaling which caused the scaling 
        # to stop?
        if reached_destination_scale:
            # Yes, the scaling has now stopped because we've reached a 
            # specific scaling value.

            # Should we run a specific script now that the scaling animation
            # has stopped for this sprite?
            if self.scale_stop_run_script and \
                    self.scale_stop_run_script.reusable_script_name:

                # Get the name of the script we need to run now.
                reusable_script_name =\
                    self.scale_stop_run_script.reusable_script_name
                
                # Try to get the arguments value, if there is one.
                arguments =\
                    Passer.active_story.reader.\
                    try_get_arguments_attribute(self.scale_stop_run_script)
                
                # Clear the variable that holds information about which 
                # script we need to run because we're about to load that 
                # specified script below.
                # If we don't clear this variable, it will run the 
                # specified script again once the sprite stops scaling 
                # next time.
                self.scale_stop_run_script = None

                # Run the script that is supposed to run now that this 
                # sprite has stopped scaling.
                Passer.active_story.reader.\
                    spawn_new_background_reader(
                        reusable_script_name=reusable_script_name,
                        arguments=arguments)

            return

        ## Skipping the animation in this frame due to a delay?
        ## Don't apply the current value of the animation effect
        ## if it's the *only* active animation.
        #if skip_scale:
            #if self._is_only_active_animation(animation_type=SpriteAnimationType.SCALE):
                ## Don't apply this animation in this frame,
                ## because it's the only animation and it's currently
                ## on a delayed pause.
                #return

        ## rect = self._scale_or_rotate_sprite()

    def _scale_or_rotate_sprite(self):
        """
        Scale and/or rotate the sprite and then update the sprite's rect.
        Return: None
        """

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

        ## Scale and/or rotate the image, which is based on the original image.
        self.image = pygame.transform.rotozoom(self.get_original_image_with_text(),
                                               current_rotate,
                                               current_scale)

        # Record how much rotate/scale we've applied so we don't keep applying
        # the rotate/scale unnecessarily during a non-animation sudden rotate 
        # or scale change.
        self.applied_rotate_value = current_rotate
        self.applied_scale_value = current_scale

        # Get the new rect of the rotated or scaled image
        self.rect = self.image.get_rect(center=self.rect.center)

    def _apply_still_effects(self):
        """
        Apply scale/rotation/fade effects to the sprite if the amount of
        effects applied to the sprite is different than the expected amounts.
        
        This doesn't mean the sprite is necessarily being 'animated'.
        A still-effect could have been applied
        OR an animation could be occurring and the time to apply the effect
        may not have come yet (too soon).
        
        Either way, this method only checks if the applied effect is different
        from what it *should* be, regardless if the sprite is being animated
        or not.
        """
        
        at_least_one_effect_applied = False
        

        # # Is a required scale/rotate effect caught up with what's required?
        if self.is_scale_or_rotate_needed():
            
            # Apply a scale/rotation effect to the current sprite.
            self._scale_or_rotate_sprite()
            
            # So the rest of the effect methods know that the sprite
            # has been altered in some way.
            at_least_one_effect_applied = True
            
        # Is a required tint effect caught up with what's required?
        if self.tint_handler.is_tint_animation_needed():
            
            # Apply a tint effect to the current sprite.
            self._tint_sprite(
                skip_copy_original_image=at_least_one_effect_applied)
            
            # So the rest of the effect methods know that the sprite
            # has been altered in some way.            
            at_least_one_effect_applied = True
                
            
        # We need to check if we need to apply fade *after* a scale/rotation
        # and *after* a tint effect because a scale/rotation/tint will 
        # make the image opaque.
        if self.is_fade_needed():
            """
            A fade is needed. Apply the fade to the scaled/rotated/tinted 
            version of the image the image was just scaled or rotated or tinted
            (if skip_copy_original_image == True)
            
            Otherwise apply the fade to the original version of the image.
            That's why we're using at_least_one_effect_applied as a bool 
            in the argument below.
            (skip_copy_original_image == at_least_one_effect_applied)
            """
            
            skip_copy = at_least_one_effect_applied

            self._fade_sprite(skip_copy_original_image=skip_copy)
            
            at_least_one_effect_applied = True
            
        # print(f"Applying scale or fade for {self.name} at: {datetime.now()} ")
            
        if not at_least_one_effect_applied:
            """
            No effects needed to be applied in this frame.
            Either the sprite has had its effect animations finished
            or has no effects at all.
            """

            """
            If no effects are currently applied to the sprite,
            and the displayed image is different from the original sprite
            with text, then that means there is some text on the sprite
            that we're currently not showing and that we need to show.
            
            OR there was text before (and we're showing the sprite with text)
            but now the sprite's text has been cleared, but we're still showing
            the sprite with text.
            
            We need to copy the original image with text to self.image,
            which gets shown to the viewer.
            
            This gets handled automatically when effects have been
            applied or animations are ongoing. But if the sprite hasn't had
            any animations or effects applied to it, we need to handle this
            here.
            For details, read the comment in the method 'any_effects_applied'            
            """

            # Update the displayed image with the sprite with text. 
            # If the two sprites are different, use the sprite with text.
            if not self.any_effects_applied() \
               and self.image != self.original_image:
                
                # The displayed image is different from the image with text,
                # so get the image with text on it (self.original_image)
                self.image = self.original_image

                print("Copied sprite with text", datetime.now())
                
            #print("Animation not needed")
            
    def any_effects_applied(self) -> bool:
        """
        Return whether the sprite has had any type of effect applied to it,
        such as fade, rotate, scale, tint.
        
        Return: True if at least one of the effects has been applied
        to the sprite (fade, rotate, scale, tint)
        
        Return: False if the sprite does not have any effects applied to it.
        
        Purpose: if the sprite does not have any effects applied to it,
        then the caller needs to check if the sprite has any text and get
        a copy of the sprite image with text; otherwise the visible sprite
        won't have text on it.
        
        Effects will automatically take care of a sprite's text by making
        the sprite's text show up during animations.
        But if a sprite has had no animations or is not going through an
        animation now, then we need to deal with showing the sprite's text
        a different way, and this method is used as part of this.
        """
        if not self.is_dirty_with_fade() \
           and not self.is_dirty_with_rotate_or_scale() \
           and not self.tint_handler.is_dirty_with_tint():
            
            # This sprite currently does not have any effects applied to it.
            return False
        else:
            # This sprite has at least one type of effect applied to it.
            # Fade and/or scale/rotation and/or tint.
            return True     

    def is_fade_needed(self) -> bool:
        """
        Return whether the applied fade amount is the same
        as the expected fade amount.
        """
        # Is fade enabled on this sprite?
        if self.current_fade_value is not None:
            
            # If there's a current fade value (even zero or 255) and the 
            # sprite is still fading, then proceed to evaluate if a fade
            # is still needed.
            if self.current_fade_value.current_fade_value or self.is_fading:
                
                # Proceed to check if a fade is still needed or not.
                
                # If the current fade value is set to 255 for the sprite
                # but no fade has been applied to the sprite yet, then
                # no fade needs to be applied, because the fade value wants
                # to set the sprite to 255, but it already is.
                if self.current_fade_value.current_fade_value == 255 \
                   and self.applied_fade_value is None:
                    return
                
    
                # Is the applied fade amount the same
                # as the expected fade amount?
                if self.current_fade_value.current_fade_value != self.applied_fade_value:
                    # The applied fade amount is different than
                    # the expected fade amount.
                    return True

    def is_scale_or_rotate_needed(self) -> bool:
        """
        Return whether the applied scale or rotation value is the same
        as the expected scale or rotation value.
        
        Purpose: to know whether a scale and/or rotation effect is required
        on self.image
        """
        
        # -------
        # Scale check
        
        # Scale check #1
        # Animating a scale?
        reapply_scale = (self.scale_current_value is not None \
                         and self.scale_current_value.scale_current_value) \
            or self.is_scaling
        
        # Scale check #2 - continued challenge
        # Is the 'applied' scale value different from the destination 
        # scale value?
        if reapply_scale:
            
            # Scale if the 'applied' scale is different from the 
            # destination scale.
            reapply_scale = (self.applied_scale_value is None \
                or self.applied_scale_value != self.scale_current_value.scale_current_value)

            
        
        # ------
        # Rotation check
        
        # Rotate check #1
        # Animating a rotation?
        reapply_rotate = (self.rotate_current_value is not None \
                          and self.rotate_current_value.rotate_current_value > 1) \
            or self.is_rotating
        
        # Rotate check #2 - continued challenge
        # Is the 'applied' rotate value the different from the destination 
        # rotate value?
        if reapply_rotate:
            
            # Rotate if the 'applied' rotation is different from the 
            # destination rotate.
            reapply_rotate = self.applied_rotate_value is None \
                or self.applied_rotate_value != self.rotate_current_value.rotate_current_value
                
        
        return reapply_scale or reapply_rotate
        
        #if self.scale_current_value \
                #and self.scale_current_value.scale_current_value != self.applied_scale_value:
            
            ## Scale already at normal scale and no scale effect applied?
            ## No need to apply a scale-effect
            #if self.scale_current_value.scale_current_value == 1.0 and self.applied_scale_value is None:
                ## No scale animation needed
                #pass
            #else:
                ## The applied scale value is different than
                ## the expected scale value.
                #return True


        #if self.rotate_current_value \
                #and self.rotate_current_value.rotate_current_value != self.applied_rotate_value:
            
            ## Rotation already at 0 degrees and no rotation effect applied?
            ## No need to apply a rotation-effect
            #if self.rotate_current_value.rotate_current_value == 0 and self.applied_rotate_value is None:
                #return False            
            
            ## The applied rotation value is different than
            ## the expected rotation value.
            #return True

    def _animate_fading(self):
        """
        Fade the sprite (if required), but only if we know how far
        to fade the sprite.
        Return: None
        """

        ## Did a sudden fade value change occur without an animation? (direct command)
        ## Then fade the sprite and return.
        # if self.sudden_fade_change:
        # self.sudden_fade_change = False
        # self._fade_sprite()
        #return

        # Not fading the sprite? Return.
        if not self.is_fading:
            return

        ## If there is no fade_until value, but the fade
        ## value is not fully opaque, then apply the fade,
        ## even though we're not fading to a fade-destination.
        #if not self.fade_until and self.current_fade_value is not None:
            #if self.current_fade_value.current_fade_value < 255:
                #self._fade_sprite()
                #return

        # At this point, we need a fade speed.
        # If that hasn't been decided (fade_speed), return
        if not self.fade_speed:
            return
        
        # We must also have a fade_until, otherwise we won't know whether
        # to fade in or fade out
        elif not self.fade_until:
            return
        

        # Are we fading-in or fading-out? We need to know so that we can
        # determine when to stop the fade.
        if self.current_fade_value.current_fade_value < self.fade_until.fade_value:
            fade_type = FadeType.FADE_IN
            
        elif self.current_fade_value.current_fade_value > self.fade_until.fade_value:
            fade_type = FadeType.FADE_OUT
            
        else:
            # The fade value has reached its fade_until value.
            fade_type = FadeType.FADE_REACHED_DESTINATION

        # Initialize
        reached_destination_fade = False

        # Has the sprite reached the destination fade value?
        if fade_type in (FadeType.FADE_IN,
                         FadeType.FADE_REACHED_DESTINATION):
            
            # We either need to keep fading-in or we've already reached
            # the final fade-in or fade-out and we need to use this block
            # to stop the fade effect.
            if self.current_fade_value.current_fade_value >= self.fade_until.fade_value:

                # We've reached the destination fade value, so stop fading.
                self.stop_fading()

                reached_destination_fade = True
            else:
                # Increment fade

                # Calculate the change in fade value that occurred in the 
                # time delta
                fade_change_this_frame =\
                    self.fade_speed.fade_speed * AnimationSpeed.delta
                
                # Add this change from the current fade value to get 
                # the new fade value
                self.calculated_fade_value += fade_change_this_frame
                
                # Don't allow the calculated fade value to go beyond 255.
                if self.calculated_fade_value > 255:
                    self.calculated_fade_value = 255
                
                # Convert the float fade value to an int, because
                # pygame uses the int value to set the opacity, not a float.
                new_fade_value = int(self.calculated_fade_value)

                # Set what the new int fade value should be so that it gets
                # applied to the sprite later on.
                self.current_fade_value =\
                    self.current_fade_value._replace(current_fade_value=new_fade_value)

                
        elif fade_type == FadeType.FADE_OUT:
            if self.current_fade_value.current_fade_value <= self.fade_until.fade_value:

                # We've reached the destination fade out value.
                # Set a flag so we can check if a reusable script needs to run
                reached_destination_fade = True

                # The sprite has reached its fade-value destination,
                # so stop the fade-out animation.
                self.stop_fading()

            else:
                # Decrease fade

                # Calculate the change in fade value that occurred in the 
                # time delta
                fade_change_this_frame =\
                    self.fade_speed.fade_speed * AnimationSpeed.delta
                
                # Subtract this change from the current fade value to get 
                # the new fade value
                self.calculated_fade_value -= fade_change_this_frame
                
                # Don't allow the calculated fade value to go below 0.
                if self.calculated_fade_value < 0:
                    self.calculated_fade_value = 0
                
                # Convert the float fade value to an int, because
                # pygame uses the int value to set the opacity, not a float.
                new_fade_value = int(self.calculated_fade_value)

                # Set what the new int fade value should be so that it gets
                # applied to the sprite later on.
                self.current_fade_value = self.current_fade_value._replace(current_fade_value=new_fade_value)
                

        # Have we reached a destination fade which caused the fade to stop?
        if reached_destination_fade:
            # Yes, the fade has now stopped because we've reached a specific fade value.
            
            # Reset the fade_until value
            self.fade_until = None

            # Should we run a specific script now that the fade animation
            # has stopped for this sprite?
            if self.fade_stop_run_script \
               and self.fade_stop_run_script.reusable_script_name:

                # Get the name of the script we need to run now.
                reusable_script_name =\
                    self.fade_stop_run_script.reusable_script_name

                # Try to get the arguments attribute value, if there is one.
                arguments =\
                    Passer.active_story.reader.\
                    try_get_arguments_attribute(self.fade_stop_run_script)                 

                # Clear the variable that holds information about which 
                # script we need to run because we're about to load that 
                # specified script below.
                # If we don't clear this variable, it will run the 
                # specified script again once the sprite stops fading 
                # next time.
                self.fade_stop_run_script = None

                # Run the script that is supposed to run, 
                # now that this sprite has stopped fading.
                Passer.active_story.reader.\
                    spawn_new_background_reader(
                        reusable_script_name=reusable_script_name,
                        arguments=arguments)

            # Apply the fade effect one last time for the destination fade amount
            # that we're in. Without this, the destination fade amount
            # won't get blitted.
            # self._fade_sprite()

            return
        
    def _tint_sprite(self, skip_copy_original_image: bool = False):
        """
        Tint the sprite to the current tint value.

        If the sprite is being scaled (as an animation)
        or being rotated (as an animation), don't copy the original image,
        because then the scaling and/or rotation changes won't show.
        
        If the sprite is not scale-animating, but has a scale effect applied
        and/or the sprite is not rotate-animating, but has a rotation effect
        applied, then apply the rotate/scale effect in this method after
        getting the original image (with optional sprite text), then in the
        end, apply the fade effect.
        
        Arguments:
        
        - skip_copy_original_image: if the sprite was not animated before this
        method was called, this variable will be False. When False, it means
        we should copy the original sprite with optional text, before applying
        the tint effect.
        
        if True, it means the original image was recently copied by a previous
        animation, and we should *not* copy the original image because it would
        erase the recent prior animation that was done (such as a scale and/or
        a rotation).
        """

        # Tint not applied to the sprite? return
        if self.tint_handler.current_tint_value is None:
            return
        
        # Get a tuple with the current RGB dim values.
        tint_values: Tuple
        tint_values = self.tint_handler.get_tint_values()
        if not tint_values:
            # No tinting required; an untinted image should be displayed.
            return

        replaced_image = False


        # Should we consider copying the original image to self.image?
        # The caller of this method may have already done this, which is
        # why we check here.
        if not skip_copy_original_image:

            # Yes, we should consider copying the original image to self.image
            
            # Get the original image (no effects), but with sprite text (if any).
            # Then re-apply a scale or rotate effect if it's currently applied.
        
            """
            The method call below, self._scale_or_rotate_sprite(), will
            deal with getting the original image (no effects), but with
            sprite text (if any), and that same method will also rotate/scale 
            right after it's done getting the original image.
            """
            
            
            # Is the image touched with a scale or rotate effect?
            # (regardless if there's a gradual animation or not)
            if self.is_dirty_with_rotate_or_scale():
                
                # The scale or rotate effect is eligible to this sprite.
                # So get the original image (with sprite text, if any)
                # and reapply the scale and/or rotation effect, before
                # we tint the image a few lines later.
                self._scale_or_rotate_sprite()
            else:
                
                # No scale or rotation necessary, just get the original image
                # with sprite text (if any), before we apply a tint effect.
                self.image = self.get_original_image_with_text()
                

            # So the caller knows the displayed image was altered.
            replaced_image = True
            
        # Apply the tint values to the displayed sprite.
        # We use RGB here, instead of RGBA, to keep the alpha channel as-is.
        if self.tint_handler.tint_style == TintStyle.REGULAR:
            self.image.fill(tint_values, special_flags=pygame.BLEND_RGB_MULT)
        else:
            self.image.fill(tint_values, special_flags=pygame.BLEND_RGB_ADD)
        
        # Record the tint value that is now applied to the sprite
        # so that we can check in the next frame if we need to reapply the
        # tint effect again or not.
        self.tint_handler.applied_tint_value = tint_values[0]

        return replaced_image

    def _fade_sprite(self, skip_copy_original_image: bool = False):
        """
        Fade the sprite to the current fade value.

        If the sprite needs a scale/rotation/tint effect applied, don't copy
        the original image, because then the scaling and/or rotating
        and/or tint changes won't show - they'll get replaced with a faded
        sprite with none of those effects, which we don't want.
        
        If the sprite needs a scaling/rotating/tinting effect  applied, then
        apply the rotate/scale/tint effect(s) in this method after
        getting the original image (with optional sprite text), then in the
        end, apply the fade effect.
        
        Arguments:
        
        - skip_copy_original_image: used by a sprite's clear_text_and_redraw()
        method. Sometimes we shouldn't attempt to copy self.original_image
        to self.image, because it has already been done and all we want to do
        is fade the image. In a case like that, this variable will be set to
        True.
        Under normal use-cases (without clear_text_and_redraw()) this variable
        will be False.
        """

        # Fade not applied to the sprite? return
        if not self.current_fade_value:
            return

        replaced_image = False


        # Should we consider copying the original image to self.image?
        # The caller of this method may have already done this, which is
        # why we check here.
        if not skip_copy_original_image:

            # Yes, we should consider copying the original image to self.image
            
            # Get the original image (no effects), but with sprite text (if any).
            # Then re-apply a scale or rotate or tint effect if it's currently 
            # applied.
        
            """
            The method calls below, self._scale_or_rotate_sprite(),
            self._tint_sprite(), will deal with getting the original image
            (no effects), but with sprite text (if any), and those same methods
            will also rotate/scale/tint right after they're done getting the
            original image.
            """
            
            # Keep track when an effect is applied, so when the second effect
            # is applied, it doesn't overwrite the image with the previous
            # effect, causing the previous effect to not appear on the sprite.
            scale_rotation_was_dirty = False
            tint_was_dirty = False
            
            # Is the image touched with a scale or rotate effect?
            # (regardless if there's a gradual animation or not)
            if self.is_dirty_with_rotate_or_scale():
                
                # The scale or rotate effect is eligible to this sprite.
                # So get the original image (with sprite text, if any)
                # and reapply the scale and/or rotation effect, before
                # we fade the image a few lines later.
                self._scale_or_rotate_sprite()
                
                scale_rotation_was_dirty = True
                
            # Should a tint effect be applied to the image?
            if self.tint_handler.is_dirty_with_tint():
                
                # Apply a tint effect before doing a fade.
                
                # If a scale/rotate above just replaced the image,
                # then we won't need to replace the sprite again before doing 
                # a tint. That's what, scale_rotation_was_dirty, is for.
                self._tint_sprite(
                    skip_copy_original_image=scale_rotation_was_dirty)
                
                tint_was_dirty = True

                
            # Check if the image was replaced with a rotated/scaled
            # or tinted version. If not, we should get the original image
            # so we we don't keep fading an already-faded sprite on top of 
            # itself.
            if not any([scale_rotation_was_dirty, tint_was_dirty]):
            
                # The sprite is not dirty with either scale/rotation
                # nor a tint.
            
                # No scale/rotation/tint is applied to the sprite, so it's safe
                # to get the original image with sprite text (if any), before
                # we apply a fade.
                self.image = self.get_original_image_with_text()

                # Flag to indicate the sprite was replaced with the original
                # copy with sprite text (if any).
                replaced_image = True
            
        
        # self.image.fill((255, 255, 255, self.current_fade_value.current_fade_value), None, pygame.BLEND_RGBA_MULT)
        
        # Now we're ready to apply a fade to this image.
        # This is the last step. This image should already be rotated or scaled
        # before we get here.
        self.image.set_alpha(self.current_fade_value.current_fade_value)

        # Record how much fade we've applied so we don't keep applying
        # the fade unnecessarily during a non-animation sudden fade change.
        self.applied_fade_value = self.current_fade_value.current_fade_value
            
        # print(f"{self.name} fade: {self.applied_fade_value}")
        
        return replaced_image
    
    def is_dirty_with_rotate_or_scale(self) -> bool:
        """
        Return whether the sprite has a non-default scale or non-default rotate
        value. In other words, if the sprite has been touched or should be
        touched with a rotate or scale effect.
        
        It doesn't check whether a scale or rotate is actively applied to the
        sprite - it just checks whether the effect is applicable to the sprite,
        regardless if it currently actually has a rotate/scale effect applied
        to it or not.
        
        Purpose: before applying a fade effect, this method gets used
        to determine whether the image needs to be scaled/rotated first, before
        a fade effect is used.
        """
        
        # Has a scale value that is not 1 (original size)? Consider it
        # dirty with a scale.
        # Or has a rotate value that is greater than 0? Consider it
        # dirty with a rotate.
        if (self.scale_current_value and self.scale_current_value != 1) \
           or (self.rotate_current_value and self.rotate_current_value > 0):
                return True
            
        else:
            return False
        
    def is_dirty_with_fade(self) -> bool:
        """
        Return whether the sprite has a non-default fade (non-opaque) value.
        In other words, if the sprite has been touched or should be
        touched with a fade effect.
        
        It doesn't check whether a fade effect is actively applied to the
        sprite - it just checks whether the effect is applicable to the sprite,
        regardless if it currently actually has a fade applied to it or not.
        
        Purpose: this method is called by the any_effects_applied() method,
        to check if a fade effect is applied to the sprite.
        to determine whether the image needs to be scaled/rotated first, before
        a fade effect is used.
        """
        
        # Has a fade value that is not 255 (fully opaque)? Consider it
        # dirty with a fade.
        if self.current_fade_value is not None \
           and self.current_fade_value.current_fade_value < 255:
            
            return True
        else:
            return False

    def get_original_image_with_text(self) -> pygame.Surface:
        """
        Return a copy of the original image (that has no rotation,
        no scale, no fade) but might have text on it. This copy
        will eventually be copied to self.image
        
        Also, reset the variables that keep track of the amount of
        rotation, scale, and fade, because eventually once the original image
        has been copied to self.image, then self.image won't have those
        effects applied anymore.
        """

        self.reset_applied_effects()
        
        return self.original_image.copy()

    def get_original_image_without_text(self) -> pygame.Surface:
        """
        Return a copy of the original image (that has no rotation,
        no scale, no fade) and has no text on it. This copy
        will eventually be copied to self.original_image
        
        Also, reset the variables that keep track of the amount of
        rotation, scale, and fade, because once the original image has
        been copied to self.image, self.image won't have those effects
        applied anymore.
        
        Eventually 'original_image' will want to be copied to self.image,
        so that's why we need to reset the effect flags so that we can
        re-apply them to self.image
        """

        self.reset_applied_effects()
        

        return self.original_image_before_text.copy()

    def reset_applied_effects(self):
        """
        Reset the variables that keep track of the amount of
        rotation, scale, tint, and fade.
        
        Purpose: once the original image of a sprite has been copied to
        self.image, the self.image won't have effects applied anymore.
        """
        self.applied_fade_value = None
        self.applied_rotate_value = None
        self.applied_scale_value = None
        self.tint_handler.applied_tint_value = None

    def _animate_movement(self):
        """
        Move the sprite (if required) based on the sprite's movement speed.

        Return: None
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

                    # Should we run a specific reusable script now that the 
                    # movement has stopped?
                    # (this is if 'character_after_movement_stop' has been 
                    # used on this sprite).
                    if self.movement_stop_run_script:

                        # Get the name of the script we need to run now.
                        reusable_script_name =\
                            self.movement_stop_run_script.reusable_script_name
                        
                        # Try to get optional arguments, if there are any.
                        arguments =\
                            Passer.active_story.reader.\
                            try_get_arguments_attribute(
                                self.movement_stop_run_script)

                        # At this point, we know the reusable script name we 
                        # need to run, now that this sprite has stopped moving.
                        # So clear the variable that holds information about 
                        # which script we need to run because we're about to 
                        # load that specified script below.
                        # If we don't clear this variable, it will run the 
                        # specified script again once the sprite stops moving 
                        # next time.
                        self.movement_stop_run_script = None

                        # Run the script that is supposed to run, now that this 
                        # sprite has stopped moving.
                        Passer.active_story.reader.spawn_new_background_reader \
                            (reusable_script_name=reusable_script_name,
                             arguments=arguments)

                    return


        if self.movement_speed.x:
            # Move the X position
            self.calculated_pos_moving_x +=\
                self.movement_speed.x * AnimationSpeed.delta
            
            self.rect.x = int(self.calculated_pos_moving_x)
            # self.rect.move_ip(int(self.pos_x), 0)

        if self.movement_speed.y:
            # Move the Y position
            self.calculated_pos_moving_y +=\
                self.movement_speed.y * AnimationSpeed.delta
            
            self.rect.y = int(self.calculated_pos_moving_y)
            # self.rect.move_ip(0, self.movement_speed.y)


class SpriteGroup:

    def __init__(self):
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
            sprite.update()

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
