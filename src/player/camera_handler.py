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

import pygame
import random
from enum import Enum, auto
from animation_speed import AnimationSpeed



class SmoothingStyle(Enum):
    LINEAR_CONSTANT_SPEED = auto()
    IN_START_SLOW_SPEED_UP = auto()
    OUT_START_FAST_SLOW_DOWN = auto()
    SMOOTH_EASE_IN_OUT = auto()


class Camera:
    def __init__(self, screen_size):
        
        # Store the width/height of the actual display window
        self.screen_width = screen_size[0]
        self.screen_height = screen_size[1]
        
        # Default to the center of the provided screen size.
        # This ensures the camera looks at the middle of the window by default.
        self.x = self.screen_width / 2.0
        self.y = self.screen_height / 2.0
        
        # Initialize zoom level to 1.0 (100% scale, no zoom)
        self.zoom = 1.0
        
        # A flag to indiciate if a pan/zoom animation is currently occurring.
        # It does not include shaking.
        self.is_animating_zoom_pan = False
        
        # A flag to indicate if the shake effect is active or not.
        self.is_animating_shake = False
        
        # How much time has passed since the animation started
        self.elapsed_time = 0.0
        
        # Total time (in seconds) the current animation should take to finish.
        self.duration = 1.0
        
        # The type of movement smoothing (linear, smooth, ease-in, etc.)
        self.easing_mode = SmoothingStyle.SMOOTH_EASE_IN_OUT
        
        # Tuple storing the camera's position/zoom at the start of an animation.
        self.start_state = (self.x, self.y, self.zoom)
        
        # Tuple storing the target position/zoom of where the animation ends.
        # For now, it's the same as start_state.
        self.end_state = (self.x, self.y, self.zoom)
        
        # How many pixels the screen shifts during a shake
        self.shake_intensity = 0.0
        
        # How long the shake lasts in seconds
        self.shake_duration = 0.0
        
        # Countdown timer for the current shake effect
        self.shake_timer = 0.0
        
        # A persistent surface used to store the zoomed/scaled image.
        # We reuse this to avoid creating a new image in memory every frame.
        self.scaling_buffer: pygame.Surface
        self.scaling_buffer = None
        
        # Tracks the dimensions of the buffer to compare if we need to scale
        # the zoom level in the current frame or not. If the camera is not
        # scaling/moving, last_buffer_size will be the same size as the current
        # calculated size of the surface, so there will be no need to scale
        # the surface again. This saves CPU time. It's a caching system to
        # prevent unnecessary transform.smoothscale(), because it can be
        # a CPU intense process.
        self.last_buffer_size = (0, 0)

    def start_move(self,
                   target_x: int=None,
                   target_y: int=None,
                   target_zoom: float=None,
                   duration: float=1.0,
                   mode: SmoothingStyle=SmoothingStyle.SMOOTH_EASE_IN_OUT):
        """
        Start the animation of zooming in and/or panning.
        
        Arguments:
        
        - target_x: the x location to zoom in or out on
        
        - target_y: the y location to zoom in or out on
        
        - target_zoom: the destination zoom level.
        
        - duration: how long to it should take to finish the animation,
        in seconds. This affects the speed of the animation.
        
        - mode: the smoothness type for zooming in/out.
        
        If target_x or target_y is None, it defaults to the screen center,
        so it will zoom it on the center.
        
        If target_zoom is None, it stays at the current zoom.
        """
        
        # Record the current state as the starting point for the new animation
        self.start_state = (self.x, self.y, self.zoom)
        
        # If no destination coordinates are supplied, assume the center of the 
        # surface.
        # Check if X is provided, otherwise use screen center
        if target_x is None:
            final_x = self.screen_width / 2.0
        else:
            final_x = target_x
            
        # final_x = target_x if target_x is not None else self.screen_width / 2.0
        
        # Check if Y is provided, otherwise use screen center
        if target_y is None:
            final_y = self.screen_height / 2.0
        else:
            final_y = target_y
        # final_y = target_y if target_y is not None else self.screen_height / 2.0
        
        # Check if Zoom is provided, otherwise keep current zoom
        if target_zoom is None:
            # Default to 1.0 zoom
            final_zoom = self.zoom
        else:
            final_zoom = target_zoom
        # final_zoom = target_zoom if target_zoom is not None else self.zoom

        # Set the target destination values
        self.end_state = (final_x, final_y, final_zoom)
        
        # Ensure duration is at least 0.01 to prevent division by zero 
        # errors later
        self.duration = max(0.01, duration)
        
        # Reset the animation timer
        self.elapsed_time = 0.0
        
        # Set the smoothing style
        self.easing_mode = mode
        
        # Set the animation flag so 'update' knows to process movement
        self.is_animating_zoom_pan = True

    def start_shake(self, intensity: float, duration: float):
        """
        Start a screen shake animation.
        
        A screen shake effect decays over time.

        This effect is additive, meaning it can run simultaneously with 
        pan and zoom animations without interrupting them.
        
        Arguments:
        
        - intensity: the max pixel distance the screen will offset.
        
        - duration: how long the shake animation will occur, in seconds.
        The duration will be attempted but not guaranteed. The reason is:
        a shake animation will start off stronger and will gradually get weaker.
        If the shake intensity is low, the intensity will get weaker sooner,
        which may not reach the duration. Use a higher intensity, such as 5.0
        or 10.0, to ensure the duration in seconds, will be reached.
        """

        # Set the max pixel distance the screen will offset
        self.shake_intensity = intensity
        
        # Set the total duration of the shake in seconds.
        self.shake_duration = duration
        
        # Reset the countdown timer
        # This is used to know when a shake animation should be stopped.
        self.shake_timer = duration
        
        # Set active flag
        self.is_animating_shake = True

    def stop_move(self, jump_to_end: bool = False):
        """
        Immediately stops any active pan/zoom animation.
    
        Arguments:
        - jump_to_end: If True, instantly teleports the camera to its
        final destination. This will be True if the mouse is clicked while
        the camera is moving.
        
        If False, the camera freezes exactly where it is currently. 
        (Use this for dramatic interruptions).
        """
        
        # Skip to the destination? (used when the user clicks to proceed
        # faster)
        if jump_to_end and self.is_animating_zoom_pan:
            # Snap position and zoom to the values stored in end_state
            self.x = self.end_state[0]
            self.y = self.end_state[1]
            self.zoom = self.end_state[2]
    
        # No longer animationg zoom/pan
        self.is_animating_zoom_pan = False
    
        # 3. Reset the timer, ready for next time.
        self.elapsed_time = 0.0

    def stop_shake(self):
        """
        Stop the shake effect if it's active.
        """
        
        if self.is_animating_shake:
            
            # Reset the shake effect variables
            self.shake_intensity = 0.0
            self.shake_duration = 0.0            
            self.shake_timer = 0.0
            
            self.is_animating_shake = False

    def _get_progress(self, t) -> float:
        """
        Calculate the eased animation progress based on the normalized time.
        
        Arguments:
        - t (float): the raw time normalized progress from 0.0 (start)
        to 1.0 (end).
            
        Returns:
        float: The eased progress value (typically 0.0 to 1.0) used to 
               interpolate position and zoom. Depending on the easing 
               mode, this value creates a sense of acceleration, 
               deceleration, or smoothness.
        """
        
        # If linear, return the raw time percentage (constant speed)
        if self.easing_mode == SmoothingStyle.LINEAR_CONSTANT_SPEED:
            return t
        
        # If 'in', use quadratic easing (starts slow, speeds up)
        if self.easing_mode == SmoothingStyle.IN_START_SLOW_SPEED_UP:
            return t * t
        
        # If 'out', use inverse quadratic (starts fast, slows down)
        if self.easing_mode == SmoothingStyle.OUT_START_FAST_SLOW_DOWN:
            return 1 - (1 - t) * (1 - t)
        
        # Default to Ease-In-Out Quad (Used for "smooth")
        # Uses a piecewise function to speed up in middle and slow down 
        # at both ends
        if t < 0.5:
            return 2*t*t
        else:
            return 1 - (-2*t + 2)**2 / 2
        # return 2*t*t if t < 0.5 else 1 - (-2*t + 2)**2 / 2

    def update(self, dt: float):
        """
        Advance the camera's internal timers and calculate current state values.
        
        This method must be called once per frame. It processes active pan/zoom 
        animations and countdowns for screen shake effects. All movement is 
        frame-rate independent, relying on the delta time (dt).

        Arguments:
        
        - dt (float): The time elapsed since the last frame in seconds 
        (e.g., 0.016 for 60 FPS).
        """
        
        # Check if we are currently moving/zooming (doesn't apply to shaking)
        if self.is_animating_zoom_pan:
            
            # Add the time passed since the last frame, to the timer
            self.elapsed_time += dt
            
            # Normalized time.
            # This calculates the percentage complete (0.0 to 1.0) for the 
            # zoom/pan. It normalizes the elapsed time and duration so it 
            # fits into a range (0.0 to 1.0)
            t = min(1.0, self.elapsed_time / self.duration)
            
            # Apply easing math to get the smoothed progress value
            prog = self._get_progress(t)

            # Determine the X position based on the animation's progress
            self.x = self.start_state[0]\
                + (self.end_state[0] - self.start_state[0])\
                * prog
            
            # Determine the Y position based on the animation's progress
            self.y = self.start_state[1]\
                + (self.end_state[1] - self.start_state[1])\
                * prog
            
            # Determine the current Zoom based on the animation's progress.
            self.zoom = self.start_state[2]\
                + (self.end_state[2] - self.start_state[2])\
                * prog

            # Has the zoom/pan animation finished?
            if t >= 1.0:
                # Stop the zoom/pan logic
                self.is_animating_zoom_pan = False
                

        # Check if a screen shake is active
        if self.shake_timer > 0:
            
            # Decrease the shake timer by delta time
            self.shake_timer -= dt
            
            # Ensure timer doesn't go below zero
            if self.shake_timer < 0:
                
                # The shake effect is finished.
                
                # Reset the shake effect variables
                self.stop_shake()

    def apply(self,
              virtual_surface: pygame.Surface, main_surface: pygame.Surface):
        """
        Blit virtual_surface (the scaled/zoomed/panned surface) onto the
        main display surface.

        This method handles the final transformation pipeline, including 
        frame-rate independent scaling (zoom), camera centering (panning), 
        and screen shake offsets. It utilizes a caching buffer to minimize 
        CPU-intensive scaling operations.

        Arguments:
        
        - virtual_surface: the surface where scaling/panning effects take
        place.
        
        - main_surface: the main display surface - what the user sees.

        If the zoom level is 1.0, no scaling is done. At that point,
        virtual_surface is just blitted onto main_surface, without CPU
        intensive scaling.
        """
        
        # Get the dimensions of the virtual surface; we'll need it
        # when calculating scaling (zooming).
        VIRTUAL_RES = virtual_surface.get_size()
    
        # If the zoom level is 1.0 (or very close to 1.0), skip the expensive
        # scaling entirely. There's no need to scale when the zoom is 1.0 or
        # very close to 1.0
        if abs(self.zoom - 1.0) < 0.001:
            
            # No zoom is required.
 
            # The zoom is 1.0 or very close to 1.0, such as 1.000002
 
            # We don't need to calculate the center since the zoom is 1.0,
            # so leave X and Y at the defaults (0,0) so the surface covers
            # the whole window.
            render_x = 0
            render_y = 0
    
            # Apply the shake effect (if the effect is active)
            # Check if the shake countdown is still active (above zero)
            if self.shake_timer > 0:
                
                # Calculate how much of the shake is left as a percentage 
                # (1.0 at start, 0.0 at end)
                # This creates a "linear falloff" so the shake weakens over time                
                falloff = self.shake_timer / self.shake_duration
                
                # Multiply the max shake strength by the falloff to get the 
                # current frame's power
                # If cur_shake drops below 0.5, Pygame will round that offset 
                # to 0, which is why very long, low-intensity shakes seem to 
                # "stop early" visually. See the docstring in the update()
                # method for more info.
                cur_shake = self.shake_intensity * falloff
                
                # Pick a random number between negative and positive power 
                # and add it to the X and Y positions
                render_x += random.uniform(-cur_shake, cur_shake)
                render_y += random.uniform(-cur_shake, cur_shake)
    
            # Draw directly, no scaling needed because the zoom is 1.0.
            # We must clear the screen first to avoid "trails" if the shake
            # effect is being used. If a shake effect is not being used, then 
            # the virtual_surface will simply be rendered on the main_surface.
            main_surface.fill((0, 0, 0))
            main_surface.blit(virtual_surface, (round(render_x), round(render_y)))
            
            # No zoom will be taking place, so return.
            return
    
        # -- Zoom logic (when zoom != 1.0) --
        curr_w = int(round(VIRTUAL_RES[0] * self.zoom))
        curr_h = int(round(VIRTUAL_RES[1] * self.zoom))
        current_size = (curr_w, curr_h)
    
        # Buffer Memory Management (only create new surfaces when size changes)
        if current_size != self.last_buffer_size:
            
            # Create a new surface, the size is different from last time.
            self.scaling_buffer = pygame.Surface(current_size, pygame.SRCALPHA)
            self.last_buffer_size = current_size
    
        # Draw virtual_surface to the buffer *every frame*; 
        # not just when size changes, because other changes could have occurred
        # in the virtual_surface (dialogue text, other types of animations, etc.)
        pygame.transform.smoothscale(virtual_surface,
                                     current_size,
                                     self.scaling_buffer)
    
        # Calculate Position using Effective Zoom (prevents wobble)
        # This math ensures that the "center" of the zoom doesn't jitter 
        # or wobble as the image resizes.
        
        # Calculate the real horizontal/vertical zoom by dividing the rounded 
        # width/height by the original width/height. This tells us exactly how 
        # much the pixels were stretched after rounding to an integer        
        eff_zoom_x = curr_w / float(VIRTUAL_RES[0])
        eff_zoom_y = curr_h / float(VIRTUAL_RES[1])
    
        # Calculate the X and Y coordinates to draw at.
        # This keeps the final render centered.   
        render_x = (self.screen_width / 2) - (self.x * eff_zoom_x)
        render_y = (self.screen_height / 2) - (self.y * eff_zoom_y)
    
        # Apply Shake to the Zoomed View
        if self.shake_timer > 0:
            
            # Determine the shake strength multiplier (1.0 at start, 
            # fading to 0.0 at the end)
            falloff = self.shake_timer / self.shake_duration
            
            # Calculate the maximum pixel distance to shift based on 
            # intensity and time remaining
            cur_shake = self.shake_intensity * falloff
            
            # Add a random horizontal/vertical shift within the current shake 
            # range to the draw position
            render_x += random.uniform(-cur_shake, cur_shake)
            render_y += random.uniform(-cur_shake, cur_shake)
    
        # Final draw
        # Fill the background with solid black to prevent seeing "ghost" 
        # images behind the buffer
        main_surface.fill((0, 0, 0))
        
        # Draw the zoomed buffer to the screen, rounding the coordinates 
        # to the nearest whole pixel to prevent "blurry" edges or sub-pixel 
        # rendering artifacts        
        main_surface.blit(self.scaling_buffer, (round(render_x), round(render_y)))


        
#"""
#Usage:

## Script Example: shake

## Zoom in slightly so it doesn't show the borders around the image when
## it's shaken.
#camera.start_move(target_x=960, target_y=540, target_zoom=1.05, duration=0.1)

## Shake
#camera.start_shake(intensity=20, duration=1.0)
#"""