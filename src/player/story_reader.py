"""
Copyright 2023, 2024 Jobin Rezai

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


"""
Nov 27, 2023 (Jobin Rezai) - Improve _is_sprite_animating() detection with
fade animations.
"""

import copy
import re
import pygame
import string
import secrets
import active_story
import file_reader
import dialog_rectangle
import font_handler
import logging
import sprite_definition as sd
import cover_screen_handler
import font_handler
import audio_player
import command_helper as ch
import command_class as cc
from re import search, findall
from typing import Tuple
# from font_handler import ActiveFontHandler
from typing import Dict
from shared_components import Passer
# from audio_player import AudioChannel
from rest_handler import RestHandler
from variable_handler import VariableHandler
from condition_handler import Condition



class AfterCounter:
    """
    Used with the AfterManager class.
    
    Purpose: to keep track of how many frames need to be skipped
    and how many frames have been skipped so far.
    """
    def __init__(self,
                 frames_to_skip: int,
                 optional_arguments: str = None):
        """
        Arguments:
        
        - frames_to_skip: the number of frames to elapse
        until the reusable script is run.
        
        - optional_arguments: arguments to pass to the reusable script
        once the number of frames has been satisfied.
        """
        
        self.frames_to_skip = frames_to_skip
        self.frames_skipped_so_far = 0
        
        self.optional_arguments = optional_arguments

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
        
    def add_timer(self,
                  reusable_script_name: str,
                  frames_to_skip: int,
                  optional_arguments: str|None = None):
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

        counter = AfterCounter(frames_to_skip=frames_to_skip,
                               optional_arguments=optional_arguments)

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

        # Key: reusable script name
        # Value: optional additional arguments to pass to the reusable script
        #        or None if not available.
        run_script_names = {}

        counter: AfterCounter
        for reusable_script_name, counter in self.scripts_and_timers.items():

            # Increment this timer by 1 frame.
            counter.elapse()
            
            # Is this queue ready to run the script?
            if counter.is_ready():
                # Yes, run this script at the end of this method with
                # optional arguments, if available.
                run_script_names[reusable_script_name] = \
                    counter.optional_arguments
            else:
                # This queue is not ready to run the script yet.
                # Updated the counter with the elapsed version.
                self.scripts_and_timers[reusable_script_name] = counter

        # Remove timers that have expired and run the reusable scripts.
        for reusable_script_name, optional_arguments in run_script_names.items():
            
            # Remove expired timer
            del self.scripts_and_timers[reusable_script_name]
            
            if optional_arguments:
                with_arguments = True
                
                # Combine the reusable script name with the optional arguments
                # because it gets passed all as one string when spawning
                # a background reader.
                reusable_script_name =\
                    f"{reusable_script_name},{optional_arguments}"
            else:
                with_arguments = False

            # Spawn a new background reader so we can run
            # the reusable script that we're iterating on.
            self.method_spawn_background_reader(reusable_script_name,
                                                with_arguments=with_arguments)


class StoryReader:
    """
    Reads a story script line by line.

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
    # (There are currently no commands that can't be called from a reusable script)
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

        # self.dialog_rectangle: dialog_rectangle.DialogRectangle
        # self.dialog_rectangle = None

        # So we can load sprites and audio
        self.data_requester: file_reader.FileReader
        self.data_requester = data_requester

        # Used if we are instantiating a background reader
        self.background_reader_name = background_reader_name

        # The story is read line by line
        self.script_lines = []
        
        # The lastest condition name that evaluated to False.
        # The name is case-sensitive. If there is a value here,
        # the current reader will skip all script lines except for:
        # <case_end> and <or_case>.
        self.condition_name_false = None

        # For reading variables and replacing them with values.
        # Both the main scripts and reusable scripts can use variables.
        self.variable_handler = VariableHandler()

        # This gets set to True once there are no more scripts to read.
        # This is used so we don't attempt to reload the story again.
        self.story_finished = False

        # Only a reusable secondary reader should contain arguments
        # (for use with <call> with arguments)
        if self.background_reader_name:
            self.argument_handler = ReusableScriptArgument()

        # Only the main story reader should contain the fields below.
        elif not self.background_reader_name:
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
            
            # This is used for manually pausing the reading of the 
            # main script until <unpause_main_script> is used.
            # Purpose: to prevent the main reader from advancing until
            # the viewer clicks on a sprite (button) which then manually
            # unpauses the main reader.
            self.pause_main_script = False
            
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
            self.active_font_handler =\
                font_handler.ActiveFontHandler(story=self.story)
            
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
            
            # Read the visual novel's variables.
            VariableHandler.variables = self.data_requester.detail_header.get("StoryVariables")
            
    def main_script_should_pause(self):
        """
        Check if there are any animations occurring
        or pauses (halt, rest, manual pause) that should cause
        the main story script to not continue reading.
        
        This does not apply to background scripts.
        """
        main_reader = self.get_main_story_reader()
        
        return any((main_reader.animating_dialog_rectangle,
                    main_reader.halt_main_script,
                    main_reader.rest_handler.pause_required(),
                    main_reader.wait_for_animation_handler.check_wait(),
                    main_reader.pause_main_script))

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
        chapter_script = self.chapters_and_scenes.get(startup_chapter_name)
        if chapter_script:
            # Get just the chapter's script
            chapter_script = chapter_script[0]
        else:
            # Chapter not found
            return

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

            # Are there any running background reusable scripts that are no longer needed
            # and need to be deleted?
            if self.background_readers_deletion_queue:
                # Yes, there are some running background readers that need to be deleted.

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

    def replace_tokens_with_arguments(self, line_to_check: str) -> str | None:
        """
        Look for (@parameter) tokens in the given string and
        replace it with the value of the report from the reusable script's arguments
        dictionary.

        This is only used with reusable scripts that have parameters/arguments.

        Arguments:
            - line_to_check: a line in a reusable script

        Return:
            A new string with the (@parameter) tokens replaced, or None if
            no parameters were found in the string.
        """
        # This check should only apply to background readers (reusable scripts)
        if not self.background_reader_name:
            return

        if not line_to_check:
            return

        pattern = r"[(][@][a-zA-Z\d]*[_]*[\w ]+[)]"

        results = findall(pattern=pattern,
                          string=line_to_check)

        replaced_token = False

        # Example:
        # ['(@)', '(@character)', '(@last name)']
        for token in results:
            # Get the token without the starting (@ and ending )
            parameter_name = token.strip().lstrip("(@").rstrip(")")
            if not parameter_name:
                continue

            # Get the argument value for the specified parameter in the reusable script.
            parameter_value = self.argument_handler.get_argument_value(parameter_name)

            # Argument not found for the token? Consider this an error in the visual novel.
            if not parameter_value:
                raise ValueError(f"Reusable script error - no replaceable value found for token '{parameter_name}',"
                                 f" in reusable script: '{self.background_reader_name}'")

            # Replace the token with the argument
            line_to_check = line_to_check.replace(token, parameter_value)

            # So we know whether to return the modified line or None
            replaced_token = True

        if replaced_token:
            return line_to_check

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
            # The chapter's script gets loaded automatically
            # for each scene.
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

                # Still pause? We quickly double-check here because
                # elapse_halt_timer() just ran a few lines above, so it's possible that
                # we won't need to pause anymore. If we don't check in this frame
                # and wait for the next frame, in some cases, any text after <halt_auto> will
                # be skipped if we're in sudden-mode.
                # To elaborate, the quick check here will avoid not reading 'You look familiar'
                # in this script, when in sudden-mode.
                """
                Hello
                <no_clear>
                <continue>
                <halt_auto: 60>
                   ...
                <no_clear>
                <halt_auto: 60>
                You look familiar.  <--- this won't run if we don't re-check for a halt in this frame.
                <halt>
                """
                # Re-check
                if self.main_script_should_pause():
                    return

        command_line = True

        # Keep looping while we're reading <command: x> type lines
        # Execute the commands as we read through them.
        while command_line:
            
            line = self.script_lines.pop(0)
            
            # Remove leading and trailing spaces temporarily.
            # Commands with leading or trailing spaces won't be read as
            # commands. If it appears to be a command, record the line
            # without the leading/trailing spaces so the command will run later.
            line_strip = line.strip()
            if line_strip.startswith("<") and line_strip.endswith(">"):
                line = line_strip
            
            # Replace variable names with variable values, if possible.
            line = self.variable_handler.find_and_replace_variables(line=line)

            # Nothing else to read?
            # Consider the current script to be now finished.
            if not self.script_lines:
                self.story_finished = True
                command_line = False
                
            # A blank line or a comment line? Ignore the line completely.
            if not line or line.startswith("#"):
                continue
            
            # Should we skip reading this line because an earlier
            # condition evaluated to False?
            if not Condition.evaluate_line_check(script_line=line,
                            false_condition_name=self.condition_name_false):
                # An earlier condition evaluated to False, 
                # and the current line is not <case_end> or <or_case..
                # so ignore this line.
                continue
            
            # This is a special command, which gets replaced 
            # with a blank string, because real blank strings are ignored
            # if this command is not used.
            elif line == "<line>":
                line = ""

            # Replaced tokens with argument values (reusable scripts only)
            # The method below will check if we are in a reusable script or not.
            line_with_replaced_tokens = self.replace_tokens_with_arguments(line)
            if line_with_replaced_tokens:
                line = line_with_replaced_tokens

            results = self.extract_arguments(line)
            if results:
                command_name = results.get("Command")
                arguments = results.get("Arguments")

                if arguments:
                    arguments = arguments.strip()

                if command_name:

                    self.run_command(command_name, arguments)

                    # <scene>, <scene_with_fade>, <exit> will cause the current 
                    # story reader to finish (<scene> and <scene_with_fade> 
                    # make way for a new scene - new main reader), so those
                    # two commands will set story_finished to True, 
                    # and so will <exit>.
                    if self.story_finished:
                        # Either <scene>, <scene_with_fade>, or <exit> was used, 
                        # so don't continue with this reader anymore.
                        command_line = False
                        self.script_lines.clear()

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
        
        # Prepare to show the line of text
        self.active_font_handler.process_text(line_text=line_text)

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

        elif command_name in ("case", "or_case"):
            self._condition_read(command_name=command_name, arguments=arguments)

        elif command_name == "case_else":
            self._condition_else()

        elif command_name == "case_end":
            self._condition_end()
            
        elif command_name == "exit":
            self._exit()

        elif command_name == "play_sound":
            self._play_audio(arguments=arguments,
                             audio_channel=audio_player.AudioChannel.FX)
            
        elif command_name == "play_voice":
            self._play_audio(arguments=arguments,
                             audio_channel=audio_player.AudioChannel.VOICE)
            
        elif command_name == "play_music":
            self._play_audio(arguments=arguments,
                             audio_channel=audio_player.AudioChannel.MUSIC)
            
        elif command_name == "sprite_text":
            self._sprite_text(arguments=arguments)
            
        elif command_name == "sprite_text_clear":
            # This command is just like <sprite_text> except we're going
            # to pass in an empty string, which causes the text to get cleared.
            if arguments:
                # For passing an empty string
                arguments += ","
                self._sprite_text(arguments=arguments)
            
        elif command_name == "sprite_font":
            self._sprite_text_font(arguments=arguments)
            
        elif command_name == "sprite_font_x":
            self._sprite_text_start_position(True, arguments)
            
        elif command_name == "sprite_font_y":
            self._sprite_text_start_position(False, arguments)
            
        elif command_name == "sprite_font_delay":
            self._sprite_text_font_delay(arguments=arguments)
            
        elif command_name == "sprite_font_delay_punc":
            self._sprite_text_font_delay_punc(arguments=arguments)
            
        elif command_name == "sprite_font_fade_speed":
            self._sprite_text_font_fade_speed(arguments=arguments)
        
        elif command_name == "sprite_font_intro_animation":
            self._sprite_text_font_intro(arguments=arguments)
            
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
            """
            Start the outro animation of the dialog rectangle if it's visible.
            """
            self._text_dialog_close()
                
        elif command_name in ("character_flip_both", "character_flip_horizontal",
                              "character_flip_vertical", "object_flip_both",
                              "object_flip_horizontal", "object_flip_vertical",
                              "dialog_sprite_flip_both", "dialog_sprite_flip_horizontal",
                              "dialog_sprite_flip_vertical"):

            self._flip(command_name=command_name, arguments=arguments)
            
        elif command_name in ("dialog_sprite_on_mouse_enter",
                              "object_on_mouse_enter",
                              "character_on_mouse_enter",
                              "dialog_sprite_on_mouse_leave",
                              "object_on_mouse_leave",
                              "character_on_mouse_leave",
                              "dialog_sprite_on_mouse_click", 
                              "object_on_mouse_click", 
                              "character_on_mouse_click"):
            self._mouse_event_reusable_script(command_name=command_name,
                                              arguments=arguments)

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
            
        elif command_name == "halt_and_pause_main_script":
            """
            Pause the main story reader until the command <unpause_main_script>
            is used.
            
            This is the same as using <halt> and pausing the story
            by setting the 'pause_main_script' flag.
            
            The reason this command was made: to prevent the main reader
            from advancing until a sprite (button) has been clicked, and the
            button would run the command: <unhalt_and_unpause_main_script>.
            
            If we didn't have this, then clicking anywhere in the story
            would cause the story to advance, so we have this command
            to make the dialog text appear (halt) and to prevent the story
            from advancing if the viewer clicks anywhere on the story, until
            the command <unhalt_and_unpause_main_script> is used.
            """
            main_reader = self.get_main_story_reader()
            
            # Is the main reader already paused? return.
            if main_reader.pause_main_script:
                return
            
            main_reader.pause_main_script = True
            main_reader.halt()
            
        elif command_name == "unhalt_and_unpause_main_script":
            """
            Unpause the main story reader that was manually paused with
            <pause_main_script>.
            """
            main_reader = self.get_main_story_reader()
            
            # Is the main reader not paused? Return, to avoid
            # unhalting unnecessarily because the main reader is not paused.
            if not main_reader.pause_main_script:
                return
            
            main_reader.pause_main_script = False
            main_reader.unhalt()

        elif command_name == "scene_with_fade":
            """
            Gradually fade-in then fade-out the entire pygame window.
            Right before it starts fading out, play a specific scene.
            This is used when transitioning between scenes.
            """
            self._scene_with_fade(arguments=arguments)
            
        elif command_name == "variable_set":
            """
            Create a new variable or update an existing variable.
            """
            self._variable_set(arguments=arguments)

        elif command_name == "character_show":
            """
            Show a character sprite by setting its visibility flag to True.
            """
            self._sprite_show(arguments=arguments,
                              sprite_type=file_reader.ContentType.CHARACTER)
            
        elif command_name == "dialog_sprite_show":
            """
            Show a dialog sprite by setting its visibility flag to True.
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

            self._sprite_set_position(
                command_name=command_name,
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

            if "," in arguments:
                use_arguments = True
            else:
                use_arguments = False
            self.spawn_new_background_reader(reusable_script_name=arguments,
                                             with_arguments=use_arguments)
            
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

        elif command_name == "dialog_sprite_start_scaling":
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
        
        volume: cc.Volume
        volume = self._get_arguments(class_namedtuple=cc.Volume,
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

        channel_mapping = {"volume_text": audio_player.AudioChannel.TEXT,
                           "volume_music": audio_player.AudioChannel.MUSIC,
                           "volume_voice": audio_player.AudioChannel.VOICE,
                           "volume_fx": audio_player.AudioChannel.FX}

        audio_channel = channel_mapping.get(command_name)

        if audio_channel == audio_player.AudioChannel.TEXT:
            self.story.audio_player.volume_text = float_volume
            
        elif audio_channel == audio_player.AudioChannel.FX:
            self.story.audio_player.volume_sound = float_volume

        elif audio_channel == audio_player.AudioChannel.VOICE:
            self.story.audio_player.volume_voice = float_volume

        elif audio_channel == audio_player.AudioChannel.MUSIC:
            self.story.audio_player.volume_music = float_volume

    def _stop_audio(self, command_name: str):
        """
        Stop the audio in a specific channel, but only
        if the channel has already been initialized.
        
        Note: there is no command to stop text audio (ie: when an audio
        is played for each letter, letter-by-letter), because it will
        just immediately play again on the next letter.
        """
        
        channel_mapping = {"stop_fx": audio_player.AudioChannel.FX,
                           "stop_voice": audio_player.AudioChannel.VOICE,
                           "stop_music": audio_player.AudioChannel.MUSIC,
                           "stop_all_audio": audio_player.AudioChannel.ALL}
        
        audio_channel = channel_mapping.get(command_name)
        
        # Stop the audio on a specific audio channel.
        self.story.audio_player.stop_audio(audio_channel=audio_channel)

    def _dialog_text_sound(self, arguments: str):
        """
        Set the dialog rectangle to play a specific audio
        for letter-by-letter non-gradual text displays.
        """

        dialog_sound: cc.DialogTextSound
        dialog_sound = self._get_arguments(class_namedtuple=cc.DialogTextSound,
                                           given_arguments=arguments)

        if not dialog_sound:
            return

        # Don't allow the dialog sound to be set if the dialog rectangle hasn't been
        # initialized yet.
        if not self.story.dialog_rectangle:
            raise ValueError(
                "Cannot set the dialog text sound because the dialog has not been defined yet."
                " Use <text_dialog_define> first.")

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
        
        flip: cc.Flip
        flip = self._get_arguments(class_namedtuple=cc.Flip,
                                   given_arguments=arguments)

        if not flip:
            return

        # Determine the sprite type based on the command name.
        sprite_type = self.get_sprite_type_from_command(command_name=command_name)
            
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
        
        general_alias_and_position = \
            self._split_arguments_to_tuple(arguments=arguments)

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

        name: cc.SpriteCenterWith
        name = self._get_arguments(class_namedtuple=cc.SpriteCenterWith,
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

        # before_move_rect = sprite_to_move.rect.copy()
        sprite_to_move.rect.centerx = sprite_to_center_with.rect.centerx
        # after_move_rect = sprite_to_move.rect.copy()
        
        ## Queue the rects for a manual screen update.
        ## Regular animations (such as <character_start_moving: rave>)
        ## are updated automatically, but since this is a manual animation,
        ## we need to queue it for updating here.
        #active_story.ManualUpdate.queue_for_update(before_move_rect)        
        #active_story.ManualUpdate.queue_for_update(after_move_rect) 

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

            # # The dialog rectangle has closed, so hide all
            # # dialog-related sprites.
            # sd.Groups.dialog_group.hide_all()

        # Now that the animation has finished for the dialog rect, record
        # the dialog's rect so when we add letters to the dialog, we won't
        # need to call .get_rect() for each letter being added.
        self.story.dialog_rectangle_rect = final_dest_rect.copy()

        # Run a reusable script for when the animation has stopped?
        if run_reusable_script_name:
            self.spawn_new_background_reader \
                (reusable_script_name=run_reusable_script_name)

    def _sprite_set_center(self,
                           sprite_type: file_reader.ContentType,
                           arguments: str):
        """
        Set the center point of the sprite's rect.
        
        :param arguments: (str) sprite general alias, x position, y position
        :return: None
        """

        scale_center: cc.SpriteCenter
        scale_center = self._get_arguments(class_namedtuple=cc.SpriteCenter,
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
                # The unhalt() method below will reset the halt_auto counter variables.
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

        # If the main story reader is paused due to a manual pause
        # with the <pause_main_script> command, then don't unhalt yet
        # until the main story reader is unpaused manually with the
        # <unpause_main_script> command.
        if main_reader.pause_main_script:
            return

        main_reader.halt_main_script = False

        # Clear the fade-in intro animation, if any.
        main_reader.active_font_handler.font_animation.stop_intro_animation()

        # Reset halt_auto variables, if they were used.
        # Note: these two variables need to be here, *after* stop_intro_animation() above,
        # because stop_intro_animation() will try and run reusable_on_halt, which we shouldn't
        # if we just came out of halt_auto.
        main_reader.halt_main_script_auto_mode_frames = 0
        main_reader.halt_main_script_frame_counter = 0

        # Clear the current letter list because we should make way for
        # other dialog text.
        main_reader.active_font_handler.clear_letters()

        # Re-draw the dialog rectangle shape so that any previous text
        # gets blitted over with the new rectangle.
        main_reader.story.dialog_rectangle.clear_text()

    def _variable_set(self, arguments: str):
        """
        Create a new variable if it doesn't exist
        or update an existing variable's value.
        """
        
        variable_set: cc.VariableSet
        variable_set = self._get_arguments(class_namedtuple=cc.VariableSet,
                                           given_arguments=arguments)
        
        if variable_set:
            
            # Update or create variable.
            # The method will also check for invalid variable name characters.
            VariableHandler.set_variable(variable_name=variable_set.variable_name,
                                         variable_value=variable_set.variable_value)

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
            adjust_y: cc.Continue
            adjust_y = self._get_arguments(class_namedtuple=cc.Continue,
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

    def _font_intro_animation(self,
                              arguments,
                              sprite_object: sd.SpriteObject = None):
        """
        Set the intro animation of the current active font sprite sheet.
        This will be the animation style to use when showing dialog text.
        
        Arguments:
        
        - arguments: the value given by the visual novel's command line.
        
        - sprite_object: this will be a SpriteObject instance if the font text
        option is being applied to a sprite object such as a character, object
        or dialog sprite. If it's None, then it's being applied to a dialog
        rectangle.
        """
        animation_type: cc.FontIntroAnimation
        animation_type =\
            self._get_arguments(class_namedtuple=cc.FontIntroAnimation,
                                given_arguments=arguments)

        if not animation_type:
            return
        
        subject_font_handler: font_handler.ActiveFontHandler
        
        # Applying a font intro to a sprite object?
        if sprite_object:
            # Applying font intro to a sprite object.
            
            # Sprite font handler (character, object, dialog sprite)
            subject_font_handler = sprite_object.active_font_handler
        else:
            # Applying font intro to the dialog rectangle.
            subject_font_handler =\
                self.get_main_story_reader().active_font_handler

        # This will always been initialized to something, it won't be None.
        subject_font_handler.font_animation.start_animation_type =\
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

        rotate_current_value: cc.RotateCurrentValue
        rotate_current_value =\
            self._get_arguments(class_namedtuple=cc.RotateCurrentValue,
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

        # sprite.sudden_rotate_change = True

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

        rotate_until: cc.RotateUntil
        rotate_until = self._get_arguments(class_namedtuple=cc.RotateUntil,
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

        rotate_delay: cc.RotateDelay
        rotate_delay = self._get_arguments(class_namedtuple=cc.RotateDelay,
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

        rotate_speed: cc.RotateSpeed
        rotate_speed = self._get_arguments(class_namedtuple=cc.RotateSpeed,
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
        rotate_speed = cc.RotateSpeed(rotate_speed.sprite_name,
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
        When a specific sprite image stops rotating, run a specific
        reusable script.
        
        Arguments:
        
        - sprite_type: so we can know which dictionary to get the sprite from.
        - arguments: (str) sprite general alias, reusable script name
       
        return: None
        """

        rotate_stop_run_script: cc.RotateStopRunScript
        rotate_stop_run_script =\
            self._get_arguments(class_namedtuple=cc.RotateStopRunScript,
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
                        cc.RotateCurrentValue(sprite_name=sprite_name,
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

        scale_delay: cc.ScaleDelay
        scale_delay = self._get_arguments(class_namedtuple=cc.ScaleDelay,
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
                        cc.ScaleCurrentValue(sprite_name=sprite_name,
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

        scale_stop_run_script: cc.ScaleStopRunScript
        scale_stop_run_script =\
            self._get_arguments(class_namedtuple=cc.ScaleStopRunScript,
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

        scale_current_value: cc.ScaleCurrentValue
        scale_current_value =\
            self._get_arguments(class_namedtuple=cc.ScaleCurrentValue,
                                given_arguments=arguments)

        if not scale_current_value:
            return

        # Get the active/visible sprite
        sprite: sd.SpriteObject
        sprite = self.story.get_visible_sprite(content_type=sprite_type,
                                               general_alias=scale_current_value.sprite_name)

        if not sprite:
            return        

        # Set the scale value of the sprite (immediate, no gradual animation).
        sprite.scale_current_value = scale_current_value

        # sprite.sudden_scale_change = True

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

        scale_until: cc.ScaleUntil
        scale_until = self._get_arguments(class_namedtuple=cc.ScaleUntil,
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

        scale_by: cc.ScaleBy
        scale_by = self._get_arguments(class_namedtuple=cc.ScaleBy,
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
        if percent_to_float is None:
            return

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
        
        rotate_direction = rotate_direction.lower()
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

        fade_speed: cc.FadeSpeed
        fade_speed = self._get_arguments(class_namedtuple=cc.FadeSpeed,
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
        fade_speed = cc.FadeSpeed(fade_speed.sprite_name,
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
                cc.FadeCurrentValue(sprite_name=fade_speed.sprite_name,
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

        current_fade_value: cc.FadeCurrentValue
        current_fade_value =\
            self._get_arguments(class_namedtuple=cc.FadeCurrentValue,
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

        fade_until: cc.FadeUntilValue
        fade_until = self._get_arguments(class_namedtuple=cc.FadeUntilValue,
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

        fade_delay: cc.FadeDelay
        fade_delay = self._get_arguments(class_namedtuple=cc.FadeDelay,
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

    def _sprite_load(self, arguments: str, sprite_type: file_reader.ContentType):
        """
        Load a sprite image/sprite into memory and give it a general alias
        so it's ready to be displayed whenever it's needed.
        """
        
        sprite_name_and_alias: cc.SpriteLoad
        sprite_name_and_alias = \
            self._get_arguments(class_namedtuple=cc.SpriteLoad,
                                given_arguments=arguments)

        if not sprite_name_and_alias:
            return
        
        # Is there 'Load As' in the sprite name? That means there is a
        # a different preferred name, so we should load the sprite As the
        # new name.
        # For example: <load_character: theo Load As th>
        original_and_preferred_name =\
            ch.CommandHelper.get_preferred_sprite_name(
                sprite_name_argument=sprite_name_and_alias.sprite_name)
        
        # Separate the original name and preferred load-as name,
        # if a preferred name was provided.
        if original_and_preferred_name:
            # A preferred name was provided.
            
            original_sprite_name = original_and_preferred_name.get("OriginalName")
            preferred_sprite_name = original_and_preferred_name.get("LoadAsName")
  
        else:
            # There is no preferred name; use the original name.
            original_sprite_name = sprite_name_and_alias.sprite_name
            preferred_sprite_name = None
        
        # Get the sprite from the .lvna file.
        loaded_sprite =\
            self.data_requester.get_sprite(
                content_type=sprite_type,
                item_name=original_sprite_name,
                general_alias=sprite_name_and_alias.sprite_general_alias,
                load_item_as_name=preferred_sprite_name)
        
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
        
        # Use the preferred sprite name when adding the sprite to the dictionary
        # if it's there; otherwise use the sprite's original sname.
        sprite_group.add(
            preferred_sprite_name or original_sprite_name, loaded_sprite)

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

        fade_stop_run_script: cc.FadeStopRunScript
        fade_stop_run_script =\
            self._get_arguments(class_namedtuple=cc.FadeStopRunScript,
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

        movement_stop_run_script: cc.MovementStopRunScript
        movement_stop_run_script =\
            self._get_arguments(class_namedtuple=cc.MovementStopRunScript,
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
        
        if arguments.count(",") > 1:
            class_type = cc.AfterWithArguments
        else:
            class_type = cc.AfterWithoutArguments
            optional_arguments = None

        after_timer: cc.AfterWithArguments
        after_timer =\
            self._get_arguments(class_namedtuple=class_type,
                                given_arguments=arguments)

        if class_type == cc.AfterWithArguments:
            optional_arguments = after_timer.arguments

        # Use the after manager of the main reader if we're currently
        # in a background reader.
        after_manager_method = self._get_after_manager()

        # Create a timer to run the specific reusable script.
        after_manager_method.add_timer(reusable_script_name=after_timer.reusable_script_name,
                                       frames_to_skip=after_timer.frames_elapse,
                                       optional_arguments=optional_arguments)
        
    def after_cancel(self, arguments):
        """
        Cancel an existing 'after' timer.
        Example: <after_cancel: reusable script here>
        
        After timers are known by the reusable script name that they're
        supposed to end up running and only 1 of each reusable script
        can be added to a timer. So we can use the reusable script name
        to cancel a timer.
        """

        after_cancel: cc.AfterCancel
        after_cancel =\
            self._get_arguments(class_namedtuple=cc.AfterCancel,
                                given_arguments=arguments)
        

        # Use the after manager of the main reader if we're currently
        # in a background reader.
        after_manager_method = self._get_after_manager()

        # Remove the timer with the name that matches the
        # specified reusable script name. If the name doesn't exist,
        # it won't raise an exception.
        after_manager_method.remove_timer(reusable_script_name=after_cancel.reusable_script_name)

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
    
    def spawn_new_background_reader_auto_arguments(
        self, reusable_script_name_maybe_with_arguments: str):
        """
        Create a new background reader for playing a reusable script.
        This is the same as the other method, spawn_new_background_reader(),
        with one difference: the given argument can contain arguments
        and the arguments will be passed to the reusable script automatically.
        
        This is a wrapper method that runs spawn_new_background_reader().
        It basically looks for a comma and uses that determine if there are
        arguments to pass or not.
        
        Arguments:
        
        - reusable_script_name_maybe_with_arguments: either the reusable
        script name alone, or the reusable script name, followed by arguments
        to pass to the reusable script.
        
        Example: 'my second script'
        or
        'my second script, name=theo, sky=blue'
        """
        with_arguments = "," in reusable_script_name_maybe_with_arguments
        
        self.spawn_new_background_reader(
            reusable_script_name=reusable_script_name_maybe_with_arguments,
        with_arguments=with_arguments)

    def spawn_new_background_reader(self,
                                    reusable_script_name: str,
                                    with_arguments: bool = False):
        """
        Create a new background reader.
        :param reusable_script_name: (str) the case-sensitive name of the reusable script we should load.

        :param with_arguments: (bool) True if arguments have been supplied (comma separated)
        as part of the reusable_script_name.
        For example: 'character=theo,last name=something' (two arguments in this example)

        :return: None
        """

        call: cc.CallWithArguments

        if not with_arguments:
            # The class type will be CallWithNoArguments here
            call = \
                self._get_arguments(class_namedtuple=cc.CallWithNoArguments,
                                    given_arguments=reusable_script_name)
        else:
            call = \
                self._get_arguments(class_namedtuple=cc.CallWithArguments,
                                    given_arguments=reusable_script_name)

        # If a reusable script is calling another reusable script, spawn the new background reader
        # from the main story reader, not from the background reader that requested the reusable script.
        # That way, all the background readers will be tied to the main story reader.
        if self.background_reader_name:
            # Load the reusable script from the main story reader.
            self.story.reader.spawn_new_background_reader(reusable_script_name=call.reusable_script_name)
            return

        # Is the requested reusable script already loaded and running? Don't allow another one.
        elif call.reusable_script_name in self.background_readers:
            return

        script = self._get_reusable_script(reusable_script_name=call.reusable_script_name)

        if not script:
            return

        # Instantiate a new background reader
        reader = StoryReader(story=self.story,
                             data_requester=self.data_requester,
                             background_reader_name=call.reusable_script_name)

        reader.script_lines = script.splitlines()

        # Add the background reader to the main dictionary that holds the background readers.
        self.background_readers[call.reusable_script_name] = reader

        # Debugging
        # print("BG Reader:", call.reusable_script_name)

        def get_reusable_script_arguments(unsorted_arguments_line: str) -> Dict | None:
            """
            Parse the parameter name(s) and argument value(s) from
            the given line.

            Example:
                character name=theo,last name=test
                will result to: {"character name": "theo",
                                 "last name": "test"}

            return: Dict
            """
            if not unsorted_arguments_line:
                return

            pattern = r"^(?P<Parameter>[a-zA-Z\d]*[_]*[\w ]+)={1}(?P<Argument>.*)$"

            # We need to evaluate multiple arguments separately,
            # with each parameter/value pair on its own line.
            argument_lines = unsorted_arguments_line.split(",")

            parameters_and_arguments = {}

            # Example: ["character=theo", "background=sky"]
            for line in argument_lines:
                result = search(pattern=pattern,
                                string=line)

                if result:
                    # Get the parameter name (ie: 'character name'
                    parameter = result.groupdict().get("Parameter")

                    # Get the argument value (after the = sign), ie: Theo
                    argument_value = result.groupdict().get("Argument")

                    # Strip spaces around the parameter and argument
                    # so that something like ' character =  theo ' will still work.
                    if parameter and argument_value:
                        parameter = parameter.strip()
                        argument_value = argument_value.strip()

                    # Add to dictionary which will be returned
                    parameters_and_arguments[parameter] = argument_value

            return parameters_and_arguments

        # Was the reusable script called with parameters/arguments?
        # Then add those arguments to argument_handler for the new background reader.
        if with_arguments:
            # Get the parameter names and values by recording them in a dictionary.
            parameter_arguments = \
                get_reusable_script_arguments(unsorted_arguments_line=call.arguments)

            # Add the parameter names and argument values to
            # the argument handler's dictionary, so <call> reusable scripts
            # can read from that dictionary when (@symbol) tokens are found.
            if parameter_arguments:
                reader.argument_handler.add_arguments(parameter_arguments)

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
        
        load_scene: cc.SceneLoad
        load_scene =\
            self._get_arguments(class_namedtuple=cc.SceneLoad,
                                given_arguments=arguments)

        chapter_name = load_scene.chapter_name
        scene_name = load_scene.scene_name

        # Make sure the given chapter name exists.
        
        # {chapter name: [chapter script, {scene name: scene script}] }
        chapters = self.chapters_and_scenes.get(chapter_name)
        if not chapters:
            raise ValueError(f"The chapter '{chapter_name}' was not found in the visual novel.\n"
                             "Possible reason: the visual novel might have been played from a different chapter.\n"
                             "Try playing the visual novel from the beginning rather than a specific scene so it includes all the chapters.")

        # Make sure the given scene name exists.
        if scene_name not in chapters[1]:
            return

        # Each time a new scene plays, the dialog rectangle should be re-initialized
        # manually by the visual novel author, because any scene might start first,
        # without being transitioned-into from another scene.
        self.story.dialog_rectangle = None

        # So the main reader does not continue reading its script
        # (because a new main reader scene will be loaded/played soon).
        # Without this, loading a new scene will produce some expected results if
        # the scene we're coming out of has more lines of script in it after the <scene> line.
        self.story_finished = True

        # {chapter_name: scene_name}
        # When StoryReader() instantiates, it will look at the startup
        # script and will load it automatically.
        Passer.manual_startup_chapter_scene = {chapter_name: scene_name}

        # Create a new main reader
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
        movement_delay: cc.MovementDelay
        movement_delay = self._get_arguments(class_namedtuple=cc.MovementDelay,
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

        movement_speed: cc.MovementSpeed
        movement_speed = self._get_arguments(class_namedtuple=cc.MovementSpeed,
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

        # Set the directions to lowercase
        movement_speed._replace(x_direction=movement_speed.x_direction.lower())
        movement_speed._replace(y_direction=movement_speed.y_direction.lower())

        # Horizontal direction going left? Set the X to a negative int.
        if movement_speed.x_direction == "left":
            movement_speed = movement_speed._replace(x=-abs(movement_speed.x))

        # Vertical direction going up? Set the Y to a negative int.
        if movement_speed.y_direction == "up":
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

    def _font_text_fade_speed(self,
                              arguments,
                              sprite_object: sd.SpriteObject = None):
        """
        Set the gradual text fade speed of the dialog text.
        It applies to both letter by letter fade-in and overall fade-in.
        
        Arguments:
        
        - arguments: an int between 1 and 10.
        1 is the slowest speed, 10 is the fastest speed.
        
        - sprite_object: this will be a SpriteObject instance if the font text
        option is being applied to a sprite object such as a character, object
        or dialog sprite. If it's None, then it's being applied to a dialog
        rectangle.
        """

        fade_speed: cc.FontTextFadeSpeed
        fade_speed =\
            self._get_arguments(class_namedtuple=cc.FontTextFadeSpeed,
                                given_arguments=arguments)

        fade_speed = fade_speed.fade_speed

        # Don't allow the speed to be less than 1 or more than 10
        if fade_speed > 10:
            fade_speed = 10
        elif fade_speed < 1:
            fade_speed = 1
            
        # Type-hint
        subject_font_handler: font_handler.ActiveFontHandler
            
        if sprite_object:
            # Sprite font handler (character, object, dialog sprite)
            subject_font_handler = sprite_object.active_font_handler
        else:
            # Dialog rectangle font handler
            subject_font_handler =\
                self.get_main_story_reader().active_font_handler
        
        subject_font_handler.font_animation.font_text_fade_speed = fade_speed

    def _font_text_delay_punc(self,
                              arguments,
                              sprite_object: sd.SpriteObject = None):
        """
        Set the number of frames to skip *after* a specific letter has
        finished being blitted.
        
        Arguments:
        
        - arguments: an int between 0 and 150.
        For example: a value of 2 means: apply the letter by letter animation
        every 2 frames. A value of 0 means apply the animation at every frame.
        
        - sprite_object: this will be a SpriteObject instance if the font text
        option is being applied to a sprite object such as a character, object
        or dialog sprite. If it's None, then it's being applied to a dialog
        rectangle.
        """

        delay_punc: cc.FontTextDelayPunc
        delay_punc =\
            self._get_arguments(class_namedtuple=cc.FontTextDelayPunc,
                                given_arguments=arguments)

        previous_letter = delay_punc.previous_letter
        delay_frame_count = delay_punc.number_of_frames

        # Don't allow the speed to be less than 0 or more than 150
        if delay_frame_count > 150:
            delay_frame_count = 150
        elif delay_frame_count < 0:
            delay_frame_count = 0
            
        # Get the font handler of either the sprite object (dialog sprite, object, character)
        # or the dialog rectangle.
        if sprite_object:
            # Sprite object font handler
            subject_font_handler = sprite_object.active_font_handler
        else:
            # Dialog rectangle font handler
            subject_font_handler = self.get_main_story_reader().active_font_handler
            
        # Add the after-previous-letter delay setting.
        subject_font_handler.font_animation.set_letter_delay(previous_letter, delay_frame_count)

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

    def _font_text_delay(self,
                         arguments,
                         sprite_object: sd.SpriteObject = None):
        """
        Set the number of frames to skip when animating letter-by-letter dialog text.
        Does not apply to letter fade-ins.
        
        Arguments:
        
        - arguments: an int between 0 and 600.
        For example: a value of 2 means: apply the letter by letter animation
        every 2 frames. A value of 0 means apply the animation at every frame.
        
        - sprite_object: this will be a SpriteObject instance if the font text
        option is being applied to a sprite object such as a character, object
        or dialog sprite. If it's None, then it's being applied to a dialog
        rectangle.

        Changes:
        Nov 4, 2023 (Jobin Rezai) - Fix <font_text_delay> trying to access the
        active font handler in a reusable script.
        """

        text_speed_delay: cc.FontTextDelay
        text_speed_delay =\
            self._get_arguments(class_namedtuple=cc.FontTextDelay,
                                given_arguments=arguments)
        
        text_speed_delay = text_speed_delay.number_of_frames

        # Don't allow the speed to be less than 0 or more than 600
        # 600 means 10 seconds (60 frames X 10).
        if text_speed_delay > 600:
            text_speed_delay = 600
        elif text_speed_delay < 0:
            text_speed_delay = 0
            
        # Type-hint
        subject_font_handler: font_handler.ActiveFontHandler
            
        if sprite_object:
            # Get the given sprite's font handler (object, dialog sprite, or character)
            subject_font_handler = sprite_object.active_font_handler
        else:
            # The active font handler is only available in the main reader, not in reusable scripts.
            subject_font_handler = self.get_main_story_reader().active_font_handler


        # Record the delay value
        subject_font_handler.font_animation.font_text_delay = text_speed_delay
        
        # For the initial text frame, consider the text delay limit having been reached,
        # so that the delay doesn't occur before the first letter has been shown.
        # Without this, the text delay will apply before the first letter has been shown.
        subject_font_handler.font_animation.gradual_delay_counter = text_speed_delay

    def _font_start_position(self,
                             x: bool,
                             arguments: str,
                             sprite_object: sd.SpriteObject = None):
        """
        Set the X or Y starting position of the active font, relative
        to the dialog rectangle. The default is 0.
        
        Arguments:
        
        - x: (bool) True if setting the text position for X
        False if setting the text position for Y
        
        - arguments: this is expected to contain a numeric string value
        for the starting position of either X or Y, relative to the active
        dialog rectangle.
        
        - sprite_object: this will be a SpriteObject instance if the font text
        option is being applied to a sprite object such as a character, object
        or dialog sprite. If it's None, then it's being applied to a dialog
        rectangle.
        """
        
        start_position: cc.FontStartPosition
        start_position =\
            self._get_arguments(class_namedtuple=cc.FontStartPosition,
                                given_arguments=arguments)

        if not start_position:
            return
        
        # Type-hint
        subject_font_handler: font_handler.ActiveFontHandler
        
        if sprite_object:
            # Sprite font handler (character, object, or dialog sprite)
            subject_font_handler = sprite_object.active_font_handler
        else:
            # Dialog rectangle font handler
            subject_font_handler =\
                self.get_main_story_reader().active_font_handler

        # Should we set the text start position for X or Y?
        if x:
            subject_font_handler.default_x_position =\
                start_position.start_position
        else:
            subject_font_handler.default_y_position =\
                start_position.start_position

    def _sprite_text_get_basic_values(self, arguments: str) -> Tuple | None:
        """
        Get the basic variables that are shared amongst all the
        <sprite_text...> commands.
        
        Return: a tuple (the sprite, sprite type, sprite_text (argument info))
        """
        
        sprite_text: cc.SpriteText
        sprite_text = self._get_arguments(class_namedtuple=cc.SpriteText,
                                          given_arguments=arguments)

        if not sprite_text:
            return
        
        # Get the type of sprite (ie: object, dialog sprite, character)
        sprite_type: file_reader.ContentType
        sprite_type =\
            dialog_rectangle.to_enum(cls=file_reader.ContentType,
                                     string_representation=sprite_text.sprite_type)         
        
        # Make sure we have a ContentType Enum
        if not isinstance(sprite_type, file_reader.ContentType):
            return
        
        # Get the visible sprite
        sprite: sd.SpriteObject
        sprite =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                          general_alias=sprite_text.general_alias)

        if not sprite:
            return
        
        return (sprite, sprite_text)

    def _sprite_text_start_position(self, x: bool, arguments: str):
        """
        Set the X or Y starting position of the active font, relative
        to the object itself (character, object, or dialog sprite).
        The default is 0.
        
        Arguments:
        
        - x: (bool) True if setting the text position for X
        False if setting the text position for Y
        
        - arguments: a numeric string value
        """
        
        # Type-hints
        sprite: sd.SpriteObject
        command_arguments: cc.SpriteText
        
        # Get the sprite we want to deal with
        # and the command arguments we want to apply.
        sprite_details = self._sprite_text_get_basic_values(arguments=arguments)
        if not sprite_details:
            return
        
        # Split tuple
        sprite, command_arguments = sprite_details
        
        # Set the font's starting position relative to the sprite object.
        self._font_start_position(x=x,
                                  arguments=command_arguments.value,
                                  sprite_object=sprite)

    def _sprite_text_font(self, arguments: str):
        """
        Specify a font to use for a sprite (object, dialog sprite, object)
        <sprite_text_font: character, rave, Some Font Name Here>
        """
        
        # Type-hints
        sprite: sd.SpriteObject
        command_arguments: cc.SpriteText
        
        # Get the sprite we want to deal with
        # and the command arguments we want to apply.
        sprite_details = self._sprite_text_get_basic_values(arguments=arguments)
        if not sprite_details:
            return
        
        # Split tuple
        sprite, command_arguments = sprite_details
        
        # Set the font to use for the given sprite.
        sprite.active_font_handler.set_active_font(font_name=command_arguments.value)

    def _sprite_text_font_intro(self, arguments: str):
        """
        Set the intro type of a sprite font's animation
        (object, dialog sprite, object)
        <sprite_text_font_intro: character, rave, animation type here>
        
        Possible values for animation types:
        sudden
        fade in
        gradual letter
        gradual letter fade in
        """
    
        # Type-hints
        sprite: sd.SpriteObject
        command_arguments: cc.SpriteText
        
        # Get the sprite we want to deal with
        # and the command arguments we want to apply.
        sprite_details = self._sprite_text_get_basic_values(arguments=arguments)
        if not sprite_details:
            return
        
        # Split tuple
        sprite, command_arguments = sprite_details
        
        # active_font_handler will always been initialized to something, 
        # it won't be None.
        self._font_intro_animation(arguments=command_arguments.value,
                                   sprite_object=sprite)     

    def _sprite_text_font_fade_speed(self, arguments: str):
        """
        Set the gradual text fade speed of the dialog text.
        It applies to both letter by letter fade-in and overall fade-in.
        """
    
        # Type-hints
        sprite: sd.SpriteObject
        command_arguments: cc.SpriteText
        
        # Get the sprite we want to deal with
        # and the command arguments we want to apply.
        sprite_details = self._sprite_text_get_basic_values(arguments=arguments)
        if not sprite_details:
            return
        
        # Split tuple
        sprite, command_arguments = sprite_details
        
        # Set the gradual text fade speed of the dialog text.
        # It applies to both letter by letter fade-in and overall fade-in.     
        self._font_text_fade_speed(arguments=command_arguments.value,
                                   sprite_object=sprite)

    def _sprite_text_font_delay(self, arguments: str):
        """
        Set the number of frames to skip when animating letter-by-letter dialog text.
        Does not apply to letter fade-ins.
        """
    
        # Type-hints
        sprite: sd.SpriteObject
        command_arguments: cc.SpriteText
        
        # Get the sprite we want to deal with
        # and the command arguments we want to apply.
        sprite_details = self._sprite_text_get_basic_values(arguments=arguments)
        if not sprite_details:
            return
        
        # Split tuple
        sprite, command_arguments = sprite_details
        
        # Set the number of frames to skip when animating letter-by-letter dialog text.
        # Does not apply to letter fade-ins.        
        self._font_text_delay(arguments=command_arguments.value,
                              sprite_object=sprite)
        
    def _sprite_text_font_delay_punc(self, arguments: str):
        """
        Set the number of frames to skip *after* a specific letter has
        finished being blitted.
        """
    
        # Type-hints
        sprite: sd.SpriteObject
        command_arguments: cc.SpriteText
        
        # Get the sprite we want to deal with
        # and the command arguments we want to apply.
        sprite_details = self._sprite_text_get_basic_values(arguments=arguments)
        if not sprite_details:
            return
        
        # Split tuple
        sprite, command_arguments = sprite_details
        
        # Set the number of frames to skip *after* a specific letter has
        # finished being blitted.      
        self._font_text_delay_punc(arguments=command_arguments.value,
                                   sprite_object=sprite)

    def _sprite_text_clear(self, arguments: str):
        """
        Clear any text that is displayed on a specific sprite.
        Copy original_image_before_text to original_image.
        
        <sprite_text_clear: character, rave>
        """

        # Type-hints
        sprite: sd.SpriteObject
        command_arguments: cc.SpriteTextClear
        
        # Get the sprite we want to deal with
        # and the command arguments we want to apply.
        sprite_details = self._sprite_text_get_basic_values(arguments=arguments)
        if not sprite_details:
            return
        
        # Split tuple
        sprite, command_arguments = sprite_details
        
        # Are we just clearing text?
        if not command_arguments.value:
            sprite.clear_text_and_redraw()
            return
        
        # Prepare letter sprites for blitting later.
        sprite.active_font_handler.process_text(line_text=command_arguments.value)
        
        # If sudden-text was already blitted before (from previous text), 
        # reset the blitted flag so we can append more sudden-text.
        if sprite.active_font_handler.font_animation.start_animation_type == font_handler.FontAnimationShowingType.SUDDEN \
           and sprite.active_font_handler.sudden_text_drawn_already:
            sprite.active_font_handler.reset_sudden_text_finished_flag()
        
        # Start showing animation of font text, unless it's set to
        # sudden-mode.        
        sprite.active_font_handler.font_animation.\
            start_show_animation(letters=sprite.active_font_handler.letters_to_blit)

    def _sprite_text(self, arguments: str):
        """
        Add font sprite sheet text to a sprite (object, dialog sprite, object)
        <sprite_text: character, rave, Some Text Here>
        
        Purpose: to allow the visual novel author to create buttons.
        """

        # Type-hints
        sprite: sd.SpriteObject
        command_arguments: cc.SpriteText
        
        # Get the sprite we want to deal with
        # and the command arguments we want to apply.
        sprite_details = self._sprite_text_get_basic_values(arguments=arguments)
        if not sprite_details:
            return
        
        # Split tuple
        sprite, command_arguments = sprite_details
        
        # Are we just clearing text?
        if not command_arguments.value:
            sprite.clear_text_and_redraw()
            return
        
        # Prepare letter sprites for blitting later.
        sprite.active_font_handler.process_text(line_text=command_arguments.value)
        
        # If sudden-text was already blitted before (from previous text), 
        # reset the blitted flag so we can append more sudden-text.
        if sprite.active_font_handler.font_animation.start_animation_type == font_handler.FontAnimationShowingType.SUDDEN \
           and sprite.active_font_handler.sudden_text_drawn_already:
            sprite.active_font_handler.reset_sudden_text_finished_flag()
        
        # Start showing animation of font text, unless it's set to
        # sudden-mode.        
        sprite.active_font_handler.font_animation.\
            start_show_animation(letters=sprite.active_font_handler.letters_to_blit)       

    def _condition_else(self):
        """
        If the last condition evaluated to True (the story reader
        is not bound to a condition name in self.condition_name_false),
        then make the story reader enter skip-mode so the script below
        <case_else> doesn't run.
        <case_end> will be needed eventually to make the reader
        get out of skip-mode.
        
        If the last condition evaluated to False (the story reader
        is bound to a condition name in self.condition_name_false), then
        the story reader is already in skip-mode so get it out of skip-mode
        so that the script below <case_else> will run.
        <case_end> is not technically needed in this situation because
        it's no longer in skip-mode, but having <case_end> is ok too.
        """
        
        # Did the last condition evaluate to True?
        if not self.condition_name_false:
            
            # Enter skip-mode so the script below 'case_else' won't run.
            self.condition_name_false = "!else-condition!"
        
        else:
            # The last condition evaluated to False.
            
            # Get the story reader out of skip-mode so that the script
            # below 'case_else' will run.
            self.condition_name_false = None

    def _exit(self):
        """
        Finish the current script automatically without reaching the end.
        
        Purpose: used for exiting any type of script (chapter, scene,
        reusable script) before it reaches the end of the script. One example
        use case is not having sufficient 'credits' or 'score' to buy an item,
        so the store owner character no longer has anything to say.
        """
        self.story_finished = True

    def _condition_end(self):
        """
        Get the story reader out of 'skip-mode' so it doesn't keep
        skipping script lines due to a condition in the past being
        evaluated to False.
        """
        self.condition_name_false = None

    def _condition_read(self, command_name: str, arguments: str):
        """
        Check if a condition evaluates to True or False.
        If it's False, set a flag for the current reader to ignore
        all upcoming script lines unless it reaches an
        <or_case> command or <case_end> command.
        
        Example of a condition:
        <case: 10, more than, 5, number check>`
        """
        
        # In the case of a <case> command, if no condition name was provided,
        # then generate a random name. Reason: the <case> command's condition
        # name is optional, and is used only if the visual novel writer
        # plans on using an <or_case> later.
        if arguments.count(",") == 2:
            
            # No condition name was provided. Generate a random string.
            random_condition_name = string.ascii_letters + string.digits
            random_condition_name =\
                "".join([secrets.choice(random_condition_name)
                         for item in range(12)])
            
            # Add the random condition name to the arguments.
            arguments += f", {random_condition_name}"
        
        condition: cc.ConditionDefinition
        condition = self._get_arguments(class_namedtuple=cc.ConditionDefinition,
                                        given_arguments=arguments)
        
        condition_checker = Condition(value1=condition.value1,
                                      value2=condition.value2,
                                      operator=condition.operator)
        
        
        # If <or_case> is used, make sure the story reader is in
        # skip-mode (in other words, a condition evaluated to False before).
        if command_name == "or_case":
            if self.condition_name_false:
                
                # Is the condition name that evaluated to False before the
                # same condition name in the <or_case> command?
                if self.condition_name_false != condition.condition_name:
                    # The <or_case> has a different name than the
                    # last condition that evaluated to False, so we shouldn't
                    # process this <or_case> command.
                    return
            else:
                # This story reader is not in skip-mode, so the <or_case>
                # doesn't need to be evaluated.
                return
        
        if condition_checker.evaluate():
            # Evaluation passed
            
            # Clear the variable that holds the condition name that
            # evaluated to False. This variable might be set to something if
            # the <or_case> command was used here, so we clear it here
            # to make sure the story reader is not in skip-mode.
            self.condition_name_false = None
            
        else:
            # Evaluated to False
            
            # Keep track of the latest condition that evaluated to False
            # so we can end it using <case_end> or give it another chance
            # with <or_case>.
            self.condition_name_false = condition.condition_name

    def _play_audio(self, arguments: str, audio_channel: audio_player.AudioChannel):
        """
        Play an audio file through the appropriate channel.
        
        If the command is <play_music>, check if the music should be looped.
        """
        
        loop_music = False
        audio_name = None
        
        # If it's a play_music command and there's a second argument,
        # check if the song needs to be looped.
        
        # <play_music: name, loop>
        if audio_channel == audio_player.AudioChannel.MUSIC and arguments.count(",") == 1:
            
            # <play_music: name, loop>
            audio_name, loop_music = self._split_arguments_to_tuple(arguments=arguments)
            
            # Only allow the string, "loop", as an argument for looping.
            if loop_music.lower() != "loop" or not audio_name:
                return
            
            loop_music = True
          
        else:
            # We're playing an audio file or a music file with no loop.
            
            play_audio: cc.PlayAudio
            play_audio = self._get_arguments(class_namedtuple=cc.PlayAudio,
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
        halt_auto: cc.HaltAuto
        halt_auto = self._get_arguments(class_namedtuple=cc.HaltAuto,
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
        """
        Set a flag so the dialog text won't clear
        when the next halt or halt_auto is reached.
        """
        
        main_reader = self.get_main_story_reader()
        main_reader.active_font_handler.font_animation. \
            no_clear_handler.pass_clearing_next_halt = True

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
        rest: cc.Rest
        rest = self._get_arguments(class_namedtuple=cc.Rest,
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

    def get_sprite_type_from_command(self, command_name: str) -> file_reader.ContentType:
        """
        Return the type of sprite the command is for based
        on the command name.
        """
        if "character" in command_name:
            return file_reader.ContentType.CHARACTER
        elif "object" in command_name:
            return file_reader.ContentType.OBJECT
        elif "dialog" in command_name:
            return file_reader.ContentType.DIALOG_SPRITE

    def _mouse_event_reusable_script(self, command_name, arguments: str):
        """
        When a mouse action occurs, run a specific reusable script.
        """
        
        class_name = cc.MouseEventRunScriptWithArguments \
            if arguments.count(",") >=2 \
            else cc.MouseEventRunScriptNoArguments
        
        mouse_run_script: cc.MouseEventRunScriptWithArguments
        mouse_run_script =\
            self._get_arguments(class_namedtuple=class_name,
                                given_arguments=arguments)
        
        if not mouse_run_script:
            return
        
        # Determine the sprite type that the command will be applied to
        # based on the command name.
        sprite_type =\
            self.get_sprite_type_from_command(command_name=command_name)
        
        # Get the visible sprite based on the general alias
        # Used for setting a reusable script to run when specific
        # mouse events occur on the sprite.
        existing_sprite: sd.SpriteObject =\
            self.story.get_visible_sprite(content_type=sprite_type,
                                    general_alias=mouse_run_script.sprite_name)

        if not existing_sprite:
            return
        
        if class_name == cc.MouseEventRunScriptWithArguments:
            reusable_script_name = mouse_run_script.reusable_script_name + \
                ", " + mouse_run_script.arguments
            
        elif class_name == cc.MouseEventRunScriptNoArguments:
            reusable_script_name = mouse_run_script.reusable_script_name
        
        # Set the name of the reusable script to run when a specific 
        # mouse event occurs.
        if "_mouse_enter" in command_name:
            existing_sprite.on_mouse_enter_run_script = reusable_script_name
            
        elif "_mouse_leave" in command_name:
            existing_sprite.on_mouse_leave_run_script = reusable_script_name
            
        elif "_mouse_click" in command_name:
            existing_sprite.on_mouse_click_run_script = reusable_script_name

    def _wait_for_animation(self, arguments: str):
        """
        Pause the main story reader until a specific animation has finished.
        This is similar to <halt> except it's not interactive (mouse-clicking)
        will not resume it.

        It forces the main reader to pause.
        It has no effect on background readers.
        """

        # <wait_for_animation: fade screen> ?
        if "," not in arguments:
            # There are no commas, which means it is probably:
            # <wait_for_animation: fade screen>

            wait_for_fade_screen: cc.WaitForAnimationFadeScreen
            wait_for_fade_screen =\
                self._get_arguments(
                    class_namedtuple=cc.WaitForAnimationFadeScreen,
                    given_arguments=arguments)

            if not wait_for_fade_screen:
                return

            if wait_for_fade_screen.fade_screen.lower() != "fade screen":
                return

            # Get the story reader that's not a reusable script reader,
            # because everything in this method involves the main reader only.
            main_reader = self.get_main_story_reader()

            main_reader.wait_for_animation_handler.enable_wait_for(sprite_type="cover",
                                                                   general_alias=None,
                                                                   animation_type=None)

        else:
            # We probably need to wait for a specific type of sprite.
            # Example: <wait_for_animation: character, theo, move>

            wait_for_sprite_animation: cc.WaitForAnimation
            wait_for_sprite_animation =\
                self._get_arguments(class_namedtuple=cc.WaitForAnimation,
                                    given_arguments=arguments)

            if not wait_for_sprite_animation:
                return

            # Get the story reader that's not a reusable script reader,
            # because everything in this method involves the main reader only.
            main_reader = self.get_main_story_reader()

            main_reader.wait_for_animation_handler. \
                enable_wait_for(sprite_type=wait_for_sprite_animation.sprite_type,
                                general_alias=wait_for_sprite_animation.general_alias,
                                animation_type=wait_for_sprite_animation.animation_type)

    def _scene_with_fade(self, arguments: str):
        """
        Gradually fade in, then fade-out a color that covers the entire pygame window.
        Right before it starts fading out, play a specific scene.
        This is used when transitioning between scenes.
        """
        scene_with_fade: cc.SceneWithFade
        scene_with_fade = self._get_arguments(class_namedtuple=cc.SceneWithFade,
                                              given_arguments=arguments)

        if not scene_with_fade:
            return

        # Get the story reader that's not a reusable script reader,
        # because everything in this method involves the main reader only.
        main_reader = self.get_main_story_reader()

        # Start off with zero opacity in fade-in mode
        direction = cover_screen_handler.FadeDirection.FADE_IN
        initial_fade = 0

        incremental_fade_in_speed = \
            self._sprite_fade_speed_get_value_from_percent(percent=scene_with_fade.fade_in_speed,
                                                           fade_direction="fade in")

        incremental_fade_out_speed = \
            self._sprite_fade_speed_get_value_from_percent(percent=scene_with_fade.fade_out_speed,
                                                           fade_direction="fade out")

        # None and zero are not proper values and will result to an exception.
        if not all([incremental_fade_in_speed, incremental_fade_out_speed]):
            return

        # So the main reader does not continue reading while
        # the screen is fading-out. (a new scene will be shown soon).
        main_reader.story_finished = True

        main_reader.story.cover_screen_handler. \
            start_fading_screen(hex_color=scene_with_fade.hex_color,
                                initial_fade_value=initial_fade,
                                fade_in_speed_incremental=incremental_fade_in_speed,
                                fade_out_speed_incremental=incremental_fade_out_speed,
                                hold_frame_count=scene_with_fade.fade_hold_for_frame_count,
                                chapter_name=scene_with_fade.chapter_name,
                                scene_name=scene_with_fade.scene_name,
                                fade_direction=direction)

    def _sprite_hide(self,
                     arguments: str,
                     sprite_type: file_reader.ContentType):
        """
        Hide a sprite (any sprite, such as character, name)
        by setting its visibility to False.
        
        Find the sprite using its general alias.
        """
        name: cc.SpriteShowHide
        name = self._get_arguments(class_namedtuple=cc.SpriteShowHide,
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
        Show a sprite (any sprite, such as character, object, dialog sprite)
        by setting its visibility to True.

        Changes:
        Oct 12, 2023 - Match flip values when swapping sprites (Jobin Rezai)
        """
        name: cc.SpriteShowHide
        name = self._get_arguments(class_namedtuple=cc.SpriteShowHide,
                                   given_arguments=arguments)

        if not name:
            return

        # Set the visibility to True and also
        # set a flag to indicate in the next sprite update that we should
        # update the screen rect of this sprite.

        # Is there a sprite with a general alias that matches
        # what we want to show? If so, replace that sprite with
        # the new sprite that we have now.

        if sprite_type not in (file_reader.ContentType.CHARACTER,
                           file_reader.ContentType.OBJECT,
                           file_reader.ContentType.DIALOG_SPRITE,
                           file_reader.ContentType.BACKGROUND):
            return

        if sprite_type == file_reader.ContentType.CHARACTER:
            sprite_group = sd.Groups.character_group

        elif sprite_type == file_reader.ContentType.OBJECT:
            sprite_group = sd.Groups.object_group

        elif sprite_type == file_reader.ContentType.DIALOG_SPRITE:
            sprite_group = sd.Groups.dialog_group
            
        elif sprite_type == file_reader.ContentType.BACKGROUND:
            sprite_group = sd.Groups.background_group
            
        loaded_sprite: sd.SpriteObject
        loaded_sprite = sprite_group.sprites.get(name.sprite_name)
        
        if not loaded_sprite:
            return
        
        # Is the sprite already visible and not waiting to hide? return
        # because the sprite is already fully visible.
        elif loaded_sprite.visible and not loaded_sprite.pending_hide:
            return            

        # Find the sprite that we're swapping 'out'
        visible_sprite: sd.SpriteObject
        visible_sprite = None
        
        current_visible_sprite: sd.SpriteObject
        for current_visible_sprite in sprite_group.sprites.values():
            
            # Did we find a fully visible sprite with the same alias?
            # If so, we'll swap that sprite out.
            if current_visible_sprite.visible and \
                       current_visible_sprite.general_alias == loaded_sprite.general_alias:
                
                # We found a visible sprite with the same alias.
                # and it's not the same sprite that we're swapping in, 
                # because the sprite names are different.
                visible_sprite = current_visible_sprite                    
                break
            
            # Did we find a pending visible sprite with the same alias?
            # Keep a reference to it in case we don't find a fully visible
            # sprite with the same alias, but don't stop checking for
            # visible sprites yet.
            elif current_visible_sprite.pending_show and \
               current_visible_sprite.general_alias == loaded_sprite.general_alias:
                
                # We found a visible sprite with the same alias,
                # but don't break out of the loop yet because this sprite
                # is only pending to be visible, it's not fully visible yet.
                # Keep looping to see if there is a fully visible sprite
                # with the same alias, and if not, we'll end up swapping 
                # out this sprite.
                visible_sprite = current_visible_sprite                    


        # Did we end up finding a visible sprite with the same alias?
        if visible_sprite:

            # Copy the currently visible sprite
            # so that we can turn this copy into a new sprite later.
            copied_visible_sprite = copy.copy(visible_sprite)

            # Keep track of the center of the current sprite
            # so we can restore the center when the new
            # sprite is shown. If we don't do this, the new sprite
            # will show up in a different position.
            current_center = visible_sprite.rect.center

            # Get the new image that we want to show
            copied_visible_sprite.original_image = loaded_sprite.original_image
            copied_visible_sprite.original_image_before_text = loaded_sprite.original_image_before_text
            copied_visible_sprite.original_rect = loaded_sprite.original_rect
            copied_visible_sprite.image = loaded_sprite.image
            copied_visible_sprite.rect = loaded_sprite.rect
            copied_visible_sprite.name = loaded_sprite.name
            

            # Update the active font handler's sprite reference
            # (if there is one) to the new sprite that has 
            # the new images. If we don't do this, the active font
            # handler will have a reference to the swapped-out sprite
            # rather than the newly swapped-in sprite, and then text
            # won't display on the new sprite.
            if copied_visible_sprite.active_font_handler \
               and copied_visible_sprite.active_font_handler.sprite_object:

                # Update sprite reference
                copied_visible_sprite.active_font_handler.sprite_object =\
                    copied_visible_sprite
                
                ## Prepare letter sprites for blitting later.
                #copied_visible_sprite.active_font_handler.process_text(line_text="")
                
                # If sudden-text was already blitted before (from previous text), 
                # reset the blitted flag so we can append more sudden-text.
                # We need this block for sudden text to show after the swap.
                if copied_visible_sprite.active_font_handler.\
                   font_animation.start_animation_type ==\
                   font_handler.FontAnimationShowingType.SUDDEN \
                   and copied_visible_sprite.active_font_handler.\
                   sudden_text_drawn_already:
                    
                    # Reset sudden-mode finished-showing flag
                    copied_visible_sprite.active_font_handler.\
                        reset_sudden_text_finished_flag()
                
                
                """
                There is no need to re-run an animation if the sprite's text
                has already finished animating. Only animate the sprite's text
                if the previous sprite was in the middle of animating the
                sprite's text and this new sprite that's being swapped-in needs
                to continue the previous sprite's animation. However, if the
                previous sprite had already finished showing the sprite's text,
                prevent the newly swapped-in sprite from restarting the font
                animation. But each time a sprite is swapped-in, it technically
                has to re-draw the sprite's text. So what we need to do is
                temporarily set the font's text to 'sudden' mode and after the
                newly swapped-in sprite's text has been shown, then set it back
                to whatever animation type the 'old' sprite's text had, just in
                case more text gets appended to the sprite's text later on
                or if the sprite's text gets changed.
                """

                """
                'copied_visible_sprite' is the 'new' sprite that's
                being swapped-in, but it also has attributes from
                the old sprite that is being swapped-out, such as
                the sprite text font intro animation type 
                and animation status.
                """

                # Initialize
                copied_visible_sprite. \
                    active_font_handler.font_animation. \
                    restore_sprite_intro_animation_type = None

                # If the old sprite's animation type is not sudden-mode
                # and has already finished animating the intro text font 
                # animation, we'll need to temporarily set the new sprite's 
                # text font intro animation to SUDDEN, so that the sprite 
                # text's animation doesn't re-run.
                if copied_visible_sprite.active_font_handler\
                   .font_animation.start_animation_type != \
                   font_handler.FontAnimationShowingType.SUDDEN \
                   and not copied_visible_sprite.active_font_handler.\
                   font_animation.is_start_animating:
                    
                    # The sprite's text intro animation is not sudden-mode
                    # and the sprite's text has finished animating.
                    
                    # Get the animation-type of the sprite that's being
                    # swapped-out.
                    old_sprite_animation_type = \
                        copied_visible_sprite.active_font_handler \
                            .font_animation.start_animation_type

                    # Temporarily set the newly-swapped in's font intro
                    # animation to sudden-mode so that the
                    # new sprite's text animation doesn't run again.
                    # We need to do this for the newly swapped sprite's text
                    # to show text; otherwise the text won't appear for the
                    # newly swapped-in sprite.
                    copied_visible_sprite.active_font_handler\
                        .font_animation.start_animation_type\
                        = font_handler.FontAnimationShowingType.SUDDEN

                    # Record the old/original font intro animation type
                    # to indicate that we should change the sprite's intro
                    # animation type back later on.
                    copied_visible_sprite. \
                        active_font_handler.font_animation. \
                        restore_sprite_intro_animation_type = \
                        old_sprite_animation_type


            # Record whether the new sprite has been flipped in any way
            # at any time in the past, because we'll need to compare the flip
            # values with the sprite that is being swapped out later in this method.
            copied_visible_sprite.flipped_horizontally = loaded_sprite.flipped_horizontally
            copied_visible_sprite.flipped_vertically = loaded_sprite.flipped_vertically

            # The new sprite does not have any scale/rotate/fade effects
            # applied to it, but the flags (self.applied..) at this 
            # point indicate that effects are applied 
            # (those flags are not up-to-date).
            # So reset the flags so that we will end up applying
            # necessary effects to make it match the effects of 
            # the previous sprite.
            copied_visible_sprite.reset_applied_effects()

            # Make the new sprite the same as the current sprite
            # but with the new images, rects, and new name.
            loaded_sprite = copied_visible_sprite
            

            # Restore the center position so the new sprite
            # will be positioned exactly where the old sprite is.
            loaded_sprite.rect.center = current_center

            # Hide the old sprite (that we're swapping out)
            visible_sprite.start_hide()

            # If the sprite that is being swapped out was flipped horizontally and/or vertically,
            # then make sure the new sprite is flipped horizontally and/or vertically too.
            loaded_sprite.flip_match_with(visible_sprite)

            # Show the new sprite (that we're swapping in)
            loaded_sprite.start_show()

            # Update the new sprite in the main character sprites dictionary
            sprite_group.sprites[loaded_sprite.name] = loaded_sprite



        # If the sprite is not already visible, start to make it visible.
        if not loaded_sprite.visible:

            # If the sprite is a background, hide all backgrounds
            # before showing the new background.

            # Reason: only 1 background at a time should be allowed
            # to be displayed.
            if sprite_type == file_reader.ContentType.BACKGROUND:
                sd.Groups.background_group.hide_all()

            loaded_sprite.start_show()
            
            ## Update the newly set-visible sprite in the sprites dictionary
            #sprite_group.sprites[loaded_sprite.name] = loaded_sprite            

    def _text_dialog_close(self):
        """
        Start the outro animation of the dialog rectangle if it's visible.
        """
        if self.story.dialog_rectangle and self.story.dialog_rectangle.visible:
            # Used to indicate that the main script should pause
            self.animating_dialog_rectangle = True

            self.story.dialog_rectangle.start_hide()

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

        dialog_rectangle_arguments: cc.DialogRectangleDefinition
        dialog_rectangle_arguments = self._get_arguments(class_namedtuple=cc.DialogRectangleDefinition,
                                                         given_arguments=arguments)

        if not dialog_rectangle_arguments:
            return

        # Get the main reader, because a dialog rectangle can only
        # be part of the main reader.
        main_reader = self.get_main_story_reader()

        # If the dialog is currently visible, don't allow the properties
        # to change while it's being displayed.
        if main_reader.story.dialog_rectangle and main_reader.story.dialog_rectangle.visible:
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
        if reusable_on_intro_starting == "none":
            reusable_on_intro_starting = None

        reusable_on_intro_finished =\
            dialog_rectangle_arguments.reusable_on_intro_finished
        if reusable_on_intro_finished == "none":
            reusable_on_intro_finished = None
        
        reusable_on_outro_starting =\
            dialog_rectangle_arguments.reusable_on_outro_starting
        if reusable_on_outro_starting == "none":
            reusable_on_outro_starting = None
        
        reusable_on_outro_finished =\
            dialog_rectangle_arguments.reusable_on_outro_finished
        if reusable_on_outro_finished == "none":
            reusable_on_outro_finished = None
        
        reusable_on_halt = dialog_rectangle_arguments.reusable_on_halt
        if reusable_on_halt == "none":
            reusable_on_halt = None

        reusable_on_unhalt = dialog_rectangle_arguments.reusable_on_unhalt
        if reusable_on_unhalt == "none":
            reusable_on_unhalt = None

        main_reader.story.dialog_rectangle = \
            dialog_rectangle.DialogRectangle(
                main_screen=main_reader.story.main_surface,
                width_rectangle=dialog_rectangle_arguments.width,
                height_rectangle=dialog_rectangle_arguments.height,
                animation_speed=dialog_rectangle_arguments.animation_speed,
                intro_animation=intro_animation,
                outro_animation=outro_animation,
                anchor=anchor,
                bg_color_hex=dialog_rectangle_arguments.bg_color_hex,
                animation_finished_method=main_reader.on_dialog_rectangle_animation_completed,
                spawn_new_background_reader_method=main_reader.spawn_new_background_reader,
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
                except ValueError:
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
        # or
        # "cover" (single string) which means screen cover (screen fade-in/fade-out)
        self.wait_list = []

    def enable_wait_for(self, sprite_type: str, general_alias: str = None, animation_type: str = None):
        """
        Record a new reason to pause the main story reader.
        Reusable scripts are not affected.
        """

        # Should we wait for a screen cover animation? (ie: <scene_with_fade>
        if sprite_type == "cover":

            # Already in the wait_list? return.
            if "cover" in self.wait_list:
                return

            self.wait_list.append("cover")
        else:

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

            # Initialize
            wait = False

            if isinstance(wait_info, str) and wait_info == "cover":
                # Wait for a screen fade-in / fade-out animation to finish
                # (even if the screen is fully faded-in, it's still considered to be animating)
                if Passer.active_story.cover_screen_handler.is_cover_animating:
                    wait = True

            else:
                # Wait for a sprite to finish a specific animation

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

            # Consider pending_show to be visible.
            if not sprite_object.visible and not sprite_object.pending_show:
                continue
            elif not sprite_object.general_alias:
                continue
            elif sprite_object.general_alias != general_alias:
                continue

            # Check if a specific type of animation is occurring
            # on a specific sprite.
            if isinstance(animation_type, sd.SpriteAnimationType):
                
                # Fading in or out and haven't reached the fade destination?
                # Consider that as still animating.
                if WaitForAnimationHandler.\
                   is_fading_extended_check(sprite_object=sprite_object):
                    return True
                
                elif animation_type == sd.SpriteAnimationType.MOVE \
                     and sprite_object.is_moving:
                    return True
                
                elif animation_type == sd.SpriteAnimationType.ROTATE and sprite_object.is_rotating:
                    return True
                elif animation_type == sd.SpriteAnimationType.SCALE and sprite_object.is_scaling:
                    return True

            elif isinstance(animation_type, str):
                # Check if all the animations are occurring on the sprite.
                if animation_type == "all" and all([WaitForAnimationHandler.is_fading_extended_check(sprite_object=sprite_object),
                                                    sprite_object.is_moving,
                                                    sprite_object.is_rotating,
                                                    sprite_object.is_scaling]):
                    return True

                # Check if at least one animation is occurring on the sprite.
                elif animation_type == "any" and any([WaitForAnimationHandler.is_fading_extended_check(sprite_object=sprite_object),
                                                      sprite_object.is_moving,
                                                      sprite_object.is_rotating,
                                                      sprite_object.is_scaling]):
                    return True

    @staticmethod
    def is_fading_extended_check(sprite_object: sd.SpriteObject) -> bool:
        """
        Return whether the sprite object is busy fading in or fading out.
        
        Fading in or out and haven't reached the fade destination?
        Consider that as still animating.
        
        The reason we don't just use 'is_fading' is because when
        a destination fade value is somewhere in the middle, not
        fully transparent (0) and not fully opaque (255), then
        the flag 'is_fading' will still be True, even though it
        doesn't appear to be fading in or out anyomre.
        
        So we use the logic below to determine if it has actually
        reached its destination fade value, and we'll use that
        to know whether the sprite is still fading or not.
        """
        return sprite_object.is_fading \
        and isinstance(sprite_object.current_fade_value,
                       cc.FadeCurrentValue) \
        and isinstance(sprite_object.fade_until,
                       cc.FadeUntilValue) \
        and sprite_object.current_fade_value != sprite_object.fade_until.fade_value

class ReusableScriptArgument:
    """
    Used for keeping a reusable script and its argument names and values.

    The arguments only get populated when <call> is used on the reusable script.
    After each <call>, the 'old' arguments are cleared.

    For example:
    <call: move left>
    will run 'move left' with no arguments.

    whereas:
    <call: move left, character=theo>
    will run 'move left' with argument: {'character': 'theo'}
    After the reusable script finishes, the arguments for that reusable script will be cleared.

    If we run <call: move left> again, with no arguments
    then the old arguments {'character': 'theo') will no longer be there.
    """

    def __init__(self,
                 arguments: Dict = None):
        self.arguments = arguments

        # Arguments is a dict:
        # key: argument name
        # value: the value of the argument
        # example: {"character": "theo"}
        if arguments is None:
            self.arguments = {}

    def get_all_arguments(self) -> Dict:
        return self.arguments

    def get_argument_value(self, argument_name) -> str | None:
        return self.arguments.get(argument_name)

    def add_arguments(self, arguments: Dict):
        self.arguments = self.arguments | arguments

    def clear_arguments(self):
        self.arguments.clear()
