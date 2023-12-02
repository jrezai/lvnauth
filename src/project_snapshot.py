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

from pathlib import Path
from enum import Enum
from typing import Dict, Tuple, List
from config_handler import ConfigHandler


class ProjectSnapshot:

    # Used when comparing to the player in code.
    EDITOR_VERSION = 1
    
    # Used in the About dialog
    EXACT_EDITOR_VERSION = "0.3"

    # Default the story window size to 640x480
    story_window_size = (640, 480)

    # Path to full save project file (.lvnap extension)
    save_full_path = None
    
    # Config parser
    config = ConfigHandler()

    # Story details (author, license, etc.)
    # Key (str): 'Author', Value (str): 'Name Here'
    details = {}

    # Paths to rectangle images
    # Key (str): image name, Value: image file name (str)
    character_images = {}
    background_images = {}
    object_images = {}
    font_sprites = {}
    dialog_images = {}

    #  Key (str): image name, Value: FontSprite class object
    font_sprite_properties = {}
    

    sounds = {}
    music = {}

    # Main story scripts
    # Key (str): chapter name, Value: [ chapter script,  another dict {Key: scene name (str): Value script (str)} ]
    chapters_and_scenes = {}

    # Reusable scripts
    # Key (str): function name, value: script (str)
    reusables = {}

    project_path = None

    @staticmethod
    def get_chapter_script(chapter_name: str) -> str:
        """
        Return the script of the specified chapter.

        :param chapter_name:
        :return: None
        """
        return ProjectSnapshot.chapters_and_scenes[chapter_name][0]
    
    @staticmethod
    def get_chapter_script_with_one_level_call(chapter_name: str) -> str:
        """
        Return a chapter's script along with any reusable scripts that
        the chapter's script references, but only one level of a reusable script.
        
        If the reusable script(s) call nested reusable scripts, those
        nested reusable scripts won't be included.
        
        Purpose: the caller of this method will look for <load_> commands
        so that the compiler knows which images/sprites to inlude in the project.
        In this method, we will include one-level down reusable scripts so that
        if there are any <load_> commands, the caller of this method can include
        those resources.
        
        Arguments:
        
        - chapter_name: the chapter name to return the script for, along
        with the reusable scripts that the chapter script calls.
        """
        
        # Get the chapter's script
        chapter_script =\
            ProjectSnapshot.get_chapter_script(chapter_name=chapter_name)
        
        if not chapter_script:
            return ""
        
        # We need to analyze the chapter's script line by line
        # because we're looking for <call> commands.
        chapter_lines = chapter_script.splitlines()
        
        # Look for <call> commands
        loaded_reusable_scripts = []
        for line in chapter_lines:
            
            line = line.strip()
            if line.startswith("<call:") and line.endswith(">"):
                
                # Get the reusable script's name
                first_colon = line.index(":")
                reusable_script_name = line[first_colon + 1:-1].strip()
                
                # If we've already loaded this reusable script,
                # don't include it again.
                if reusable_script_name.lower() in loaded_reusable_scripts:
                    continue
                
                # Get the reusable script so we can include it as part of
                # of the returned chapter script.
                reusable_script =\
                    ProjectSnapshot.get_reusable_script(reusable_script_name)
                
                # Include the reusable script as part of the returned
                # chapter script.
                chapter_script += "\n" + reusable_script
                
                # So we don't include the same reusable script again
                # if there are more calls to it.
                loaded_reusable_scripts.append(reusable_script_name.lower())

        return chapter_script

    @staticmethod
    def get_reusable_script(script_name: str) -> str:
        """
        Return the reusable script with a given name.

        :param script_name: the name of the script (case-sensitive)
        :return: str script
        """

        if not script_name:
            return ""

        script = ProjectSnapshot.reusables.get(script_name)

        if not script:
            return ""
        else:
            return script

    @staticmethod
    def get_scene_script(chapter_name: str, scene_name: str) -> str:

        if not scene_name or not chapter_name:
            return

        scene_dict = ProjectSnapshot.chapters_and_scenes[chapter_name][1]

        # Empty scene dictionary? return
        if not scene_dict:
            return

        scene_script = scene_dict.get(scene_name)
        if not scene_script:
            return ""

        return scene_script
    
    @staticmethod
    def get_scene_script_with_one_level_call(chapter_name: str,
                                             scene_name: str) -> str:
        """
        Get the scene script but also read <call> commands and analyze the
        reusable scripts that are used with <call> by looking for <load_>
        commands.
        
        Nested <call> commands are not analyzed - only one level of reusable
        scripts
        """
        
        scene_script =\
            ProjectSnapshot.get_scene_script (chapter_name=chapter_name,
                                              scene_name=scene_name)

        if not scene_script:
            return ""

        return scene_script

    @staticmethod
    def update_reusable_script(script_name: str, new_content: str):
        """
        Add or update a reusable script.
        
        Arguments:
        
        - script_name: case-sensitive reusable script name
        - new_content: the new script to save
        
        return: None
        """
        ProjectSnapshot.reusables[script_name] = new_content

    @staticmethod
    def update_chapter_script(chapter_name: str, new_content: str):
        """
        Update the chapter's script.

        Arguments:
        - chapter_name: chapter name (case-sensitive)
        - new_content: the new script
        
        return: None
        """
        chapter_value = ProjectSnapshot.chapters_and_scenes[chapter_name]

        # This will automatically update the list in the dictionary (it's a reference).
        chapter_value[0] = new_content

    @staticmethod
    def get_all_chapters_and_scenes() -> str:
        """
        Get all the scripts of chapters and scenes and put them into one string.
        
        Return: chapter scripts and scene scripts combined into one string
        """
        # Main story scripts
        # Key (str): chapter name, Value: [ chapter script,  another dict {Key: scene name (str): Value script (str)} ]

        final = ""
        for chapter_name, chapter_details in\
            ProjectSnapshot.chapters_and_scenes.items():

            # Get the chapter's script with one-level down of reusable scripts.
            # This is so if there are reusable scripts that contain <load_>
            chapter_script =\
                ProjectSnapshot.get_chapter_script_with_one_level_call(chapter_name)
            
            # {Key: scene name (str): Value script (str)}
            scene_dict = chapter_details[1]

            final += "\n" + chapter_script

            for scene_name, scene_script in scene_dict.items():
                final += "\n" + scene_script

        return final

    @staticmethod
    def update_scene_script(chapter_name: str, scene_name: str, new_content: str):
        """
        Update a scene's script in a specific chapter.
        :param chapter_name: case-sensitive
        :param scene_name: case-sensitive
        :param new_content:
        :return: None
        """

        chapter_value = ProjectSnapshot.chapters_and_scenes[chapter_name]
        scene_dict = chapter_value[1]

        scene_dict[scene_name] = new_content


