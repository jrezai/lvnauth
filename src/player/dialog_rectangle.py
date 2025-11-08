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
import sprite_definition as sd
from enum import Enum, auto
from typing import NamedTuple
from shared_components import Passer


#class Color(NamedTuple):
    #red: int
    #green: int
    #blue: int
    

def to_enum(cls, string_representation: str):
    """
    Convert a string like 'MID_BOTTOM' to the enum version,
    which is AnchorRectangle.MID_BOTTOM
    and return the enum version.
    """
    if not string_representation:
        return
    else:
        # The expected value is case-sensitive. The string
        # needs to be all uppercase.
        string_representation = string_representation.upper()
        
        # Replace spaces with underscores because enums don't have spaces.
        string_representation = string_representation.replace(" ", "_")

        try:
            return cls[string_representation]
        except KeyError:
            return


class RectangleIntroAnimation(Enum):
    """
    A definition for how a rectangle should first be displayed on the screen.
    """
    NO_ANIMATION = auto()
    LEFT_TO_RIGHT = auto()
    RIGHT_TO_LEFT = auto()
    FADE_IN = auto()
    SCALE_UP_HEIGHT_THEN_WIDTH = auto()
    SCALE_UP_WIDTH_THEN_HEIGHT = auto()
    SCALE_UP_WIDTH_AND_HEIGHT = auto()

    
class RectangleOutroAnimation(Enum):
    """
    A definition for how a rectangle should disappear from the screen.
    """
    NO_ANIMATION = auto()
    GO_RIGHT = auto()
    GO_LEFT = auto()
    GO_UP = auto()
    GO_DOWN = auto()
    FADE_OUT = auto()
    SCALE_DOWN_HEIGHT_THEN_WIDTH = auto()
    SCALE_DOWN_WIDTH_THEN_HEIGHT = auto()
    SCALE_DOWN_WIDTH_AND_HEIGHT = auto()


class AnchorRectangle(Enum):
    MID_LEFT = auto()
    BOTTOM_LEFT = auto()
    TOP_LEFT = auto()
    MID_BOTTOM = auto()
    BOTTOM_RIGHT = auto()
    MID_RIGHT = auto()
    TOP_RIGHT = auto()
    MID_TOP = auto()
    CENTER = auto()
    

