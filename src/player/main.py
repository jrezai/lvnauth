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

import sys
import pygame
import argparse
from active_story import ActiveStory
from file_reader import FileReader
from shared_components import Passer
from datetime import datetime
from launch_window import LaunchWindow
from io import BytesIO
from typing import Dict
from pathlib import Path


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
        self.launch_window =\
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
                            background_surface=background_surface)
        Passer.active_story = story

        # The first time the story starts, we need to refresh the whole screen
        # so that sprites that don't animate will get shown.
        self.initial_screen_refresh_done = False

        # We need this flag because when we minimize pygame and restore it again,
        # the window won't update until we refresh the whole screen.
        self.pygame_window_last_visible = pygame.display.get_active()
        
        # Hodls the number of milliseconds elapsed in each frame
        milliseconds_elapsed = 0
        
        while story.story_running:
            
            # The number of milliseconds elapsed in this frame
            milliseconds_elapsed = clock.tick(60)               
                        
            # Used for a constant move speed of all objects
            # regardless of the FPS
            Passer.seconds_elapsed = milliseconds_elapsed / 1000
            

            main_surface.fill((0, 0, 0))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    story.story_running = False
                else:
                    story.on_event(event)

                    # print("Mouse:", pygame.mouse.get_pos())
                    
                    left_clicked = False
                    list_test = []
                    
                    if pygame.mouse.get_pressed(num_buttons=3)[0]:
                        left_clicked = True
                        manual_update = pygame.Rect(15, 352, 45, 47)

                        list_test.append(manual_update)


            # Handle movements
            story.on_loop()

            # Handle drawing
            update_rects = story.on_render()
            
            # TODO: For debugging, remove later
            if left_clicked:
                pass



            # Update portions of the screen or the entire screen, depending on some factors.
            self.refresh_screen(update_rects)
       

            #print(update_rects)

            # For debugging
            # pygame.display.flip()
            

                        


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
        args.file = "../draft/draft.lvna"
        args.show_launch = "True"
        
    if not args.file:
        print("No file specified. Use --file to specify a path to a .lvna file.")
        quit()

    # Should we show the launch window?
    show_launch = args.show_launch in ("true", "True")

    # print(f"{args.file=},{args.show_menu=}")
    
    main = Main()
    main.begin()