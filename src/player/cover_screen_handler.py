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
from shared_components import Passer
from enum import Enum, auto
from typing import List


class FadeDirection:
    FADE_IN = auto()
    FADE_OUT = auto()


class CoverScreenHandler:
    """
    Handles fading in and fading out the entire screen.
    This is meant for transitioning between scenes.

    It gets used using the <fade_screen> command.
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

        # Controls the fade-speed
        self.frame_delay = 0

        # So we know when to apply the fading animation
        # (when elapsed_frames reaches frame_delay)
        self.elapsed_frames = 0

        # So we know to draw the cover surface or not.
        self.is_cover_animating = False

        self.current_fade_value = 0

        # Fade color
        self.color = None

    def start_fading_screen(self,
                            hex_color: str,
                            initial_fade_value: int,
                            frame_delay: int,
                            fade_direction: FadeDirection = FadeDirection.FADE_IN):
        """
        Start fading in or fading out the entire pygame screen.

        Arguments:
            - hex_color: the color, in hex, that we want to cover the screen with.
            - initial_fade_value: 0 for fully transparent, 255 for fully opaque.
            - frame_delay: how many frames to skip before applying each fade animation.
            - fade_direction: fade in or fade out (based on the FadeDirection class).
        """

        # Already animating? return
        if self.is_cover_animating:
            return

        # Initialize
        self.frame_delay = frame_delay
        self.elapsed_frames = 0
        self.color = pygame.Color(hex_color)
        self.current_fade_value = initial_fade_value
        self.fade_direction = fade_direction

        # So the main draw method knows to draw the cover surface.
        self.is_cover_animating = True

    def stop_fading_screen(self):
        """
        Stop drawing the cover surface.
        """
        if not self.is_cover_animating:
            return

        self.is_cover_animating = False

    def update(self):
        """
        Elapse the frame counter and increase/decrease the fade value
        if the elapsed frame count has reached the frame_delay value.

        No rect is updated, because it's always the full size of the pygame window.
        """
        if not self.is_cover_animating:
            return

        if self.elapsed_frames <= self.frame_delay:
            self.elapsed_frames += 1
            return

        self.color: pygame.Color

        if self.fade_direction == FadeDirection.FADE_IN:

            # Have we reached fully opacity?
            if self.current_fade_value >= 255:
                self.current_fade_value = 255
            else:
                # Fade-in more.
                self.current_fade_value += 1

        elif self.fade_direction == FadeDirection.FADE_OUT:

            # Have we reached full transparency?
            if self.current_fade_value == 0:

                # There is no need to draw the cover surface anymore.
                self.is_cover_animating = False
            else:
                # Fade-out more
                self.current_fade_value -= 1

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

    def get_updated_rect(self) -> List[pygame.Rect]:
        """
        Return a list with the rect of the main surface, but only if the cover
        surface is animating. If not animating, return an empty list.
        """
        if self.is_cover_animating:
            return [self.main_surface_rect]
        else:
            return []
