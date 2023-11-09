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
import active_story
import logging
import audio_player
import story_reader
from typing import Dict, List, Tuple
from enum import Enum, auto
from shared_components import Passer
from datetime import datetime


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

    
class FontAnimation:
    """
    Controls the opacity level of font sprites
    (intro of dialog text)
    """
    def __init__(self,
                 reset_sudden_text_finished_flag_method,
                 start_animation_type: FontAnimationShowingType = FontAnimationShowingType.SUDDEN):

        """
        Arguments:
        
        - start_animation_type: the type of font/text animation to use when displaying
        dialog text (ie: gradual letters showing or gradual letter fade-ins)
        """
        
        self.start_animation_type = start_animation_type

        self.reset_sudden_text_finished_flag_method = reset_sudden_text_finished_flag_method


        # Key: (str) letter
        # Value: (int) number of frames to delay
        # Used for gradual letter text displays (not gradual letter fading)
        self.letter_delays = {}        

        # The number of frames to skip when applying gradual text animation.
        # For letter-by-letter animation only (not *any* fade-ins.)
        self.font_text_delay: int = 0

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
        
        # For keeping track of the number of frames
        # that have been skipped so far for gradual text display animation.
        self.gradual_delay_counter = 0

        # This will eventually hold a list of Letter objects.
        self.letters = None
        
        # Deals with the <no_clear> command
        self.no_clear_handler = NoClearHandler(self)
        

    def set_letter_delay(self, letter: str, delay_frames: int):
        """
        Set a delay for a specific letter.
        
        For example, if "." is provided as the letter with a delay_frame
        value of 30, then any period that gets shown will pause for 1 second
        before showing the next letter.
        
        Used with <font_text_delay_punc>
        """

        if not letter:
            return
        elif len(letter) > 1:
            return
        elif not isinstance(letter, str):
            return
        elif not isinstance(delay_frames, int):
            return
        elif delay_frames < 0:
            return
        
        # If the value is 0 (zero), remove the delay rule if the letter exists.
        if delay_frames == 0:
            if letter in self.letter_delays:
                del self.letter_delays[letter]
        else:
            
            # Add or update letter delay.
            self.letter_delays[letter] = delay_frames

    def get_font_after_letter_delay(self, letter: str) -> int:
        """
        Get the number of frames to delay after a specific letter is shown.
    
        A letter's delay is set using the command: <font_text_delay_punc>
        """
        delay_frames =\
            self.letter_delays.get(letter, 0)
        
        return delay_frames

    def get_font_text_fade_speed(self, full_text_fade_in: bool = False) -> int:
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
        """

        letter_by_letter_speed_mapping =\
            {1: 0.50,
             2: 1,
             3: 2.50,
             4: 3.50,
             5: 5,
             6: 5.50,
             7: 6,
             8: 6.50,
             9: 7,
             10: 8}

        full_text_speed_mapping =\
            {1: 1.50,
             2: 3,
             3: 5.50,
             4: 8.50,
             5: 10,
             6: 12.50,
             7: 14,
             8: 16.50,
             9: 18,
             10: 20}

        if full_text_fade_in:
            # Default the speed to 5
            speed = full_text_speed_mapping.get(self.font_text_fade_speed, 5)
        else:
            # Default the speed to 5
            speed = letter_by_letter_speed_mapping.get(self.font_text_fade_speed, 5)
        
        return speed

    def get_font_text_delay(self) -> int:
        """
        Return the number of frames to skip when animating gradual
        dialog text.
        For example, if the value is 2, it means to run the text
        animation after skipping 2 frames. If the value is zero, it means
        to run the text animation on every frame.
        """
        return self.font_text_delay
        
    def start_show_animation(self, letters: List[Letter]):
        """
        Set a flag to indicate that the individual letter objects in the
        letters list should be gradually animated, unless the animation
        is set to 'sudden'.
        """

        # Run the on unhalt reusable script (if any) here
        if Passer.active_story.dialog_rectangle.reusable_on_unhalt:
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
                self.gradual_letter_cursor_position = 0

        self.letters = letters
        
    def get_start_opacity_level(self) -> int:
        """
        Get the opacity level a newly added letter should be at
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

    def get_text_fade_speed(self) -> Tuple:
        """
        Return the speed of the gradual letter fade-in animation
        for 3 letters, as a tuple.
        
        Why 3? There letter-by-letter fade-in animation occurs for 3 letters
        at the same time. The first letter gets faded-in the fastest,
        the second letter gets faded-in medium, the third letter gets faded-in
        the slowest.
        
        Example return value:
        
        (25, 15, 5)
        Which means:
        fade-in letter 1 by 25 opacity
        fade-in letter 2 by 15 opacity
        fade-in letter 3 by 5 opacity
        """
        
        if self.faster_text_mode:
            # If we're in fast-mode (the user clicked the mouse button),
            # then default to a speed of 10.
            fade_in_speed = 10           
        else:
            # Run the method that will return the text speed
            # setting as defined by the story script.
            # Example value (int): 1 to 10 (1 being the slowest, 10 being the fastest)
            fade_in_speed = self.get_font_text_fade_speed()
            

        # We'll start with this speed as the starting point
        base_start = (15, 5, -5)

        # We're going to increment the opacity of the letters by this much.
        increment_base_speed_by = 10 * fade_in_speed
        
        return (base_start[0] + increment_base_speed_by,
                base_start[1] + increment_base_speed_by,
                base_start[2] + increment_base_speed_by)

    def animate(self):
        """
        Increase the opacity of the letters in the dialog text (self.letters),
        which makes a fade animation.
        
        Also, re-draw each of the letters with the new fade value.
        """

        # Not animating and not in sudden-mode? There is nothing to animate, so return.

        # However, if we are in sudden-mode, we must run this method until the end, because
        # the end of this method will run stop_intro_animation(), which needs to happen for
        # the on_halt script run, even when in sudden-mode.
        if not self.is_start_animating and \
                self.start_animation_type != FontAnimationShowingType.SUDDEN:
            return

        # For debugging
        # print(datetime.now())

        # No letters to show? Return.
        # Needed if <halt> is used multiple times in a row, with no letters to show.
        if not self.letters:
            return

        stop_intro = False

        if self.start_animation_type == FontAnimationShowingType.FADE_IN:
            
            # Has the user clicked to make the text go faster?
            if self.faster_text_mode:
                # Set the speed to full speed.
                # 20 here refers to the opacity increment per frame.
                fade_in_speed = 20
            else:
                # The text is going at a normal speed.
                
                # Get the fade-in speed from the script.
                fade_in_speed = self.get_font_text_fade_speed(True)

            # self.current_font_fade_value += 15
            self.current_font_fade_value += fade_in_speed
            
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
                
        elif self.start_animation_type == FontAnimationShowingType.GRADUAL_LETTER_FADE_IN:

            def increase_opacity_three_letters():
                """
                Increase the opacity 3 letters at a time.
                The letter we're on will fade-in faster
                The second letter will fade-in a little slower
                The third letter will fade-in the slowest.
                """

                # Get the fade-in speeds of 3 letters as a tuple.
                # Example: (45, 35, 25)
                gradual_fade_in_speeds: Tuple =\
                    self.get_text_fade_speed()
                
                first_letter_speed = gradual_fade_in_speeds[0]
                second_letter_speed = gradual_fade_in_speeds[1]
                third_letter_speed = gradual_fade_in_speeds[2]

                letters_count = len(self.letters)

                # For knowing whether we needed to change any opacities.
                # If we don't change any opacities, it means we're finished.
                opacity_changed = False

                letter: Letter
                for idx, letter in enumerate(self.letters):

                    # Don't gradually fade-in space characters 
                    # because they're invisible.
                    if letter.is_space:
                        self.letters[idx].set_opacity(255)
                        continue
                    
                    # If this letter is at full opacity already,
                    # continue to the next letter.
                    if letter.opacity == 255:
                        continue

                    # Gradually fade-in the current letter we're on

                    # Set this to indicate that there might be more letters
                    # in the next frame that may need the opacity changed.

                    # In other words, we're not done fading in the text yet.
                    opacity_changed = True

                    # Increase the opacity of the letter we're on.
                    self.letters[idx].increase_opacity_by(first_letter_speed)

                    # Increase the next letter's opacity by this much.
                    increase_next_by = second_letter_speed

                    # Increase the opacity of the second letter a little bit
                    if idx + 1 <= letters_count - 1:

                        # Make sure it's not a space character.
                        if not self.letters[idx + 1].is_space:
                            self.letters[idx + 1].increase_opacity_by(increase_next_by)

                            # Increase the next letter's opacity by this much.
                            increase_next_by = third_letter_speed

                    # Increase the opacity of the third letter a little bit
                    if idx + 2 <= letters_count - 1:

                        # Make sure it's not a space character.
                        if not self.letters[idx + 2].is_space:
                            self.letters[idx + 2].increase_opacity_by(increase_next_by)

                    # That's enough fading-in for this frame.
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

            # Was the previous letter a letter that should cause this new letter
            # to delay for X number of frames? (ie: if the previous letter was a ".")
            num_of_frames_to_skip =\
                self.get_font_after_letter_delay(
                    self.letters[self.gradual_letter_cursor_position].previous_letter)

            # No delay set based on the previous letter?
            # Check if there's a global delay setting.
            if num_of_frames_to_skip == 0:

                # Get the number of frames we should skip (delay)
                # when showing a letter-by-letter dialog text animation.
                num_of_frames_to_skip = self.get_font_text_delay()
                
            is_space =\
                    self.letters[self.gradual_letter_cursor_position].is_space

            # Don't skip this frame if:
            # 1. There is no delay set.
            # 2. The current letter is a space (spaces shouldn't be delayed).
            # 3. We've delayed long enough.
            # 4. We're in fast-text mode (the user clicked to make it go faster.)
            
            # Don't skip any frames or we've delayed long enough?
            # Then process the letter-by-letter animation.
            if num_of_frames_to_skip == 0 \
               or (is_space and num_of_frames_to_skip == 0) \
               or self.gradual_delay_counter > num_of_frames_to_skip \
               or self.faster_text_mode:
                
                # Process the letter-by-letter animation, we don't need
                # to delay in this frame.

                self.gradual_delay_counter = 0

                # Show the letter
                self.letters[self.gradual_letter_cursor_position].set_opacity(255)

                # Play a sound for this letter, if configured to do so.
                # Don't play a sound for a space ' ' character.
                if not is_space:
                    Passer.active_story.audio_player.play_audio(
                        audio_name=Passer.active_story.dialog_rectangle.text_sound_name,
                        audio_channel=audio_player.AudioChannel.TEXT)

                self.gradual_letter_cursor_position += 1

                if self.gradual_letter_cursor_position >= len(self.letters):
                    stop_intro = True
                    
            else:
                self.gradual_delay_counter += 1

        elif self.start_animation_type == FontAnimationShowingType.SUDDEN:
            # The text in sudden-mode has finished being displayed, so
            # set the flag to run stop_intro_animation(), so that the
            # on_halt reusable script (if any) can run and <no_clear>
            # can be checked.
            stop_intro = True

        if stop_intro:
            self.stop_intro_animation()

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

        self.gradual_letter_cursor_position = 0
        self.gradual_delay_counter = 0
        self.current_font_fade_value = 255

        # Run a reusable script now that the dialog text is finished displaying?
        # (ie: for when <halt> is used)
        main_reader = active_story.Passer.active_story.reader.get_main_story_reader()

        # Run reusable_on_halt, if we're not in halt_auto mode.
        # halt_auto should not show on_halt animations, because it will proceed on its own.
        if active_story.Passer.active_story.dialog_rectangle.reusable_on_halt and \
                not main_reader.halt_main_script_auto_mode_frames:
            active_story.Passer.active_story.reader.spawn_new_background_reader(
                reusable_script_name=active_story.Passer.active_story.dialog_rectangle.reusable_on_halt)


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

    def __init__(self, story):

        # So we can access the loaded fonts
        # and the active dialog rectangle.
        self.story: active_story.ActiveStory
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
                          start_animation_type=FontAnimationShowingType.FADE_IN)

        # Will contain a list of pygame.rects that needs to be updated.
        # Each single rect will be a single Letter object.
        self.update_rects = []

    def reset_sudden_text_finished_flag(self):
        """
        Reset flag which indicates that all the text in sudden-mode
        has already been blitted (to prevent repeated letter blittings in sudden-mode
        because there is no gradual animation for sudden-mode).
        """
        self.sudden_text_drawn_already = False

    def get_updated_rects(self):
        """
        Return a list of pygame.rects that need to be updated.
        """
        if self.update_rects:

            # If a dialog text intro animation is currently happening,
            # return the updated rects without clearing it. We don't clear it
            # yet because the animation of the letters (fading-in) is still ongoing.
            if self.font_animation.is_start_animating:
                return self.update_rects

            else:
                # There are no animations occuring with the dialog text.
                # Return the updated rects (the letter rects) and clear the updates.
                update_copy = self.update_rects.copy()
                self.update_rects.clear()
                return update_copy

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

        # The update rect's X and Y will be different than the letter's X and Y.
        # The letter's drawing X and Y will be based on the dialog rectangle,
        # so in other words, it'll be (0,0) if the text is being drawn on the
        # top-left of the dialog rectangle. However, when updating the letters,
        # we need to use overall pygame window size (main surface size),
        # not based on just the dialog rectangle.

        # Get the update rect based on the overall pygame window size,
        # so we're going to add the dialog rectangle's X to the letter's X
        # and we're going to add the dialog rectangle's Y to the letter's Y.

        # left, top, width, height
        update_rect = rect.copy()
        update_rect.x += self.story.dialog_rectangle_rect.x
        update_rect.y += self.story.dialog_rectangle_rect.y


        self.update_rects.append(update_rect)

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
        Blit the letters to the current dialog rectangle's surface.
        """

        # We are either animating the text gradually (fade or gradual letter)
        # or the text-mode is in sudden-mode and the text is ready to be blitted.

        # Redraw the rectangle so all the letters get cleared
        # and then animate the new text animations (fade values).
        if self.font_animation.is_start_animating or not self.sudden_text_drawn_already:

            # We're animating the text or there is text already
            # waiting to be fully displayed, if it's in sudden-mode.

            # Re-draw the dialog rectangle so the text gets cleared from before
            # and re-draw the font text again.
            self.story.dialog_rectangle.redraw_rectangle()

            # Animate any gradual text animations (fade values).
            self.font_animation.animate()

            # Get the dialog surface so we can blit letters onto it.
            dialog_surface = self.story.dialog_rectangle.surface

            # Used inside the loop below; meant for sudden-mode
            blitted_a_letter = False

            # Blit letters onto the newly (re)drawn dialog rectangle.
            letter: Letter
            for letter in self.letters_to_blit:
                dialog_surface.blit(letter.surface,
                                    letter.rect)

                # Meant for sudden-mode, used later in this method.
                blitted_a_letter = True

            # If we blitted letter(s) and the font mode is sudden-mode,
            # that means we blitted all the text for this current letter-set,
            # In a case like that, set 'sudden_text_drawn_already' to True
            # so we don't draw keep re-drawing the dialog rectangle for no reason
            # in the next call to this method.
            if blitted_a_letter:
                if self.font_animation.start_animation_type == FontAnimationShowingType.SUDDEN:
                    # We've blitted sudden-mode text
                    # So we don't redraw the dialog rectangle again in the next frame.
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
            