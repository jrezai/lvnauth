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
from enum import Enum, auto
from typing import List
from shared_components import Passer
from animation_speed import AnimationSpeed



class FadeDirection(Enum):
    FADE_IN = auto()
    FADE_OUT = auto()


class CoverScreenHandler:
    """
    Handles fading in and fading out the entire screen.
    This is meant for transitioning between scenes.

    It gets used using the <scene_with_fade> command.
    """
    def __init__(self, main_surface: pygame.Surface):

        # Pygame's main surface.
        # This is where we need to blit the cover surface onto.
        self.main_surface = main_surface

        # The cover surface will be blit covering entire size of pygame's window.
        # We'll use the rect below to get the full size we need when blitting.
        self.main_surface_rect = main_surface.get_rect()

        # The size of the 'cover' surface will be the same
        # size as the main surface, because it will cover the entire pygame window.
        width = self.main_surface_rect.width
        height = self.main_surface_rect.height
        self.cover_surface = pygame.Surface((width, height),
                                            flags=pygame.SRCALPHA).convert_alpha()

        # Default to fade-in.
        # This will get overwritten in the start_fading_screen() method
        self.fade_direction = FadeDirection.FADE_IN

        # Controls the fade-speed (float value)
        self.fade_in_speed_incremental = 0
        self.fade_out_speed_incremental = 0

        # The number of seconds that have elapsed so far
        # while at full opacity.
        self.elapsed_full_opacity_seconds:float
        self.elapsed_full_opacity_seconds = 0

        # The number of seconds that we need to reach before
        # starting to fade-out.
        self.hold_seconds_at_full_opacity:float
        self.hold_seconds_at_full_opacity = 0

        # So we know to draw the cover surface or not.
        self.is_cover_animating = False

        self.current_fade_value = 0

        # Initialize
        self.chapter_name = None
        self.scene_name = None

        # Fade color
        self.color = None

    def is_busy_fading(self) -> bool:
        """
        Check whether the screen is fading in or out and not finished
        fading yet.

        Purpose: to prevent a second fade-in / fade-out attempt while the
        first one is busy.
        """

        # Already currently fading in and not finished yet? return True
        if self.is_cover_animating and \
                self.fade_direction == FadeDirection.FADE_IN and \
                self.current_fade_value < 255:
            return True

        # Already currently fading out and not finished yet? return True
        elif self.is_cover_animating and \
                self.fade_direction == FadeDirection.FADE_OUT and \
                self.current_fade_value > 0:
            return True

        else:
            # We're not fading in or fading out.
            return False

    def start_fading_screen(self,
                            hex_color: str,
                            initial_fade_value: int,
                            fade_in_speed_incremental: float,
                            fade_out_speed_incremental: float,
                            hold_seconds: int,
                            chapter_name: str,
                            scene_name: str,
                            fade_direction: FadeDirection = FadeDirection.FADE_IN):
        """
        Start fading in or fading out the entire pygame screen.

        Arguments:
        
        - hex_color: the color, in hex, that we want to cover the screen with.
        
        - initial_fade_value: 0 for fully transparent, 255 for fully opaque.
        
        - fade_in_speed_incremental: the fade-in will increment by this much
        (a float value)
        
        - fade_out_speed_incremental: the fade-out will increment by this
        much (a float value)
        
        - hold_seconds: the number of seconds to hold at full opacity
        before starting to fade out
        
        - chapter_name: the chapter the scene is in that we need to run
        before starting to fade out
        
        - scene_name: the scene we need to run before starting to fade out
        
        - fade_direction: fade in or fade out (based on the FadeDirection
        class).
        """

        # Already fading in or fading out? return
        if self.is_busy_fading():
            return

        # Initialize
        self.fade_in_speed_incremental = fade_in_speed_incremental
        self.fade_out_speed_incremental = fade_out_speed_incremental
        self.color = pygame.Color(hex_color)
        self.current_fade_value = initial_fade_value
        self.chapter_name = chapter_name
        self.scene_name = scene_name
        self.fade_direction = fade_direction
        self.hold_seconds_at_full_opacity = hold_seconds
        self.elapsed_full_opacity_seconds = 0

        # So the main draw method knows to draw the cover surface.
        self.is_cover_animating = True

    def stop_fading_screen(self):
        """
        Stop drawing the cover surface.
        """
        if not self.is_cover_animating:
            return

        self.is_cover_animating = False

    def _get_main_reader(self):
        """
        Return the main active story reader (non-reusable script reader).

        Purpose: we need the main reader object to play a scene
        right before the fade out process.
        """
        main_reader = Passer.active_story.reader.get_main_story_reader()

        return main_reader

    def play_scene(self, chapter_name: str, scene_name: str):
        """
        Play a scene in a specific chapter.
        """
        main_reader = self._get_main_reader()
        main_reader.spawn_new_reader(arguments=f"{chapter_name}, {scene_name}")

    def update(self):
        """
        Elapse the frame counter and increase/decrease the fade value
        if the elapsed frame count has reached the frame_delay value.

        No rect is updated, because it's always the full size of the pygame window.
        """
        
        # Not animating or no speed specified? Return.
        if not self.is_cover_animating or not all([self.fade_in_speed_incremental,
                                                   self.fade_out_speed_incremental]):
            return

        if self.fade_direction == FadeDirection.FADE_IN:

            # Have we reached fully opacity?
            if self.current_fade_value >= 255:
                
                # We've reached full opacity, but we should not
                # stop drawing the cover surface on the screen,
                # because otherwise, the cover surface will just disappear.
                self.current_fade_value = 255

                if self.elapsed_full_opacity_seconds \
                   > self.hold_seconds_at_full_opacity:
                    
                    # We've reached the seconds limit at full opacity.

                    # Run the scene that is supposed to run and then
                    # start fading-out.
                    self.play_scene(self.chapter_name, self.scene_name)

                    # Start fading-out
                    self.fade_direction = FadeDirection.FADE_OUT

                    # Re-run this method immediately, now that 
                    # we're in fade-out mode.
                    self.update()

                    return

                else:
                    # We haven't reached the seconds-elapsed limit at full
                    # opacity. We're not ready to start fading-out yet.
                    self.elapsed_full_opacity_seconds += AnimationSpeed.delta

                    return

            # Fade-in more
            self.current_fade_value += self.fade_in_speed_incremental \
                * AnimationSpeed.delta

            # Don't allow the fade to go out of range.
            if self.current_fade_value > 255:
                self.current_fade_value = 255

        elif self.fade_direction == FadeDirection.FADE_OUT:

            # Have we reached full transparency?
            if self.current_fade_value <= 0:
                # Stop animating, we've reached full transparency.
                self.current_fade_value = 0
                self.is_cover_animating = False
                return

            # Fade-out more
            # (fade_speed_incremental will be a negative value when fading out).
            self.current_fade_value -= self.fade_out_speed_incremental \
                * AnimationSpeed.delta

            # Don't allow the fade to go out of range.
            if self.current_fade_value < 0:
                self.current_fade_value = 0

    def draw(self):
        """
        Blit the cover surface on pygame's main surface.
        """
        if not self.is_cover_animating:
            return

        # Fill the cover surface with the latest fade value.
        self.cover_surface.fill(color=(self.color.r,
                                       self.color.g,
                                       self.color.b,
                                       self.current_fade_value))

        # Draw the cover surface on pygame's main surface.
        self.main_surface.blit(self.cover_surface, self.main_surface_rect)

