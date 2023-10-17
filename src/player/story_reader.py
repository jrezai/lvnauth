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

import copy
import pygame
import active_story
import file_reader
import dialog_rectangle
import font_handler
import logging
import sprite_definition as sd
from re import search
from typing import Tuple, NamedTuple
from font_handler import ActiveFontHandler
from typing import Dict
from shared_components import Passer
from audio_player import AudioPlayer, AudioChannel
from rest_handler import RestHandler


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


class PlayAudio(NamedTuple):
    audio_name: str


class DialogTextSound(NamedTuple):
    audio_name: str
    

class Volume(NamedTuple):
    volume: int


class Flip(NamedTuple):
    general_alias: str


class FontTextFadeSpeed(NamedTuple):
    fade_speed: int


class FontTextDelay(NamedTuple):
    number_of_frames: int

    
class FontTextDelayPunc(NamedTuple):
    previous_letter: str
    number_of_frames: int


class FontStartPosition(NamedTuple):
    start_position: int
    
    
class FontIntroAnimation(NamedTuple):
    animation_type: str


class FontOutroAnimation(NamedTuple):
    animation_type: str


class After(NamedTuple):
    frames_elapse: int
    reusable_script: str
    

class AfterCancel(NamedTuple):
    reusable_script: str

    
class SceneLoad(NamedTuple):
    chapter_name: str
    scene_name: str




class AfterCounter:
    """
    Used with the AfterManager class.
    
    Purpose: to keep track of how many frames need to be skipped
    and how many frames have been skipped so far.
    """
    def __init__(self, frames_to_skip: int):
        """
        Arguments:
        
        - frames_to_skip: the number of frames to elapse
        until the reusable script is run.
        """
        
        self.frames_to_skip = frames_to_skip
        self.frames_skipped_so_far = 0

    def elapse(self):
        """
        Elapse/increment by 1 frame.
        """
        self.frames_skipped_so_far += 1

    def is_ready(self) -> bool:
        """
        Return True if the number of frames that has been skipped
        has reached its limit.
        """

        return self.frames_skipped_so_far >= self.frames_to_skip


class AfterManager:
    """
    Handle running reusable scripts after X number of frames.
    
    The same reusable script cannot be queued up multiple times.
    There is no technical reason for this; I could think of no situation
    where the same reusable script needs to run at different times.
    """
    def __init__(self, method_spawn_background_reader):
        """
        A new object used for running reusable scripts after a certain
        number of frames have elapsed.
        
        Arguments:
        
        - method_spawn_background_reader: a method used for spawning
        a new background reader to run a reusable script.
        """

        # Key: reusable script name
        # Value: AfterCounter object
        self.scripts_and_timers = {}
        
        # The method used for spawning a new background reader.
        # We'll need this method in the tick_elapse() method.
        self.method_spawn_background_reader = method_spawn_background_reader
        
    def add_timer(self, reusable_script_name: str, frames_to_skip: int):
        """
        Add the given reusable script to a queue so that after X number of
        frames has been elapsed, run the reusable script and then remove it
        from the queue.
        """

        if not reusable_script_name and not frames_to_skip:
            return

        # Only allow each reusable script to be in the queue one-time.
        if reusable_script_name in self.scripts_and_timers:
            return

        counter = AfterCounter(frames_to_skip=frames_to_skip)

        # Add to dictionary
        self.scripts_and_timers[reusable_script_name] = counter

    def remove_timer(self, reusable_script_name: str):
        """
        Remove the specific reusable script name from the queue.
        
        Purpose: used with <after_cancel>
        """

        if reusable_script_name not in self.scripts_and_timers:
            return
        
        del self.scripts_and_timers[reusable_script_name]
        
    def remove_all_timers(self):
        """
        Remove all after timers from the queue.
        
        Purpose: used with <after_cancel_all>
        """
        
        self.scripts_and_timers.clear()
        
    def tick_elapse(self):
        """
        Increment all the items in the queue by 1 and then
        run reusable scripts that need to run.
        
        This method gets run every frame of the story,
        even if the queue is empty.
        """

        run_script_names = []

        counter: AfterCounter
        for reusable_script_name, counter in self.scripts_and_timers.items():

            # Increment this timer by 1 frame.
            counter.elapse()
            
            # Is this queue ready to run the script?
            if counter.is_ready():
                # Yes, run this script at the end of this method.
                run_script_names.append(reusable_script_name)
            else:
                self.scripts_and_timers[reusable_script_name] = counter

        # Remove timers that have expired and run the reusable scripts.
        for reusable_script_name in run_script_names:
            
            # Remove expired timer
            del self.scripts_and_timers[reusable_script_name]

            # Spawn a new background reader so we can run
            # the reusable script that we're iterating on.
            self.method_spawn_background_reader(reusable_script_name)


