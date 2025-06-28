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

import sys
import pygame
import argparse
import sprite_definition as sd
import web_handler
from active_story import ActiveStory
from file_reader import FileReader
from shared_components import Passer
from datetime import datetime
from launch_window import LaunchWindow
from io import BytesIO
from typing import Dict
from pathlib import Path
from pygame import scrap

# We need to add the parent directory so
# the container_handler module will be seen.
this_module_path = Path(__file__)
one_level_up_directory = str(Path(*this_module_path.parts[0:-2]))
sys.path.append(one_level_up_directory)
from container_handler import ContainerHandler


class Main:

    def __init__(self):

        self.launch_window: LaunchWindow
        self.launch_window = None

    def show_launch_window(self, data_requester: FileReader):
        """
        Show the story's launch window, allowing the viewer to pick and choose
        which chapter or scene to play.
        
        Arguments:
        
        - data_requester: used for reading the story's info (name, etc) from
        an lvna file.
        """
        story_details = data_requester.general_header

        # Get the 'StoryInfo' dictionary, which contains details like
        # author, copyright, description, etc.
        story_info = story_details.get("StoryInfo")

        chapters_and_scenes = story_details.get("StoryChapterAndSceneNames")

        # Get the BytesIO of the poster image.
        # We're going to use this to show the poster image later.
        image_file_object = self._get_poster_image(data_requester=data_requester)

        # Instantiate the launch window
        self.launch_window = \
            LaunchWindow(story_info=story_info,
                         poster_file_object=image_file_object,
                         chapter_and_scene_names=chapters_and_scenes)
        
        # Center the launch window
        Passer.center_window_active_monitor(self.launch_window.mainwindow)

        # Run tkinter's main loop
        self.launch_window.run()

    def _get_poster_image(self, data_requester: FileReader) -> BytesIO:
        """
        Return the poster image (if any), as a BytesIO object.
        """

        # Example:
        # ['8-157434', '.png']
        range_and_file_extension = data_requester.general_header.get("PosterTitleImageLocation")

        if not range_and_file_extension:
            # There is no poster image for this visual novel.
            return

        # BytesRange object
        bytes_range = data_requester._extract_range(data_range=range_and_file_extension[0])

        # Get the image as bytes``
        bytes_data = data_requester.view[bytes_range.from_bytes:bytes_range.to_bytes]

        # Put the bytes into a BytesIO object
        file_object = BytesIO(bytes_data)

        return file_object
    
    def initialize_web(self, data_requester: FileReader):
        """
        Initialize web_handler for handling xml rpc connections for
        web-enabled visual novels. If it's not a web-enabled visual novel,
        initialize to Passer.web_handler to None.
        """
        
        story_details = data_requester.general_header

        # Get the 'StoryInfo' dictionary, which contains details like
        # author, copyright, description, etc.
        story_info = story_details.get("StoryInfo")        
        
        # bool
        web_enabled = story_info.get(web_handler.WebKeys.WEB_ACCESS.value)
        
        web_address = story_info.get(web_handler.WebKeys.WEB_ADDRESS.value)
        
        web_certificate = story_info.get(web_handler.WebKeys.WEB_CA_CERT.value)
        
        # If it's a shared license key, get it here.
        # If it's a private license key, we don't have it yet; this will be None
        web_key = story_info.get(web_handler.WebKeys.WEB_KEY.value)
        web_license_type =\
            story_info.get(web_handler.WebKeys.WEB_LICENSE_TYPE.value)
        
        if web_license_type == "private":
            web_license_type = web_handler.WebLicenseType.PRIVATE
        else:
            web_license_type = web_handler.WebLicenseType.SHARED
        
        # Initialize web_handler. This will be used throughout the visual
        # novel for interacting with flask and the database.
        
        # The callback method will be specified later, because the story reader
        # object hasn't been initialized yet at this point, which is where
        # the callback method is located.
        Passer.web_handler =\
            web_handler.WebHandler(
                web_key,
                web_address,
                web_license_type,
                web_certificate, 
                web_enabled,
                story_info.get("StoryTitle"),
                story_info.get("Episode"))

    def begin(self):

        # Read the .lvna file from the provided argument command switch.
        # The path to the .lvna file will be in args.file
        data_requester = FileReader(args.file)

        # Get the story's requestes window size
        # in pixels (width, height)
        screen_size = tuple(data_requester.general_header.get("StoryWindowSize"))

        # 'Draft' or 'Final'
        # To know whether to show the draft rectangle or not, and
        # whether to allow some keyboard shortcuts or not.
        compile_mode = data_requester.general_header.get("StoryCompileMode")

        draft_mode = compile_mode == "Draft"
        
        # Initialize web_handler for handling xml rpc connections
        self.initialize_web(data_requester=data_requester)

        # Should we show the launch window?
        if show_launch:
            self.show_launch_window(data_requester=data_requester)
            if Passer.close_after_launch_window:
                sys.exit(0)

        # screen_size = (640, 480)

        pygame.init()

        clock = pygame.time.Clock()

        pygame.display.set_caption("LVNAuth Player")

        # The app's icon file will be either in the current directory
        # or in the 'player' directory. It depends whether the visual novel
        # is being played from the editor, or directly.
        if ContainerHandler.is_in_snap_package() or ContainerHandler.is_in_flatpak_package():
            app_icon_path = ContainerHandler.get_lvnauth_editor_icon_path_small()
        else:
            # Not in a Snap package.
            app_icon_path = Path(r"app_icon_small.png")
            if not app_icon_path.exists():
                app_icon_path = Path(r"./player/app_icon_small.png")

        pygame.display.set_icon(pygame.image.load(app_icon_path))

        # Create the main surface
        main_surface = pygame.display.set_mode(screen_size)

        main_surface.fill((0, 0, 0))

        background_surface = pygame.Surface(size=screen_size)
        background_surface.fill((0, 0, 0))

        story = ActiveStory(screen_size=screen_size,
                            data_requester=data_requester,
                            main_surface=main_surface,
                            background_surface=background_surface,
                            draft_mode=draft_mode)
        Passer.active_story = story
        
        # Now that the story reader object has been initialized above, use
        # on_web_request_finished() as the callback method for xml rpc
        # replies. We couldn't specify the callback method earlier because
        # the story reader object hadn't been initialized yet.
        Passer.web_handler.callback_method_finished =\
            Passer.active_story.reader.on_web_request_finished

        # Holds the number of milliseconds elapsed in each frame
        milliseconds_elapsed = 0

        while story.story_running:

            # The number of milliseconds elapsed in this frame
            milliseconds_elapsed = clock.tick(60)

            main_surface.fill((0, 0, 0))

            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    story.story_running = False
                    
                    # Without the block below, attempting to
                    # close pygame using the window manager
                    # will sometimes freeze pygame.
                    pygame.display.quit()
                    sys.exit(0)
                    return
    
                elif event.type == pygame.KEYDOWN:
                    self.on_key_down(event.key)
    
                else:
                    story.on_event(event)
                    
            # Check for <remote> finished requests.
            self.check_queue()

            # Handle movements
            story.on_loop()

            # Handle drawing
            story.on_render()
            

            # For debugging
            pygame.display.flip()
            
    def check_queue(self):
        """
        Read the queue that was sent by a secondary thread.
        This method will run in the main pygame thread.
        
        This method for polling is for within pygame, not tkinter.
        This method is used for reading responses from the <remote> command.
        """
        
        if web_handler.WebHandler.the_queue.empty():
            return
        
        msg = web_handler.WebHandler.the_queue.get()
                
        self.run_remote_finished_method(msg=msg)
        
    def run_remote_finished_method(self, msg):
        """
        Run the finished method from the ServerResponseReceipt msg,
        initiated from a <remote> command.
        """
        msg.callback_method(msg)

    def on_key_down(self, key_pressed):
        """
        Handle keyboard letter presses.

        Changes:
        Nov 4, 2023 (Jobin Rezai) - Copy sprite horizontal / vertical flip values,
        but only if the values have been changed.
        """

        # The following key presses only apply to draft-mode.
        if not Passer.active_story.draft_mode:
            return

        if key_pressed == pygame.K_h:
            # Toggle the visibility of the draft rectangle.
            Passer.active_story.draft_rectangle.toggle_visibility()

        elif key_pressed == pygame.K_c:
            """
            Copy the visible sprite locations, as commands, to the clipboard.
            """

            # The lines that will be copied to the clipboard.
            copy_info = []

            # The words to use in the commands.
            group_words = {0: "character",
                           1: "object",
                           2: "dialog_sprite"}

            # Loop through all visible sprites in 3 sprite groups
            # and generate the X/Y commands for them.
            for idx, sprite_group in enumerate((sd.Groups.character_group,
                                                sd.Groups.object_group,
                                                sd.Groups.dialog_group)):

                # Get the word to use in the commands (ie: character, object, dialog_sprite).
                group_word = group_words.get(idx)

                # Loop through the visible sprites in the current group we're looping on.
                sprite_name: str
                sprite_object: sd.SpriteObject
                for sprite_name, sprite_object in sprite_group.sprites.items():
                    if sprite_object.visible:
                        copy_info.append(f"# {sprite_object.general_alias}")
                        copy_info.append(
                            f"<{group_word}_set_position_x: {sprite_object.general_alias}, {sprite_object.rect.x}>")
                        copy_info.append(
                            f"<{group_word}_set_position_y: {sprite_object.general_alias}, {sprite_object.rect.y}>")

                        # Flip both directions?
                        if all([sprite_object.flipped_vertically, sprite_object.flipped_horizontally]):
                            copy_info.append(f"<{group_word}_flip_both: {sprite_object.general_alias}>")

                        # Flip only horizontally?
                        elif sprite_object.flipped_horizontally:
                            copy_info.append(f"<{group_word}_flip_horizontal: {sprite_object.general_alias}>")

                        # Flip only vertically?
                        elif sprite_object.flipped_vertically:
                            copy_info.append(f"<{group_word}_flip_vertical: {sprite_object.general_alias}>")

                        # Add an empty line
                        copy_info.append("\n")

            # Anything to copy to the clipboard?
            if copy_info:
                # Combine the list into one string
                generated_str = "\n".join(copy_info)

                # Copy the string to the clipboard
                scrap.put_text(generated_str)

                # Show a 'copied' text in the draft rectangle
                # so that the user knows it's been copied to the clipboard.
                Passer.active_story.draft_rectangle.temporary_text = "Copied sprite locations!"



if __name__ == "__main__":

    read_arguments = argparse.ArgumentParser()
    read_arguments.add_argument("--file",
                                dest="file",
                                type=str,
                                help="Specify a story file for playing.")
    read_arguments.add_argument("--show-launch",
                                dest="show_launch",
                                default=False,
                                help="Whether to show a list of chapters and scenes.")
    args = read_arguments.parse_args()

    # Debug for playing in the player
    if not args.file:

        if ContainerHandler.is_in_snap_package() \
           or ContainerHandler.is_in_flatpak_package():
            draft_path = ContainerHandler.get_draft_path()
            args.file = str(draft_path)
        else:
            # Not inside a Snap or Flatpak
            args.file = r"../draft/draft.lvna"
        args.show_launch = "True"

    if not args.file:
        print("No file specified. Use --file to specify a path to a .lvna file.")
        quit()

    # Should we show the launch window?
    show_launch = args.show_launch in ("true", "True")

    # print(f"{args.file=},{args.show_menu=}")

    main = Main()
    main.begin()