class DialogRectangle:

    def __init__(self,
                 main_screen: pygame.Surface,
                 width_rectangle: int,
                 height_rectangle: int,
                 animation_speed: float,
                 intro_animation: RectangleIntroAnimation,
                 outro_animation: RectangleOutroAnimation,
                 anchor: AnchorRectangle,
                 bg_color_hex: str,
                 animation_finished_method,
                 spawn_new_background_reader_method,
                 padding_x: int = 0,
                 padding_y: int = 0,
                 alpha: int = 150,
                 rounded_corners: bool = True,
                 reusable_on_intro_starting=None,
                 reusable_on_intro_finished=None,
                 reusable_on_outro_starting=None,
                 reusable_on_outro_finished=None,
                 reusable_on_halt=None,
                 reusable_on_unhalt=None,
                 border_color_hex: str = None,
                 border_width: int = 0,
                 border_alpha :int = 0):
        

        # Flag to indicate whether this dialog rectangle should show
        # and/or animate on the screen.
        self.visible = False
        
        
        # The method to run when the intro/outro animation of this
        # dialog rectangle has finished.
        # It runs this method:
        # The story reader's on_dialog_rectangle_animation_completed()
        self.animation_finished_method = animation_finished_method

        # The method for spawning a new background reader.
        # Purpose: for running reusable scripts when the dialog animation starts/finishes.
        self.spawn_new_background_reader_method = spawn_new_background_reader_method

        # Reusable script names to run when the dialog is starting or closing.
        self.reusable_on_intro_starting = reusable_on_intro_starting
        self.reusable_on_intro_finished = reusable_on_intro_finished
        self.reusable_on_outro_starting = reusable_on_outro_starting
        self.reusable_on_outro_finished = reusable_on_outro_finished
        
        # Reusable script names to run when <halt> or <unhalt> are used.
        self.reusable_on_halt = reusable_on_halt
        self.reusable_on_unhalt = reusable_on_unhalt

        # If there are any rect updates (animation updates)
        # the rect will be put here so the screen can get updated.
        self.updated_rect = None

        # So we can get the width/height of the main surface
        rect_main_screen = main_screen.get_rect()

        self.main_screen = main_screen
        self.width_rectangle = width_rectangle
        self.height_rectangle = height_rectangle
        self.screen_size = screen_size = (rect_main_screen.width,
                                          rect_main_screen.height)


        # We will use the convenient (1-100) speed when showing and hiding
        # the dialog. We use different speed float values for
        # fading and non-fading intro/outro animations.

        # We need the convenient value to convert to the appropriate
        # float value when we show/hide the dialog.
        self.animation_speed_convenient = animation_speed

        # Will contain a float value when we show/hide the dialog rectangle.
        self.animation_speed = None
        
        self.intro_animation = intro_animation
        self.outro_animation = outro_animation
        self.anchor = anchor
        self.bg_color = pygame.Color(bg_color_hex)
        self.border_color = pygame.Color(border_color_hex)
        self.border_color.a = border_alpha
        self.border_width = border_width
        self.border_alpha = border_alpha
        self.padding_x = padding_x
        self.padding_y = padding_y
        self.alpha = alpha
        self.rounded_corners = rounded_corners
        self.current_fade_value: int = 0

        
        self.next_rect_update_hide_dialog = False
        
        self.intro_complete = False
        self.outro_complete = False
        
        self.rect_destination = None
        self.rect = None

        # The audio name to play for each letter
        # when using letter-by-letter non-gradual animation.
        self.text_sound_name = None

        # This will be set to True if it's going to be the last rectangle
        # update. Purpose: when an outro animation finishes its last animation,
        # the .visible flag of the dialog rectangle can't be immediately set
        # to False, because the loop won't finish updating the last outro
        # animation frame. So we set this to indicate to the update loop that
        # after this dialog rectangle update, set the dialog's visibility
        # flag to False. This is only used for an outro dialog animation,
        # not for an intro.
        self.next_rect_update_hide_dialog = False
                
        # Get the destination rectangle ready so we know what size
        # the final rectangle needs to animate to.
        self._prepare_intro_animation()

    def start_show(self):
        """
        Make the dialog visible and start the intro animation (if any).
        """
        
        # If the dialog is already visible, don't do anything.
        if self.visible:
            return

        self._prepare_intro_animation()
        self.visible = True
        
    def start_hide(self):
        """
        Start to hide the dialog by starting the outro animation (if any).
        When the outro animation finishes, that's when it'll be fully hidden.
        """

        self._prepare_outro_animation()

    def convenient_animation_speed_to_value(self,
                                            int_speed: int,
                                            animation_type: str) -> int:
        """
        Convert a regular convenient value, such as 5, to a value
        that can be used for incremental animation speeds.
        """

        fade_value_speeds = """20
30
40
50
60
70
80
90
100
110
120
130
140
150
160
170
180
190
200
210
220
230
240
250
260
270
280
290
300
310
320
330
340
350
360
370
380
390
400
410
420
430
440
450
460
470
480
490
500
510
520
530
540
550
560
570
580
590
600
610
620
630
640
650
660
670
680
690
700
710
720
730
740
750
760
770
780
790
800
810
820
830
840
850
860
870
880
890
900
910
920
930
940
950
960
970
980
990
1000
1010"""
            

        movement_value_speeds = """70
95
120
145
170
195
220
245
270
295
320
345
370
395
420
445
470
495
520
545
570
595
620
645
670
695
720
745
770
795
820
845
870
895
920
945
970
995
1020
1045
1070
1095
1120
1145
1170
1195
1220
1245
1270
1295
1320
1345
1370
1395
1420
1445
1470
1495
1520
1545
1570
1595
1620
1645
1670
1695
1720
1745
1770
1795
1820
1845
1870
1895
1920
1945
1970
1995
2020
2045
2070
2095
2120
2145
2170
2195
2220
2245
2270
2295
2320
2345
2370
2395
2420
2445
2470
2495
2520
2545"""

        # Key: int convenient value (1 to 100)
        # Value: int value used in animation math.
        speed_mapping = {}

        # Get the int value speeds depending on the type of animation
        # because the animation speeds will differ for fade vs non-fade.
        if "fade" in animation_type:
            speed_values = fade_value_speeds
        else:
            speed_values = movement_value_speeds
        
        # Get a list of float values.
        speed_values = speed_values.split()
        
        # Set the default speed to convenient value 10
        default_speed = float(speed_values[9])

        # Populate the speed_mapping dictionary.
        for idx, f in enumerate(speed_values):
            speed_mapping[idx + 1] = float(f)

        # Get the requested speed and if the speed isn't available,
        # use the default speed.
        animation_speed = speed_mapping.get(int_speed, default_speed)
        
        return animation_speed

    def _prepare_intro_animation(self):

        # Initialize
        self.updated_rect = None
        self.current_fade_value = 0
        initial_alpha: int = 0
        
        # The intro animation hasn't started yet,
        # so the animation is not finished.
        self.intro_complete = False

        # Reset the outro animation flag, because if outro_complete is set to True,
        # it will not be reset again until here. It's necessary for it to be here,
        # so that the outro animation finishes properly; otherwise, the border during
        # the outro will draw in the last few frames of the outro.
        self.outro_complete = False

        # Initial alpha-value
        if self.intro_animation == RectangleIntroAnimation.FADE_IN:
            # We're going to do a fade-in animation,
            # so set the initial fade to zero
            initial_alpha = 0
        else:
            initial_alpha = self.alpha
            

        # Set the current fade value to the same value as the initial fade
        self.fade_current_value = initial_alpha

        # Set the intro animation speed by converting the convenient speed
        # value (1-100) into a value that we can use.
        self.animation_speed =\
            self.convenient_animation_speed_to_value(
                self.animation_speed_convenient,
                self.intro_animation.name.lower())

        # Rectangle width (for borders)
        self.width = self.width_rectangle

        # Rounded corners? Set the size of the rounded corners to 5.
        if self.rounded_corners:
            self.border_radius_rounded_corners = 5
        else:
            self.border_radius_rounded_corners = 0
        
        # Run a reusable script for when the intro animation is starting?
        if self.reusable_on_intro_starting \
           and self.intro_animation != RectangleIntroAnimation.NO_ANIMATION:
            self.spawn_new_background_reader_method\
                (reusable_script_name=self.reusable_on_intro_starting)        

        # Initialize a destination rectangle, which is used to know the final
        # destination of the animation.
        # This is just the initialization part.
        # The X and Y values are decided later in this method,
        # depending on the anchor argument.
        self.rect_destination = pygame.Rect(0, 0, self.width_rectangle,
                                            self.height_rectangle)

        # Make the surface the same size as the rectangle should be
        # once the animation is finished. We will draw the rectangle
        # on this surface.
        self.surface = pygame.Surface((self.rect_destination.width,
                                       self.rect_destination.height),
                                      pygame.SRCALPHA).convert_alpha()

        # Set the destination rectangle, based on the given anchor parameter.
        if self.anchor == AnchorRectangle.MID_BOTTOM:
            self.rect_destination.centerx = self.screen_size[0] / 2 + self.padding_x
            self.rect_destination.y = self.screen_size[1] - self.height_rectangle - self.padding_y
    
        elif self.anchor == AnchorRectangle.MID_LEFT:
            self.rect_destination.x = 0 + self.padding_x
            self.rect_destination.y = self.screen_size[1] / 2 - (self.height_rectangle / 2) + self.padding_y
    
        elif self.anchor == AnchorRectangle.MID_TOP:
            self.rect_destination.centerx = self.screen_size[0] / 2 + self.padding_x
            self.rect_destination.y = 0 + self.padding_y
    
        elif self.anchor == AnchorRectangle.MID_RIGHT:
            self.rect_destination.x = self.screen_size[0] - self.width_rectangle - self.padding_x
            self.rect_destination.y = self.screen_size[1] / 2 - (self.height_rectangle / 2) + self.padding_y
    
        elif self.anchor == AnchorRectangle.TOP_LEFT:
            self.rect_destination.x = 0 + self.padding_x
            self.rect_destination.y = 0 + self.padding_y
    
        elif self.anchor == AnchorRectangle.TOP_RIGHT:
            self.rect_destination.x = self.screen_size[0] - self.width_rectangle - self.padding_x
            self.rect_destination.y = 0 + self.padding_y
    
        elif self.anchor == AnchorRectangle.BOTTOM_LEFT:
            self.rect_destination.x = 0 + self.padding_x
            self.rect_destination.y = self.screen_size[1] - self.height_rectangle - self.padding_y
    
        elif self.anchor == AnchorRectangle.BOTTOM_RIGHT:
            self.rect_destination.x = self.screen_size[0] - self.width_rectangle - self.padding_x
            self.rect_destination.y = self.screen_size[1] - self.height_rectangle - self.padding_y
    
        elif self.anchor == AnchorRectangle.CENTER:
            self.rect_destination.x = self.screen_size[0] / 2 - (self.width_rectangle / 2)
            self.rect_destination.y = self.screen_size[1] / 2 - (self.height_rectangle / 2)


        # Initial rect (starting position, before the animation has started)
        # We're going to alter the initial_rect later to match the start
        # of the effect
        initial_rect = self.rect_destination.copy()


        # Set the initial position, based on the animation
        if self.intro_animation == RectangleIntroAnimation.LEFT_TO_RIGHT:
            initial_rect.x = 0 - self.width_rectangle
    
        elif self.intro_animation == RectangleIntroAnimation.RIGHT_TO_LEFT:
            initial_rect.x = self.screen_size[0]
    
        elif self.intro_animation in (RectangleIntroAnimation.SCALE_UP_HEIGHT_THEN_WIDTH, RectangleIntroAnimation.SCALE_UP_WIDTH_THEN_HEIGHT, RectangleIntroAnimation.SCALE_UP_WIDTH_AND_HEIGHT):
            # Set the initial rectangle to a small size, so it can expand gradually later.
    
            # Set the initial rectangle width/height, depending on the type of animation
            if self.intro_animation == RectangleIntroAnimation.SCALE_UP_HEIGHT_THEN_WIDTH:
                initial_rect.width = 5
                initial_rect.height = 0
            elif self.intro_animation == RectangleIntroAnimation.SCALE_UP_WIDTH_THEN_HEIGHT:
                initial_rect.width = 0
                initial_rect.height = 5      
            elif self.intro_animation == RectangleIntroAnimation.SCALE_UP_WIDTH_AND_HEIGHT:
                initial_rect.width = 5
                initial_rect.height = 5                 


        # Set the animation rect (self.rect) to the initial rect.
        # This is so that self.rect starts at the starting point,
        # before the animation has started.
        self.rect = initial_rect.copy()

        # Set flag so the main game loop knows which method
        # to call for the animation.
        self.animating_intro = True
        self.animating_outro = False        
        
    def update(self) -> pygame.Rect | None:
        """
        Animate the dialog rectangle if needed and save the updated rect.
        """

        if self.animating_intro:
            self._animate_intro()

        elif self.animating_outro:
            self._animate_outro()

    def draw(self):
        """
        Draw the dialog rectangle based on the current animation rectangle.
        """
        if self.visible:
            self.main_screen.blit(self.surface, self.rect)

    def clear_text(self):
        """
        Re-draw the dialog rectangle shape so that any previous text
        gets blitted over with the new rectangle. This causes the previous
        dialog text to get cleared.
        """
        self.redraw_rectangle()

    def _prepare_outro_animation(self):
        """
        Initiate the closing animation of this rectangle.
        """
        
        ## If the waiting arrow is currently animating, hide the image and unload the script that animates it.
        #if StorySettings.waiting_arrow_script_alias in StorySettings.active_scene.scripts.keys():
            #StorySettings.waiting_arrow_image.visible = False
            #StorySettings.active_scene.unload_script(StorySettings.waiting_arrow_script_alias)

        # Set the outro animation speed by converting the convenient speed
        # value (1-100) into a value that we can use.
        self.animation_speed =\
            self.convenient_animation_speed_to_value(
                self.animation_speed_convenient,
                self.outro_animation.name.lower())

        # Reset the text, so it doesn't show any text while
        # the outro animation is occurring.
        self.clear_text()
        
        # Set the outro animation flag so the main game loop knows 
        # to run the outro animation method.
        # self.animating_intro = False
        self.animating_outro = True

        # Hide all dialog-related sprites,
        # because the dialog rectangle is about to close.
        sd.Groups.dialog_group.hide_all()

        ## Consider the intro animation complete at this point, 
        ## even if it hasn't finished yet.
        #self.intro_complete = True
        
        # Consider the outro animation incomplete. This gets
        # used by animate_outro()
        self.outro_complete = False

        # Run a reusable script for when the outro script is starting?
        if self.reusable_on_outro_starting\
           and self.outro_animation != RectangleOutroAnimation.NO_ANIMATION:
            self.spawn_new_background_reader_method\
                (reusable_script_name=self.reusable_on_outro_starting)
        
        # Record where the current center of the rectangle is,
        # before starting the closing animation.
        # This is really only for ScaleDown type animations.
        # ScaleDown type animations will make the destination rectangle
        # smaller below, so we need to know
        # where the center is, before the rectangle is made smaller,
        # so when the gradual animation is run,
        # it can decrease in size with the same center.
        center_before = self.rect_destination.center
        
        # Set the destination of where the animation needs to end
        # We use self.animation_rect, instead of self.rect, so in case
        # the rectangle was in the middle of an intro animation, we use the current
        # size, not the final size.
        if self.outro_animation == RectangleOutroAnimation.GO_RIGHT:
            self.rect_destination.x = self.screen_size[0]
            
        elif self.outro_animation == RectangleOutroAnimation.GO_LEFT:
            self.rect_destination.x = 0 - self.rect.width

        elif self.outro_animation == RectangleOutroAnimation.GO_UP:
            self.rect_destination.y = 0 - self.rect.height

        elif self.outro_animation == RectangleOutroAnimation.GO_DOWN:
            self.rect_destination.y = self.screen_size[1]
            
        elif self.outro_animation == RectangleOutroAnimation.SCALE_DOWN_HEIGHT_THEN_WIDTH:
            self.rect_destination.height = 5
            self.rect_destination.width = 0
            
            # Restore the center it had before (for ScaleDown type animations)
            self.rect_destination.center = center_before                      
            
        elif self.outro_animation == RectangleOutroAnimation.SCALE_DOWN_WIDTH_THEN_HEIGHT:
            self.rect_destination.height = 0
            self.rect_destination.width = 5

            # Restore the center it had before (for ScaleDown type animations)
            self.rect_destination.center = center_before                      
            
        elif self.outro_animation == RectangleOutroAnimation.SCALE_DOWN_WIDTH_AND_HEIGHT:
            self.rect_destination.height = 0
            self.rect_destination.width = 0

            # Restore the center it had before (for ScaleDown type animations)
            self.rect_destination.center = center_before            

    def _animate_outro(self):
        """
        Animate the outro animation, if it has one.
        """
        
        if not self.animating_outro or not self.visible:
            return

        # Clear the surface because we're going to draw a new rectangle.
        # The fourth zero is the alpha (opacity).
        self.surface.fill((0, 0, 0, 0))        

        if not self.outro_complete:
        
            if self.outro_animation == RectangleOutroAnimation.NO_ANIMATION:
                # No animation, just hide the rectangle instantly
                self.outro_complete = True

            elif self.outro_animation == RectangleOutroAnimation.GO_RIGHT:
                # Calculate the animation
                self.rect.x += self.animation_speed * Passer.delta

                # Is the animation satisfied?
                if self.rect.x >= self.rect_destination.x:
                    self.rect.x = self.rect_destination.x
                
                    self.outro_complete = True

            elif self.outro_animation == RectangleOutroAnimation.GO_LEFT:
                # Calculate the animation
                self.rect.x -= self.animation_speed * Passer.delta

                # Is the animation satisfied?
                if self.rect.x <= self.rect_destination.x:
                    self.rect.x = self.rect_destination.x
                
                    self.outro_complete = True

            elif self.outro_animation == RectangleOutroAnimation.GO_UP:
                # Calculate the animation
                self.rect.y -= self.animation_speed * Passer.delta

                # Is the animation satisfied?
                if self.rect.y <= self.rect_destination.y:
                    self.rect.y = self.rect_destination.y
        
                    self.outro_complete = True

            elif self.outro_animation == RectangleOutroAnimation.GO_DOWN:
                # Calculate the animation
                self.rect.y += self.animation_speed * Passer.delta
                # Is the animation satisfied?
                if self.rect.y >= self.rect_destination.y:
                    self.rect.y = self.rect_destination.y
        
                    self.outro_complete = True
        
            elif self.outro_animation == RectangleOutroAnimation.FADE_OUT:
                # Calculate the animation
                self.fade_current_value -= self.animation_speed * Passer.delta
    
                # Clear the rectangle surface because we're going to draw a new rectangle.
                # self.surface.fill((0, 0, 0, 0))

                # Is the animation satisfied?
                if self.fade_current_value <= 0:
                    self.fade_current_value = 0
                
                    self.outro_complete = True

                # Re-draw rectangle
                self.redraw_rectangle()

            elif self.outro_animation in (RectangleOutroAnimation.SCALE_DOWN_HEIGHT_THEN_WIDTH, RectangleOutroAnimation.SCALE_DOWN_WIDTH_THEN_HEIGHT, RectangleOutroAnimation.SCALE_DOWN_WIDTH_AND_HEIGHT):
                # Calculate the animation
                
                if self.outro_animation == RectangleOutroAnimation.SCALE_DOWN_HEIGHT_THEN_WIDTH:
                    # Logic for Scale up height then width

                    # Is the height satisfied?
                    if self.rect.height > self.rect_destination.height:

                        # The height hasn't been satisfied yet. Decrease its height.
                        self.rect.height -= self.animation_speed * Passer.delta
                        
                        # Is the rectangle's height less than the destination rect? Make it the same size.
                        # This is like trimming.
                        if self.rect.height < self.rect_destination.height:
                            # Trim the height to match what it needs to be.
                            self.rect.height = self.rect_destination.height
                            
                    else:

                        # The height is satisfied. Now make the rectangle less wide.

                        # Decrease the width
                        self.rect.width -= self.animation_speed * Passer.delta

                        # Has the width been satisfied?
                        if self.rect.width <= self.rect_destination.width:
                            # The width has been satisfied.

                            # Fix the width in case we're less than desired width.
                            self.rect.width = self.rect_destination.width
                        
                            # The outro animation for this rectangle is now considered complete.
                            self.outro_complete = True
                                                   
                            
                    # Clear the rectangle surface because we're going to draw a new rectangle.
                    # -----We don't need to clear the Surface for this type of animation, because we're going to 
                    # -----initialize a brand new Surface.
                    #self.surface.fill((0,0,0))
                
                
                elif self.outro_animation == RectangleOutroAnimation.SCALE_DOWN_WIDTH_THEN_HEIGHT:
                    # Logic for scaling down the width first, then height.

                    # Is the width satisfied?
                    if self.rect.width > self.rect_destination.width:

                        # The width hasn't been satisfied yet. Decrease its width.
                        self.rect.width -= self.animation_speed * Passer.delta
                        
                        # Is the rectangle's width less wide than the destination rect? Make it the same size.
                        # This is like trimming.
                        if self.rect.width < self.rect_destination.width:
                            # Trim the width to match what it needs to be.
                            self.rect.width = self.rect_destination.width
                            
                    else:

                        # The width is satisfied. Now make the rectangle less tall.
                        
                        # Decrease the height
                        self.rect.height -= self.animation_speed * Passer.delta

                        # Has the height been satisfied?
                        if self.rect.height <= self.rect_destination.height:
                            # The height has been satisfied.

                            # Trim the height in case we're less than desired height.
                            self.rect.height = self.rect_destination.height
                        
                            # The outro animation for this rectangle is now considered complete.
                            self.outro_complete = True
                            
                    
                elif self.outro_animation == RectangleOutroAnimation.SCALE_DOWN_WIDTH_AND_HEIGHT:
                    # Logic for scaling down the width first, then height.
                    
                    width_satisfied = False
                    height_satisfied = False

                    # Is the width satisfied?
                    if self.rect.width > self.rect_destination.width:

                        # The width hasn't been satisfied yet. Decrease its width.
                        self.rect.width -= self.animation_speed * Passer.delta
                        
                        # Has the rectangle's width reached the destination rect? Make it the same size, just in case.
                        # This is like trimming.
                        if self.rect.width <= self.rect_destination.width:
                            # Trim the width to match what it needs to be, just in case.
                            self.rect.width = self.rect_destination.width

                            # The width is now satisfied
                            width_satisfied = True
                            
                    else:
                        # The width is already satisfied
                        width_satisfied = True

                    # Is the height satisfied?
                    if self.rect.height > self.rect_destination.height:

                        # The height hasn't been satisfied yet. Decrease its height.
                        self.rect.height -= self.animation_speed * Passer.delta
                        
                        # Has the rectangle's height reached the destination rect? Make it the same size, just in case.
                        # This is like trimming.
                        if self.rect.height <= self.rect_destination.height:
                            # Trim the height to match what it needs to be, just in case.
                            self.rect.height = self.rect_destination.height

                            # The height is now satisfied
                            height_satisfied = True
                            
                    else:
                        # the height is already satisfied
                        height_satisfied = True

                    # If the height and width are satisfied, consider the animation complete.
                    if width_satisfied and height_satisfied:
                        
                        # The outro animation for this rectangle is now considered complete.
                        self.outro_complete = True

                
                # ---------------
                # Below applies to all scale-up/down type rectangle animations. It's a continuation of that.
                # ---------------

                # Don't create a new surface if there is no outro animation.
                if self.outro_animation != RectangleOutroAnimation.NO_ANIMATION:
                
                    # We're making the width/height of the rectangle bigger, so preserve its center so
                    # the animation happens from 'inside-out', because it's centered.
                    self.rect.center = self.rect_destination.center

                    # Make the surface that we're about to draw the rectangle in, the same as that the animation allows so far.
                    # For this type of animation, the surface is actually used to show the animation. For each frame,
                    # we need to initialize a new Surface to match the size the animation allows so far, so that the rectangle
                    # that gets drawn on the Surface will be fully transparent. If we had left the Surface at its normal size,
                    # the gradual rectangle drawing would happen on a regular-size black Surface. So to avoid a black surface
                    # from getting displayed, we resize the Surface to match the dimensions we need in the animation.
                    self.surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA).convert_alpha()

        
  
            # ---------------
            # Below applies to all types of rectangle animations - the actual drawing process.
            # ---------------            
        
            # Re-draw rectangle
            # We use self.rect to tell pygame.draw.rect() how big we want the rectangle, because the x and y co-ordinates
            # of self.rect are 0,0 (in relation to the surface that it's being drawn to). If we use self.animation_rect, then
            # the x,y of self.animation_rect is probably not 0,0, because self.animation_rect defines where we want the rectangle 
            # to finally end up,
            # so we'll only get a cropped rectangle if we were to use self.animation_rect. That's why we use self.rect.
            # Even though self.rect defines the full size of the rectangle, at this point self.surface is only the size that 
            # the animation has allowed it to be, so even if self.rect is larger than self.surface, the rectangle will still 
            # only show the same size as self.surface, which is fine in our case, because it's a gradual animation.

            # Re-draw rectangle based on its latest animation position.
            # Don't redraw the rectangle if there is no outro animation.
            if self.outro_animation != RectangleOutroAnimation.NO_ANIMATION:
                self.redraw_rectangle()

            # pygame.draw.rect(self.surface, (self.r, self.g, self.b, self.fade_current_value), self.rect, self.width)
            
             
                
                #pygame.display.flip()
        

        # Are we done animating? If so, reset the animating flag
        if self.outro_complete:

            # Indicate to the loop update part that this is the last
            # outro animation frame and after this outro dialog animation,
            # set the visibility of the dialog rectangle to False. If we
            # attempt to set the visibility of the dialog rectangle to
            # False here, the very last outro animation won't refresh/update
            # on the screen, which is why we use this flag so the update
            # gets done, even though the outro dialog animation is done.
            self.next_rect_update_hide_dialog = True

            # Run a specific reusable script?
            if self.reusable_on_outro_finished:
                reusable_on_outro_finished = self.reusable_on_outro_finished
            else:
                reusable_on_outro_finished = None

            # Run the method that resets a 'busy' flag so that the
            # main script reader can resume reading the main script
            # now that this dialog rect's animation is complete.
            self.animation_finished_method(final_dest_rect=self.rect,
                                           run_reusable_script_name=reusable_on_outro_finished)
        
    def _animate_intro(self) -> pygame.Rect | None:
        """
        Animate the intro animation, if it needs to be animated
        and if the dialog rectangle is visible.
        """

        if not self.animating_intro or not self.visible:
            return

        # Clear the surface. The fourth zero is the alpha (opacity).
        self.surface.fill((0, 0, 0, 0))

        if self.intro_animation == RectangleIntroAnimation.NO_ANIMATION:
            # No animation, just show the dialog rectangle right away.
            self.intro_complete = True

        elif self.intro_animation == RectangleIntroAnimation.LEFT_TO_RIGHT:
            # Calculate the animation
            self.rect.x += self.animation_speed * Passer.delta

            # Is the animation satisfied?
            if self.rect.x >= self.rect_destination.x:
                self.rect.x = self.rect_destination.x

                self.intro_complete = True

        elif self.intro_animation == RectangleIntroAnimation.RIGHT_TO_LEFT:
            # Calculate the animation
            self.rect.x -= self.animation_speed * Passer.delta

            # Is the animation satisfied?
            if self.rect.x <= self.rect_destination.x:
                self.rect.x = self.rect_destination.x

                self.intro_complete = True

        elif self.intro_animation == RectangleIntroAnimation.FADE_IN:
            # Calculate the animation
            self.fade_current_value += self.animation_speed * Passer.delta

            # Is the animation satisfied?
            if self.fade_current_value >= self.alpha:
                self.fade_current_value = self.alpha

                self.intro_complete = True

            # Re-draw rectangle
            pygame.draw.rect(self.surface, (self.bg_color.r,
                                            self.bg_color.g,
                                            self.bg_color.b,
                                            self.fade_current_value),
                            self.rect, self.width)

        elif self.intro_animation in (RectangleIntroAnimation.SCALE_UP_HEIGHT_THEN_WIDTH,
                                      RectangleIntroAnimation.SCALE_UP_WIDTH_THEN_HEIGHT,
                                      RectangleIntroAnimation.SCALE_UP_WIDTH_AND_HEIGHT):
            # Calculate the animation

            if self.intro_animation == RectangleIntroAnimation.SCALE_UP_HEIGHT_THEN_WIDTH:
                # Logic for Scale up height then width

                # Is the height satisfied?
                if self.rect.height < self.rect_destination.height:

                    # The height hasn't been satisfied yet. Increase its height.
                    self.rect.height += self.animation_speed * Passer.delta

                    # Is the rectangle's height taller than the destination rect? Make it the same size.
                    # This is like trimming.
                    if self.rect.height > self.rect_destination.height:
                        # Trim the height to match what it needs to be.
                        self.rect.height = self.rect_destination.height

                else:

                    # The height is satisfied. Now make the rectangle wider.

                    # Increase the width
                    self.rect.width += self.animation_speed * Passer.delta

                    # Has the width been satisfied?
                    if self.rect.width >= self.rect_destination.width:
                        # The width has been satisfied.

                        # Trim the width in case we're beyond the desired width.
                        self.rect.width = self.rect_destination.width

                        # The intro animation for this rectangle is now considered complete.
                        self.intro_complete = True

            elif self.intro_animation == RectangleIntroAnimation.SCALE_UP_WIDTH_THEN_HEIGHT:
                # Logic for scaling the width first, then height.

                # Is the width satisfied?
                if self.rect.width < self.rect_destination.width:

                    # The width hasn't been satisfied yet. Increase its width.
                    self.rect.width += self.animation_speed * Passer.delta

                    # Is the rectangle's width wider than the destination rect? Make it the same size.
                    # This is like trimming.
                    if self.rect.width > self.rect_destination.width:
                        # Trim the width to match what it needs to be.
                        self.rect.width = self.rect_destination.width

                else:

                    # The width is satisfied. Now make the rectangle taller.

                    # Increase the height
                    self.rect.height += self.animation_speed * Passer.delta

                    # Has the height been satisfied?
                    if self.rect.height >= self.rect_destination.height:
                        # The height has been satisfied.

                        # Trim the height in case we're beyond the desired height.
                        self.rect.height = self.rect_destination.height

                        # The intro animation for this rectangle is now considered complete.
                        self.intro_complete = True

            elif self.intro_animation == RectangleIntroAnimation.SCALE_UP_WIDTH_AND_HEIGHT:
                # Logic for scaling the width first, then height.

                width_satisfied = False
                height_satisfied = False

                # Is the width satisfied?
                if self.rect.width < self.rect_destination.width:

                    # The width hasn't been satisfied yet. Increase its width.
                    self.rect.width += self.animation_speed * Passer.delta

                    # Has the rectangle's width reached the destination rect?
                    # Make it the same size, just in case.
                    # This is like trimming.
                    if self.rect.width >= self.rect_destination.width:
                        # Trim the width to match what it needs to be, just in case.
                        self.rect.width = self.rect_destination.width

                        # The width is now satisfied
                        width_satisfied = True

                else:
                    # The width is already satisfied
                    width_satisfied = True

                # Is the height satisfied?
                if self.rect.height < self.rect_destination.height:

                    # The height hasn't been satisfied yet. Increase its height.
                    self.rect.height += self.animation_speed * Passer.delta

                    # Has the rectangle's height reached the destination rect? 
                    # Make it the same size, just in case.
                    # This is like trimming.
                    if self.rect.height >= self.rect_destination.height:
                        # Trim the height to match what it needs to be, just in case.
                        self.rect.height = self.rect_destination.height

                        # The height is now satisfied
                        height_satisfied = True

                else:
                    # the height is already satisfied
                    height_satisfied = True

                # If the height and width are satisfied, consider the animation complete.
                if width_satisfied and height_satisfied:

                    # The intro animation for this rectangle is now considered complete.
                    self.intro_complete = True

            # ---------------
            # Below applies to all scale-up/down type rectangle animations. It's a continuation of that.
            # ---------------

            # We're making the width/height of the rectangle bigger,
            # so preserve its center so the animation happens from
            # 'inside-out', because it's centered.
            self.rect.center = self.rect_destination.center


        # ---------------
        # Below applies to all types of rectangle animations - the actual drawing process.
        # ---------------

        # Re-draw rectangle based on its latest animation position.
        self.redraw_rectangle()


        # pygame.display.flip()
    
        # Are we done animating? If so, reset the animating flag
        if self.intro_complete:
            
            # Run a specific reusable script?
            if self.reusable_on_intro_finished:
                reusable_on_intro_finished = self.reusable_on_intro_finished
            else:
                reusable_on_intro_finished = None

            # Run the method that resets a 'busy' flag so that the
            # main script reader can resume reading the main script
            # now that this dialog rect's animation is complete.
            self.animation_finished_method(final_dest_rect=self.rect_destination,
                                           run_reusable_script_name=reusable_on_intro_finished)


    def redraw_rectangle(self):
        """
        Re-draw the dialog rectangle based on its latest animation position
        and its latest fade value.
        
        self.surface is already the size of the destination rectangle,
        but self.surface needs to be told where to be blitted.
        
        We use self.rect to tell self.surface where to be blit (in the draw
        method, not in this method).
        
        self.rect's left and X is likely not going to be at zero
        because it is constantly being animated, relative to the
        main screen.
        
        We need to draw the rectangle at X=0, Y=0 onto self.surface,
        relative to self.surface, not the main screen.
        
        Below, we're going to re-draw the rectangle so its shown with its
        newest animation location. We're going to pass in a copy of self.rect
        but with its X and Y at zero.
        """
        
        animated_rect = self.rect.copy()
        animated_rect.x = 0
        animated_rect.y = 0

        # Draw the dialog rectangle
        pygame.draw.rect(surface=self.surface,
                         color=(self.bg_color.r,
                                self.bg_color.g,
                                self.bg_color.b,
                                self.fade_current_value),
                         rect=animated_rect,
                         width=0,
                         border_radius=self.border_radius_rounded_corners)

        # If the outro is being animated, don't draw the border
        # because the border fade value can be different from the dialog's opacity,
        # which can look odd if the two fades don't match, plus it won't update the rect
        # properly on the last frame.
        if not self.animating_outro and not self.outro_complete:

            # We're not doing an outro animation, so it's OK to draw the border.
            if self.border_alpha > 0 and self.border_width > 0:
                pygame.draw.rect(surface=self.surface,
                                 color=(self.border_color.r,
                                        self.border_color.g,
                                        self.border_color.b,
                                        self.border_alpha),
                                 rect=animated_rect,
                                 width=self.border_width,
                                 border_radius=self.border_radius_rounded_corners)