class StoryReader:
    """
    Reads a story script line by line.
    When reading dialogue text, it will also look for in-between text commands,
    such as <delay: 400>.

    This class populates the story variable with the sprites/audio that it needs.
    It also starts/stops animation by calling the story variable to do things as needed.

    The story variable is the 'renderer' while this is the script reader which finds out
    what needs to be rendered next by altering the story variable (adding sprites to groups, etc.)
    """

    COMMANDS_REQUIRE_ARGUMENTS = ("load_character", "character_set_position_x",
                                  "character_set_position_y", "character_stop_movement_condition",
                                  "character_move", "character_start_moving", "character_move_delay",
                                  "call")
    

    # These commands will be ignored if used in a reusable script.
    # (currently there are no commands that can't be used in a reusable script)
    COMMANDS_CANNOT_RUN_IN_REUSABLE_SCRIPTS = ()
    

    def __init__(self,
                 story,
                 data_requester,
                 background_reader_name: str | None):
        """
        This object is responsible for parsing/reading scripts.

        This object can either be the main story reader or it can be a background reader.

        There can only be one main story reader and the main story reader is the only
        reader that can spawn new background readers.

        Arguments:
        
        - story: the ActiveStory object - so we can spawn a new background reader.
        
        - data_requester: FileReader object - so we can load sprites and audio.
        
        - background_reader_name: (str) if None, it means this is the main story reader object.
                                       if a name is supplied, it means this is a new background reader
        """

        # So we can spawn new background readers
        self.story: active_story
        self.story = story

        # So we can load sprites and audio
        self.data_requester: file_reader.FileReader
        self.data_requester = data_requester

        # Used if we are instantiating a background reader
        self.background_reader_name = background_reader_name

        # The story is read line by line
        self.script_lines = []

        # This gets set to True once there are no more scripts to read.
        # This is used so we don't attempt to reload the story again.
        self.story_finished = False

        # Only the main story reader should contain the fields below.
        if not self.background_reader_name:
            # It's the main story reader.

            # Gets set to True when <halt> is reached.
            # This pauses the reading of the main script until the mouse is clicked.
            self.halt_main_script = False
            
            # Gets used with <rest>.
            # This pauses the reading of the main script, regardless if the
            # mouse is clicked. It forces the main story reader to pause for
            # a specific number of frames.
            self.rest_handler = RestHandler()

            # Gets used with <wait_for_animation>
            # This object gets used for checking wait-rules (waiting
            # for specific sprites to finish specific animations).
            # It forces the main story reader to pause until there are
            # no more sprites animating that were in the wait list.
            self.wait_for_animation_handler = WaitForAnimationHandler()
    
            # When halted in auto-mode, a mouse click or keyboard press won't
            # advance the story. Instead, the story will be advanced automatically
            # after X number of frames have elapsed.
            self.halt_main_script_auto_mode_frames = 0
            
            # This will increment until we reach the frame count above.
            self.halt_main_script_frame_counter = 0            

            # Used for starting a timer which runs a reusable script
            # after X number of frames have elapsed.
            self.after_manager =\
                AfterManager(method_spawn_background_reader=self.spawn_new_background_reader)
                       
            
            # A new foreground reader is being instaniated 
            # (ie: new scene, or new chapter)
            
            # so unload all previously loaded sprites so we can start fresh.
            self.clear_all_sprite_groups()
            

            # Deals with showing/hiding dialog text
            self.active_font_handler = ActiveFontHandler(story=self.story)
            
            # When <text_dialog_show> is used, it might show an animation.
            # While the dialog rectangle is animating, we don't want to proceed
            # with the main script until the dialog rect's animation is done.
            
            # We use this flag to check whether the dialog rect is animating
            # and if its, don't progress the main script yet.
            self.animating_dialog_rectangle = False

            # Key (str): reusable script name (background reader name)
            # Value: StoryReader object (background reader)
            self.background_readers = {}

            # When a background script (reusable script) is finished,
            # it can't be deleted directly while all the background scripts are being enumerated.
            # So we use this queue list to delete background scripts after reading through
            # the background scripts.
            self.background_readers_deletion_queue = []

            # Should we use a custom startup chapter and scene?
            # {chapter name: scene name}
            if Passer.manual_startup_chapter_scene:
                # Yes, a custom startup chapter and scene that the user
                # has selected from the Launch window.
                
                # {chapter_name: scene_name}
                self.story_startup_script = Passer.manual_startup_chapter_scene
            else:
                # Use the story-defined standard startup chapter and scene.

                # {chapter name: scene name}
                self.story_startup_script = self.data_requester.detail_header.get("StoryStartScript")

            # {chapter name: [chapter script, {scene name: scene script}] }
            self.chapters_and_scenes = self.data_requester.detail_header.get("StoryScript")

    def main_script_should_pause(self):
        """
        Check if there are any animations occurring
        or pauses (halt, rest) that should cause
        the main story script to not continue reading.
        
        This does not apply to background scripts.
        """
        main_reader = self.get_main_story_reader()
        
        return any((main_reader.animating_dialog_rectangle,
                    main_reader.halt_main_script,
                    main_reader.rest_handler.pause_required(),
                    main_reader.wait_for_animation_handler.check_wait()))

    def clear_all_sprite_groups(self):
        """
        Clear all the sprite group dictionaries.
        
        Purpose: when a new foreground story reader is instantiated,
        it means that a new scene is being loaded. So each time a new
        scene is played, one of the first things to happen is clearing
        the loaded sprites so we can start fresh, because it might
        be a new chapter too.
        """
        sd.Groups.background_group.clear()
        sd.Groups.character_group.clear()
        sd.Groups.object_group.clear()
        sd.Groups.dialog_group.clear()

    def _get_startup_chapter_script(self) -> str | None:
        """
        Return the story script for the startup chapter.
        :return: str (story script)
        """
        # {chapter name: scene name}
        for k in self.story_startup_script.keys():
            startup_chapter_name = k
            break
        else:
            return

        # {chapter name: [chapter script, {scene name: scene script}] }
        chapter_script = self.chapters_and_scenes.get(startup_chapter_name)[0]

        return chapter_script

    def _get_startup_scene_script(self) -> str | None:
        """
        Return the story script for the startup scene.
        :return: str (story script)
        """
        # {chapter name: scene name}
        for k, v in self.story_startup_script.items():
            startup_chapter_name, startup_scene_name = k, v
            break
        else:
            return

        # {chapter name: [chapter script, {scene name: scene script}] }
        scene_script = self.chapters_and_scenes.get(startup_chapter_name)[1].get(startup_scene_name)

        return scene_script

    def _get_reusable_script(self, reusable_script_name) -> str | None:
        """
        Return a reusable script.

        :param reusable_script_name: The case-sensitive name of the reusable script.
        :return: str (script) or None if not found
        """
        reusable_scripts = self.data_requester.detail_header.get("StoryReusables")

        script = reusable_scripts.get(reusable_script_name)

        if not script:
            return

        return script

    @staticmethod
    def extract_arguments(command_line: str):
        """
        Given a line, such as <load_character: rave_normal, second argument, third argument>,
        return {'Command': 'load_character', 'Arguments': ' rave_normal, second argument, third argument'}
        :param command_line: the story script line
        :return: Dict
        """
        pattern_with_arguments =\
            r"^<(?P<Command>[a-z]+[_]*[\w]+):{1}(?P<Arguments>.*)>$"
        
        pattern_no_arguments =\
            r"^<(?P<Command>[a-z]+[_]*[\w]+)>$"

        # Try searching for a command with arguments.
        # Example: <call: some script>
        result = search(pattern=pattern_with_arguments,
                        string=command_line)

        # No results? Try searching for a command with no arguments.
        # Example: <halt>
        if not result:
            result = search(pattern=pattern_no_arguments,
                            string=command_line)

        if result:
            return result.groupdict()

    def read_all_scripts(self):
        """
        Read the main story script followed by the background scripts.
        :return:
        """

        # Progress the main story script.
        self.read_story()
        
        # Increment all After timers (if any) by 1 frame.
        self.after_manager.tick_elapse()

        # If this is the main story reader, read the background readers.
        if not self.background_reader_name:
            # We are in the main story reader.

            # Read background readers (reusable scripts)
            for background_reader in self.background_readers.values():
                background_reader.read_story()

            # Background reader deletions need to occur below and not inside an actual reader
            # because if we delete inside a reader, we'll get a 'deletion during enumeration' exception.

            # Are there any background reusable scripts that are no longer needed
            # and need to be deleted?
            if self.background_readers_deletion_queue:
                # Yes, there are some background readers that need to be deleted.

                for bg_reader_name in self.background_readers_deletion_queue:

                    # Delete this background reader if it's still there.
                    # It may not be there if a new scene was loaded in the meantime.

                    # Loading a new scene automatically removes all background scenes,
                    # which is why we need to check if the background scene is still there.
                    if bg_reader_name in self.background_readers:
                        del self.background_readers[bg_reader_name]

                # All the bg readers that were queued for deletion are deleted
                # so clear the deletion queue.
                self.background_readers_deletion_queue.clear()

    def read_story(self):
        """
        Read the story line by line, starting with the startup chapter script,
        then followed by the startup scene script.
        :return:
        """

        # If the story is finished, stop here. If we don't have this stop here,
        # the method will reload the script and the story will play again
        # (which we don't want).
        if self.story_finished:

            # If this story reader (that is now finished) is a
            # background reader, remove it from the main story reader
            # background dictionary because it's finished reading.
            if self.background_reader_name:
                self.story.reader.background_readers_deletion_queue.append(self.background_reader_name)

            # Don't continue reading this story reader because it's finished
            # (regardless if it's the main story reader or not).
            return

        # Loading the startup script for the first time.
        if not self.script_lines:
            chapter_script = self._get_startup_chapter_script()
            scene_script = self._get_startup_scene_script()

            script = chapter_script + "\n" + scene_script

            self.script_lines = script.splitlines()


        """
        If this is the main story reader and there are blocking animations
        (such as a dialog rectangle being animated), don't proceed with
        the main script animation(s) is finished.
        """
        if not self.background_reader_name:
            # We're in the main story reader (not a reusable script)
            
            if self.main_script_should_pause():

                # If the story is halted with a timer (halt_auto),
                # elapse the counter. The method below will check for this.
                self.elapse_halt_timer()
                
                # If the story is in rest-mode (the same as halt_auto,
                # but not limited to dialog text), then elapse the counter.
                # The method below will check fot his.
                self.rest_handler.tick()
                
                return

        command_line = True

        # Keep looping while we're reading <command: x> type lines
        # Execute the commands as we read through them.
        while command_line:
            
            line = self.script_lines.pop(0)

            # Nothing else to read?
            # Consider the current script to be now finished.
            if not self.script_lines:
                self.story_finished = True
                command_line = False
                
            # A blank line or a comment line? Ignore the line completely.
            if not line or line.startswith("#"):
                continue
            
            # This is a special command, which gets replaced 
            # with a blank string, because real blank strings are ignored
            # if this command is not used.
            elif line == "<line>":
                line = ""

            results = self.extract_arguments(line)
            if results:
                command_name = results.get("Command")
                arguments = results.get("Arguments")

                if arguments:
                    arguments = arguments.strip()

                if command_name:
                    self.run_command(command_name, arguments)

                    # Did we run just a command that should cause this loop
                    # to stop? Then break the loop.
                    # Example: <text_dialog_define: ...>
                    if self.main_script_should_pause():
                        
                        # If we're in the main reader 
                        # (not the background reader)
                        # then we need to pause.
                        if not self.background_reader_name:
                            return
                        
            else:
                # Not a command, probably dialog text.
                
                # Reading letters should only be allowed in the main script.
                if self.background_reader_name:
                    continue                     
                
                command_line = False

                # Not a command, probably dialog text.
                self.read_dialog_text(line_text=line)

    def read_dialog_text(self, line_text):
        """
        Read the letters on this line by cropping the letters from
        the full font spritesheet, letter by letter.
        
        Also, record the kerning rules (left_trim, right_trim) and apply them.
        
        Add the letters to a list called 'letters_to_blit', which will
        eventually be iterated when ready to blit the letters.
        
        Note:
        Backgrounds readers (reusable scripts) should never call this method,
        because reusable scripts can't contain dialog text. If they do,
        the dialog text will be ignored.
        """

        # If there is no active font, there is no point in trying to
        # get the letters on this line of text.
        if not self.active_font_handler.current_font:
            # No active font. Possible reason: when <font: name> was used,
            # the wrong name was entered (typo) or not at all.
            logging.info(f"No font loaded - can't display text.")

            # There is no font to show text, so continue on with the main script
            # and skip over the current dialog text.
            self.read_story()
            return


        # Make sure the dialog rectangle is visible because if it's not,
        # there is no point in reading dialog text.
        if not self.story.dialog_rectangle or not self.story.dialog_rectangle.visible \
           or self.story.dialog_rectangle.animating_outro:
            # There is no dialog rectangle or it's not visible.
            # Continue on with the main script and pass over the dialog text.
            self.read_story()
            return
        
        # Used for letter kerning
        previous_letter = None

        # Read the line we've been given, line by line.
        for letter in self.read_next_letter(line_text=line_text):

            # print("Read letter:", letter)
            logging.info(f"Read letter: {letter}")

            # Now get the letter surface (the cropped image of the letter)
            letter_surface =\
                self.active_font_handler.current_font.get_letter(letter=letter)

            # Get the amount of padding/kerning to use for the letter
            # that we're going to blit soon, based on the kerning rules
            # and the previous letter.
            left_trim, right_trim =\
                self.active_font_handler.current_font.get_letter_trims(letter=letter,
                                                                       previous_letter=previous_letter)

            # Was the letter sprite found?
            if letter_surface:
                # Yes, it was found. Add it to the list of letters that
                # should be displayed in the dialog rectangle.
                self.active_font_handler.add_letter(letter_subsurface=letter_surface,
                                                   is_space=(letter == " "),
                                                   previous_letter=previous_letter,
                                                   left_trim=left_trim,
                                                   right_trim=right_trim)
                
                # Keep track of the previous letter for kerning purposes.
                previous_letter = letter                
                
        
        # Keep track of where the end of the line is for the X position.
        # Used for restoring the X position when <continue> is reached.
        self.active_font_handler.next_letter_x_position_continue = \
            self.active_font_handler.next_letter_x_position

        # We finished reading the entire line, so position the text cursor
        # on the next line, in case there is more text to read on the next line.
        self.active_font_handler.next_letter_x_position =\
            self.active_font_handler.default_x_position

        # Keep track of where the end of the line is for the Y position.
        # Used for restoring the X position when <continue> is reached.
        self.active_font_handler.next_letter_y_position_continue = \
            self.active_font_handler.next_letter_y_position

        # Set the Y 'cursor' to the next line.
        self.active_font_handler.next_letter_y_position += \
            self.active_font_handler.current_font.height + \
            self.active_font_handler.current_font.padding_lines
        
        # Is the Y coordinate of the dialog text temporarily adjusted
        # after using the <continue> command? Reset it back to without its adjustment.
        if self.active_font_handler.adjusted_y:
            self.active_font_handler.next_letter_y_position -= self.active_font_handler.adjusted_y
            self.active_font_handler.adjusted_y = 0


        print("Finished reading.")
        
        ## Experimental - Sept 25, 2023
        ###############
        ## Start the animation of the dialog text.
        #self.active_font_handler.\
            #font_animation.start_show_animation(letters=self.active_font_handler.letters_to_blit)        
        ###############
        
        ######Uncomment line 918 below after experiment - Sept 25, 2023
        ## Don't wait until the next frame to read a possible
        ## other line of text. Run read_story() so it can check if there's
        ## another line of text, and if there is, this method (read_dialog_text)
        ## will run again.
        self.read_story()

    def read_next_letter(self, line_text):
        """
        The story doesn't currently contain a command to run, so
        the read_story() method wants us to show the text now as dialog text.
        
        But while we're reading the dialog text, we should look for commands
        and run read_story() once we find any.
        
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

    @staticmethod
    def _split_arguments_to_tuple(arguments: str) -> Tuple | None:
        """
        Take a comma separated arguments string and convert it to a tuple:

        Example: 'rave_normal, start of display' becomes ('rave_normal', 'start of display')
        :param arguments:
        :return:
        """
        if not arguments:
            return

        splitter = arguments.split(",")

        # Remove excess spaces
        for counter, part in enumerate(splitter):
            splitter[counter] = part.strip()

        return tuple(splitter)

    def run_command(self, command_name, arguments=None):
        """
        Perform an action based on the given command and its optional argument(s).
        If there are multiple arguments, they will be separate by commas.


        :param command_name: (str) example: load_character
        :param arguments: (str) example: rave_normal
               (if there are multiple arguments, they will be delimited by commas
               like this: "first argument, second argument, third argument..."
        :return:

        Changes
        Oct 13, 2023 - Process text_dialog_show only if the dialog isn't already visible (Jobin Rezai)
        """
        if command_name in StoryReader.COMMANDS_REQUIRE_ARGUMENTS and not arguments:
            print(f"{command_name} was used without an argument.")
            logging.warning(f"{command_name} was used without an argument.")
            return

        # Some commands should be ignored if they attempt to be used in
        # a reusable script.
        if command_name in StoryReader.COMMANDS_CANNOT_RUN_IN_REUSABLE_SCRIPTS:
            if self.background_reader_name:
                return


        if command_name == "load_character":
            self._sprite_load(arguments=arguments,
                                 sprite_type=file_reader.ContentType.CHARACTER)

        elif command_name == "load_object":
            self._sprite_load(arguments=arguments,
                              sprite_type=file_reader.ContentType.OBJECT)
            
        elif command_name == "load_dialog_sprite":
            self._sprite_load(arguments=arguments,
                              sprite_type=file_reader.ContentType.DIALOG_SPRITE)

        elif command_name == "load_font_sprite":
            
            font_full_sprite_sheet_sprite = \
                self.data_requester.get_sprite(content_type=file_reader.ContentType.FONT_SPRITE_SHEET,
                                               item_name=arguments)

            if not font_full_sprite_sheet_sprite:
                return
            
            self.story: active_story.ActiveStory
            self.story.add_font(font_name=arguments,
                                font_sprite=font_full_sprite_sheet_sprite)

        elif command_name == "play_sound":
            self._play_audio(arguments=arguments,
                             audio_channel=AudioChannel.FX)
            
        elif command_name == "play_voice":
            self._play_audio(arguments=arguments,
                             audio_channel=AudioChannel.VOICE)
            
        elif command_name == "play_music":
            self._play_audio(arguments=arguments,
                             audio_channel=AudioChannel.MUSIC)            
            
        elif command_name == "font":
            # Set the font to use in the main story reader, for the next letter.
            
            # Reusable scripts don't have a font handler, so we need
            # to handle this in the main reader.
            main_reader = self.get_main_story_reader()
            
            main_reader.active_font_handler.set_active_font(font_name=arguments)
            
        elif command_name == "font_x":
            # Set the X starting position of the active font,
            # relative to the dialog rectangle.
            self._font_start_position(x=True, arguments=arguments)

        elif command_name == "font_y":
            # Set the Y starting position of the active font,
            # relative to the dialog rectangle.
            self._font_start_position(x=False, arguments=arguments)
            
        elif command_name == "font_text_fade_speed":
            # Set the speed of letter by letter fade-in and
            # overall fade-in dialog text.
            # The speed range is 1 (slowest) to 10 (fastest)
            self._font_text_fade_speed(arguments=arguments)
            
        elif command_name == "font_text_delay":
            # Set the number of frames to skip when applying
            # the gradual dialog text animation (letter by letter).
            self._font_text_delay(arguments=arguments)
            
        elif command_name == "font_text_delay_punc":
            # Set the number of frames to skip
            # *after* a specific letter is blitted.
            self._font_text_delay_punc(arguments=arguments)
            
        elif command_name == "font_intro_animation":
            # The animation to use when showing dialog text.
            self._font_intro_animation(arguments=arguments)

        elif command_name == "load_background":

            # Background sprites don't use aliases, but the method below
            # will expect it (_sprite_load()), so just satisfy it with a dummy
            # general alias value.
            if "," not in arguments:
                arguments += ", fixed_alias"

            self._sprite_load(arguments=arguments,
                              sprite_type=file_reader.ContentType.BACKGROUND)
            #background_sprite = self.data_requester.get_sprite(content_type=file_reader.ContentType.BACKGROUND,
                                                               #item_name=arguments)

            #active_story.Groups.background_group.add(arguments, background_sprite)

        elif command_name == "continue":
            self._continue(arguments=arguments)

        elif command_name == "text_dialog_define":
            
            self._text_dialog_define(arguments=arguments)

        elif command_name == "text_dialog_show":

            self.story: StoryReader
            if self.story.dialog_rectangle:

                # Start showing the intro animation for
                # the dialog rectangle, only if it's not already visible.

                # Reason: otherwise, the story will wait for a dialog
                # intro animation that has already finished.
                if not self.story.dialog_rectangle.visible:
                    # Used to indicate that the main script should pause
                    self.animating_dialog_rectangle = True

                    self.story.dialog_rectangle.start_show()

        elif command_name == "text_dialog_close":

            self.story: StoryReader
            if self.story.dialog_rectangle and self.story.dialog_rectangle.visible:

                # Used to indicate that the main script should pause
                self.animating_dialog_rectangle = True
                
                self.story.dialog_rectangle.start_hide()
                
        elif command_name in ("character_flip_both", "character_flip_horizontal",
                              "character_flip_vertical", "object_flip_both",
                              "object_flip_horizontal", "object_flip_vertical",
                              "dialog_sprite_flip_both", "dialog_sprite_flip_horizontal",
                              "dialog_sprite_flip_vertical"):

            self._flip(command_name=command_name, arguments=arguments)

        elif command_name == "no_clear":
            self._no_clear()

        elif command_name == "halt":
            """
            Pause the reading of the main script
            until the user clicks the mouse.
            """
            self.halt()

        elif command_name == "halt_auto":
            """
            Same as <halt> except it won't respond to mouse or keyboard
            events until X number of frames have elapsed.
            
            In other words, it will automatically 'click'
            after X number of frames.
            """
            self._halt_auto(arguments=arguments)
            
        elif command_name == "rest":
            """
            Same as <halt> except the number of frames to pause is specified
            and the pause can't be skipped (only pauses the main reader,
            not background readers).
            """
            self._rest(arguments=arguments)

        elif command_name == "wait_for_animation":
            """
            Pause the main story reader until a specific animation has finished.
            """
            self._wait_for_animation(arguments=arguments)

        elif command_name == "character_show":
            """
            Show a character sprite by setting its visibility flag to True.
            """
            self._sprite_show(arguments=arguments,
                              sprite_type=file_reader.ContentType.CHARACTER)
            
        elif command_name == "dialog_sprite_show":
            """
            Show a dialog sprite sprite by setting its visibility flag to True.
            """
            self._sprite_show(arguments=arguments,
                              sprite_type=file_reader.ContentType.DIALOG_SPRITE)
            
        elif command_name == "object_show":
            """
            Show an object sprite by setting its visibility flag to True.
            """
            self._sprite_show(arguments=arguments,
                              sprite_type=file_reader.ContentType.OBJECT)

        elif command_name == "object_hide":
            """
            Hide an object sprite by setting its visibility flag to False.
            """
            self._sprite_hide(arguments=arguments,
                              sprite_type=file_reader.ContentType.OBJECT)
            
        elif command_name == "dialog_sprite_hide":
            """
            Hide an dialog sprite by setting its visibility flag to False.
            """
            self._sprite_hide(arguments=arguments,
                              sprite_type=file_reader.ContentType.DIALOG_SPRITE)

        elif command_name in ("character_hide_all",
                              "object_hide_all",
                              "dialog_sprite_hide_all"):
            """
            Hide all the sprites in a specific sprite group,
            depending on the command name.
            """
            self._sprite_hide_all(command_name=command_name)

        elif command_name == "dialog_text_sound":
            """
            Specify the sound to play for letter-by-letter non-gradual
            animations in the dialog rectangle.
            """
            self._dialog_text_sound(arguments=arguments)
            
        elif command_name == "dialog_text_sound_clear":
            """
            Specify no audio to play for letter-by-letter non-gradual
            text that is shown.
            """
            self._dialog_text_sound_clear()
            
        elif command_name in ("volume_fx", "volume_voice", "volume_music",
                              "volume_text"):
            """
            Set the volume for a specific audio channel.
            
            We'll know which audio channel based on the command_name.
            """

            self._volume(command_name=command_name,
                         arguments=arguments)
            
        elif command_name in ("stop_fx", "stop_voice",
                              "stop_music", "stop_all_audio"):
            """
            Stop the audio from a specific audio channel(s).
            """
            
            self._stop_audio(command_name=command_name)
            
        elif command_name == "background_show":
            """
            Show a background sprite by setting its visibility flag to True.
            """

            self._sprite_show(arguments=arguments,
                              sprite_type=file_reader.ContentType.BACKGROUND)
            
        elif command_name == "background_hide":
            """
            Hide a background sprite by setting its visibility flag to False.
            """
            self._sprite_hide(arguments=arguments,
                              sprite_type=file_reader.ContentType.BACKGROUND)

        elif command_name == "character_hide":
            """
            Hide a character sprite by settings its visibility flag to False.
            """
            self._sprite_hide(arguments=arguments,
                              sprite_type=file_reader.ContentType.CHARACTER)

        elif command_name in ("character_set_position_x",
                              "character_set_position_y"):

            self._sprite_set_position(command_name=command_name,
                                      arguments=arguments,
                                      sprite_type=file_reader.ContentType.CHARACTER)
            
        elif command_name in ("object_set_position_x",
                              "object_set_position_y"):

            self._sprite_set_position(command_name=command_name,
                                      arguments=arguments,
                                      sprite_type=file_reader.ContentType.OBJECT)
            
        elif command_name in ("dialog_sprite_set_position_x",
                              "dialog_sprite_set_position_y"):

            self._sprite_set_position(command_name=command_name,
                                      arguments=arguments,
                                      sprite_type=file_reader.ContentType.DIALOG_SPRITE)

        elif command_name in ("dialog_sprite_center_x_with",
                              "object_center_x_with",
                              "character_center_x_with"):
            self._sprite_center_x_with(command_name=command_name,
                                       arguments=arguments)

        elif command_name == "character_set_center":
            self._sprite_set_center(sprite_type=file_reader.ContentType.CHARACTER,
                                    arguments=arguments)

        elif command_name == "object_set_center":
            self._sprite_set_center(sprite_type=file_reader.ContentType.OBJECT,
                                    arguments=arguments)
            
        elif command_name == "dialog_sprite_set_center":
            self._sprite_set_center(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                    arguments=arguments)

        elif command_name == "character_stop_movement_condition":
            self._add_stop_movement_condition(sprite_type=file_reader.ContentType.CHARACTER,
                                              command_name=command_name,
                                              arguments=arguments)
            
        elif command_name == "object_stop_movement_condition":
            self._add_stop_movement_condition(sprite_type=file_reader.ContentType.OBJECT,
                                              command_name=command_name,
                                              arguments=arguments)
            
        elif command_name == "dialog_sprite_stop_movement_condition":
            self._add_stop_movement_condition(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                              command_name=command_name,
                                              arguments=arguments)

        elif command_name == "character_after_movement_stop":
            self._sprite_after_movement_stop(sprite_type=file_reader.ContentType.CHARACTER,
                                             arguments=arguments)
            
        elif command_name == "object_after_movement_stop":
            self._sprite_after_movement_stop(sprite_type=file_reader.ContentType.OBJECT,
                                             arguments=arguments)

        elif command_name == "dialog_sprite_after_movement_stop":
            self._sprite_after_movement_stop(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                             arguments=arguments)

        elif command_name == "character_move":
            self._set_movement_speed(sprite_type=file_reader.ContentType.CHARACTER,
                                     arguments=arguments)
            
        elif command_name == "object_move":
            self._set_movement_speed(sprite_type=file_reader.ContentType.OBJECT,
                                     arguments=arguments)

        elif command_name == "dialog_sprite_move":
            self._set_movement_speed(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                     arguments=arguments)

        elif command_name == "character_start_moving":
            self._sprite_start_or_stop_moving(sprite_type=file_reader.ContentType.CHARACTER,
                                              arguments=arguments,
                                              start_or_stop=sd.StartOrStop.START)
            
        elif command_name == "object_start_moving":
            self._sprite_start_or_stop_moving(sprite_type=file_reader.ContentType.OBJECT,
                                              arguments=arguments,
                                              start_or_stop=sd.StartOrStop.START)

        elif command_name == "dialog_sprite_start_moving":
            self._sprite_start_or_stop_moving(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                              arguments=arguments,
                                              start_or_stop=sd.StartOrStop.START)

        elif command_name == "character_stop_moving":
            self._sprite_start_or_stop_moving(sprite_type=file_reader.ContentType.CHARACTER,
                                              arguments=arguments,
                                              start_or_stop=sd.StartOrStop.STOP)
            
        elif command_name == "object_stop_moving":
            self._sprite_start_or_stop_moving(sprite_type=file_reader.ContentType.OBJECT,
                                              arguments=arguments,
                                              start_or_stop=sd.StartOrStop.STOP)
            
        elif command_name == "dialog_sprite_stop_moving":
            self._sprite_start_or_stop_moving(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                              arguments=arguments,
                                              start_or_stop=sd.StartOrStop.STOP)

        elif command_name == "character_move_delay":
            self._set_movement_delay(sprite_type=file_reader.ContentType.CHARACTER,
                                     arguments=arguments)
            
        elif command_name == "object_move_delay":
            self._set_movement_delay(sprite_type=file_reader.ContentType.OBJECT,
                                     arguments=arguments)

        elif command_name == "dialog_sprite_move_delay":
            self._set_movement_delay(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                     arguments=arguments)
            
        elif command_name == "call":
            self.spawn_new_background_reader(reusable_script_name=arguments)
            
        elif command_name == "scene":
            self.spawn_new_reader(arguments=arguments)
            
        elif command_name == "after":
            self.after_run(arguments=arguments)
            
        elif command_name == "after_cancel":
            self.after_cancel(arguments=arguments)
            
        elif command_name == "after_cancel_all":
            self.after_cancel_all()

        elif command_name == "character_fade_until":
            self._sprite_fade_until(sprite_type=file_reader.ContentType.CHARACTER,
                                    arguments=arguments)

        elif command_name == "object_fade_until":
            self._sprite_fade_until(sprite_type=file_reader.ContentType.OBJECT,
                                    arguments=arguments)
            
        elif command_name == "dialog_sprite_fade_until":
            self._sprite_fade_until(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                    arguments=arguments)

        elif command_name == "character_fade_current_value":
            self._sprite_current_fade_value(
                sprite_type=file_reader.ContentType.CHARACTER,
                arguments=arguments)

        elif command_name == "object_fade_current_value":
            self._sprite_current_fade_value(
                sprite_type=file_reader.ContentType.OBJECT,
                arguments=arguments)
            
        elif command_name == "dialog_sprite_fade_current_value":
            self._sprite_current_fade_value(
                sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                arguments=arguments)

        elif command_name == "character_fade_speed":
            self._sprite_fade_speed(sprite_type=file_reader.ContentType.CHARACTER,
                                    arguments=arguments)
            
        elif command_name == "object_fade_speed":
            self._sprite_fade_speed(sprite_type=file_reader.ContentType.OBJECT,
                                    arguments=arguments)
            
        elif command_name == "dialog_sprite_fade_speed":
            self._sprite_fade_speed(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                    arguments=arguments)

        elif command_name == "character_after_fading_stop":
            self._sprite_after_fading_stop(sprite_type=file_reader.ContentType.CHARACTER,
                                           arguments=arguments)
            
        elif command_name == "object_after_fading_stop":
            self._sprite_after_fading_stop(sprite_type=file_reader.ContentType.OBJECT,
                                           arguments=arguments)
            
        elif command_name == "dialog_sprite_after_fading_stop":
            self._sprite_after_fading_stop(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                           arguments=arguments)

        elif command_name == "character_fade_delay":
            self._sprite_fade_delay(sprite_type=file_reader.ContentType.CHARACTER,
                                    arguments=arguments)
            
        elif command_name == "object_fade_delay":
            self._sprite_fade_delay(sprite_type=file_reader.ContentType.OBJECT,
                                    arguments=arguments)
            
        elif command_name == "dialog_sprite_fade_delay":
            self._sprite_fade_delay(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                    arguments=arguments)

        elif command_name == "character_start_fading":
            self._sprite_start_or_stop_fading(sprite_type=file_reader.ContentType.CHARACTER,
                                              arguments=arguments,
                                              start_or_stop=sd.StartOrStop.START)
            
        elif command_name == "dialog_sprite_start_fading":
            self._sprite_start_or_stop_fading(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                              arguments=arguments,
                                              start_or_stop=sd.StartOrStop.START)
            
        elif command_name == "object_start_fading":
            self._sprite_start_or_stop_fading(sprite_type=file_reader.ContentType.OBJECT,
                                              arguments=arguments,
                                              start_or_stop=sd.StartOrStop.START)

        elif command_name == "character_stop_fading":
            self._sprite_start_or_stop_fading(sprite_type=file_reader.ContentType.CHARACTER,
                                              arguments=arguments,
                                              start_or_stop=sd.StartOrStop.STOP)
            
        elif command_name == "object_stop_fading":
            self._sprite_start_or_stop_fading(sprite_type=file_reader.ContentType.OBJECT,
                                              arguments=arguments,
                                              start_or_stop=sd.StartOrStop.STOP)
            
        elif command_name == "dialog_sprite_stop_fading":
            self._sprite_start_or_stop_fading(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                              arguments=arguments,
                                              start_or_stop=sd.StartOrStop.STOP)

        elif command_name == "character_scale_by":
            self._sprite_scale_by(sprite_type=file_reader.ContentType.CHARACTER,
                                  arguments=arguments)
            
        elif command_name == "object_scale_by":
            self._sprite_scale_by(sprite_type=file_reader.ContentType.OBJECT,
                                  arguments=arguments)
            
        elif command_name == "dialog_sprite_scale_by":
            self._sprite_scale_by(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                  arguments=arguments)

        elif command_name == "character_scale_until":
            self._sprite_scale_until(sprite_type=file_reader.ContentType.CHARACTER,
                                     arguments=arguments)

        elif command_name == "object_scale_until":
            self._sprite_scale_until(sprite_type=file_reader.ContentType.OBJECT,
                                     arguments=arguments)

        elif command_name == "dialog_sprite_scale_until":
            self._sprite_scale_until(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                     arguments=arguments)
            
        elif command_name == "character_scale_current_value":
            self._sprite_scale_current_value(sprite_type=file_reader.ContentType.CHARACTER,
                                             arguments=arguments)
            
        elif command_name == "object_scale_current_value":
            self._sprite_scale_current_value(sprite_type=file_reader.ContentType.OBJECT,
                                             arguments=arguments)
            
        elif command_name == "dialog_sprite_scale_current_value":
            self._sprite_scale_current_value(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                             arguments=arguments)

        elif command_name == "character_after_scaling_stop":
            self._sprite_after_scaling_stop(sprite_type=file_reader.ContentType.CHARACTER,
                                            arguments=arguments)
            
        elif command_name == "object_after_scaling_stop":
            self._sprite_after_scaling_stop(sprite_type=file_reader.ContentType.OBJECT,
                                            arguments=arguments)
            
        elif command_name == "dialog_sprite_after_scaling_stop":
            self._sprite_after_scaling_stop(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                            arguments=arguments)

        elif command_name == "character_scale_delay":
            self._sprite_scale_delay(sprite_type=file_reader.ContentType.CHARACTER,
                                     arguments=arguments)

        elif command_name == "object_scale_delay":
            self._sprite_scale_delay(sprite_type=file_reader.ContentType.OBJECT,
                                     arguments=arguments)

        elif command_name == "dialog_sprite_scale_delay":
            self._sprite_scale_delay(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                     arguments=arguments)

        elif command_name == "character_start_scaling":
            self._sprite_start_or_stop_scaling(sprite_type=file_reader.ContentType.CHARACTER,
                                               arguments=arguments,
                                               start_or_stop=sd.StartOrStop.START)

        elif command_name == "object_start_scaling":
            self._sprite_start_or_stop_scaling(sprite_type=file_reader.ContentType.OBJECT,
                                               arguments=arguments,
                                               start_or_stop=sd.StartOrStop.START)

        elif command_name == "dialog_start_scaling":
            self._sprite_start_or_stop_scaling(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                               arguments=arguments,
                                               start_or_stop=sd.StartOrStop.START)

        elif command_name == "character_stop_scaling":
            self._sprite_start_or_stop_scaling(sprite_type=file_reader.ContentType.CHARACTER,
                                               arguments=arguments,
                                               start_or_stop=sd.StartOrStop.STOP)
            
        elif command_name == "object_stop_scaling":
            self._sprite_start_or_stop_scaling(sprite_type=file_reader.ContentType.OBJECT,
                                               arguments=arguments,
                                               start_or_stop=sd.StartOrStop.STOP)
            
        elif command_name == "dialog_sprite_stop_scaling":
            self._sprite_start_or_stop_scaling(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                               arguments=arguments,
                                               start_or_stop=sd.StartOrStop.STOP)
            
        elif command_name == "character_rotate_current_value":
            self._sprite_rotate_current_value(sprite_type=file_reader.ContentType.CHARACTER,
                                              arguments=arguments)
            
        elif command_name == "object_rotate_current_value":
            self._sprite_rotate_current_value(sprite_type=file_reader.ContentType.OBJECT,
                                              arguments=arguments)
            
        elif command_name == "dialog_sprite_rotate_current_value":
            self._sprite_rotate_current_value(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                              arguments=arguments)

        elif command_name == "character_rotate_until":
            self._sprite_rotate_until(sprite_type=file_reader.ContentType.CHARACTER,
                                      arguments=arguments)
            
        elif command_name == "object_rotate_until":
            self._sprite_rotate_until(sprite_type=file_reader.ContentType.OBJECT,
                                      arguments=arguments)

        elif command_name == "dialog_sprite_rotate_until":
            self._sprite_rotate_until(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                      arguments=arguments)

        elif command_name == "character_rotate_speed":
            self._sprite_rotate_speed(sprite_type=file_reader.ContentType.CHARACTER,
                                      arguments=arguments)

        elif command_name == "object_rotate_speed":
            self._sprite_rotate_speed(sprite_type=file_reader.ContentType.OBJECT,
                                      arguments=arguments)
            
        elif command_name == "dialog_sprite_rotate_speed":
            self._sprite_rotate_speed(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                      arguments=arguments)

        elif command_name == "character_after_rotating_stop":
            self._sprite_after_rotating_stop(sprite_type=file_reader.ContentType.CHARACTER,
                                             arguments=arguments)
            
        elif command_name == "object_after_rotating_stop":
            self._sprite_after_rotating_stop(sprite_type=file_reader.ContentType.OBJECT,
                                             arguments=arguments)
            
        elif command_name == "dialog_sprite_after_rotating_stop":
            self._sprite_after_rotating_stop(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                             arguments=arguments)

        elif command_name == "character_rotate_delay":
            self._sprite_rotate_delay(sprite_type=file_reader.ContentType.CHARACTER,
                                      arguments=arguments)

        elif command_name == "object_rotate_delay":
            self._sprite_rotate_delay(sprite_type=file_reader.ContentType.OBJECT,
                                      arguments=arguments)
            
        elif command_name == "dialog_sprite_rotate_delay":
            self._sprite_rotate_delay(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                      arguments=arguments)

        elif command_name == "character_start_rotating":
            self._sprite_start_or_stop_rotating(sprite_type=file_reader.ContentType.CHARACTER,
                                                arguments=arguments,
                                                start_or_stop=sd.StartOrStop.START)
            
        elif command_name == "object_start_rotating":
            self._sprite_start_or_stop_rotating(sprite_type=file_reader.ContentType.OBJECT,
                                                arguments=arguments,
                                                start_or_stop=sd.StartOrStop.START)
            
        elif command_name == "dialog_sprite_start_rotating":
            self._sprite_start_or_stop_rotating(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                                arguments=arguments,
                                                start_or_stop=sd.StartOrStop.START)

        elif command_name == "character_stop_rotating":
            self._sprite_start_or_stop_rotating(sprite_type=file_reader.ContentType.CHARACTER,
                                                arguments=arguments,
                                                start_or_stop=sd.StartOrStop.STOP)

        elif command_name == "object_stop_rotating":
            self._sprite_start_or_stop_rotating(sprite_type=file_reader.ContentType.OBJECT,
                                                arguments=arguments,
                                                start_or_stop=sd.StartOrStop.STOP)

        elif command_name == "dialog_sprite_stop_rotating":
            self._sprite_start_or_stop_rotating(sprite_type=file_reader.ContentType.DIALOG_SPRITE,
                                                arguments=arguments,
                                                start_or_stop=sd.StartOrStop.STOP)

    def _volume(self, command_name: str, arguments: str):
        """
        Set the volume for a specific audio channel.
        
        We'll know which audio channel based on the command_name
        
        The convenient volume value range is: 0 to 100
        but pygame expects 0 to 1.
        """
        
        volume: Volume
        volume = self._get_arguments(class_namedtuple=Volume,
                                     given_arguments=arguments)
        
        if not volume:
            return
        
        def get_volume_from_convenient_value(self, convenient_value: int):
            """
            Take a value from 0 to 10 and return its float equivalent.
        
            pygame uses 0 to 1.0
            LVNAuth accepts: 0 to 100
            """
    
            float_values = """0.00
    0.01
    0.02
    0.03
    0.04
    0.05
    0.06
    0.07
    0.08
    0.09
    0.10
    0.11
    0.12
    0.13
    0.14
    0.15
    0.16
    0.17
    0.18
    0.19
    0.20
    0.21
    0.22
    0.23
    0.24
    0.25
    0.26
    0.27
    0.28
    0.29
    0.30
    0.31
    0.32
    0.33
    0.34
    0.35
    0.36
    0.37
    0.38
    0.39
    0.40
    0.41
    0.42
    0.43
    0.44
    0.45
    0.46
    0.47
    0.48
    0.49
    0.50
    0.51
    0.52
    0.53
    0.54
    0.55
    0.56
    0.57
    0.58
    0.59
    0.60
    0.61
    0.62
    0.63
    0.64
    0.65
    0.66
    0.67
    0.68
    0.69
    0.70
    0.71
    0.72
    0.73
    0.74
    0.75
    0.76
    0.77
    0.78
    0.79
    0.80
    0.81
    0.82
    0.83
    0.84
    0.85
    0.86
    0.87
    0.88
    0.89
    0.90
    0.91
    0.92
    0.93
    0.94
    0.95
    0.96
    0.97
    0.98
    0.99
    1.00"""
    
            # Key: convenient value (such as 50)
            # Value: float value (such as 0.50)
            volume_mapping = {}
    
            float_lines = float_values.split()
            
            # Populate volume mapping dictionary
            for idx, float_value in enumerate(float_lines):
                volume_mapping[idx] = float_value
    
            float_value = volume_mapping.get(convenient_value)
    
            return float_value
        
        float_volume =\
            get_volume_from_convenient_value(self, convenient_value=volume.volume)
        
        if not float_volume:
            return
        
        # Convert the string value to a float, because pygame will
        # not accept a string.
        float_volume = float(float_volume)

        channel_mapping = {"volume_text": AudioChannel.TEXT,
                           "volume_music": AudioChannel.MUSIC,
                           "volume_voice": AudioChannel.VOICE,
                           "volume_fx": AudioChannel.FX}

        audio_channel = channel_mapping.get(command_name)

        if audio_channel == AudioChannel.TEXT:
            self.story.audio_player.volume_text = float_volume
            
        elif audio_channel == AudioChannel.FX:
            self.story.audio_player.volume_sound = float_volume

        elif audio_channel == AudioChannel.VOICE:
            self.story.audio_player.volume_voice = float_volume

        elif audio_channel == AudioChannel.MUSIC:
            self.story.audio_player.volume_music = float_volume

    def _stop_audio(self, command_name: str):
        """
        Stop the audio in a specific channel, but only
        if the channel has already been initialized.
        
        Note: there is no command to stop text audio (ie: when an audio
        is played for each letter, letter-by-letter), because it will
        just immediately play again on the next letter.
        """
        
        channel_mapping = {"stop_fx": AudioChannel.FX,
                           "stop_voice": AudioChannel.VOICE,
                           "stop_music": AudioChannel.MUSIC,
                           "stop_all_audio": AudioChannel.ALL}
        
        audio_channel = channel_mapping.get(command_name)
        
        # Stop the audio on a specific audio channel.
        self.story.audio_player.stop_audio(audio_channel=audio_channel)

    def _dialog_text_sound(self, arguments: str):
        """
        Set the dialog rectangle to play a specific audio
        for letter-by-letter non-gradual text displays.
        """

        dialog_sound: DialogTextSound
        dialog_sound = self._get_arguments(class_namedtuple=DialogTextSound,
                                           given_arguments=arguments)

        if not dialog_sound:
            return

        # Set the audio name to use for each letter.
        # Only applies to: gradual-letter-by-letter (not fade)
        self.story.dialog_rectangle.text_sound_name = dialog_sound.audio_name
        
    def _dialog_text_sound_clear(self):
        """
        Set the dialog rectangle to play no audio when showing
        letters one by one (non-fading).
        """

        # Set no audio to play for each letter.
        self.story.dialog_rectangle.text_sound_name = None

    def _flip(self, command_name: str, arguments: str):
        """
        Flip a character/object/dialog surface horizontally, vertically, or both.
        """
        
        # Make sure an argument is provided (ie: a sprite alias)
        if not arguments:
            return
        
        flip: Flip
        flip = self._get_arguments(class_namedtuple=Flip,
                                   given_arguments=arguments)

        if not flip:
            return

        if "character" in command_name:
            sprite_type = active_story.ContentType.CHARACTER
        elif "object" in command_name:
            sprite_type = active_story.ContentType.OBJECT
        elif "dialog" in command_name:
            sprite_type = active_story.ContentType.DIALOG_SPRITE
            
        vertical = False
        horizontal = False

        if "both" in command_name:
            vertical = True
            horizontal = True
        elif "horizontal" in command_name:
            horizontal = True
        elif "vertical" in command_name:
            vertical = True

        # Get the visible sprite
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=flip.general_alias)

        if not sprite:
            return
        
        sprite.flip(horizontal=horizontal, vertical=vertical)


    def _sprite_set_position(self,
                             command_name: str,
                             arguments: str,
                             sprite_type: file_reader.ContentType) -> pygame.Rect:
        """
        Set the X or Y coordinates of a sprite of type:
        character, object, name
        
        Return: a rect with the new position.
        
        Example:
        <character_set_position_x: rave, 35>
        <character_set_position_y: rave, 135>
        <character_set_position_x: rave, start of display>
        <character_set_position_y: rave, bottom of display>

        <object_set_position_x: rave, 35>
        <object_set_position_y: rave, 135>
        <object_set_position_x: rave, start of display>
        <object_set_position_y: rave, bottom of display>
        """
        
        general_alias_and_position = self._split_arguments_to_tuple(arguments=arguments)

        if not general_alias_and_position:
            return

        try:
            general_alias, position = general_alias_and_position
        except ValueError as e:
            logging.warning(f"{command_name} error: {e}")
            return

        position_type = sd.str_to_position_type(position)

        if not position_type:
            try:
                position_numeric = int(position)
            except ValueError:
                position_numeric = None
    
        # Get the sprite that is currently visible
        # based on the general alias.
        # We're not interested in spawning a new sprite, just the
        # sprite that is already visible.
        sprite = self.story.get_visible_sprite(content_type=sprite_type,
                                               general_alias=general_alias)
    
        if not sprite:
            return
    
        if command_name.endswith("_set_position_x"):
            if position_type:
                sprite.set_position_x(position_type=position_type)
            else:
                sprite.set_position_x(position_absolute_x=position_numeric)
    
        elif command_name.endswith("_set_position_y"):
            if position_type:
                sprite.set_position_y(position_type=position_type)
            else:
                sprite.set_position_y(position_absolute_y=position_numeric)

    def _sprite_center_x_with(self,
                              command_name: str,
                              arguments: str):
        """
        Center the X of the given sprite with the center x of another sprite.
        
        Syntax:
        <command: alias to move, type of sprite to align with, alias to center x with>
        
        Example:
        <character_center_x_with: theo, dialog sprite, some name here>
        <dialog_sprite_center_x_with: some dialog sprite name, character, theo>
        <object_center_x_with: my object name, character, theo>
        """

        name: sd.SpriteCenterWith
        name = self._get_arguments(class_namedtuple=sd.SpriteCenterWith,
                                   given_arguments=arguments)

        if not name:
            return
        
        # Get the type of sprite we need to move
        if "character" in command_name:
            sprite_type_to_move = file_reader.ContentType.CHARACTER
            
        elif "dialog" in command_name:
            sprite_type_to_move = file_reader.ContentType.DIALOG_SPRITE
            
        elif "object" in command_name:
            sprite_type_to_move = file_reader.ContentType.OBJECT
        else:
            return
        
        # Get the type of sprite we need to center with
        if "character" in name.sprite_type_to_center_with:
            sprite_type_center_with = file_reader.ContentType.CHARACTER
            
        elif "dialog" in name.sprite_type_to_center_with:
            sprite_type_center_with = file_reader.ContentType.DIALOG_SPRITE
            
        elif "object" in name.sprite_type_to_center_with:
            sprite_type_center_with = file_reader.ContentType.OBJECT
            
        else:
            return
        
        # Get the sprite that we want to align with
        sprite_to_center_with =\
            self.story.get_visible_sprite(content_type=sprite_type_center_with,
                                          general_alias=name.center_with_alias)
        if not sprite_to_center_with:
            return
    
        # Get the sprite that we want to move
        sprite_to_move =\
            self.story.get_visible_sprite(content_type=sprite_type_to_move,
                                          general_alias=name.alias_to_move)
        
        if not sprite_to_move:
            return

        before_move_rect = sprite_to_move.rect.copy()
        sprite_to_move.rect.centerx = sprite_to_center_with.rect.centerx
        after_move_rect = sprite_to_move.rect.copy()
        
        # Queue the rects for a manual screen update.
        # Regular animations (such as <character_start_moving: rave>)
        # are updated automatically, but since this is a manual animation,
        # we need to queue it for updating here.
        active_story.ManualUpdate.queue_for_update(before_move_rect)        
        active_story.ManualUpdate.queue_for_update(after_move_rect) 

    def on_dialog_rectangle_animation_completed(self,
                                                final_dest_rect: pygame.Rect,
                                                run_reusable_script_name: str = None):
        """
        The intro or outro animation for the dialog rectangle has finished.
        Reset the 'animating' flag so that the main script can resume reading
        the script, because while the dialog animation was occuring, the main
        script was waiting for the dialog animation to finish.
        
        # Arguments:
        
        - final_dest_rect: the rect of where the dialog box finished
        animating. It includes the x and y locations in the rect.
        
        - run_reusable_script_name: if this contains a value, we should run
        the specified reusable script. This will come from the dialog rectangle
        whenever an animation (intro or outro) finishes animating, if the user
        has specified to run a reusable script.
        """
        self.animating_dialog_rectangle = False
        
        if self.story.dialog_rectangle.animating_intro:
            self.story.dialog_rectangle.animating_intro = False
            
        elif self.story.dialog_rectangle.animating_outro:
            self.story.dialog_rectangle.animating_outro = False

            # The dialog rectangle has closed, so hide all
            # dialog-related sprites.
            active_story.Groups.dialog_group.hide_all()

        # Now that the animation has finished for the dialog rect, record
        # the dialog's rect so when we add letters to the dialog, we won't
        # need to call .get_rect() for each letter being added.
        self.story.dialog_rectangle_rect = final_dest_rect.copy()

        # Run a reusable script for when the animation has stopped?
        if run_reusable_script_name:
            self.spawn_new_background_reader\
                (reusable_script_name=run_reusable_script_name)

    def _sprite_set_center(self,
                           sprite_type: file_reader.ContentType,
                           arguments: str):
        """
        Set the center point of the sprite's rect.
        
        :param arguments: (str) sprite general alias, x position, y position
        :return: None
        """

        scale_center: sd.SpriteCenter
        scale_center = self._get_arguments(class_namedtuple=sd.SpriteCenter,
                                           given_arguments=arguments)

        if not scale_center:
            return

        # Get the active character sprite
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=scale_center.sprite_name)

        if not sprite:
            return        

        # Center the sprite to the specified coordinates.
        sprite.set_center(center_x=scale_center.x, center_y=scale_center.y)
        
    def elapse_halt_timer(self):
        """
        If we're in automated halt mode, elapse the wait counter
        until the required number of frames have elapsed.
        """
        
        # Get the story reader that's not a reusable script reader,
        # because everything in this method involves the main reader only.
        main_reader = self.get_main_story_reader()           
        
        if main_reader.halt_main_script_auto_mode_frames:
            # We're in auto-halt mode
            
            # Have we reached the number of frames that we need to wait?
            if main_reader.halt_main_script_frame_counter >= main_reader.halt_main_script_auto_mode_frames:
                
                # Yes, we've reached the amount needed to wait.

                # Now we can reset the counter and unhalt the story.
                main_reader.halt_main_script_auto_mode_frames = 0
                main_reader.halt_main_script_frame_counter = 0
                main_reader.unhalt()
                
            else:
                # No, we still need to halt the story.
                

                # If the dialog text is still being animated
                # (ie: fading in, or being shown letter-by-letter),
                # then don't increment the halt counter until all the 
                # dialog letters have finished being displayed.
                # Reason: if we don't have this check, halt_auto's counter might
                # finish before all the letters have finished being displayed.
                if main_reader.active_font_handler.font_animation.is_start_animating:
                    return
                
                # Increment the frame counter
                main_reader.halt_main_script_frame_counter += 1

    def halt(self, automate_after_frame_count: int = 0):
        """
        Pause the reading of the main script
        until the user clicks the mouse.
        
        Arguments:
        
        - automate_after_frame_count: if specified (>0), it will be considered
        an automatic halt, which means that the keyboard and mouse won't
        progress the story. Instead X number of frames must elapse first,
        and then the story will unhalt automatically.
        """
        
        # Get the story reader that's not a reusable script reader,
        # because everything in this method involves the main reader only.
        main_reader = self.get_main_story_reader()        
        
        # Is the story already halted? return so we don't
        # re-run the font animation for no reason.
        if main_reader.halt_main_script:
            return
        
        # No dialog rectangle defined in the story yet?
        # No point in using halt.
        if not main_reader.story.dialog_rectangle:
            return

        # A regular halt flag
        main_reader.halt_main_script = True
        
        # Automated halt flag (if > 0)
        main_reader.halt_main_script_auto_mode_frames = automate_after_frame_count

        # So <continue> can't be used after using the <halt> command.
        main_reader.active_font_handler.next_letter_x_position_continue = None
        main_reader.active_font_handler.next_letter_y_position_continue = None
        main_reader.active_font_handler.adjusted_y = 0

        if main_reader.story.dialog_rectangle.visible:        

            # Start the animation of the dialog text.
            main_reader.story.reader.active_font_handler.\
                font_animation.start_show_animation(letters=main_reader.active_font_handler.letters_to_blit)

    def go_faster_text_mode(self) -> bool:
        """
        Set a flag to make the text show as fast as it can.
        
        Purpose: when the user wants to progress through the text quickly.
        
        Return True if the dialog text is now sped up.
        
        Return False if the dialog text is not currently being gradually
        shown, so it can't be sped up.
        """

        # Get the FontAnimation object from the main reader
        
        # because if we're in a reusable script, it won't
        # have a FontAnimation object.
        font_animation =\
            self.get_main_story_reader().active_font_handler.font_animation

        # This will be True if the dialog text is being animated.
        if font_animation.is_start_animating:
            
            # The dialog text is being animated/shown, so speed it up.
            font_animation.faster_text_mode = True

            # So the caller can know that the text has been sped up.
            return True
        
        return False
        
    def unhalt(self):
        """
        Unhalt the main script reader.
        """
        
        # Get the story reader that's not a reusable script reader,
        # because everything in this method involves the main reader only.
        main_reader = self.get_main_story_reader()
        
        main_reader.halt_main_script = False

        # Clear the fade-in intro animation, if any.
        main_reader.active_font_handler.font_animation.stop_intro_animation()

        # Clear the current letter list because we should make way for
        # other dialog text.
        main_reader.active_font_handler.clear_letters()

        # Re-draw the dialog rectangle shape so that any previous text
        # gets blitted over with the new rectangle.
        main_reader.story.dialog_rectangle.clear_text()
               

    def _continue(self, arguments: str):
        """
        Restore the X and Y positions of the text 'cursor'.
        
        Purpose: to continue showing the text on the last-displayed line
        in the dialog rectangle instead of showing text on a new line.
        
        Argument:
        
        - The amount to change the Y coordinate. For example, a value of -10
        means to minus 10 the current Y coordinate of the text.
        Example: <continue: -10>
        
        The purpose of wanting to continue at a different Y position is if
        the font has changed and the new font's height is different than
        the text before it. So for example: you can use <continue: -10>
        to position the new text slightly higher than the previous text.
        
        The <continue> command can be used with or without an argument.
        """
        adjust_y = None

        # Is there an argument?
        if arguments:
            adjust_y: Continue
            adjust_y = self._get_arguments(class_namedtuple=Continue,
                                           given_arguments=arguments)

        if not adjust_y:
            # No argument, default to a custom Y adjustment of 0
            custom_y_adjustment = 0
        else:
            custom_y_adjustment = adjust_y.adjust_y

        if self.active_font_handler.next_letter_x_position_continue is not None:
            # Restore the X position of the text 'cursor'
            
            self.active_font_handler.next_letter_x_position =\
                self.active_font_handler.next_letter_x_position_continue
            
            self.active_font_handler.next_letter_x_position_continue = None

        if self.active_font_handler.next_letter_y_position_continue is not None:
            # Restore the Y position of the text 'cursor'

            # Record the adjusted Y coordinate by the <continue> command
            # so after we reach the next line, we can reset it back to its
            # original Y coordinate.
            self.active_font_handler.adjusted_y = custom_y_adjustment
            
            # New Y coordinate because we just used the <continue> command.
            self.active_font_handler.next_letter_y_position = \
                self.active_font_handler.next_letter_y_position_continue + custom_y_adjustment

            # We're done adjusting the Y coordinate to its new position.
            self.active_font_handler.next_letter_y_position_continue = None

    def _font_intro_animation(self, arguments):
        """
        Set the intro animation of the current active font sprite sheet.
        This will be the animation style to use when showing dialog text.
        """
        animation_type: FontIntroAnimation
        animation_type =\
            self._get_arguments(class_namedtuple=FontIntroAnimation,
                                given_arguments=arguments)

        if not animation_type:
            return

        # This will always been initialized to something, it won't be None.
        self.get_main_story_reader().active_font_handler.font_animation.start_animation_type =\
            dialog_rectangle.to_enum(cls=font_handler.FontAnimationShowingType,
                                     string_representation=animation_type.animation_type)

    def _sprite_rotate_current_value(self,
                                     sprite_type: file_reader.ContentType,
                                     arguments):
        """
        Immediately set a sprite's rotation value (no gradual animation).
        Example of value: 90  (90 means 90 degree angle)

        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from.
        - arguments: sprite general alias, rotation value
        
        return: None
        """

        rotate_current_value: sd.RotateCurrentValue
        rotate_current_value = self._get_arguments(class_namedtuple=sd.RotateCurrentValue,
                                                   given_arguments=arguments)

        if not rotate_current_value:
            return

        # Get the visible sprite
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=rotate_current_value.sprite_name)

        if not sprite:
            return

        # Set the rotation value of the sprite (immediate, no gradual animation).
        sprite.rotate_current_value = rotate_current_value

        sprite.sudden_rotate_change = True

    def _sprite_rotate_until(self,
                             sprite_type: file_reader.ContentType,
                             arguments):
        """
        Set when to stop rotating a sprite.
        Example: 90  (90 means when the sprite reaches a 90-degree angle)
        
        If the rotation value is a negative number, such as -1, it will
        cause the rotation to occur continuously without stopping, by setting
        the .rotate_until variable to None.

        Arguments:
         - sprite_type: so we can know which dictionary to get the sprite from.
         - arguments: sprite general alias, angle (float)
         
        Return: None
        """

        rotate_until: sd.RotateUntil
        rotate_until = self._get_arguments(class_namedtuple=sd.RotateUntil,
                                           given_arguments=arguments)

        if not rotate_until:
            return

        # Get the visible sprite
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=rotate_until.sprite_name)

        if not sprite:
            return

        # Rotate continuously?
        # if isinstance(rotate_until, int) and rotate_until < 0:
        if rotate_until.rotate_until.lower() == "forever":
            # Rotate continuously.
            sprite.rotate_until = None
        else:
            
            # Attempt to convert the rotate_until to a float
            # because the rotate_until value is currently a str.
            try:
                rotate_float = float(rotate_until.rotate_until)
            except ValueError:
                return
            
            rotate_until = rotate_until._replace(rotate_until=rotate_float)

            # Set the property for the character sprite to know when to stop the rotating animation.
            sprite.rotate_until = rotate_until

    def _sprite_rotate_delay(self,
                             sprite_type: file_reader.ContentType,
                             arguments):
        """
        Specify the number of frames to skip for this sprite's rotate animation.
        This is used to create an extra-slow rotating effect.
        
        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from.
        - arguments: (str) sprite general alias, number of frames to skip (int)
        
        Return: None
        """

        rotate_delay: sd.RotateDelay
        rotate_delay = self._get_arguments(class_namedtuple=sd.RotateDelay,
                                           given_arguments=arguments)

        if not rotate_delay:
            return

        # Get the visible sprite
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=rotate_delay.sprite_name)

        if not sprite:
            return        

        # We use the object below because it's part of a class that keeps
        # track of the number of frames skipped.
        rotate_delay_main = sd.RotateDelayMain(rotate_delay=rotate_delay)

        # Set the property for the sprite so when the rotate animation
        # is working, it'll read this variable value and delay the rotate effect.
        sprite.rotate_delay_main = rotate_delay_main

    def _sprite_rotate_speed(self,
                             sprite_type: file_reader.ContentType,
                             arguments):
        """
        Set the rotation speed of a sprite.
        Example: 0.50
        A positive value will rotate the sprite counterclockwise.
        A negative value (such as -0.50) will rotate the sprite clockwise.

        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from.
        - arguments: sprite general alias, rotation speed, rotation direction
        
        Return: None
        """

        rotate_speed: sd.RotateSpeed
        rotate_speed = self._get_arguments(class_namedtuple=sd.RotateSpeed,
                                           given_arguments=arguments)

        if not rotate_speed:
            return

        # Get the visible character sprite
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=rotate_speed.sprite_name)

        if not sprite:
            return        

        # Convert the user-provided percent value speed (1 to 100)
        # from sprite.rotate_speed to a float that pygame can use.
        # Depending on the rotation direction, the float will either be a positive
        # float or a negative float.
        rotate_float_value = self._sprite_rotate_speed_get_value_from_percent(
            rotate_speed.rotate_speed, rotate_speed.rotate_direction)

        # Make sure we have a float value, otherwise stop here.
        if not rotate_float_value:
            return
        
        # Use the new float value instead of the convenience value.
        rotate_speed = sd.RotateSpeed(rotate_speed.sprite_name,
                                      rotate_float_value,
                                      rotate_speed.rotate_direction)

        # Set the property for the sprite to know how fast
        # (or slow) the rotation animation should occur, 
        # and also which direction the rotate should occur.
        sprite.rotate_speed = rotate_speed

    def _sprite_after_rotating_stop(self,
                                    sprite_type: file_reader.ContentType,
                                    arguments):
        """
        When a specific sprite image stops rotating, run a specific reusable script.
        
        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from.
        - arguments: (str) sprite general alias, reusable script name
       
        return: None
        """

        rotate_stop_run_script: sd.RotateStopRunScript
        rotate_stop_run_script = self._get_arguments(class_namedtuple=sd.RotateStopRunScript,
                                                     given_arguments=arguments)

        if not rotate_stop_run_script:
            return

        # Get the visible sprite
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=rotate_stop_run_script.sprite_name)

        if not sprite:
            return        

        # Set the property for the character sprite so when the rotation stops, it'll read this variable value.
        sprite.rotate_stop_run_script = rotate_stop_run_script

    def _sprite_start_or_stop_rotating(self,
                                       sprite_type: file_reader.ContentType,
                                       arguments,
                                       start_or_stop: sd.StartOrStop):
        """
        Set the flag for the sprite object
        to indicate that rotating animations should start or stop.

        Arguments:
         - sprite_type: so we can know which dictionary to get the sprite from.
        
         - arguments: a str with the sprite's general alias (example: 'rave')
         
         - start_or_stop: whether we should start the animation
        or stop the animation. Based on extract_functions.StartOrStop
        
        Return: None
        """
        if arguments and isinstance(arguments, str):
            sprite_name = arguments.strip()

            # Get the visible character sprite
            sprite =\
                self.story.get_visible_sprite(content_type=sprite_type,
                                              general_alias=sprite_name)

            if not sprite:
                return

            if start_or_stop == sd.StartOrStop.START:

                # Initialize the RotateCurrentValue object, we need to have
                # it for the animation to work.
                if sprite.rotate_current_value is None:
                    sprite.rotate_current_value = \
                        sd.RotateCurrentValue(sprite_name=sprite_name,
                                              rotate_current_value=0)
                
                sprite.start_rotating()

            elif start_or_stop == sd.StartOrStop.STOP:
                sprite.stop_rotating()

    def _sprite_scale_delay(self,
                            sprite_type: file_reader.ContentType,
                            arguments):
        """
        Specify the number of frames to skip for this sprite's scaling animation.
        This is used to create an extra-slow scale effect.
        
        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from.
        - arguments: (str) sprite name, number of frames to skip (int)
        
        return: None
        """

        scale_delay: sd.ScaleDelay
        scale_delay = self._get_arguments(class_namedtuple=sd.ScaleDelay,
                                          given_arguments=arguments)

        if not scale_delay:
            return

        # Get the active sprite
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=scale_delay.sprite_name)

        if not sprite:
            return        

        # We use the object below because it's part of a class that keeps
        # track of the number of frames skipped.
        scale_delay_main = sd.ScaleDelayMain(scale_delay=scale_delay)

        # Set the property for the sprite so when the scaling animation
        # is working, it'll read this variable value and delay the scale effect.
        sprite.scale_delay_main = scale_delay_main

    def _sprite_start_or_stop_scaling(self,
                                      sprite_type: file_reader.ContentType,
                                      arguments,
                                      start_or_stop: sd.StartOrStop):
        """
        Set the flag for the sprite object to indicate
        that a scaling animation should start or stop.

        Arguments:
        
        - arguments: a str with the sprite's general alias (example: 'rave')
        
        - start_or_stop: whether we should start the animation
        or stop the animation. Based on extract_functions.StartOrStop
        
        Return: None
        """
        if arguments and isinstance(arguments, str):
            sprite_name = arguments.strip()

            # Get the active sprite using the general alias.
            sprite = self.story.get_visible_sprite(content_type=sprite_type,
                                                   general_alias=sprite_name)

            if not sprite:
                return

            if start_or_stop == sd.StartOrStop.START:
                
                # Initialize the ScaleCurrentValue object, we need to have
                # it for the animation to work.
                if sprite.scale_current_value is None:
                    sprite.scale_current_value = \
                        sd.ScaleCurrentValue(sprite_name=sprite_name,
                                             scale_current_value=0)
                
                sprite.start_scaling()

            elif start_or_stop == sd.StartOrStop.STOP:
                sprite.stop_scaling()

    def _sprite_after_scaling_stop(self,
                                   sprite_type: file_reader.ContentType,
                                   arguments):
        """
        When a specific sprite image stops scaling, run a specific reusable script.
        
        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from.
        - arguments: (str) sprite general alias, reusable script name
        
        return: None
        """

        scale_stop_run_script: sd.ScaleStopRunScript
        scale_stop_run_script = self._get_arguments(class_namedtuple=sd.ScaleStopRunScript,
                                                    given_arguments=arguments)

        if not scale_stop_run_script:
            return

        # Get the active sprite
        sprite = self.story.get_visible_sprite(content_type=sprite_type,
                                               general_alias=scale_stop_run_script.sprite_name)

        if not sprite:
            return        

        # Set the property for the sprite so when the scale stops, it'll read this variable value.
        sprite.scale_stop_run_script = scale_stop_run_script

    def _sprite_scale_current_value(self,
                                    sprite_type: file_reader.ContentType,
                                    arguments):
        """
        Immediately set a sprite's scale value (no gradual animation).
        Example of value: 2  (2 means twice as big as the original sprite)

        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from.
        - arguments: sprite name, scale value
        
        return: None
        """

        scale_current_value: sd.ScaleCurrentValue
        scale_current_value = self._get_arguments(class_namedtuple=sd.ScaleCurrentValue,
                                                  given_arguments=arguments)

        if not scale_current_value:
            return

        # Get the active/visible sprite
        sprite = self.story.get_visible_sprite(content_type=sprite_type,
                                               general_alias=scale_current_value.sprite_name)

        if not sprite:
            return        

        # Set the scale value of the sprite (immediate, no gradual animation).
        sprite.scale_current_value = scale_current_value

        sprite.sudden_scale_change = True

    def _sprite_scale_until(self,
                            sprite_type: file_reader.ContentType,
                            arguments):
        """
        Set when to stop scaling a sprite.
        Example: 2  (2 means twice as big as the original sprite)

        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from.
        - arguments: sprite name, scale until value
        
        return: None
        """

        scale_until: sd.ScaleUntil
        scale_until = self._get_arguments(class_namedtuple=sd.ScaleUntil,
                                          given_arguments=arguments)

        if not scale_until:
            return

        # Get the active sprite
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=scale_until.sprite_name)

        if not sprite:
            return        

        # Set the property for the sprite to know when to stop the scaling animation.
        sprite.scale_until = scale_until

    def _sprite_scale_by(self,
                         sprite_type: file_reader.ContentType,
                         arguments):
        """
        Set the scale speed of a sprite.
        Example: 0.00050  (2 means twice as big)
        A positive value will scale up the sprite. A negative value (such as -0.00050)
        will scale down a sprite.
        
        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from
        - arguments: sprite name, scale speed, scale direction
        
        return: None
        """

        scale_by: sd.ScaleBy
        scale_by = self._get_arguments(class_namedtuple=sd.ScaleBy,
                                       given_arguments=arguments)

        if not scale_by:
            return

        # Get the active sprite
        sprite = self.story.get_visible_sprite(content_type=sprite_type,
                                               general_alias=scale_by.sprite_name)
        
        if not sprite:
            return

        # Convert the user-provided percent value speed (1 to 100)
        # from scale_by.scale_by to a float that pygame can use.
        # Depending on the scale direction, the float will either be a positive
        # float or a negative float.
        scale_by_float_value = self._sprite_scale_by_get_value_from_percent(
            scale_by.scale_by, scale_by.scale_rotation)

        # Make sure we have a float value, otherwise stop here.
        if not scale_by_float_value:
            return

        # Use the new float value instead of the convenience value.
        scale_by = scale_by._replace(scale_by=scale_by_float_value)
        
        # Set the property for the sprite to know how fast
        # (or slow) the scale animation should occur.
        sprite.scale_by = scale_by

    def _sprite_start_or_stop_fading(self,
                                     sprite_type: file_reader.ContentType,
                                     arguments,
                                     start_or_stop: sd.StartOrStop):
        """
        Set the flag for the sprite object to indicate that a fading animation
        should start or stop.

        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from.
        
        - arguments: a str with the character general alias (example: 'rave')
    
        - start_or_stop: whether we should start the animation
        or stop the animation. Based on extract_functions.StartOrStop
        
        Return: None
        """
        if arguments and isinstance(arguments, str):
            sprite_name = arguments.strip()

            # Get the visible sprite
            sprite =\
                self.story.get_visible_sprite(content_type=sprite_type,
                                              general_alias=sprite_name)

            if not sprite:
                return

            if start_or_stop == sd.StartOrStop.START:
                sprite.start_fading()

            elif start_or_stop == sd.StartOrStop.STOP:
                sprite.stop_fading()

    def _sprite_fade_speed_get_value_from_percent(self, percent, fade_direction: str) -> float | None:
        """
        Take a percent value from 1 to 100 and convert it to a float
        that we can use for the fade speed in pygame.
        
        Purpose: the percentage 1-100 is only a convenience value for the user
        when using the editor. We need to take that percent value and
        convert it to something real that pygame can use.
        
        Arguments:
        
        - percent: the user-friendly value (between 1 and 100) that the editor
        has provided us which we need to convert to a float so that it makes
        sense for pygame.
        """

        if not fade_direction and not percent:
            return
        
        fade_direction = fade_direction.lower()
        if fade_direction not in ("fade in", "fade out"):
            return

        # The fade speed (slowest to fastest). There are 100 lines in the string.
        values = """0.01