class SubPaths(Enum):
    CHARACTER_IMAGE_FOLDER = Path("images") / "characters"
    BACKGROUND_IMAGE_FOLDER = Path("images") / "backgrounds"
    OBJECT_IMAGE_FOLDER = Path("images") / "objects"
    FONT_SPRITE_FOLDER = Path("images") / "font_sprites"
    DIALOG_IMAGE_FOLDER = Path("images") / "dialog_rectangle"

    POSTER_IMAGE_PATH = Path("images") / "poster.png"

    SOUND_FOLDER = Path("audio") / "sounds"
    MUSIC_FOLDER = Path("audio") / "music"
    
    
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
    Stores properties of a full size font spritesheet.
    Properties include letter rects, padding, letter size, physical file name.
    """
    def __init__(self, width: int = 0, height: int = 0,
                 padding_letters: int = 0, padding_lines: int = 0,
                 detect_letter_edges: bool = False,
                 letters: Dict = None):

        self.width = width
        self.height = height
        
        self.padding_letters = padding_letters
        self.padding_lines = padding_lines
        self.detect_letter_edges = detect_letter_edges

        # Key: letter (str) - example: "A" which means the letter A
        # Value: LetterProperties object
        # Examples:
        # self.letters["A"] = LetterProperties(..)
        # self.letters["B"] = LetterProperties(..)
        
        # which contains the rect crop info [left, right, upper, lower]
        # and also the left_trim, right_trim and previous letter rules.
        if letters:
            self.letters = letters
        else:
            self.letters = {}
        
    @staticmethod
    def get_all_font_properties() -> Dict:
        """
        Get all the font properties and convert them from a FontSprite
        object to a regular Python dict.
        
        Return the dict. The keys will be the item names (as they appear
        in the treeview widget), the values will be a dict.
        
        Purpose: for saving JSON data (the project file and also for use
        in a compiled .lvna)
        """

        data = {}

        # type-hints
        sprite_name: str
        font_property: FontSprite

        # Convert font properties to a regular dict.
        for sprite_name, font_property in \
            ProjectSnapshot.font_sprite_properties.items():

            data[sprite_name] = font_property._get_dict_data()
            
        return data

    def _get_dict_data(self) -> Dict:
        """
        Convert the data in this FontSprite object to a dictionary which
        can be used to save the font sprite's properties in a JSON project file
        and can also be used in a compiled .lvna file.
        """

        # self.letters is a dictionary that has single letters as keys
        # and LetterProperties as a value.
        # Examples:
        # self.letters["A"] = LetterProperties(...)
        # self.letters["B"] = LetterProperties(...)

        letter: str
        properties: LetterProperties

        letter_properties_for_dict = {}
        
        if self.letters:
            for letter, properties in self.letters.items():
                
                # The way a kerning_rules list looks.
                # [("abcd", -1, 0), ("efgh", -5, 2)]
                # -1 is the left trim, 0 is the right trim

                # Create a letters dictionary that can be saved
                # to a JSON file. This basically converts LetterProperties
                # objects to a normal dictionary so we can put it in the "data"
                # dictionary below, and then ultimately save it to a JSON.
                letter_properties_for_dict[letter] =\
                    {"rect_crop": properties.rect_crop,
                     "kerning_rules": properties.kerning_rules
                     }

        data = {"Width": self.width,
                "Height": self.height,
                "PaddingLetters": self.padding_letters,
                "PaddingLines": self.padding_lines,
                "DetectLetterEdges": self.detect_letter_edges,
                "Letters": letter_properties_for_dict}

        return data
        
    def add_letter(self, letter: str,
                   rect_crop: Tuple,
                   kerning_rules: List[Tuple]) -> bool:
        """
        Add the given letter to the letters dictionary with the
        specified x and y coordinates. Check to make sure
        the letter hasn't already been assigned.
        
        Arguments:
        
        - letter: a single character. The dialog rectangle will look
        for this letter and put the specified sprite in there.
        
        - rect_crop: a tuple (left, upper, right, bottom) that pygame
        needs to crop an image.
        
        - kerning_rules: a list of tuples which looks like this:
        [(previous_letters, left_trim, right_trim), (previous_letters, left_trim, right_trim)]
        
        Data example:
        [("abcd", -3, 5), ("efgh", -5, 0)]
        
        Return: True if the letter was added successfully
        or False if the letter already has an assignment or if more than
        one character has been given.
        """

        # Make sure a letter has been specified.
        if not letter:
            return False

        # Is the letter already added? return.
        elif letter in self.letters:
            return False

        # Only allow 1 letter.
        elif len(letter) != 1:
            return False
        
        letter_properties = LetterProperties(rect_crop=rect_crop,
                                             kerning_rules=kerning_rules)

        self.letters[letter] = letter_properties

        return True
