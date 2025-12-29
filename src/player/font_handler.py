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


from __future__ import annotations
from animation_speed import AnimationSpeed


"""
Changes:

Nov 29, 2023 (Jobin Rezai) - check for gradual_delay_counter >= instead of
just '>'. fade_text_delay value of 1 was being represented as 2 before
this fix.)
"""
import pygame
# import active_story
import logging
import audio_player
from typing import Dict, List, Tuple, TYPE_CHECKING
from enum import Enum, auto
from shared_components import Passer
import time

if TYPE_CHECKING:
    # Only gets imported for type checking
    from sprite_definition import SpriteObject

logging.basicConfig(format="%(levelname)s:%(message)s")


"""
Holds a surface (of a single letter's image)
and its rect position (pygame rect), relative to
the dialog rectangle, and also its alpha (opacity) level (0 to 255)
"""
class Letter:

    def __init__(self,
                 rect: pygame.Rect,
                 surface: pygame.Surface,
                 opacity: int = 255,
                 is_space: bool = False,
                 previous_letter: str = None):

        # For debugging
        # opacity = 100
    
        self.rect = rect
        self.surface = surface
        self.surface_original = surface.copy()
        self.opacity = opacity
        self.is_space = is_space
        self.previous_letter = previous_letter

        # Apply the given opacity to the letter image.
        # If the opacity is 255, it won't make a difference to have this line,
        # but if the opacity is less than 255, we need to apply it here.
        if opacity < 255:
            self.surface.fill((255, 255, 255, opacity), None, pygame.BLEND_RGBA_MULT)

    def set_opacity(self, opacity: int):
        """
        Set the new opacity level using the original letter (which always has
        an opacity of 255) as its source image.
        """

        if opacity > 255:
            opacity = 255
            
        elif opacity < 0:
            opacity = 0
            
        if self.opacity == opacity:
            return
        
        self.opacity = opacity

        self.surface = self.surface_original.copy()
        self.surface.fill((255, 255, 255, self.opacity), None, pygame.BLEND_RGBA_MULT)

    def increase_opacity_by(self, increment_by: int):
        """
        Increase the letter's current opacity by the given amount.
        
        Purpose: this gets used by gradual letter fade in animation.
        """
        opacity = self.opacity
        opacity += increment_by

        self.set_opacity(opacity)

# For when the character text is being displayed.
class FontAnimationShowingType(Enum):
    SUDDEN = auto()
    FADE_IN = auto()
    GRADUAL_LETTER = auto()
    GRADUAL_LETTER_FADE_IN = auto()