0.03
0.05
0.07
0.09
0.11
0.13
0.15
0.17
0.19
0.44
0.69
0.94
1.19
1.44
1.69
1.94
2.19
2.44
2.59
2.74
2.89
3.04
3.19
3.34
3.49
3.64
3.79
3.94
4.09
4.19
4.29
4.39
4.49
4.59
4.69
4.79
4.89
4.99
5.09
5.19
5.21
5.23
5.25
5.27
5.29
5.31
5.33
5.35
5.37
5.42
5.47
5.52
5.57
5.62
5.67
5.72
5.77
5.82
5.87
5.97
6.07
6.17
6.27
6.37
6.47
6.57
6.67
6.77
6.87
6.89
6.91
6.93
6.95
6.97
6.99
7.01
7.03
7.05
7.13
7.21
7.29
7.37
7.45
7.53
7.61
7.69
7.77
7.85
7.93
8.18
8.43
8.68
8.93
9.18
12.00
19.00
30.00
45.00
60.00"""

        # Create a list from the values
        values = values.split()

        # Key: percent value (int) - 1 to 100
        # Value: float value that pygame needs
        percent_mapping = {}
        for counter, value in enumerate(values):
            percent_mapping[counter + 1] = float(value)

        percent_to_float = percent_mapping.get(percent)

        if fade_direction == "fade out":
            # Convert from a positive float to a negative float.
            # A negative float will cause a pygame to fade out the sprite.
            percent_to_float = -abs(percent_to_float)
        return percent_to_float

    def _sprite_rotate_speed_get_value_from_percent(self, percent, rotate_direction: str) -> float | None:
        """
        Take a percent value from 1 to 100 and convert it to a float
        that we can use for the rotation speed in pygame.
        
        Purpose: the percentage 1-100 is only a convenience value for the user
        when using the editor. We need to take that percent value and
        convert it to something real that pygame can use.
        
        Arguments:
        
        - percent: the user-friendly value (between 1 and 100) that the editor
        has provided us which we need to convert to a float so that it makes
        sense for pygame.
        """

        if not rotate_direction and not percent:
            return
        
        # Has to be between 1 and 100 %
        if percent > 100:
            percent = 100
        elif percent < 1:
            percent = 1
        
        fade_direction = rotate_direction.lower()
        if not rotate_direction in ("clockwise", "counterclockwise"):
            return

        # The rotation speed (slowest to fastest). There are 100 lines in the string.
        values = """0.02
