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


import re
from pathlib import Path
from typing import List


class ActionTaker:
    pass


class StoryReader:
    def __init__(self, story_file: str):
        path = Path(story_file)
        self.story_lines = path.read_text().splitlines()

        # If there are errors reading the story script, add the errors to this list.
        self.errors = []

    def read_line(self):

        if not self.story_lines:
            return

        current_line = self.story_lines.pop(0)

        # Look for <command-arguments, here>
        result = re.findall(r"^<(\w+)-(.+)(,+)?(.+)?>$", current_line)

        if result:

            # Remove empty items
            result = [item for item in result[0] if item]

            # None if successful, a string with the error if not successful.
            if decision_result := self._decide_line(result):
                self.errors.append(decision_result)

    def _decide_line(self, line: List[str]):
        """
        Perform an action based on the text in the first item in the given tuple.

        :param line: Example of a line with a command: ['load_image', 'rave_normal.png,Rave Normal')
        :return: None
        """

        # The 'action' will always be in the first item.
        action = line[0]

        if len(line) > 1:
            arguments = line[1:]
            arguments = arguments[0].split(",")
            arguments_length = len(arguments)
        else:
            arguments = None
            arguments_length = 0

        match action:
            case "load_image":
                if arguments_length != 2:
                    return f"Error: {action} has {arguments_length} arguments. Expected 2."

                file_name, image_name = arguments

                image_path = (Path(__file__).parent / StoryPath.IMAGES_FOLDER_NAME / file_name)

                image = pygame.image.load(image_path)

                if image_name in Story.story_images:
                    return f"Error: {image_name} is already loaded. Cannot load again."

                Story.story_images[image_name] = image


class StoryPath:
    IMAGES_FOLDER_NAME = "images"


class StoryImage:
    def __init__(self, name, image):
        self.name = name
        self.image = image



class Story:
    reader: StoryReader = None

    # Key: str (an image's name)
    # Value: a StoryImage object
    story_images = {}

    # The image names to blit to the screen.
    show_images = []
