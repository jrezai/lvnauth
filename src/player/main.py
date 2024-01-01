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
# the snap_handler module will be seen.
this_module_path = Path(__file__)
one_level_up_directory = str(Path(*this_module_path.parts[0:-2]))
sys.path.append(one_level_up_directory)
from snap_handler import SnapHandler


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

        # Should we show the launch window?
        if show_launch:
            self.show_launch_window(data_requester=data_requester)
            if Passer.close_after_launch_window:
                sys.exit(0)

        # screen_size = (640, 480)

        pygame.init()

        # Used for copying text to the clipboard.
        scrap.init()
        scrap.set_mode(pygame.SCRAP_CLIPBOARD)

        clock = pygame.time.Clock()

        pygame.display.set_caption("LVNAuth Player")

        # The app's icon file will be either in the current directory
        # or in the 'player' directory. It depends whether the visual novel
        # is being played from the editor, or directly.
        if SnapHandler.is_in_snap_package():
            app_icon_path = SnapHandler.get_lvnauth_editor_icon_path_small()
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

        # The first time the story starts, we need to refresh the whole screen
        # so that sprites that don't animate will get shown.
        self.initial_screen_refresh_done = False

        # We need this flag because when we minimize pygame and restore it again,
        # the window won't update until we refresh the whole screen.
        self.pygame_window_last_visible = pygame.display.get_active()

        # Holds the number of milliseconds elapsed in each frame
        milliseconds_elapsed = 0

        while story.story_running:

            # The number of milliseconds elapsed in this frame
            milliseconds_elapsed = clock.tick(60)

            main_surface.fill((0, 0, 0))

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

                    # print("Mouse:", pygame.mouse.get_pos())

                    # left_clicked = False
                    # list_test = []
                    #
                    # if pygame.mouse.get_pressed(num_buttons=3)[0]:
                    #     left_clicked = True
                    #     manual_update = pygame.Rect(15, 352, 45, 47)
                    #
                    #     list_test.append(manual_update)

            # Handle movements
            story.on_loop()

            # Handle drawing
            update_rects = story.on_render()

            # Update portions of the screen or the entire screen, depending on some factors.
            self.refresh_screen(update_rects)

            # print(update_rects)

            # For debugging
            # pygame.display.flip()

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

    def refresh_screen(self, update_rects):
        """
        Refresh the screen based on the best decision. Return a list of updated rects, if applicable.

        For example: if the pygame window is active, only update parts of the screen
                     that have changed. However, if the pygame window is inactive (minimized),
                     then as soon as the window is restored, refresh the 'whole' screen because
                     otherwise the window will be blank.

        :param update_rects:
        :return:
        """

        # Is the active active? (active means not-minimized)
        window_active = pygame.display.get_active()

        # If the window is active (not-minimized) but wasn't active before (was minimized before),
        # then refresh the whole screen.
        if window_active and not self.pygame_window_last_visible:
            self.pygame_window_last_visible = True
            pygame.display.flip()
            print("Updated the whole screen")

        # Refresh the screen when the story first starts up.
        # After this refresh, only individual sprite updates will be done.
        # Without this part, only sprites that animate will show, not sprites that don't animate.
        elif not self.initial_screen_refresh_done:
            self.initial_screen_refresh_done = True
            pygame.display.flip()
            print("Updated the whole screen")

        # If the window is not active (minimized) but was active before (not minimized before),
        # then set the flag.
        elif not window_active and self.pygame_window_last_visible:
            self.pygame_window_last_visible = False

        # Specific parts that need updating?
        elif update_rects:
            pygame.display.update(update_rects)
            # print("Updated some parts", update_rects, datetime.now())


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

        if SnapHandler.is_in_snap_package():
            draft_path = SnapHandler.get_draft_path()
            args.file = str(draft_path)
        else:
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