0.07
0.12
0.17
0.22
0.27
0.32
0.37
0.42
0.47
0.52
0.57
0.62
0.67
0.72
0.77
0.82
0.87
0.92
0.97
1.02
1.07
1.12
1.17
1.22
1.27
1.32
1.37
1.42
1.47
1.52
1.57
1.62
1.67
1.72
1.77
1.82
1.87
1.92
1.97
2.02
2.07
2.12
2.17
2.22
2.27
2.32
2.37
2.42
2.47
2.52
2.57
2.62
2.67
2.72
2.77
2.82
2.87
2.92
2.97
3.02
3.07
3.12
3.17
3.22
3.27
3.32
3.37
3.42
3.47
3.52
3.57
3.62
3.67
3.72
3.77
3.82
3.87
3.92
3.97
4.02
4.07
4.12
4.17
4.22
4.27
4.32
4.37
4.42
4.47
4.72
4.97
5.22
5.47
5.92
6.37
6.82
8.27
10.72
20.17"""

        # Create a list from the values
        values = values.split()
        
        # Key: percent value (int) - 1 to 100
        # Value: float value that pygame needs
        percent_mapping = {}
        for counter, value in enumerate(values):
            percent_mapping[counter + 1] = float(value)

        percent_to_float = percent_mapping.get(percent)

        if rotate_direction == "clockwise":
            # A positive value will rotate the sprite counterclockwise.
            # A negative value(such as -0.50) will rotate the sprite clockwise.
            percent_to_float = -abs(percent_to_float)
        return percent_to_float

    def _sprite_scale_by_get_value_from_percent(self, percent, scale_direction: str) -> float | None:
        """
        Take a percent value from 1 to 100 and convert it to a float
        that we can use for the scale-by value in pygame.
        
        Purpose: the percentage 1-100 is only a convenience value for the user
        when using the editor. We need to take that percent value and
        convert it to something real that pygame can use.
        
        Arguments:
        
        - percent: the user-friendly value (between 1 and 100) that the editor
        has provided us which we need to convert to a float so that it makes
        sense for pygame.
        
        - scale_direction: (str) "scale up" or "scale down".
        Internally, a positive value will scale up the sprite.
        A negative value (such as -0.00050) will scale down a sprite.
        We use "scale up" and "scale down" in the editor for convenience.
        """

        if not scale_direction and not percent:
            return
        
        if percent > 100:
            percent = 100
        elif percent < 1:
            return
        
        scale_direction = scale_direction.lower()
        if not scale_direction in ("scale up", "scale down"):
            return

        # The scale speed (slowest to fastest). There are 100 lines in the string.
        values = """0.0001