class FontLetterDelayHandler:
    """
    Used for calculating and elapsing second delays when showing
    letter by letter gradual font animations (non-fading).
    
    This prioritizes time accuracy over over frame-by-frame consistency.
    If the frame rate drops, the text will advance by multiple 
    characters in one frame to keep time with the clock.
    """
    def __init__(self, sprite_mode: bool):
        
        # Punctuation delay
        # Key: (str) letter
        # Value: (float) number of seconds to delay
        # Used for gradual letter text displays (not gradual letter fading)
        self.letter_delays = {}
        
        # For measuring the speed of gradual letter by letter (non-fade)
        # at different frame rates. Used for development-only.
        self.start_time = None

        # The number of seconds to delay when applying gradual text 
        # animation.
        # For letter-by-letter animation only (not *any* fade-ins.)
        self.font_text_delay: float = 0.10
        
        # For keeping track of the number of seconds that have been elapsed 
        # so far for gradual text display animation.
        self.time_since_last_letter_shown: float = 0
        
        # The number of characters that should be visible based on time.
        self.count_letters_should_be_visible:int = 0
        
        # The number of seconds to wait due to reaching a punctuation 
        # letter. This is separate from the regular gradual text delay.
        self.punct_wait_seconds:float = 0
        
        # How many seconds have been waited so far on a punctuation pause.
        self.punct_waited_so_far:float = 0
        
        self.sprite_mode = sprite_mode
        
    def set_letter_delay(self, letter: str, delay_seconds: int):
        """
        Set a delay for a specific letter.
        
        For example, if "." is provided as the letter with a delay_seconds
        value of 0.5, then any period that gets shown will pause for half a
        second, before showing the next letter.
        
        Used with <font_text_delay_punc>
        """

        if not letter:
            return
        elif len(letter) > 1:
            return
        elif not isinstance(letter, str):
            return
        elif not isinstance(delay_seconds, int) \
             and not isinstance(delay_seconds, float):
            return
        elif delay_seconds < 0:
            return
        
        # If the value is 0 (zero), remove the delay rule if the letter exists.
        if delay_seconds == 0:
            if letter in self.letter_delays:
                del self.letter_delays[letter]
        else:
            
            # Add or update letter delay.
            self.letter_delays[letter] = delay_seconds

    def get_font_after_letter_delay(self, letter: str) -> int:
        """
        Get the number of seconds to delay after a specific
        letter is shown.
    
        A letter's delay is set using the command: <font_text_delay_punc>
        """
        delay_seconds =\
            self.letter_delays.get(letter, 0)
        
        return delay_seconds
    
    def check_wait_punctuation(self, previous_letter: str) -> bool:
        """
        Check if the given letter is a letter that should be cause a delay
        for X number of seconds. If so, set a variable to the number of
        seconds that should be waited (self.punct_wait_seconds).
        
        Return: True if the given letter should cause a delay. The caller then
        should wait before showing the next letter.
        
        Return: False if the given letter is a normal letter with no delay
        required.
        """
        
        # Was the previous letter a letter that should 
        # cause this new letter to delay for X number of seconds?
        # (ie: if the previous letter was a ".")
        self.punct_wait_seconds =\
            self.get_font_after_letter_delay(previous_letter)
        
        # Should we wait a few seconds because the last letter
        # was a punctuation letter?
        if self.punct_wait_seconds > 0:
            # Yes, we should wait before showing the current letter
            # because the last letter had a punctuation delay.
            # Check again in the next frame to find out if enough
            # time has elapsed in the next frame.
            return True
        
        return False
    
    def update(self, 
               delta: float, 
               letter_cursor_position: int, 
               letters: List[Letter], 
               fast_mode: bool = False) -> Tuple[int, bool] | int | None:
        """
        Advances the text index using delta time. Uses a while loop to ensure 
        the cursor letter index catches up by making multiple letters opaque
        if needed, if the frame rate is slow. The purpose is to ensure
        the making-letters-opaque process finishes making all the letters
        opaque at the roughly the same time, regardless of the frame rate.
        
        It prioritizes time-accuracy rather than making sure it's always one
        letter per frame.
        
        Return: a tuple (int, bool) to indicate where the letter cursor
        has stopped/finished, and True to indiciate that all the letters
        have been made opaque so the caller should stop animating the text.
        
        Return: None if no letters should be shown in the current frame
        by the caller due to an unfinished punctuation delay.
        
        Return: an int that represents the letter cursor position, to let
        the caller of this method know how far the letters have been made
        opaque, ready to be passed in again to this method in the next frame.
        
        Arguments:
        
        - delta: the number of seconds elapsed since the last frame.
        
        - letter_cursor_position: where we are in the visibility cursor
        when showing letter-by-letter non-fading letters. This is a reference
        to FontAnimation's self.gradual_letter_cursor_position
        
        - letters: a list of letter objects that need to eventually all be
        displayed. We use this list to show letters gradually by changing
        their opacity levels to 255. This variable is a reference to
        FontAnimation's self.letters, not a copy. So any changes we make to
        this list inside this method affects the caller of this method's
        list instance too.
        
        - fast_mode: whether the dialogue text animation is in fast-mode.
        Fast-mode is when the viewer has clicked on the visual novel to
        accelerate the text animation.
        """
    
        ### 1. Handle Punctuation Delays (seconds-based, not milliseconds) ---
        
        # Is there a punctuation delay we need to enforce?
        # Enforce a punctuation delay if:
        # 1) The VN is not in fast-mode
        # 2) The VN has been told to wait for a punctuation delay
        # since the last letter was shown.
        if not fast_mode and self.punct_wait_seconds > 0:
            
            # Check if we've waited long enough for the punct delay.
            if self.punct_waited_so_far < self.punct_wait_seconds:
                
                # No, we have not waited long enough.
                
                # Increment the punctuation delay counter.
                self.punct_waited_so_far += delta
                
                # We haven't waited long enough for a punctuation delay.
                # Return and check again in the next frame.                
                return
            else:
                # Yes, we've waited long enough for a punctuation delay.
                # Reset the wait variables.                
                self.punct_wait_seconds = 0
                self.punct_waited_so_far = 0
                
        """
        At this point, no punctuation delay waiting is needed because
        the checks have already been done at the top.
        """        
    
        ### Time Accumulation
        
        # Accumulate the time elapsed since the last frame
        self.time_since_last_letter_shown += delta
    
        # Target delay in seconds
        # If we're in fast-mode or if no delay has been set (0 zero),
        # then set the delay speed to a fast value.
        if fast_mode or not self.font_text_delay:
            target_delay = 0.012
        else:
            target_delay = self.font_text_delay
    
        # Calculate how many letters we're allowed to show to keep sync 
        # with time.
        chars_to_process =\
            int(self.time_since_last_letter_shown // target_delay)
    
        # Too soon to display another letter? Return.
        # This way, if the frame rate is really fast, it should return 
        # here often.
        if chars_to_process == 0:
            return

        # print(f"{chars_to_process=}")
    
        # To let this method know to return the current latest cursor position
        # after it's finished, so the caller knows which letter needs to be
        # shown next in the next frame.    
        letter_position_advanced = False
        
        # This gets set to True if there are no more letters to show.
        is_finished = False
    
        # Make opaque as many letters as we're allowed in this frame.
        for _ in range(chars_to_process):

            ### Handle Spaces Quickly
            
            # If we're on a space letter, make it opaque now.
            # Make all consecutive spaces opaque.
            while letters[letter_cursor_position].is_space:
                
                # The current letter is a space, so quickly show it.
                letters[letter_cursor_position].set_opacity(255)
                
                # No more letters to advance? Consider it done.
                if letter_cursor_position + 1 >= len(letters):
                    is_finished = True
                    break
                else:
                    # Advance by one letter, because this letter was 
                    # just a space.
                    letter_cursor_position += 1
                    letter_position_advanced = True
                
                
            # No more letters to show? Finish the letter for-loop now.
            if is_finished:
                break

            # Make the current non-space letter opaque now.
            letters[letter_cursor_position].set_opacity(255)
          
            # Play a sound for this letter, if configured to do so. 
            # Play a sound for every 3rd letter in fast-mode to help prevent 
            # audio problems.
            if not self.sprite_mode:
                should_play = not fast_mode or (letter_cursor_position % 3 == 0)
                if should_play:
                    Passer.active_story.audio_player.play_audio(
                            audio_name=Passer.active_story.dialog_rectangle.text_sound_name,
                            audio_channel=audio_player.AudioChannel.TEXT)


            # No more letters to advance? Consider it done.
            if letter_cursor_position + 1 >= len(letters):
                is_finished = True
                break
            else:
                # Yes, there are more letters to advance.
                # Advance the cursor by 1 letter if we haven't already done so.
                letter_cursor_position += 1
                letter_position_advanced = True              
    
            # Spend one unit of delay time from the accumulator
            self.time_since_last_letter_shown -= target_delay
    
            # Does the previous letter require a punctuation delay?
            # If so, self.punct_wait_seconds will be set 
            # automatically (by the method below) to the number of 
            # seconds that should be waited.
            prev_letter = letters[letter_cursor_position].previous_letter
            if self.check_wait_punctuation(prev_letter):
                # Yes, the previous letter needs a punctuation delay.
                
                # Reset the leftover time so the text does not "sprint" 
                # unnaturally immediately after the punctuation pause finishes.
                self.time_since_last_letter_shown = 0
    
                # Return the current letter's position, for use in the 
                # next frame.       
                return letter_cursor_position
    
        ### Cleanup
    
        # Have all the letters finished showing? Reset the variables so
        # we're ready for the next batch of letters if needed.    
        if is_finished:
            
            # Reset variables, making them ready for the next batch
            # of letters. There are currently no more letters to show.            
            self.count_letters_should_be_visible = 0
            self.time_since_last_letter_shown = 0.0
            self.punct_wait_seconds = 0
            
            """
            For debugging, to measure how long it took to make all
            the letters in the batch opaque (letter by letter, non fade). 
            This is useful when trying to make sure all the letters are 
            finished showing at roughly the same time regardless of 
            the frame rate.
            """
            end_time = time.perf_counter()
            duration = end_time - self.start_time
            # print(f"Time taken to show all letters: {duration*1000:.3f} milliseconds")
            
            """
            Return the cursor position and True. True tells the caller
            to stop the text intro animation.
            The reason we return the cursor position even though we're done
            showing all the letters is because more text might be needed
            to be shown where we left off, using <no_clear>, which resumes
            the cursor position and appends text to where we left off.
            So the caller still needs to know where the cursor was stopped.    
            """
            return (letter_cursor_position, True)
    
        elif letter_position_advanced:
            
            """
            At this point, we're not done showing all the letters yet.
            But we need to delay a bit before showing the next letter,
            which is why we need to return the current letter position
            to the caller so on the next frame we'll resume where we left off.
            """
            
            # The actual cursor position gets updated by the caller of this
            # method. We just use a copy of the position in this method,
            # which is why we return an updated copy of the position (so the
            # caller of this method can update the real cursor position).            
            return letter_cursor_position
    


class FontAnimation:
    """
    Controls the opacity level of font sprites
    (intro of dialog text)
    """
    
    def __init__(self,
                 reset_sudden_text_finished_flag_method,
                 start_animation_type: FontAnimationShowingType = FontAnimationShowingType.SUDDEN,
                 sprite_mode=False):

        """
        Arguments:
        
        - reset_sudden_text_finished_flag_method: this method resets a bool
        flag so that blit attempts will continue for dialog letters in
        ActiveFontHandler's draw method. Reason: <no_clear> has been used,
        so there might be more text to show. We need to run the method below
        for sudden-text mode-only. If we don't call this method, any further
        text after <no_clear> won't show when in sudden-text mode.
        
        - start_animation_type: the type of font/text animation to use when
        displaying dialog text (ie: gradual letters showing or
        gradual letter fade-ins)
        
        - sprite_mode: some things don't apply when in sprite mode.
        For example: playing text audio only applies to dialogue text, not
        sprite text. Also, play reusable scripts on halt/unhalt doesn't apply
        to sprites either. So that's why we have this flag to know
        whether it's for sprites (True) or the dialog rectangle (False).
        """
        
        self.start_animation_type = start_animation_type

        self.reset_sudden_text_finished_flag_method =\
            reset_sudden_text_finished_flag_method

        self.sprite_mode = sprite_mode

        # Letter by letter fade-in speed and overall text fade-in speed
        # for dialog text (1 being the slowest, 10 being the fastest)
        self.font_text_fade_speed: int = 5        

        # For 3 animation types:
        # letter by letter, letter by letter with fade in, or complete fade in.
        self.is_start_animating = False
        
        # Set when the user clicks to make the text go faster (ie: when impatient).

        # Applies to 3 animation types:
        # letter by letter, letter by letter with fade in, and complete fade in
        self.faster_text_mode = False

        # Default the font's opacity to fully opaque
        self.current_font_fade_value = 255
        
        # Which letter index we're currently on when showing text gradually.
        self.gradual_letter_cursor_position = 0

        # This will eventually hold a list of Letter objects.
        self.letters = None
        
        # Handles letter-by-letter non-fading delay elapsing
        # and calculations.
        self.letter_delay_handler = FontLetterDelayHandler(self.sprite_mode)
        
        # Deals with the <no_clear> command
        self.no_clear_handler = NoClearHandler(self)

        # This variable is used to indicate that we should change the intro
        # animation-type back if it was temporarily changed.
        # This gets used by story_reader.py
        # when swapping a sprite out and replacing it with another sprite.
        # During the swap, if the intro text for that sprite has already
        # finished, then we temporarily change the animation type to SUDDEN
        # so that it doesn't re-animate the text that is already done from
        # the previous sprite text. Then we change it back later to whatever
        # original animation type it had (after the swap is finished), so that
        # if any additional text wants to get appended or changed later on,
        # then the original animation type will be used rather than the
        # temporary sudden-mode. This flag below gets used to tell us we need
        # to restore it from sudden-mode back to its original animation type.
        self.restore_sprite_intro_animation_type: FontAnimationShowingType | None = None

    def get_font_text_fade_speed(self,
                                 full_text_fade_in: bool = False,
                                 get_max_speed: bool = False) -> int:
        """
        Return the speed of the gradual fade-in dialog text.
        This speed applies to:
        1) Letter by letter fade-in
        2) Overall text fade-in
        
        1 is the slowest speed and 10 is the fastest speed.
        
        Each speed represents how many increments to fade in by.
        
        Arguments:
        
        - full_text_fade_in: letter-by-letter fade in speeds are different than
        full text fade in speeds because of the way they end up animating
        while fading. If we use the same fade speeds for letter-by-letter and
        full text, then full text fade ins will appear too slow. So we use this
        to know if we should fade in using a different fade speed map.
        
        - get_max_speed: if the user has clicked to proceed faster, this will
        be True, so we use this flag to know if we need to return the fastest
        speed for either full text fade in or letter by letter fade in,
        depending on the first argument, full_tax_fade_in (bool).
        """

        if full_text_fade_in:
            
            # Should we return the fastest speed possible?
            if get_max_speed:
                requested_convenient_speed = 10
            else:
                requested_convenient_speed = self.font_text_fade_speed
            
            # Default the speed to 5
            if not requested_convenient_speed:
                row_number = 5
                
            elif requested_convenient_speed > 10 or requested_convenient_speed < 1:
                row_number = 5
                
            else:
                row_number = requested_convenient_speed
                
            float_value = \
                AnimationSpeed.get_sequence_value(
                    initial_value=50,
                    increment_by=150,
                    max_convenient_row=10,
                    convenient_row_number=row_number)
            
            speed = float_value
            
        else:
            # Gradual letter fade in speed
            
            max_rows =\
                AnimationSpeed.MAX_CONVENIENT_SPEED_LETTER_BY_LETTER_FADE_IN
            
            # Should we return the fastest speed possible?
            if get_max_speed:
                requested_convenient_speed =\
                    AnimationSpeed.MAX_CONVENIENT_SPEED_LETTER_BY_LETTER_FADE_IN
            else:
                requested_convenient_speed = self.font_text_fade_speed            
            
            # Default the speed to 500
            if not requested_convenient_speed:
                requested_convenient_speed = 500
                
            elif requested_convenient_speed > max_rows \
                 or requested_convenient_speed < 1:
                
                requested_convenient_speed = 500
                
            # debug
            # requested_convenient_speed = 5
            
            float_value = \
                AnimationSpeed.get_sequence_value(
                    initial_value=25,
                    increment_by=5,
                    max_convenient_row=AnimationSpeed.MAX_CONVENIENT_SPEED_LETTER_BY_LETTER_FADE_IN,
                    convenient_row_number=requested_convenient_speed)

            speed = float_value
        
        return speed
        
    def start_show_animation(self, letters: List[Letter]):
        """
        Set a flag to indicate that the individual letter objects in the
        letters list should be gradually animated, unless the animation
        is set to 'sudden'.
        """

        # Run the on unhalt reusable script (if any) here
        if not self.sprite_mode and Passer.active_story.dialog_rectangle.reusable_on_unhalt:
            Passer.active_story.reader.spawn_new_background_reader(
                reusable_script_name=Passer.active_story.dialog_rectangle.reusable_on_unhalt)

        if self.start_animation_type == FontAnimationShowingType.SUDDEN:
            pass

        elif self.start_animation_type == FontAnimationShowingType.FADE_IN:
            self.is_start_animating = True
            self.current_font_fade_value = 0
        
        elif self.start_animation_type in (FontAnimationShowingType.GRADUAL_LETTER,
                                           FontAnimationShowingType.GRADUAL_LETTER_FADE_IN):
            self.is_start_animating = True
            
            # Should we set the letter cursor position to somewhere else?
            # In other words, not the beginning? (in the case when
            # <no_clear> is used)
            if not self.no_clear_handler.set_custom_gradual_cursor_position():
                # No custom cursor position was set.
                
                # Reset the cursor position to zero so the dialog text
                # starts from the beginning.
                if not self.sprite_mode:
                    # We only reset the letter cursor position when
                    # in dialog rectangle-mode, because with sprites, it's
                    # OK to append text to sprite objects.
                    self.gradual_letter_cursor_position = 0

        self.letters = letters
        
    def get_start_opacity_level(self) -> int:
        """
        Get the opacity level a newly added letter,
        based on the current animation type.
        """
        if self.start_animation_type in (FontAnimationShowingType.SUDDEN,):
            return 255
        elif self.start_animation_type in (FontAnimationShowingType.FADE_IN,
                                           FontAnimationShowingType.GRADUAL_LETTER,
                                           FontAnimationShowingType.GRADUAL_LETTER_FADE_IN):
            return 0
        else:
            # The user likely typed the wrong font animation name, so the
            # starting animation is currently unknown - default to 255 opacity.
            return 255

    def get_one_letter_fade_speed(self,
                                  letter_number: int,
                                  letter_opacity: float) -> float:
        """
        
        Get the given letter number's (1 to 3) current opacity level and
        if it's zero, use the base speed in the initial opacity increment.
        
        If the opacity level is not zero, don't add the base speed because
        the base speed will have already been used on the letter.
        
        The base speed is used to give the first letter a head start when
        fading in, followed by the second letter, and finally the third letter.
        
        This method is only used for gradual letter-by-letter fade-ins.
        
        Arguments:
        
        - letter_number: the letter number that is being faded in. This can
        only be 1, 2 or 3.
        
        - letter_opacity: we use this to determine if a base speed (head start)
        needs to be applied to the current letter's fade in or not. If it's
        at opacity zero, a base speed is added, based on the letter number.
        """
        
        if self.faster_text_mode:
            
            # If we're in fast-mode (the user clicked the mouse button),
            # then get the fastest fade-in speed.
            fade_in_speed =\
                self.get_font_text_fade_speed(get_max_speed=True)
            
        else:
            # Run the method that will return the text speed
            # setting as defined by the story script.
            fade_in_speed = self.get_font_text_fade_speed()
            
        if letter_number not in (1, 2, 3):
            return

        # We'll start with this opacity boost as the starting point.
        # It helps to avoid a 'catterpillar' fade-in effect. This causes 
        # the fade-in to last longer near the end of the text, making it 
        # look nicer.
        # base_start = (24, 4, 8)
        base_start = (24, 8, 4)
        
        # Initialize
        increase_opacity_by = 0
        
        # First time increasing the opacity on this letter?
        # Add a base start boost.
        if letter_opacity == 0:
            increase_opacity_by = base_start[letter_number - 1]

        increase_opacity_by = (increase_opacity_by + fade_in_speed) \
            * AnimationSpeed.delta

        return increase_opacity_by

    def make_all_letters_opaque(self):
        """
        Set the opacity of all the letters to 255.
        
        The user has clicked twice to make the dialogue text appear suddently.
        """
        letter: Letter
        for letter in self.letters:
            letter.set_opacity(255)
            
    def set_gradual_cursor_to_end(self):
        """
        Set the gradual letter-by-letter cursor position to the end, ready
        to display more text at the stopped position if needed.
        
        Purpose: if the user clicks once or twice to advance the text faster
        or instantly, respectively, and there's a <no_clear> command, it will
        instantly show the text up to <no_clear>. We then use this method to
        move the virtual cursor to the end of where it stopped at <no_clear>,
        so once the user clicks the story again to resume where it left off,
        the cursor won't be at the original location that the user clicked,
        but where the text stopped.
        
        This is also important to prevent letter-by-letter audio from playing
        from where the user clicked, causing unnecessary audio from playing for
        letters that are already visible.
        """
        self.gradual_letter_cursor_position = len(self.letters)
                
    def animate(self) -> bool | None:
        """
        Increase the opacity of the letters in the dialog text (self.letters),
        which makes a fade animation.
        
        Also, re-draw each of the letters with the new fade value.
        
        Return: True if an animation took place or None if no animation
        took place. The return value gets used by sprite object text, to know
        whether to copy the original_image variable to sprite_object.image.
        """

        # Not animating and not in sudden-mode?
        # There is nothing to animate, so return.

        # However, if we are in sudden-mode, we must run this method until 
        # the end, because the end of this method will run 
        # stop_intro_animation(), which needs to happen for the on_halt 
        # script run, even when in sudden-mode.
        if not self.is_start_animating and \
                self.start_animation_type != FontAnimationShowingType.SUDDEN:
            return

        # For debugging
        # print(datetime.now())

        # No letters to show? Return.
        # Needed if <halt> is used multiple times in a row, with no letters to show.
        if not self.letters:
            return
        
        ## For debugging
        #if self.sprite_mode:
            #print("Animating Sprite Text -", datetime.now())

        stop_intro = False

        if self.start_animation_type == FontAnimationShowingType.FADE_IN:
            
            # Has the user clicked to make the text go faster?
            if self.faster_text_mode:
                # Set the speed to full speed.
                # 2000 here refers to a fast fade-in speed (almost instant).
                fade_in_speed = 2000
            else:
                # The text is going at a normal speed.
                
                # Get the fade-in speed from the script.
                fade_in_speed = self.get_font_text_fade_speed(True)

            # self.current_font_fade_value += 15
            self.current_font_fade_value += fade_in_speed * AnimationSpeed.delta
            
            if self.current_font_fade_value > 255:
                self.current_font_fade_value = 255            

            # Initialize to -1, which means it will fade in 
            # starting from the first letter.
            fade_from_cursor_position = -1
            
            # If previous letters in the dialog text have already been
            # fully faded in, set the cursor position to the end.
            # This will be the case if <no_clear> was recently used.
            if self.no_clear_handler.number_of_letters_faded_so_far:
                fade_from_cursor_position =\
                    self.no_clear_handler.number_of_letters_faded_so_far

            # Set the new fade value for each of the letters (dialog text)
            # that are already blitted (dialog text).
            letter: Letter
            for idx, letter in enumerate(self.letters):
                
                # If we've already fully faded letters from this
                # letter position, then continue.
                # This will be the case if <no_clear> was recently used.
                if idx < fade_from_cursor_position:
                    continue
                
                letter.set_opacity(self.current_font_fade_value)

            # Has the fade-in animation finished?
            if self.current_font_fade_value >= 255:
                stop_intro = True
                
        elif self.start_animation_type == \
             FontAnimationShowingType.GRADUAL_LETTER_FADE_IN:

            def increase_opacity_three_letters():
                """
                Increase the opacity 3 letters at a time.
                The letter we're on will fade-in faster
                The second letter will fade-in a little slower
                The third letter will fade-in the slowest.
                """

                ## Get the fade-in speeds of 3 letters as a tuple.
                ## Example: (45, 35, 25)
                #gradual_fade_in_speeds: Tuple =\
                    #self.get_one_letter_fade_speed()
                
                #first_letter_speed = gradual_fade_in_speeds[0]
                #second_letter_speed = gradual_fade_in_speeds[1]
                #third_letter_speed = gradual_fade_in_speeds[2]

                letters_count = len(self.letters)

                # For knowing whether we needed to change any opacities.
                # If we don't change any opacities, it means we're finished.
                opacity_changed = False

                letter: Letter
                for idx_search_letter_1, letter in enumerate(self.letters):

                    # Don't gradually fade-in space characters 
                    # because they're invisible.
                    if letter.is_space:
                        self.letters[idx_search_letter_1].set_opacity(255)
                        continue
                    
                    # If this letter is at full opacity already,
                    # continue to the next letter.
                    if letter.opacity == 255:
                        continue

                    # Gradually fade-in the current letter we're on

                    # Set this to indicate that there might be more letters
                    # in the next frame that may need the opacity changed.

                    # In other words, we're not done fading-in the text yet.
                    opacity_changed = True

                    increase_by_first_letter =\
                        self.get_one_letter_fade_speed(
                            letter_number=1,
                            letter_opacity=self.letters[idx_search_letter_1].opacity)
                    
                    # Increase the opacity of the letter we're on.
                    self.letters[idx_search_letter_1].increase_opacity_by(increase_by_first_letter)

                    ## Increase the next letter's opacity by this much.
                    #increase_next_by = second_letter_speed

                    # Increase the opacity of the second letter a little bit
                    if idx_search_letter_1 + 1 <= letters_count - 1:
                        
                        # Keep searching for letter 2 until a non-space character
                        # is found or until the end of the letters is reached.
                        for idx_search_letter_2, letter in enumerate(self.letters[idx_search_letter_1 + 1:], start=idx_search_letter_1+1):
                                
                            # Make sure it's not a space character.
                            if self.letters[idx_search_letter_2].is_space:
                                self.letters[idx_search_letter_2].set_opacity(255)
                                continue
                            
                            # Only start increasing the opacity of letter 2
                            # if letter 1 is at least at 120 opacity
                            if self.letters[idx_search_letter_1].opacity < 120:
                                break                            
                        
                            increase_by_second_letter =\
                                self.get_one_letter_fade_speed(
                                    letter_number=2,
                                    letter_opacity=self.letters[idx_search_letter_2].opacity)                            
                            
                            self.letters[idx_search_letter_2].increase_opacity_by(increase_by_second_letter)

                            ## Increase the next letter's opacity by this much.
                            #increase_next_by = third_letter_speed
    
                            # Increase the opacity of the third letter a little bit
                            if idx_search_letter_2 + 1 <= letters_count - 1:
                                
                                # Keep searching for letter 3 until a non-space character
                                # is found or until the end of the letters is reached.
                                for idx_search_letter_3, letter in enumerate(self.letters[idx_search_letter_2 + 1:], start=idx_search_letter_2+1):
                                                            
            
                                    # Make sure it's not a space character.
                                    if self.letters[idx_search_letter_3].is_space:
                                        self.letters[idx_search_letter_3].set_opacity(255)
                                        continue
                                    
                                    # Only start increasing the opacity of letter 3
                                    # if letter 2 is at least at 120 opacity
                                    if self.letters[idx_search_letter_2].opacity < 120:
                                        break                              
                                    
                                    increase_by_third_letter =\
                                        self.get_one_letter_fade_speed(
                                            letter_number=3,
                                            letter_opacity=self.letters[idx_search_letter_3].opacity)                               
                                    
                                    self.letters[idx_search_letter_3].increase_opacity_by(increase_by_third_letter)
                                    
                                    # Dont' look for the next letter 3
                                    # in this frame. We've fade-in up to 
                                    # letter 3 already in this frame, leave 
                                    # it until the next frame.
                                    break
                                
                            # Dont' look for the next letter 2
                            # in this frame. We've fade-in up to letter 2
                            # already in this frame, leave it until the next 
                            # frame.
                            break

                    # That's enough fading-in letter 1 in this frame.
                    # We've only faded-in letter 1, because letter 2 and 3
                    # were not available or not ready to be faded-in.
                    break
                    
                # No opacities changed in the loop above?
                # That means we've finished fading in the text.
                if not opacity_changed:

                    # Reset flags so the novel knows we're ready for the
                    # next dialog text, if any.
                    nonlocal stop_intro
                    stop_intro = True

            increase_opacity_three_letters()

        elif self.start_animation_type == FontAnimationShowingType.GRADUAL_LETTER:
            """
            Non-fading letter by letter animation.
            """
            
            # For debugging the gradual letter displays at different 
            # frame rates.
            if not self.letter_delay_handler.start_time:
                self.letter_delay_handler.start_time = time.perf_counter()

            # Advance the dialogue by 1 or more letters to catch up with
            # the wait-time delay.
            new_cursor_position = self.letter_delay_handler.update(\
                delta=AnimationSpeed.delta,
                letter_cursor_position=self.gradual_letter_cursor_position,
                letters=self.letters,
                fast_mode=self.faster_text_mode)
            
            if new_cursor_position is None:
                # We shouldn't display any letters in this frame, due to
                # a punctuation delay.
                return
            elif isinstance(new_cursor_position, tuple):
                # All the letters have finished showing.
                # Record the cursor position we finished at in case we need
                # to resume where the cursor left off later in the visual 
                # novel due to a <no_clear> command.
                self.gradual_letter_cursor_position = new_cursor_position[0]
                if new_cursor_position[1]:
                    stop_intro = True
            else:
                # The letter cursor position has advanced/progressed, so
                # record the current letter position. We'll need this
                # in the next frame so we can resume the animation again.
                self.gradual_letter_cursor_position = new_cursor_position
                

            ## Don't skip this frame if:
            ## 1. There is no delay set.
            ## 2. The current letter is a space (spaces shouldn't be delayed).
            ## 3. We've delayed long enough.
            ## 4. We're in fast-text mode (the user clicked to make it go faster.)
            
            ## Don't skip any frames or we've delayed long enough?
            ## Then process the letter-by-letter animation.
            #if num_of_milliseconds_to_delay == 0 \
               #or (is_space and num_of_milliseconds_to_delay == 0) \
               #or self.letter_delay_handler.time_since_last_letter_shown >= num_of_milliseconds_to_delay \
               #or self.faster_text_mode:
                
                # Process the letter-by-letter animation, we don't need
                # to delay in this frame.

            ############
            # self.letter_delay_handler.time_since_last_letter_shown = 0
            ############
            
            ## Show the letter
            # self.letters[self.gradual_letter_cursor_position].set_opacity(255)



            # self.gradual_letter_cursor_position += 1

            ## We need to have len(self.letters) - 1 for sprite text
            ## to show properly when swapping out a sprite with 
            ## gradual text that already finished animating the gradual text.
            #if self.gradual_letter_cursor_position > len(self.letters) - 1:
                
                ## We're done showing the letters.

                ## Set the cursor position to prepare for more sprite text
                ## in case the sprite text gets changed later.
                #self.gradual_letter_cursor_position = len(self.letters) - 1

                ## We're done showing the letters.
                #stop_intro = True
                    

        elif self.start_animation_type == FontAnimationShowingType.SUDDEN:
            # The text in sudden-mode has finished being displayed, so
            # set the flag to run stop_intro_animation(), so that the
            # on_halt reusable script (if any) can run and <no_clear>
            # can be checked.
            stop_intro = True

        if stop_intro:
            self.stop_intro_animation()
            
        return True

    def stop_intro_animation(self):
        """
        Set the flag to indicate there is no longer an intro fade in
        animation for the dialog text, and reset the fade value.
        
        This method gets called when gradual or sudden text
        is finished getting displayed.
        """
        self.is_start_animating = False
        self.faster_text_mode = False

        # Now that the text intro animation has stopped,
        # check if we should skip clearing the text the next time
        # a <halt> or <halt_auto> command is used.
        self.no_clear_handler.clear_text_check()

        # self.gradual_letter_cursor_position = 0
        self.letter_delay_handler.time_since_last_letter_shown = 0
        self.current_font_fade_value = 255

        # Run a reusable script now that the dialog text is finished displaying?
        # (ie: for when <halt> is used)
        if not self.sprite_mode:
            
            # The cursor letter position only gets cleared for the dialog
            # rectangle, because we want to still be able to append text
            # to a sprite object, even after the animation is finished.
            self.gradual_letter_cursor_position = 0
            
            main_reader = Passer.active_story.reader.get_main_story_reader()

            # Run reusable_on_halt, if we're not in halt_auto mode.
            # halt_auto should not show on_halt animations, because it will 
            # proceed on its own.
            if Passer.active_story.dialog_rectangle.reusable_on_halt and \
                    not main_reader.halt_main_script_auto_mode_seconds_reach:
                Passer.active_story.reader.spawn_new_background_reader(
                    reusable_script_name=Passer.active_story.dialog_rectangle.reusable_on_halt)


class LetterProperties:
    """
    Stores properties of a single letter font spritesheet.
    An object of this class gets stored in a FontSprite object.
    
    Letter properties include:
    
    - left, right, upper, lower (tuple[int])
    The rect size of the letter. This is used to know where to crop
    the letter rect from the full size font sprite sheet.
    
    - left trim (int)
    
    - right trim (int)
    
    - kerning_rules rules (List of Tuples)
    [("abcd", -1, 0), ("efgh", -5, 2)]
    """
    def __init__(self,
                 rect_crop: Tuple[int],
                 kerning_rules: List[Tuple]):

        self.rect_crop: Tuple[int]
        self.rect_crop = rect_crop

        # [("abcd", -1, 0), ("efgh", -5, 2)]
        self.kerning_rules = kerning_rules

class FontSprite:
    """
    Keeps the font name and the full font spritesheet.
    It also keeps all the individual font sprite rects.
    """
    def __init__(self,
                 font_name: str,
                 full_font_spritesheet: pygame.Surface,
                 font_properties: Dict):
        
        """
        Arguments:
        
        - font_name: the font name (str), as it appeared in the editor.
        
        - full_font_spritesheet: the pygame surface of the full font
        spritesheet. We will slice subsurfaces from this to make letters.
        
        - font_properties: properties such as line padding, letter padding,
        the rects of all the letters, the width/height (pixels) of each letter.
        """

        self.font_name = font_name
        self.full_font_spritesheet = full_font_spritesheet

        # The width/height (pixels) of each individual letter
        self.width = font_properties.get("Width")
        self.height = font_properties.get("Height")

        self.padding_letters = font_properties.get("PaddingLetters")
        self.padding_lines = font_properties.get("PaddingLines")
        self.detect_letter_edges = font_properties.get("DetectLetterEdges")
        
        """
        Since the dict data came from JSON data, the tuples
        of letter rects (from the editor) have now been changed to lists.
        Turn them back to tuples here, for consistency between the editor
        and the player here. The editor uses tuples, the player should
        use tuples here too.
        
        In other words, convert something like this:
        "Letters": {"A": {"rect_crop": [63, 0, 126, 85], "kerning_rules": [['tes', -2, 0]]}, "B:"....}
        to:
        "Letters": {"A": {"rect_crop": (63, 0, 126, 85), "kerning_rules": [('tes', -2, 0)]}, "B:"....}
        
        rect_crop is: (left, upper, right, lower)
        """
        letters = font_properties.get("Letters")
        # letters = {key: tuple(value) for key, value in letters.items()}

        # Convert Lists to Tuples, just for consistency between the player
        # and the editor. The editor uses tuples for letter properties.
        new_letters = {}
        for letter, details in letters.items():

            # Get the crop values as a list and then convert them to a tuple
            rect_crop = tuple(details.get("rect_crop"))

            # The kerning rules will currently be a List of Lists
            # We need to convert it to a List of Tuples.
            kerning_rules = details.get("kerning_rules")
            
            new_rules = []
            
            # Convert the kerning rules to a List of Tuples.
            for rule in kerning_rules:
                new_rules.append(tuple(rule))

            letter_properties = LetterProperties(rect_crop=rect_crop,
                                                 kerning_rules=new_rules)

            new_letters[letter] = letter_properties

        # Key: letter (str)
        # Value: LetterProperties object
        self.letters = new_letters

    def get_letter_trims(self,
                         letter: str,
                         previous_letter) -> Tuple[int, int]:
        """
        Return the left trim and right trim of the specified letter.
        These trim values are the font kerning values.
        
        Arguments:
        
        - letter: the single character letter that we want to get the trim
        rules for.
        
        - previous letter: get the kerning rule for the letter when the previous
        letter is in this variable. If the value is "(Any)", it means
        the kerning rule will apply regardless of the previous letter.
        """
        letter_properties: LetterProperties
        letter_properties = self.letters.get(letter)
        
        if not letter_properties or previous_letter is None:
            return (0, 0)

        # kerning_rules will look like this:
        # [('tes', -2, 0), ('(Any)', 1, 0), ('a', -2, 0)]
        # or
        # ('(Any)', 1, 0)

        left_trim = 0
        right_trim = 0
        
        for rule in letter_properties.kerning_rules:
            previous_letters = rule[0]

            if previous_letters == "(Any)":
                left_trim = rule[1]
                right_trim = rule[2]                
            else:
                for prev_letter in previous_letters:
                    if prev_letter == previous_letter:
                        left_trim = rule[1]
                        right_trim = rule[2]                        
                        break

        return (left_trim, right_trim)

    def get_letter(self,
                   letter: str,
                   dialog_surface: pygame.Surface = None) -> pygame.Surface:
        """
        Slice a letter from the full font spritesheet and return it
        as a subsurface of the given dialog surface.
        
        Arguments:
        
        - letter: the single character letter that we want the font sprite for.
        
        - dialog_surface: the surface where the font spritesheets will appear
        on. The letter that gets returned in this method will have
        dialog_surface as its parent.
        
        Return: letter subsurface. The parent of the subsurface will be the
        full size font spritesheet surface.
        """

        # Get the letter's properties
        letter_details: LetterProperties
        letter_details = self.letters.get(letter)
        
        if not letter_details:
            return        

        # Get the rect of the requested letter.
        # The rect here is not a normal pygame rect. It's a tuple like this:
        # (left, top, right, lower)
        rect_letter = letter_details.rect_crop


        left, top, right, lower = rect_letter

        # The .subsurface method will need the width and height of the
        # area, not the right and lower coordinates.
        width = right - left
        height = lower - top

        # The rect area that we want to crop to get the letter.
        letter_rect = pygame.Rect(left, top, width, height)

        # Get the subsurface of the requested letter.
        try:
            sub_surface_letter = \
                self.full_font_spritesheet.subsurface(letter_rect).convert_alpha()
        except ValueError:
            logging.warning(f"Could not get letter {letter} - beyond font spritesheet boundries.")
            return

        return sub_surface_letter

class ActiveFontHandler:
    """
    Handles animating and showing the current text dialog.
    Give it some text characters and then it'll handle adding them to the
    screen based on the current font rules.
    
    The rules of the current dialog text are in this object too, such as
    whether fading-in is enabled, sudden-mode, or regular gradual mode.
    """

    def __init__(self, story, sprite_object: SpriteObject = None):

        # A value in sprite_object means we will draw text on the
        # given sprite object, which is either an object, dialog sprite, 
        # or character - not on a dialog rectangle.
        self.sprite_object = sprite_object

        # So we can access the loaded fonts
        # and the active dialog rectangle.
        self.story: Passer.active_story
        self.story = story

        # If the intro text is in sudden-mode,
        # we need to set this flag to True after the text
        # has been blitted, so that the dialog rectangle
        # doesn't continue to be re-drawn for no reason.
        self.sudden_text_drawn_already = False

        self.next_letter_x_position = 0
        self.next_letter_y_position = 0
        
        # Used for keeping the dialog text on one line
        # even when the dialog text spans multiple lines in the script.
        self.next_letter_x_position_continue = None
        self.next_letter_y_position_continue = None
        
        # Used if temporarily adjusting Y coordinate of dialog text
        # using the <continue> command.
        self.adjusted_y = 0

        self.default_x_position = 0
        self.default_y_position = 0

        # List of Letter class objects.
        self.letters_to_blit = []

        # This will be a FontSprite object.
        self.current_font: FontSprite
        self.current_font = None


        # Controls the opacity level of font sprites 
        # (intro/outro of dialog text)
        self.font_animation = \
            FontAnimation(reset_sudden_text_finished_flag_method=self.reset_sudden_text_finished_flag,
                          start_animation_type=FontAnimationShowingType.FADE_IN,
                          sprite_mode=self.sprite_object is not None)

    def is_sudden_mode_text_pending(self) -> bool:
        """
        Return whether the text intro animation is in sudden-mode
        and hasn't blitting the text yet.
        """
        return self.font_animation.start_animation_type == FontAnimationShowingType.SUDDEN \
            and not self.sudden_text_drawn_already
        
    def reset_sudden_text_finished_flag(self):
        """
        Reset flag which indicates that all the text in sudden-mode
        has already been blitted (to prevent repeated letter blittings
        in sudden-mode because there is no gradual animation for sudden-mode).
        """
        self.sudden_text_drawn_already = False


    def _get_letter_right_edge(self,
                              letter_surface: pygame.Surface,
                              rect_to_check: pygame.Rect) -> int | None:
        """
        Return the last (right-most) X position where there is
        non-transparent pixel data.
        
        Purpose: to know where a letter ends so we can determine the position
        for the next letter.
        
        Arguments:
        
        - letter_surface: the surface that contains a single letter.
        We need to find out the last X position of where there is
        non-transparent pixel data.
        
        - rect_to_check: the rect of the letter's surface. We use this
        to know the width and height of the surface, so we know what area
        to check for non-transparent pixels.
        """

        # Start from the right-side to find out where the last
        # non-transparent pixel data is.

        # Loop the X axis going from right to left.
        for x in range(rect_to_check.width - 1, 1, -1):

            # Go down the letter surface in the current X position,
            # starting at the top and looping down.
            for y in range(1, rect_to_check.height):

                r, g, b, a = letter_surface.get_at((x, y))

                if a > 0:
                    logging.info(f"Last X non-transparent letter pixel found at {x}")
                    # print(f"Pixel Found at {x, y}")
                    
                    # We're only interested in the X value.
                    return x
                
    def _get_letter_left_edge(self,
                              letter_surface: pygame.Surface,
                              rect_to_check: pygame.Rect) -> int | None:
        """
        Return the first (left-most) X position where there is
        non-transparent pixel data.
        
        Purpose: to know where the letter pixels start so we can determine
        the position for the current letter.
        
        Arguments:
        
        - letter_surface: the surface that contains a single letter.
        We need to find out the first X position of where there is
        non-transparent pixel data.
        
        - rect_to_check: the rect of the letter's surface. We use this
        to know the width and height of the surface, so we know what area
        to check for non-transparent pixels.
        """

        # Start from the left-side to find out where the first
        # non-transparent pixel data is.

        # Loop the X axis going from left to right.
        for x in range(1, rect_to_check.width - 1):

            # Go down the letter surface in the current X position,
            # starting at the top and looping down.
            for y in range(1, rect_to_check.height):

                r, g, b, a = letter_surface.get_at((x, y))

                if a > 0:
                    logging.info(f"First X non-transparent letter pixel found at {x}")
                    # print(f"Pixel Found at {x, y}")
                    
                    # We're only interested in the X value.
                    return x

    def add_letter(self,
                   letter_subsurface: pygame.Surface,
                   is_space: bool,
                   previous_letter: str,
                   left_trim: int = 0,
                   right_trim: int = 0):
        """
        Add an individual subsurface letter to the list of letters
        that should be displayed.
        
        Also, calculate where the next letter, after this one,
        should be positioned.
        
        Arguments:
        
        - letter_subsurface: the surface that has the letter image.
        
        - is_space: the Letter class needs to know if it's a space character
        or not because space characters don't have a fade effect in gradual
        text mode, no text delay, and they don't have a text sound.
        
        - previous_letter: the str letter that was blitted prior to this one.
        We need this to check whether we should apply a delay to this new letter
        due to <font_text_delay_punc>. For example, if <font_text_delay_punc>
        gets used with "." and now we're on the letter *after* the ".",
        there might need to be a delay.
        
        - left_trim: used for positioning the current letter that is about
        to be added. It's used for nudging its position. A negative value
        will move it more to the left, a positive value will move it more
        to the right, and a value of 0 (zero) won't nudge the letter
        that we're about to add.
        
        - right_trim: used for positioning the next letter (the letter after
        the one we're going to be adding now). A negative value will move the
        next letter more the left, a positive value will move the next letter
        more to the right, and a value of 0 (zero) won't nudge the next letter.
        """

        rect = letter_subsurface.get_rect()
        
        # Get the rect without any transparent parts.
        rect_opague = letter_subsurface.get_bounding_rect(min_alpha=1)
        
        if self.current_font.detect_letter_edges:

            if is_space:
                pixel_edge_left = 0
                pixel_edge_right = rect.width
            else:
                # Record the last non-transparent pixel on the right
                # of the letter.
                pixel_edge_right = rect_opague.right

                #pixel_edge_right =\
                    #self._get_letter_right_edge(letter_surface=letter_subsurface,
                                                #rect_to_check=rect)

                # Record the first non-transparent pixel on the left
                # of the letter
                pixel_edge_left = rect_opague.left

                #pixel_edge_left =\
                    #self._get_letter_left_edge(letter_surface=letter_subsurface,
                                               #rect_to_check=rect)
            
        # First letter being added? Default the X and Y
        # positions to the default.
        if not self.letters_to_blit:
            self.next_letter_x_position = self.default_x_position
            self.next_letter_y_position = self.default_y_position


        # Position the new letter to where a non-transparent pixel starts?
        if self.current_font.detect_letter_edges:

            # Position the new letter to show starting at
            # where a non-transparent pixel starts in the new letter.
            self.next_letter_x_position -= pixel_edge_left

        # Position the X and Y of the letter that is about to be added
        # to the blit list.
        rect.x = self.next_letter_x_position
        rect.y = self.next_letter_y_position

        # Add left trim (if any) to the letter that is about to be added.
        # This is used for positioning the letter a little to the left (negative int)
        # or a little to the right (positive int). In other words, it's used for letter nudging.
        rect.x += left_trim
        
        # Get the starting opacity level based on the
        # font animation for the dialog text.
        opacity: int = self.font_animation.get_start_opacity_level()

        letter = Letter(rect=rect,
                        surface=letter_subsurface,
                        opacity=opacity,
                        is_space=is_space,
                        previous_letter=previous_letter)
        
        self.letters_to_blit.append(letter)

        # Calculate where the next letter should be positioned.
        if not self.current_font.detect_letter_edges:
            # Position the next letter to show at the end of the current surface,
            # without taking the letter's non-transparent pixel data into consideration.
            self.next_letter_x_position += rect.width + self.current_font.padding_letters
        else:
            # Position the next letter, taking the current letter's 
            # last non-transparent pixel into consideration (pixel_edge_right).
            self.next_letter_x_position += pixel_edge_right + self.current_font.padding_letters
            
        # Add right trim padding so the next letter starts
        # a bit to the left (negative int)
        # or a bit to the right (positive int)
        # In other words, this is used for nudging the position of the next letter.
        self.next_letter_x_position += right_trim
        
    def process_text(self, line_text: str):
        """
        Get the letter sprites for the letters in the given string
        and add them to a list so they can be blitted later,
        all while following the font kerning rules.
        
        Arguments:
        
        - line_text: the string to blit
        """
        
        # Make sure a font has been defined; otherwise we can't
        # show any text.
        if not self.current_font:
            if self.sprite_object:
                subject_name = self.sprite_object.general_alias
            else:
                subject_name = "dialog rectangle"
            raise ValueError(f"No font defined for '{subject_name}'")

        # Used for letter kerning
        previous_letter = None

        # Read the line we've been given, line by line.
        for letter in self.read_next_letter(line_text=line_text):

            # print("Read letter:", letter)
            logging.info(f"Read letter: {letter}")

            # Now get the letter surface (the cropped image of the letter)
            letter_surface =\
                self.current_font.get_letter(letter=letter)

            # Get the amount of padding/kerning to use for the letter
            # that we're going to blit soon, based on the kerning rules
            # and the previous letter.
            left_trim, right_trim =\
                self.current_font.get_letter_trims(letter=letter,
                                                   previous_letter=previous_letter)

            # Was the letter sprite found?
            if letter_surface:
                # Yes, it was found. Add it to the list of letters that
                # should be displayed in the dialog rectangle.
                self.add_letter(letter_subsurface=letter_surface,
                                is_space=(letter == " "),
                                previous_letter=previous_letter,
                                left_trim=left_trim,
                                right_trim=right_trim)
                
                # Keep track of the previous letter for kerning purposes.
                previous_letter = letter                
                
        
        # Keep track of where the end of the line is for the X position.
        # Used for restoring the X position when <continue> is reached.
        self.next_letter_x_position_continue = \
            self.next_letter_x_position

        # We finished reading the entire line, so position the text cursor
        # on the next line, in case there is more text to read on the next line.
        self.next_letter_x_position = self.default_x_position

        # Keep track of where the end of the line is for the Y position.
        # Used for restoring the X position when <continue> is reached.
        self.next_letter_y_position_continue = self.next_letter_y_position

        # Set the Y 'cursor' to the next line.
        self.next_letter_y_position += \
            self.current_font.height + \
            self.current_font.padding_lines
        
        # Is the Y coordinate of the dialog text temporarily adjusted
        # after using the <continue> command? Reset it back to without its adjustment.
        if self.adjusted_y:
            self.next_letter_y_position -= self.adjusted_y
            self.adjusted_y = 0
        

    def read_next_letter(self, line_text):
        """
        The story doesn't currently contain a command to run, so
        the read_story() method wants us to show the text now as dialog text.
                
        While text is being displayed, the main non-background story reader
        should not be allowed to progress. Only background story readers
        should be allowed to progress. But background story readers should
        not be allowed to display dialog text, because imagine what would
        happen if 15 background story readers tried to show dialog text.
        """

        # At this point, we're not reading a command, because the method,
        # read_story(), called our method here (read_dialog_text()), since
        # there are no commands (so far) to parse.

        # Loop through each individual letter
        for letter in line_text:
            yield letter

    def clear_letters(self):
        """
        Clear the list that's used for blitting letters.
        """
        if self.letters_to_blit:
            
            # Don't clear the text? (because of <no_clear>)
            if self.font_animation.no_clear_handler.pass_clearing_next_halt:
                # Don't clear the text.
                # and record where the last gradual letter cursor position is
                # so we can resume the next letter from there.
                
                # Reset <no_clear> flag, because <no_clear> can
                # only be used once each time.
                self.font_animation.no_clear_handler.\
                    pass_clearing_next_halt = False

                # Don't clear the text in this run, stop here.
                return
            
            self.letters_to_blit.clear()

            # Reset flag which indicates that all the text in sudden-mode
            # has already been blitted (to prevent repeated letter blittings in sudden-mode
            # because there is no gradual animation for sudden-mode).
            self.reset_sudden_text_finished_flag()

    def draw(self):
        """
        Blit the letters to the current dialog rectangle's surface
        or to the sprite's surface, in the case of sprite text.
        """

        # No letters to blit for? return
        if not self.letters_to_blit:
            return

        # We are either animating the text gradually (fade or gradual letter)
        # or the text-mode is in sudden-mode and the text is ready to be blitted.

        # Redraw the rectangle so all the letters get cleared
        # and then animate the new text animations (fade values).
        if self.font_animation.is_start_animating \
                or self.is_sudden_mode_text_pending():

            # We're animating the text or there is text already
            # waiting to be fully displayed, if it's in sudden-mode.

            # Drawing text sprites in the dialog rectangle?
            if not self.sprite_object:
                # Yes, we're drawing text sprites in a dialog rectangle.

                # Re-draw the dialog rectangle so the text gets cleared 
                # from before and re-draw the font text again.
                self.story.dialog_rectangle.redraw_rectangle()
    
                # Get the dialog surface so we can blit letters onto it.
                surface_to_draw_on = self.story.dialog_rectangle.surface
                
            else:
                # Not a dialog rectangle.
                # We're about to draw text on a sprite.
                
                # Reset the original image with the 'actual' original image
                # that doesn't contain any text drawn on it.
                self.sprite_object.original_image = \
                    self.sprite_object.get_original_image_without_text()

                # We're going to draw text on the sprite's surface.
                surface_to_draw_on = self.sprite_object.original_image

                # surface_to_draw_on = self.sprite_object.image
            
            # Animate any gradual text animations (gradual letter fades or 
            # letter by letter).
            # Get a value indicating whether an animation took place or not.
            animated_this_frame = self.font_animation.animate()            

            # Used inside the loop below; meant for sudden-mode
            blitted_a_letter = False

            # Blit letters onto the newly (re)drawn dialog rectangle
            # or onto the sprite object.
            letter: Letter
            for letter in self.letters_to_blit:
                surface_to_draw_on.blit(letter.surface,
                                        letter.rect)

                # Meant for sudden-mode, used later in this method.
                blitted_a_letter = True

            """
            If we blitted letter(s) and the font mode is sudden-mode,
            that means we blitted all the text for this current letter-set,
            In a case like that, set 'sudden_text_drawn_already' to True
            so we don't draw keep re-drawing the dialog rectangle for no reason
            in the next call to this method.
            """
            if blitted_a_letter:
                
                # Are we in gradual letter-by-letter font animation-mode
                # and in fast-mode?
                if self.font_animation.start_animation_type == \
                   FontAnimationShowingType.GRADUAL_LETTER \
                   and self.font_animation.faster_text_mode:
                    
                    # We're in gradual letter-by-letter mode
                    # and in fast-mode. But at this point, we don't know
                    # if it's one-click fast-mode or two-click fast-mode
                    # where it shows the text instantly. We're about to
                    # find out below.
                    
                    """
                    The user has clicked to make the text go faster.
                    They might have also clicked twice to make the text
                    advance instantly. If the user has clicked twice, all
                    the letters will be opaque and if that's the case, we should
                    now stop animating the letters so they don't get re-drawn
                    next frame, because all the letters are now fully opaque.
                    
                    We have to do this check here, after the animate() method,
                    because if we do it before the animate() method above, the
                    last frame, before the text is displayed in full, won't
                    show the full opaque text - it will show opaque letters up
                    to where the user clicked twice, and the rest of the
                    letters will not be shown. So having this check here after
                    the animte() method has given it a chance to blit one last
                    time, showing all the now-opaque letters.
                    """
                    
                    # Go through all the letters that should be displayed.
                    letter: Letter
                    for letter in self.font_animation.letters:
                        
                        # Did we find a letter that hasn't been fully made
                        # opaque yet?
                        if letter.opacity < 255:
                            # This letter hasn't been fully animated yet.
                            # That means the user did not click twice to 
                            # advance the text instantly, so we should still 
                            # animate the font intro as usual.
                            break
                    else:
                        """
                        We finished going through all the letters.
                        This means *all* the letters are fully opaque.
                        This also means the user has clicked twice to
                        advance the text instantly, so stop the intro
                        animation so we don't try to animate it on the
                        next frame.
                        """
                        self.font_animation.stop_intro_animation()
                        
                    
                # If we're drawing text on a sprite object, then the text
                # will have been blitted on sprite_object.original_image
                # So copy that surface to self.image, so it gets shown
                # on the screen.
                #if self.sprite_object:
                    #print("Blitted!", datetime.now())

                    #if self.sprite_object.is_fade_needed():
                        #self.sprite_object._fade_sprite(skip_copy_original_image=True)

                    # self.sprite_object._apply_still_effects()

                """
                Restore the font animation type, if it was temporarily
                ------------------------------------------------------
                If the sprite text animation-type for this sprite was
                temporarily changed earlier (to SUDDEN mode), due to a sprite
                swap, then restore the animation type back to its original
                text animation type.
                We'll know to restore the animation type, if the variable,
                restore_sprite_intro_animation_type,
                contains a value or not.
                """
                if self.font_animation.restore_sprite_intro_animation_type:
                    # Yes, restore the sprite text animation type.

                    self.font_animation.start_animation_type \
                        = self.font_animation. \
                        restore_sprite_intro_animation_type

                    # Reset the variable which is used for restoring
                    # the sprite text animation type.
                    self.font_animation. \
                        restore_sprite_intro_animation_type = None

                if self.font_animation.start_animation_type == FontAnimationShowingType.SUDDEN:
                    # We've blitted sudden-mode text
                    
                    # Set the flag below so we don't redraw the dialog 
                    # rectangle again in the next frame nor attempt to redraw 
                    # the text on a sprite object.
                    self.sudden_text_drawn_already = True

    def set_active_font(self, font_name):
        """
        Set the font that will be used for displaying the next letter.
        
        Arguments:
        
        - font_name: (str) the name of the font, as displayed in the editor.
        """
        if not font_name:
            return

        font_sprite: FontSprite = self.story.font_sprite_sheets.get(font_name)

        if not font_sprite:
            return

        # This will be the FontSprite object that will be used
        # for the next letter that gets displayed.
        self.current_font = font_sprite
        
        
        
class NoClearHandler:
    """
    Keeps track of the last position of dialog text when <no_clear> is used.
    
    Purpose: when <no_clear> is used, we need to know how many letters
    have faded-in so far (in the case of gradual letter fade-ins and
    overall letter fade-ins) so after the next <halt> or <halt_auto>, we
    don't end up fading in the dialog text that is already faded-in.
    
    The same applies for gradual letter text (non-fade). We keep track
    of the last cursor index of where the last blitted letter is so that
    we don't blit from the beginning after the next <halt> or <halt_auto>.
    """
    def __init__(self, font_animation: FontAnimation):
        
        # A reference to the FontAnimation object
        # We'll need this to get the text animation type.
        self.font_animation = font_animation
        
        # Used with gradual text animation so we can resume 
        # from the last cursor position when <no_clear> is used.
        self.gradual_last_index = None
        
        # Used for all-letter fade-ins and gradual fade-ins.
        self.number_of_letters_faded_so_far = None
    
        # Used for not clearing the dialog text on the screen
        # for the next halt or halt_auto.
        self.pass_clearing_next_halt = False
        
    def get_start_animation_type(self) -> FontAnimationShowingType:
        """
        Return the animation type for dialog intro text.
        """
        return self.font_animation.start_animation_type

    def set_custom_gradual_cursor_position(self) -> bool:
        """
        Set a manual gradual-text cursor position if <no_clear>
        was used recently.
        
        This method only applies to gradual-letter non-fade
        and also gradual-letter fade-in.
        
        We'll know if <no_clear> was used recently if there's a value
        in self.gradual_last_index
        
        After we set the custom cursor position, reset the record
        of it (so it's ready until another <no_clear> is used in the future.)
        
        Return True if a manual position has been set.
        
        Return None if no manual position was set (ie: <no_clear>
        was not used recently).
        """
        
        # This method only applies to gradual-letter non-fade
        # and also gradual-letter fade-in.        
        if self.get_start_animation_type() not in\
           (FontAnimationShowingType.GRADUAL_LETTER,
            FontAnimationShowingType.GRADUAL_LETTER_FADE_IN):
            
            raise ValueError("This method only applies to gradual-letter "\
                             "non-fade and gradual-letter fade-in start "\
                             "animation types.")
            
        
        # Set a custom gradual-letter cursor position?
        if self.gradual_last_index:
            # Yes. This means <no_clear> was used recently.
            
            # Set the gradual-letter cursor position
            # so that it doesn't start from the beginning.
            self.font_animation.gradual_letter_cursor_position =\
                self.gradual_last_index
            
            # Reset (until another <no_clear> is used in the future)
            self.gradual_last_index = 0
            
            # So the caller knows a custom position was set.
            return True

    def clear_text_check(self):
        """
        Check if we should skip clearing the text the next time
        a <halt> or <halt_auto> command is used.
        
        This will be the case if <no_clear> was used recently.
        
        If so:
        Record how far dialog text has been shown so far
        so the next time the dialog is unhalted, it will show
        the dialog text starting from the last blitted position.
        
        For gradual letter or gradual letter fade:
        - Record where the letter cursor position is, if the font animation
        is set to gradual or gradual fade.
        
        For all-letter fade in:
        - Record how many letters have been faded-in so far.
        
        
        If we're not passing on clearing the dialog text,
        then make sure <no_clear> related variables are reset. 
        """
        
        # Now that the text intro animation has stopped, should we
        # pass on clearing the text during the next <halt> or <halt_auto>?
        if self.pass_clearing_next_halt:
            
            # Don't clear the text on <halt> or <halt_auto>
            # because <no_clear> was just used.
            
            # Record the current dialog text position so
            # the next dialog text will blit from where the last text blit
            # left off.
            if self.get_start_animation_type() in \
               (FontAnimationShowingType.GRADUAL_LETTER, ):
                
                """
                Move the virtual cursor position to the end, in case
                more text gets added at the stopped position.
                This is here because the text has been made opaque up 
                to <no_clear>. If the user clicks again, it will
                resume from where it stopped at <no_clear>.
                Without this method below, it will resume animating letters
                from where the text position was at the time
                the user first clicked (clicked once or twice) to advance the
                text faster or advance the text instantly.
                With the method below, it will resume at the end of all the
                opaque letters.
                """                
                self.font_animation.set_gradual_cursor_to_end()
                
                # Record the current cursor index of the gradual letter.
                if self.font_animation.gradual_letter_cursor_position:
                    self.gradual_last_index =\
                        self.font_animation.gradual_letter_cursor_position
                
            elif self.get_start_animation_type() in \
                 (FontAnimationShowingType.GRADUAL_LETTER_FADE_IN,
                  FontAnimationShowingType.FADE_IN):
                
                # Record how many letters we have faded so far
                # so that on the next block of letters, we only fade in
                # the letters that haven't been faded-in yet.
                self.number_of_letters_faded_so_far =\
                    len(self.font_animation.letters)

            elif self.get_start_animation_type() == FontAnimationShowingType.SUDDEN:
                # This resets a bool flag so that blit attempts will continue for dialog letters
                # in ActiveFontHandler's draw method.
                # Reason: <no_clear> has been used, so there might be more text to show.

                # We need to run the method below for sudden-text mode-only,
                # specifically for ActiveFontHandler's draw method.

                # If we don't call this method, any further text after <no_clear> won't show
                # when in sudden-text mode.
                self.font_animation.reset_sudden_text_finished_flag_method()

        else:
            # Make sure the <no_clear> related variables
            # are reset, because <no_clear> has not been used recently.
            self.number_of_letters_faded_so_far = None
            self.gradual_last_index = None