0.0003
0.0005
0.0007
0.0009
0.0011
0.0013
0.0015
0.0017
0.0019
0.0021
0.0023
0.0025
0.0027
0.0029
0.0031
0.0033
0.0035
0.0037
0.0039
0.0041
0.0043
0.0045
0.0047
0.0049
0.0051
0.0053
0.0055
0.0057
0.0059
0.0061
0.0063
0.0065
0.0067
0.0069
0.0071
0.0073
0.0075
0.0077
0.0079
0.0081
0.0083
0.0085
0.0087
0.0089
0.0091
0.0093
0.0095
0.0097
0.0099
0.0101
0.0103
0.0105
0.0107
0.0109
0.0111
0.0113
0.0115
0.0117
0.0119
0.0121
0.0123
0.0125
0.0127
0.0129
0.0131
0.0133
0.0135
0.0137
0.0139
0.0141
0.0143
0.0145
0.0147
0.0149
0.0151
0.0153
0.0155
0.0157
0.0159
0.0161
0.0163
0.0165
0.0167
0.0169
0.0171
0.0173
0.0175
0.0177
0.0179
0.0194
0.0209
0.0224
0.0239
0.0259
0.0344
0.0429
0.0514
0.0599
0.0684
"""

        # Create a list from the values
        values = values.split()

        # Key: percent value (int) - 1 to 100
        # Value: float value that pygame needs
        percent_mapping = {}
        for counter, value in enumerate(values):
            percent_mapping[counter + 1] = float(value)

        percent_to_float = percent_mapping.get(percent)

        if scale_direction == "scale down":
            # A positive value will scale up the sprite.
            # A negative value(such as -0.00050) will scale down a sprite.
            percent_to_float = -abs(percent_to_float)
        return percent_to_float

    def _sprite_fade_speed(self,
                           sprite_type: file_reader.ContentType,
                           arguments):
        """
        Set the fade-speed of a sprite.
        Example: 0.05
        A positive value will fade-in the sprite. A negative value (such as -0.05)
        will fade out a sprite.

        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from.
        - arguments: sprite general alias, fade speed (example: 0.05 (fade in) or -0.05 (fade out))
        
        return: None
        """

        fade_speed: sd.FadeSpeed
        fade_speed = self._get_arguments(class_namedtuple=sd.FadeSpeed,
                                         given_arguments=arguments)

        if not fade_speed:
            return

        # Get the visible sprite based on the general alias
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=fade_speed.sprite_name)

        if not sprite:
            return
        
        # Convert the user-provided percent value speed (1 to 100)
        # from fade_speed.fade_speed to a float that pygame can use.
        # Depending on the fade direction, the float will either be a positive
        # float or a negative float.
        fade_float_value = self._sprite_fade_speed_get_value_from_percent(
            fade_speed.fade_speed, fade_speed.fade_direction)

        # Make sure we have a float value, otherwise stop here.
        if not fade_float_value:
            return

        # Use the new float value instead of the convenience value.
        fade_speed = sd.FadeSpeed(fade_speed.sprite_name,
                                  fade_float_value,
                                  fade_speed.fade_direction)

        # Initialize the FadeCurrentValue object, we need to have
        # it for the animation to work.
        if sprite.current_fade_value is None:

            # Since there is no current fade value for this sprite,
            # set it to either fully opaque or fully transparent
            # depending on the fade direction.

            # Without this, the user has to explicitly use <..fade_current_value:>
            # before fading a sprite.
            if fade_speed.fade_direction == "fade out":
                initial_fade_value = 255
            else:
                initial_fade_value = 0

            sprite.current_fade_value = \
                sd.FadeCurrentValue(sprite_name=fade_speed.sprite_name,
                                    current_fade_value=initial_fade_value)

        # Set the fade speed.
        # A positive value will fade-in the sprite.
        # A negative value (such as -0.05) will fade out the sprite.
        sprite.fade_speed = fade_speed

    def _sprite_current_fade_value(self,
                                   sprite_type: file_reader.ContentType,
                                   arguments):
        """
        Set the current fade value of a sprite (0 (fully transparent) to 255 (fully opaque)).

        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from.
        - arguments: sprite general alias, current fade value (example: 'rave_normal, 255')
        
        return: None
        """

        current_fade_value: sd.FadeCurrentValue
        current_fade_value = self._get_arguments(class_namedtuple=sd.FadeCurrentValue,
                                                 given_arguments=arguments)

        if not current_fade_value:
            return

        # Get the active/visible sprite based on the general alias
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=current_fade_value.sprite_name)

        if not sprite:
            return        

        # Set the current fade value for the character sprite.
        sprite.current_fade_value = current_fade_value

        # sprite.sudden_fade_change = True

    def _sprite_fade_until(self,
                           sprite_type: file_reader.ContentType,
                           arguments):
        """
        Set the property of a sprite to indicate that a fade animation should stop
        when it reaches a specific fade value (0 to 255).

        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from.
        - arguments: sprite general lias, fade value (example: 'rave, 255')
        
        return: None
        """

        fade_until: sd.FadeUntilValue
        fade_until = self._get_arguments(class_namedtuple=sd.FadeUntilValue,
                                         given_arguments=arguments)

        if not fade_until:
            return

        # Get the visible/active sprite
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=fade_until.sprite_name)

        if not sprite:
            return

        # Set the property for the sprite to know when a fade animation should stop.
        sprite.fade_until = fade_until

    def _sprite_fade_delay(self,
                           sprite_type: file_reader.ContentType,
                           arguments):
        """
        Specify the number of frames to skip for this sprite's fade animation.
        This is used to create an extra-slow fade effect.
        
        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from.
        - arguments: (str) sprite general alias, number of frames to skip (int)
        
        return: None
        """

        fade_delay: sd.FadeDelay
        fade_delay = self._get_arguments(class_namedtuple=sd.FadeDelay,
                                         given_arguments=arguments)

        if not fade_delay:
            return

        # Get the visible sprite based on the general alias
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=fade_delay.sprite_name)

        if not sprite:
            return        

        # We use the object below because it's part of a class that keeps
        # track of the number of frames skipped.
        fade_delay_main = sd.FadeDelayMain(fade_delay=fade_delay)

        # Set the property for the sprite so when the fading animation
        # is working, it'll read this variable value and delay the fade effect.
        sprite.fade_delay_main = fade_delay_main

    def _sprite_load(self, arguments, sprite_type: file_reader.ContentType):
        """
        Load a sprite image/sprite into memory and give it a general alias
        so it's ready to be displayed whenever it's needed.
        """

        sprite_name_and_alias: sd.SpriteLoad
        sprite_name_and_alias = \
            self._get_arguments(class_namedtuple=sd.SpriteLoad,
                                given_arguments=arguments)

        if not sprite_name_and_alias:
            return
        
        loaded_sprite = self.data_requester.get_sprite(content_type=sprite_type,
                                                       item_name=sprite_name_and_alias.sprite_name,
                                                       general_alias=sprite_name_and_alias.sprite_general_alias)
        
        if not loaded_sprite:
            return            

        if sprite_type == file_reader.ContentType.CHARACTER:
            sprite_group = sd.Groups.character_group
            
        elif sprite_type == file_reader.ContentType.OBJECT:
            sprite_group = sd.Groups.object_group
            
        elif sprite_type == file_reader.ContentType.BACKGROUND:
            sprite_group = sd.Groups.background_group
            
        elif sprite_type == file_reader.ContentType.DIALOG_SPRITE:
            sprite_group = sd.Groups.dialog_group

        else:
            return
            
        sprite_group.add(sprite_name_and_alias.sprite_name,
                         loaded_sprite)

    def _sprite_after_fading_stop(self,
                                  sprite_type: file_reader.ContentType,
                                  arguments):
        """
        When a specific sprite image stops fading, run a specific reusable script.
        
        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from.
        - arguments: (str) general alias, reusable script name
        
        return: None
        """

        fade_stop_run_script: sd.FadeStopRunScript
        fade_stop_run_script = self._get_arguments(class_namedtuple=sd.FadeStopRunScript,
                                                   given_arguments=arguments)

        if not fade_stop_run_script:
            return

        # Get the visible sprite
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=fade_stop_run_script.sprite_name)

        if not sprite:
            return        

        # Set the property for the sprite so when the fade stops, it'll read this variable value.
        sprite.fade_stop_run_script = fade_stop_run_script

    def _sprite_after_movement_stop(self,
                                    sprite_type: file_reader.ContentType,
                                    arguments):
        """
        When a specific sprite image stops moving, run a specific reusable script.
        
        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from.
        - arguments: (str) sprite name, reusable script name
        
        return: None
        """

        movement_stop_run_script: sd.MovementStopRunScript
        movement_stop_run_script = self._get_arguments(class_namedtuple=sd.MovementStopRunScript,
                                                       given_arguments=arguments)

        if not movement_stop_run_script:
            return

        # Get the sprite
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=movement_stop_run_script.sprite_name)
        
        if not sprite:
            logging.warning(f"Sprite ({movement_stop_run_script.sprite_name}) could not be loaded.")
            return

        # Set the property for the sprite so when the movement stops, it'll read this variable value.
        sprite.movement_stop_run_script = movement_stop_run_script

    def after_run(self, arguments):
        """
        Run a reusable script after X number of frames has elapsed.
        Example: <after: 30 (frames), reusable script here>
        """

        after_timer: After
        after_timer =\
            self._get_arguments(class_namedtuple=After,
                                given_arguments=arguments)


        # Use the after manager of the main reader if we're currently
        # in a background reader.
        after_manager_method = self._get_after_manager()

        # Create a timer to run the specific reusable script.
        after_manager_method.add_timer(reusable_script_name=after_timer.reusable_script,
                                       frames_to_skip=after_timer.frames_elapse)
        
    def after_cancel(self, arguments):
        """
        Cancel an existing 'after' timer.
        Example: <after_cancel: reusable script here>
        
        After timers are known by the reusable script name that they're
        supposed to end up running and only 1 of each reusable script
        can be added to a timer. So we can use the reusable script name
        to cancel a timer.
        """

        after_cancel: AfterCancel
        after_cancel =\
            self._get_arguments(class_namedtuple=AfterCancel,
                                given_arguments=arguments)
        

        # Use the after manager of the main reader if we're currently
        # in a background reader.
        after_manager_method = self._get_after_manager()

        # Remove the timer with the name that matches the
        # specified reusable script name. If the name doesn't exist,
        # it won't raise an exception.
        after_manager_method.remove_timer(reusable_script_name=after_cancel.reusable_script)

    def after_cancel_all(self):
        """
        Cancel all after timers.
        """
        
        # Use the after manager of the main reader if we're currently
        # in a background reader.
        after_manager_method = self._get_after_manager()

        # Cancel all after timers.
        after_manager_method.remove_all_timers()

    def _get_after_manager(self) -> AfterManager:
        """
        Return the main story reader's After Manager object.
        
        After timers are only available to the main reader,
        not background readers, so we use this method to always
        return the main story reader's After Manager object.
        """

        # Use the after manager of the main reader if we're currently
        # in a background reader.
        if self.background_reader_name:

            # Use the main reader's after manager.
            after_manager_method = self.story.reader.after_manager
        else:
            # We're already in the main reader.
            after_manager_method = self.after_manager
            
        return after_manager_method

    def spawn_new_background_reader(self, reusable_script_name):
        """
        Create a new background reader.
        :param reusable_script_name: (str) the case-sensitive name of the reusable script we should load.
        :return: None
        """

        # If a reusable script is calling another reusable script, spawn the new background reader
        # from the main story reader, not from the background reader that requested the reusable script.
        # That way, all the background readers will be tied to the main story reader.
        if self.background_reader_name:
            # Load the reusable script from the main story reader.
            self.story.reader.spawn_new_background_reader(reusable_script_name=reusable_script_name)
            return

        # Is the requested reusable script already loaded and running? Don't allow another one.
        elif reusable_script_name in self.background_readers:
            return

        script = self._get_reusable_script(reusable_script_name=reusable_script_name)

        if not script:
            return

        # Instantiate a new background reader
        reader = StoryReader(story=self.story,
                             data_requester=self.data_requester,
                             background_reader_name=reusable_script_name)

        reader.script_lines = script.splitlines()

        # Add the background reader to the main dictionary that holds the background readers.
        self.background_readers[reusable_script_name] = reader

        # Start reading the new background reusable script.
        reader.read_story()
        
    def spawn_new_reader(self, arguments):
        """
        Create a new regular (foreground) reader.
        This will replace the current main story reader.
        
        Purpose: used with the <scene> command.
        
        Arguments:
        
        - Arguments: chapter_name: the case-sensitive name of the chapter that the
        scene is in and case-sensitive name of the scene we should load.

        :return: None
        """
        
        load_scene: SceneLoad
        load_scene =\
            self._get_arguments(class_namedtuple=SceneLoad,
                                given_arguments=arguments)

        chapter_name = load_scene.chapter_name
        scene_name = load_scene.scene_name

        # Make sure the given chapter name exists.
        
        # {chapter name: [chapter script, {scene name: scene script}] }
        chapters = self.chapters_and_scenes.get(chapter_name)
        if not chapters:
            return

        # Make sure the given scene name exists.
        if scene_name not in chapters[1]:
            return

        # {chapter_name: scene_name}
        # When StoryReader() instantiates, it will look at the startup
        # script and will load it automatically.
        Passer.manual_startup_chapter_scene = {chapter_name: scene_name}
        

        self.story.reader = StoryReader(story=self.story.reader.story,
                                        data_requester=self.story.data_requester,
                                        background_reader_name=None)

        # Start reading the new scene script.
        self.story.reader.read_story()


    def _set_movement_delay(self,
                            sprite_type: file_reader.ContentType,
                            arguments: str):
        """
        Set the animation movement delay of the specified sprite.
        :param arguments: str, such as '3, 5' (which means delay x by 3 frames, delay y by 5 frames.
        :return: None
        """
        movement_delay: sd.MovementDelay
        movement_delay = self._get_arguments(class_namedtuple=sd.MovementDelay,
                                             given_arguments=arguments)

        if not movement_delay:
            return

        # Get the visible sprite
        sprite = self.story.get_visible_sprite(content_type=sprite_type,
                                               general_alias=movement_delay.sprite_name)

        if not sprite:
            return        

        # Stamp the delay onto the sprite.
        sprite.movement_delay = movement_delay

    def _sprite_start_or_stop_moving(self,
                                     sprite_type: file_reader.ContentType,
                                     arguments,
                                     start_or_stop: sd.StartOrStop):
        """
        Set the flag for the sprite object to indicate that
        a movement animation should start or stop.

        Arguments:
        - arguments: a str with the sprite's general alias name (example: 'rave')
        
        - start_or_stop: whether we should start the animation
        or stop the animation. Based on extract_functions.StartOrStop
        
        :return: None
        """
        if arguments and isinstance(arguments, str):
            sprite_name = arguments.strip()

            # Get the visible sprite
            sprite =\
                self.story.get_visible_sprite(content_type=sprite_type,
                                              general_alias=sprite_name)

            if not sprite:
                return

            if start_or_stop == sd.StartOrStop.START:
                sprite.start_moving()

            elif start_or_stop == sd.StartOrStop.STOP:
                # The user wants to stop moving this object.
                sprite.stop_moving()
                
                # When a sprite is manually stopped, stop conditions
                # don't apply, so clear the stop condition here (if any).
                sprite.movement_stop_run_script = None

    def _set_movement_speed(self,
                            sprite_type: file_reader.ContentType,
                            arguments: str):
        """
        Set the movement speed of the character sprite.

        :param arguments: str that looks like this: 'character sprite general alias, x, x_direction, y, y_direction'
                          character sprite name: the name of the sprite
                          x value is the number of pixels to move horizontally
                          x_direction is a string ("left" or "right")
                          y value is the number of pixels to move vertically
                          y_direction is a string ("up" or "down")
        :return: None
        """

        movement_speed: sd.MovementSpeed
        movement_speed = self._get_arguments(class_namedtuple=sd.MovementSpeed,
                                             given_arguments=arguments)

        if not movement_speed:
            return
        

        """
        This command internally moves a sprite left when X is a negative
        int and it moves a sprite down when Y is a negative int.
        
        In the editor, we use "left" and "up" to make it easier to read.
        So convert the editor-convenient "left" and "up" values to
        a negative int.
        """
        # Horizontal direction going left? Set the X to a negative int.
        if movement_speed.x_direction.lower() == "left":
            movement_speed = movement_speed._replace(x=-abs(movement_speed.x))

        # Vertical direction going up? Set the Y to a negative int.
        if movement_speed.y_direction.lower() == "up":
            movement_speed = movement_speed._replace(y=-abs(movement_speed.y))

        # Get the visible sprite
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=movement_speed.sprite_name)

        if not sprite:
            return        

        # Stamp the speed onto the sprite.
        sprite.movement_speed = movement_speed

    @staticmethod
    def _get_arguments(class_namedtuple, given_arguments: str):
        """
        Take the given string arguments (comma separated) and turn them
        into a namedtuple class.

        For example: if 'given_arguments' contains '5, 4'
        then this method will return an object in the given class in 'class_namedtuple'.
        That object may be something like: MovementSpeed and its fields, X and Y will be set
        to int (based on the arguments example '5, 4').

        For example; MovementSpeed.x = 5 (int)  , MovementSpeed.y = 4 (int)

        This method will convert numeric types to int and will keep string types as strings.
        For example, if the given argument is: 'Bob, 100' (str argument), then 'Bob' will end up becoming a field
        in the class object as a string, and 100 will be another field as an integer.
        This method will handle int types and str types automatically by making the class object fields match
        the expected type of variable.

        :param class_namedtuple: the class to use when returning an object in this method.
                                 One example of a class is: MovementSpeed
        :param given_arguments: string-based argument separated by commas. For example: '5, 4' or 'Bob, 100'.
        :return: an object based on the class provided in 'class_namedtuple'.
        """
        
        # Get a tuple of types that the type-hint has for the given fields of the class.
        # We'll use this to find out what type of variables each argument field needs to be.
        expected_argument_types = tuple(class_namedtuple.__annotations__.values())

        # Create a regex pattern to extract the correct number of arguments. The expected number of arguments
        # will be dictated by the number of fields in the given class: len(class._fields).
        field_count = len(class_namedtuple._fields)
        pattern = ""
        adder = r",([^,]*)"
        pattern += adder * field_count
        pattern = pattern.removeprefix(",")
        pattern += "$"
        pattern = "^" + pattern

        results = search(pattern=pattern,
                         string=given_arguments)

        if not results:
            return

        # Get the individual arguments as a tuple.
        # Example: ('5', '4')
        individual_arguments = results.groups()

        # This list will contain the individual arguments in their appropriate type
        # If it's a numeric argument, it will be added to this list as an int.
        # If it's a str argument, it will be added to this list as a str.
        converted_arguments = []

        # Combine the expected type (ie: class 'int') with each individual argument value (ie: '5')
        for expected_type, argument_value in zip(expected_argument_types, individual_arguments):
            argument_value = argument_value.strip()

            if expected_type is str:
                converted_arguments.append(argument_value)

            # elif expected_type is int or expected_type is float:
            elif any(expected_type is item for item in [int, float]):
                try:
                    converted_arguments.append(expected_type(argument_value))
                except ValueError:
                    return

        # Convert the list of arguments to a namedtuple for easier access by the caller.
        generate_class = class_namedtuple(*converted_arguments)

        return generate_class

    def _font_text_fade_speed(self, arguments):
        """
        Set the gradual text fade speed of the dialog text.
        It applies to both letter by letter fade-in and overall fade-in.
        
        Arguments:
        
        - arguments: an int between 1 and 10.
        1 is the slowest speed, 10 is the fastest speed.
        """

        fade_speed: FontTextFadeSpeed
        fade_speed =\
            self._get_arguments(class_namedtuple=FontTextFadeSpeed,
                                given_arguments=arguments)

        fade_speed = fade_speed.fade_speed

        # Don't allow the speed to be less than 1 or more than 10
        if fade_speed > 10:
            fade_speed = 10
        elif fade_speed < 1:
            fade_speed = 1
        
        self.get_main_story_reader().\
            active_font_handler.font_animation.font_text_fade_speed = fade_speed

    def _font_text_delay_punc(self, arguments):
        """
        Set the number of frames to skip *after* a specific letter has
        finished being blitted.
        
        Arguments:
        
        - arguments: an int between 0 and 150.
        For example: a value of 2 means: apply the letter by letter animation
        every 2 frames. A value of 0 means apply the animation at every frame.
        """

        delay_punc: FontTextDelayPunc
        delay_punc =\
            self._get_arguments(class_namedtuple=FontTextDelayPunc,
                                given_arguments=arguments)

        previous_letter = delay_punc.previous_letter
        delay_frame_count = delay_punc.number_of_frames

        # Don't allow the speed to be less than 0 or more than 150
        if delay_frame_count > 150:
            delay_frame_count = 150
        elif delay_frame_count < 0:
            delay_frame_count = 0
            
        # Add the after-previous-letter delay setting.
        self.get_main_story_reader().\
            active_font_handler.font_animation.\
            set_letter_delay(previous_letter, delay_frame_count)

    def get_main_story_reader(self):
        """
        Return the only reader object that is not a reusable script reader.
        
        Purpose: there are some methods that only exist in the main story
        reader, such as 'active_font_handler'. So we use this to access
        the main story reader.
        """

        # Is this method being called from a reusable script?
        if self.background_reader_name:
            
            # We're in a reusable script, so get the story's main reader.
            reader = self.story.reader
        else:
            # We are already in the main reader.
            reader = self

        return reader

    def _font_text_delay(self, arguments):
        """
        Set the number of frames to skip when animating letter-by-letter dialog text.
        Does not apply to letter fade-ins.
        
        Arguments:
        
        - arguments: an int between 0 and 600.
        For example: a value of 2 means: apply the letter by letter animation
        every 2 frames. A value of 0 means apply the animation at every frame.
        """

        text_speed_delay: FontTextDelay
        text_speed_delay =\
            self._get_arguments(class_namedtuple=FontTextDelay,
                                given_arguments=arguments)
        
        text_speed_delay = text_speed_delay.number_of_frames

        # Don't allow the speed to be less than 0 or more than 600
        # 600 means 10 seconds (60 frames X 10).
        if text_speed_delay > 600:
            text_speed_delay = 600
        elif text_speed_delay < 0:
            text_speed_delay = 0

        # Record the delay value
        self.active_font_handler.font_animation.font_text_delay = text_speed_delay
        
        # For the initial text frame, consider the text delay limit having been reached,
        # so that the delay doesn't occur before the first letter has been shown.
        # Without this, the text delay will apply before the first letter has been shown.
        self.active_font_handler.font_animation.gradual_delay_counter = text_speed_delay

    def _font_start_position(self, x: bool, arguments: str):
        """
        Set the X or Y starting position of the active font, relative
        to the dialog rectangle. The default is 0.
        
        Arguments:
        
        - x: (bool) True if setting the text position for X
        False if setting the text position for Y
        
        - arguments: this is expected to contain a numeric string value
        for the starting position of either X or Y, relative to the active
        dialog rectangle.
        """
        
        start_position: FontStartPosition
        start_position = self._get_arguments(class_namedtuple=FontStartPosition,
                                             given_arguments=arguments)

        if not start_position:
            return

        # Should we set the text start position for X or Y?
        if x:
            self.get_main_story_reader().active_font_handler.default_x_position =\
                start_position.start_position
        else:
            self.get_main_story_reader().active_font_handler.default_y_position =\
                start_position.start_position

    def _play_audio(self, arguments: str, audio_channel: AudioChannel):
        """
        Play an audio file through the appropriate channel.
        
        If the command is <play_music>, check if the music should be looped.
        """
        
        loop_music = False
        audio_name = None
        
        # If it's a play_music command and there's a second argument,
        # check if the song needs to be looped.
        
        # <play_music: name, loop>
        if audio_channel == AudioChannel.MUSIC and arguments.count(",") == 1:
            
            # <play_music: name, loop>
            audio_name, loop_music = self._split_arguments_to_tuple(arguments=arguments)
            
            # Only allow the string, "loop", as an argument for looping.
            if loop_music.lower() != "loop" or not audio_name:
                return
            
            loop_music = True
          
        else:
            # We're playing an audio file or a music file with no loop.
            
            play_audio: PlayAudio
            play_audio = self._get_arguments(class_namedtuple=PlayAudio,
                                             given_arguments=arguments)
    
            if not play_audio:
                return
            
            audio_name = play_audio.audio_name

        # Play the music or audio.
        self.story.audio_player.play_audio(audio_name=audio_name,
                                           audio_channel=audio_channel,
                                           loop_music=loop_music)

    def _halt_auto(self, arguments: str):
        """
        Use a timed <halt> command which is like a normal <halt> command
        but will not respond to mouse clicks or keyboard presses
        until X number of frames has passed.
        
        Arguments:

        - arguments: this is the number of frames to elapse while halting.
        
        Return: None
        """
        halt_auto: HaltAuto
        halt_auto = self._get_arguments(class_namedtuple=HaltAuto,
                                        given_arguments=arguments)

        if not halt_auto:
            return

        # Make sure the number of frames is an integer.
        try:
            frames_to_elapse = int(halt_auto.number_of_frames)
        except ValueError:
            return
        else:
            # Don't allow zero or a negative value.
            if frames_to_elapse <= 0:
                return
        
        self.halt(automate_after_frame_count=frames_to_elapse)

    def _no_clear(self):
        
        main_reader = self.get_main_story_reader()
        main_reader.active_font_handler.font_animation.no_clear_handler.\
            pass_clearing_next_halt = True

    def _rest(self, arguments: str):
        """
        Pause the main story reader for X number of frames.
        This is similar to <halt> except it's not interactive (mouse-clicking)
        will not unrest it.
    
        It's different from <halt_auto> in that <rest> doesn't depend
        on dialog text. It can rest without a dialog rectangle, whereas
        <halt_auto> requires a dialog rectangle to be visible.
        
        It forces the main reader to pause. It has
        no effect on background readers.
        """
        rest: Rest
        rest = self._get_arguments(class_namedtuple=Rest,
                                   given_arguments=arguments)

        if not rest:
            return

        # Make sure the number of frames is an integer.
        try:
            frames_to_elapse = int(rest.number_of_frames)
        except ValueError:
            return
        else:
            # Don't allow zero or a negative value.
            if frames_to_elapse <= 0:
                return
        
        # Get the story reader that's not a reusable script reader,
        # because everything in this method involves the main reader only.
        main_reader = self.get_main_story_reader()

        main_reader.rest_handler.setup(frames_reach=frames_to_elapse)

    def _wait_for_animation(self, arguments: str):
        """
        Pause the main story reader until a specific animation has finished.
        This is similar to <halt> except it's not interactive (mouse-clicking)
        will not resume it.

        It forces the main reader to pause. It has no effect on background readers.
        """
        wait: WaitForAnimation
        wait = self._get_arguments(class_namedtuple=WaitForAnimation,
                                   given_arguments=arguments)

        if not wait:
            return

        # Get the story reader that's not a reusable script reader,
        # because everything in this method involves the main reader only.
        main_reader = self.get_main_story_reader()

        main_reader.wait_for_animation_handler.enable_wait_for(sprite_type=wait.sprite_type,
                                                               general_alias=wait.general_alias,
                                                               animation_type=wait.animation_type)

    def _sprite_hide(self,
                     arguments: str,
                     sprite_type: file_reader.ContentType):
        """
        Hide a sprite (any sprite, such as character, name)
        by setting its visibility to False.
        
        Find the sprite using its general alias.
        """
        name: sd.SpriteShowHide
        name = self._get_arguments(class_namedtuple=sd.SpriteShowHide,
                                   given_arguments=arguments)

        if not name:
            return
        
        # Get the sprite
        existing_sprite: sd.SpriteObject

        if sprite_type in (file_reader.ContentType.CHARACTER,
                           file_reader.ContentType.OBJECT,
                           file_reader.ContentType.DIALOG_SPRITE):
            
            # Get the visible sprite based on the general alias
            # Used for hiding characters and objects.
            existing_sprite =\
                self.story.get_visible_sprite(content_type=sprite_type,
                                              general_alias=name.sprite_name)

            if not existing_sprite:
                return

            existing_sprite.start_hide()

    def _sprite_hide_all(self,
                         command_name: str):
        """
        Hide all sprites in the given sprite group (such as character, object, dialog sprite)
        by setting its visibility to False.
        """

        if not command_name:
            return

        if command_name == "character_hide_all":
            sprite_group = sd.Groups.character_group

        elif command_name == "object_hide_all":
            sprite_group = sd.Groups.object_group

        elif command_name == "dialog_sprite_hide_all":
            sprite_group = sd.Groups.dialog_group

        else:
            return

        # Go through the sprites in the given sprite group
        # and hide the sprites if they're visible.
        sprite_object: sd.SpriteObject
        for sprite_object in sprite_group.sprites.values():
            if sprite_object.visible:
                sprite_object.start_hide()

    def _sprite_show(self,
                     arguments: str,
                     sprite_type: file_reader.ContentType):
        """
        Show a sprite (any sprite, such as character, name)
        by setting its visibility to True.

        Changes:
        Oct 12, 2023 - Match flip values when swapping sprites (Jobin Rezai)
        """
        name: sd.SpriteShowHide
        name = self._get_arguments(class_namedtuple=sd.SpriteShowHide,
                                   given_arguments=arguments)

        if not name:
            return

        # Get the sprite
        new_sprite: sd.SpriteObject

        # Get the new sprite from its name, not its alias.
        
        # When we're showing a sprite, we must use its name, because if
        # we try and use an alias, multiple sprites might have the same alias.
        new_sprite = self.data_requester.get_sprite(content_type=sprite_type,
                                                    item_name=name.sprite_name)

        if not new_sprite:
            return
        
        # Is the sprite already visible? return
        elif new_sprite.visible:
            return

        # Set the visibility to True and also
        # set a flag to indicate in the next sprite update that we should
        # update the screen rect of this sprite.

        # Is there a sprite with a general alias that matches
        # what we want to show? If so, replace that sprite with
        # the new sprite that we have now.

        if sprite_type in (file_reader.ContentType.CHARACTER,
                           file_reader.ContentType.OBJECT,
                           file_reader.ContentType.DIALOG_SPRITE):

            if sprite_type == file_reader.ContentType.CHARACTER:
                sprite_group = sd.Groups.character_group

            elif sprite_type == file_reader.ContentType.OBJECT:
                sprite_group = sd.Groups.object_group
                
            elif sprite_type == file_reader.ContentType.DIALOG_SPRITE:
                sprite_group = sd.Groups.dialog_group

            # Find the sprite that we're swapping 'out'
            visible_sprite: sd.SpriteObject
            for visible_sprite in sprite_group.sprites.values():
                if visible_sprite.visible and \
                   visible_sprite.general_alias == new_sprite.general_alias:

                    # Copy the currently visible sprite
                    # so that we can turn this copy into a new sprite later.
                    copied_sprite = copy.copy(visible_sprite)

                    # Keep track of the center of the current sprite
                    # so we can restore the center when the new
                    # sprite is shown. If we don't do this, the new sprite
                    # will show up in a different position.
                    current_center = visible_sprite.rect.center

                    # Get the new image that we want to show
                    copied_sprite.original_image = new_sprite.original_image
                    copied_sprite.original_rect = new_sprite.original_rect
                    copied_sprite.image = new_sprite.image
                    copied_sprite.rect = new_sprite.rect
                    copied_sprite.name = new_sprite.name

                    # Record whether the new sprite has been flipped in any way
                    # at any time in the past, because we'll need to compare the flip
                    # values with the sprite that is being swapped out later in this method.
                    copied_sprite.flipped_horizontally = new_sprite.flipped_horizontally
                    copied_sprite.flipped_vertically = new_sprite.flipped_vertically

                    # Make the new sprite the same as the current sprite
                    # but with the new images, rects, and new name.
                    new_sprite = copied_sprite

                    # Restore the center position so the new sprite
                    # will be positioned exactly where the old sprite is.
                    new_sprite.rect.center = current_center

                    # Hide the old sprite (that we're swapping out)
                    visible_sprite.start_hide()

                    # If the sprite that is being swapped out was flipped horizontally and/or vertically,
                    # then make sure the new sprite is flipped horizontally and/or vertically too.
                    new_sprite.flip_match_with(visible_sprite)

                    # Show the new sprite (that we're swapping in)
                    new_sprite.start_show()

                    # Update the new sprite in the main character sprites dictionary
                    sprite_group.sprites[new_sprite.name] = new_sprite

                    # We found a single category character that we were looking for.
                    break

        # If the sprite is not already visible, start to make it visible.
        if not new_sprite.visible:

            # If the sprite is a background, hide all backgrounds
            # before showing the new background.
            
            # Reason: only 1 background at a time should be allowed
            # to be displayed.
            if sprite_type == file_reader.ContentType.BACKGROUND:
                sd.Groups.background_group.hide_all()
                
            new_sprite.start_show()

    def _text_dialog_define(self, arguments: str):
        """
        Handle reading and storing a new definition for a dialog
        rectangle.
        
        For example:
        <text_dialog_define: 400, 400, 7.5, scale up width and height,
        go left, mid bottom, bg color hex, 5, 5, 255, yes,
        reusable intro start, reusable intro finished, reusable outro start,
        reusable outro finished, border color hex, border opacity, border width>
        """

        dialog_rectangle_arguments: DialogRectangleDefinition
        dialog_rectangle_arguments = self._get_arguments(class_namedtuple=DialogRectangleDefinition,
                                                         given_arguments=arguments)

        
        if not dialog_rectangle_arguments:
            return

        # If the dialog is currently visible, don't allow the properties
        # to change while it's being displayed.
        if self.story.dialog_rectangle and self.story.dialog_rectangle.visible:
            return

        # Don't allow 'starting intro/outro' reusable scripts to run
        # if the there is no intro/outro animation.
        if dialog_rectangle_arguments.intro_animation == "no animation":
            dialog_rectangle_arguments = dialog_rectangle_arguments._replace(reusable_on_intro_starting=None)

        if dialog_rectangle_arguments.outro_animation == "no animation":
            dialog_rectangle_arguments = dialog_rectangle_arguments._replace(reusable_on_outro_starting=None)

        # Convert the string representation to an Enum representation.
        intro_animation =\
            dialog_rectangle.to_enum(cls=dialog_rectangle.RectangleIntroAnimation,
                                     string_representation=dialog_rectangle_arguments.intro_animation)

        outro_animation =\
            dialog_rectangle.to_enum(cls=dialog_rectangle.RectangleOutroAnimation,
                                     string_representation=dialog_rectangle_arguments.outro_animation)

        anchor =\
            dialog_rectangle.to_enum(cls=dialog_rectangle.AnchorRectangle,
                                     string_representation=dialog_rectangle_arguments.anchor)

        # Make sure the above enums conversion attempts are not None.
        if any(enum_check is None for enum_check in [intro_animation, outro_animation, anchor]):
            return
        
        if dialog_rectangle_arguments.rounded_corners == "yes":
            rounded_corners = True
        elif dialog_rectangle_arguments.rounded_corners == "no":
            rounded_corners = False
        else:
            return
        
        reusable_on_intro_starting =\
            dialog_rectangle_arguments.reusable_on_intro_starting

        reusable_on_intro_finished =\
            dialog_rectangle_arguments.reusable_on_intro_finished
        
        reusable_on_outro_starting =\
            dialog_rectangle_arguments.reusable_on_outro_starting
        
        reusable_on_outro_finished =\
            dialog_rectangle_arguments.reusable_on_outro_finished
        
        reusable_on_halt = dialog_rectangle_arguments.reusable_on_halt
        reusable_on_unhalt = dialog_rectangle_arguments.reusable_on_unhalt


        self.story.dialog_rectangle =\
            dialog_rectangle.DialogRectangle(
                main_screen=self.story.main_surface,
                width_rectangle=dialog_rectangle_arguments.width,
                height_rectangle=dialog_rectangle_arguments.height,
                animation_speed=dialog_rectangle_arguments.animation_speed,
                intro_animation=intro_animation,
                outro_animation=outro_animation,
                anchor=anchor,
                bg_color_hex=dialog_rectangle_arguments.bg_color_hex,
                animation_finished_method=self.on_dialog_rectangle_animation_completed,
                spawn_new_background_reader_method=self.spawn_new_background_reader,
                padding_x=dialog_rectangle_arguments.padding_x,
                padding_y=dialog_rectangle_arguments.padding_y,
                alpha=dialog_rectangle_arguments.opacity,
                rounded_corners=rounded_corners,
                reusable_on_intro_starting=reusable_on_intro_starting,
                reusable_on_intro_finished=reusable_on_intro_finished,
                reusable_on_outro_starting=reusable_on_outro_starting,
                reusable_on_outro_finished=reusable_on_outro_finished,
                reusable_on_halt=reusable_on_halt,
                reusable_on_unhalt=reusable_on_unhalt,
                border_color_hex=dialog_rectangle_arguments.border_color_hex,
                border_alpha=dialog_rectangle_arguments.border_opacity,
                border_width=dialog_rectangle_arguments.border_width)

    def _add_stop_movement_condition(self,
                                     sprite_type: file_reader.ContentType,
                                     command_name: str,
                                     arguments: str):
        """
        Example: <character_stop_movement_condition: rave, left, start of display>

        Arguments:
        - command_name: for example: character_stop_movement_condition
        - arguments: for example: left, start of display

        The first part of the argument is the part of the rect we're concerned about.
        possible values: left, right, top, bottom - should be converted to MovementStops enum

        The second part of the argument is where it should stop - either a numeric value, such as 300
        or a text value such as ImagePositionX.END_OF_DISPLAY, which should convert it to a pixel value first.
        :return: None
        """

        if command_name in ("character_stop_movement_condition",
                            "object_stop_movement_condition",
                            "dialog_sprite_stop_movement_condition"):

            if arguments.count(",") == 2:
                item_name, rect_section, stop_where = self._split_arguments_to_tuple(arguments=arguments)
                rect_section = sd.rect_section_to_type(rect_section=rect_section)
                
            elif arguments.count(",") == 1:
                item_name, stop_where = self._split_arguments_to_tuple(arguments=arguments)
                rect_section = None
            else:
                return

            # At this point, the stop position might be a string like "end of display"
            # or a specific coordination like "75".
            
            # If it's a string like "end of display", convert it to its Enum value.
            if not stop_where.isnumeric():
                stop_where = sd.str_to_position_type(position=stop_where)
                
                if not stop_where:
                    return
                
            else:
                # It's a numeric value. Attempt to convert it to an int.
                # Example: "75" to 75
                try:
                    stop_where = int(stop_where)
                except ValueError as e:
                    logging.warning(f"Could not convert stop location, {stop_where}, to an int")
                    return
                
            # Get the visible sprite
            sprite =\
                self.story.get_visible_sprite(content_type=sprite_type,
                                              general_alias=item_name)

            if not sprite:
                return

            sprite.movement_add_stop(rect_area=rect_section,
                                     reaches_where=stop_where)

         #   self.story.change_background(background_surface=background_surface)


class WaitForAnimationHandler:
    """
    Used with the <wait_for_animation> command.

    Used for adding new wait rules to pause the main story reader
    until specific animations have finished for specific sprites.

    Also used for checking if sprites have finished animating,
    and if they have, the wait rules for the sprites that have
    stopped animating will be removed automatically.
    """

    def __init__(self):
        # (sprite group, general alias, animation type)
        self.wait_list = []

    def enable_wait_for(self, sprite_type: str, general_alias: str, animation_type: str):
        """
        Record a new reason to pause the main story reader.
        Reusable scripts are not affected.
        """
        if not all([sprite_type, general_alias, animation_type]):
            return

        if sprite_type == "character":
            sprite_group_to_check = sd.Groups.character_group
        elif sprite_type == "object":
            sprite_group_to_check = sd.Groups.object_group
        elif sprite_type == "dialog sprite":
            sprite_group_to_check = sd.Groups.dialog_group
        else:
            return

        if animation_type == "fade":
            animation_type_to_check = sd.SpriteAnimationType.FADE
        elif animation_type == "move":
            animation_type_to_check = sd.SpriteAnimationType.MOVE
        elif animation_type == "rotate":
            animation_type_to_check = sd.SpriteAnimationType.ROTATE
        elif animation_type == "scale":
            animation_type_to_check = sd.SpriteAnimationType.SCALE
        elif animation_type == "all":
            animation_type_to_check = "all",
        elif animation_type == "any":
            animation_type_to_check = "any"
        else:
            return

        self.wait_list.append((sprite_group_to_check, general_alias, animation_type_to_check))

    def check_wait(self) -> bool:
        """
        Check the wait list to see if the main reader should pause
        until one or more sprites' animations have stopped.

        Return: True if the main story reader should wait
        or False if there is no need for the main reader to wait for animation(s) to finish.
        """
        if not self.wait_list:
            return False

        remove_indexes = []

        # Loop through wait_list to see what animation(s) we need to wait for (if any).
        for idx, wait_info in enumerate(self.wait_list):
            # Type-hints
            sprite_group: sd.SpriteGroup
            general_alias: str | None
            animation_type: sd.SpriteAnimationType | str

            sprite_group, general_alias, animation_type = wait_info
            wait = self._is_sprite_animating(sprite_group=sprite_group,
                                             general_alias=general_alias,
                                             animation_type=animation_type)
            if wait:
                return True
            else:
                # The wait rule is not animating, so remove it from the wait list later.
                remove_indexes.append(idx)
        else:

            # Remove wait rules that need to be removed.
            if remove_indexes:
                # Get a new list with only wait rules that are still waiting.
                self.wait_list = [item for idx, item in enumerate(self.wait_list)
                                  if idx not in remove_indexes]

            # So the caller knows that there is no need to wait
            return False

    @staticmethod
    def _is_sprite_animating(sprite_group: sd.SpriteGroup,
                             general_alias: str | None,
                             animation_type: sd.SpriteAnimationType | str) -> bool | None:
        """
        Check if a specific type of animation is currently occurring.

        Arguments:

            - sprite_group: the sprite group we should check sprites in
            - general_alias: we use the general alias to find a matching sprite
            that is visible.
            - animation_type: the type of animation to check for, or 'all', or 'any'.

        Return: True if the given type of animation is occurring for the given
        sprite alias in the given sprite group.
        """
        if not all([sprite_group, general_alias, animation_type]):
            return

        sprite_object: sd.SpriteObject
        for sprite_object in sprite_group.sprites.values():

            if not sprite_object.visible:
                continue
            elif not sprite_object.general_alias:
                continue
            elif sprite_object.general_alias != general_alias:
                continue

            if isinstance(animation_type, sd.SpriteAnimationType):
                if animation_type == sd.SpriteAnimationType.FADE and sprite_object.is_fading:
                    return True
                elif animation_type == sd.SpriteAnimationType.MOVE and sprite_object.is_moving:
                    return True
                elif animation_type == sd.SpriteAnimationType.ROTATE and sprite_object.is_rotating:
                    return True
                elif animation_type == sd.SpriteAnimationType.SCALE and sprite_object.is_scaling:
                    return True

            elif isinstance(animation_type, str):
                if animation_type == "all" and all([sprite_object.is_fading,
                                                    sprite_object.is_moving,
                                                    sprite_object.is_rotating,
                                                    sprite_object.is_scaling]):
                    return True
                elif animation_type == "any" and any([sprite_object.is_fading,
                                                      sprite_object.is_moving,
                                                      sprite_object.is_rotating,
                                                      sprite_object.is_scaling]):
                    return True
