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

import json
import editor_window
from tkinter import messagebox

from project_snapshot import ProjectSnapshot, SubPaths, FontSprite
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List
from re import search


def extract_arguments(command_line: str):
    """
    Given a line, such as <load_character: rave_normal, test>, return ['rave_normal', 'test']
    :param command_line: the story script line
    :return: Dict
    """
    pattern = r"^<(?P<Command>[a-z]+[_]*[\w]+):{1}(?P<Arguments>.*)>$"

    result = search(pattern=pattern,
                    string=command_line)

    if result:
        return result.groupdict()


class CompilePart(Enum):
    CURRENT_SCENE = auto()
    ALL_SCENES = auto()


class CompileMode:
    DRAFT = "Draft"
    FINAL = "Final"


class ItemSection(Enum):
    CHARACTER_IMAGE = auto()
    OBJECT_IMAGE = auto()
    BACKGROUND_IMAGE = auto()
    FONT_SPRITE_SHEET = auto()
    DIALOG_SPRITE = auto()
    AUDIO = auto()
    MUSIC = auto()


class StoryCompiler:
    """
    Create a .lvna file from one or more scripts.

    Note: chapters can't be played directly - only scenes can be played directly.
    However, the chapter of each script will be automatically included in the compilation.
    """
    def __init__(self,
                 compile_part: CompilePart,
                 save_file_path: Path,
                 startup_chapter_name: str,
                 startup_scene_name: str,
                 story_reusables_dict: Dict):
        """

        :param compile_part: So we know whether to compile all scripts for all scenes
                             or just for the current scene.

        :param save_file_path: The full Path object to where the final compiled .lvna file
                               needs to be saved. This path should include the .lvna file name.

        :param startup_chapter_name: The chapter in which the startup scene exists in.

        :param startup_scene_name: The scene which which will be read first.

        :param story_reusables_dict: reusable scripts dictionary (key: function name, value: script (str)).
        """

        self.compile_part = compile_part
        self.save_file_path = save_file_path

        self.startup_chapter_name = startup_chapter_name
        self.startup_scene_name = startup_scene_name

        self.story_reusables_dict = story_reusables_dict

        self.story_start_script_info = {self.startup_chapter_name: self.startup_scene_name}
        self.story_engine_info = ProjectSnapshot.EDITOR_VERSION

        self.story_scripts_dict = None

    @staticmethod
    def _convert_dict_to_bytes(data_dict: Dict) -> bytes:
        """
        Take a dictionary and convert it to bytes.

        Purpose: we use this method to convert story detail dictionaries and dictionary scripts
                 to bytes, so we can append it to the final .lnva file.

        :param data_dict: a regular dictionary
        :return: bytes
        """
        dict_bytes = json.dumps(data_dict).encode("utf-8")

        return dict_bytes

    def _save_lvna(self,
                   character_files: Dict[str, str],
                   background_files: Dict[str, str],
                   object_files: Dict[str, str],
                   font_sprite_files: Dict[str, str],
                   dialog_files: Dict[str, str],
                   sound_files: Dict[str, str],
                   music_files: Dict[str, str],
                   compile_mode: CompileMode):
        """
        Create a single binary file with all the included binary dictionaries,
        images, audio, in this order:

        In the parameter variables, the key is the item name,
        the value is the full path to the file.


        Binary dictionaries part:
            1. Story info dictionary (binary)
            2. Story engine version dictionary (binary)
            3. Story start script dictionary (binary) - this will either be
            the active script or complete script
            4. Story reusable scripts dictionary (binary)
        ---------------------------------
        Files part:
            5. Character images
            6. Object images
            7. Font sprite images
            8. Dialog rectangle images
            9. Music files
            10. Audio files

        For the file part, make a dictionary that keeps track of where
        each image is positioned.
        Key: image name (no extension), Value: range of bytes (ie: "6846-8532")
        
        - compile_mode: when in draft mode, the mouse pointer coordinates will
        be shown in the visual novel. When in final mode, the mouse pointer
        coordinates will not be shown.
        """

        general_header = {}
        detail_header = {}

        # Key (str): item name
        # Value (str): bytes range
        story_character_image_locations = {}
        story_background_image_locations = {}
        story_object_image_locations = {}
        story_font_sprite_image_locations = {}
        story_dialog_image_locations = {}
        story_audio_locations = {}
        story_music_locations = {}

        # List of dictionaries
        # (the dictionaries have key: item name, value: full path to file)
        files = [character_files, background_files,
                 object_files, font_sprite_files, dialog_files, sound_files, music_files]

        # List of dictionaries
        # (the dictionaries have key(str): item name, value(str): bytes range)
        image_locations = [story_character_image_locations,
                           story_background_image_locations, story_object_image_locations,
                           story_font_sprite_image_locations, story_dialog_image_locations,
                           story_audio_locations, story_music_locations]

        key_names = ["StoryCharacter_ImageLocations",
                     "StoryBackground_ImageLocations",
                     "StoryObject_ImageLocations",
                     "StoryFontSprite_ImageLocations",
                     "StoryDialog_ImageLocations",
                     "StoryAudio_Locations",
                     "StoryMusic_Locations"]

        with open(self.save_file_path, "wb") as f:

            # Beginning header
            beginning_header = "LVNAUTH-".encode("utf-8")
            f.write(beginning_header)
            current_position = f.tell()

            # Write poster image binary
            poster_image_full_path = ProjectSnapshot.project_path / SubPaths.POSTER_IMAGE_PATH.value
            if poster_image_full_path.exists() and poster_image_full_path.is_file():
                poster_bytes = poster_image_full_path.read_bytes()
                poster_file_extension = poster_image_full_path.suffix.lower()

                # Write poster image
                f.write(poster_bytes)
                from_range = current_position
                to_range = f.tell()
                current_position = f.tell()

                general_header["PosterTitleImageLocation"] = \
                    [f"{from_range}-{to_range}", poster_file_extension]
            else:
                general_header["PosterTitleImageLocation"] = None

            for file_info, location_dict, dict_name in \
                    zip(files, image_locations, key_names):
                
                # file_info: a dictionary from the files list.
                # Example: {"Rave": "/home/images/rave.png"}

                # location: a dictionary from the image_locations list.
                # Example: {"Rave": "3837-4857"}

                # dict_name: a list of key names that we will use in the
                # final dictionary.
                # Example: ['StoryCharacter_ImageLocations']

                for item_name, file_path in file_info.items():
                    full_path = Path(file_path)
                    file_extension = full_path.suffix.lower()
                    binary_data = full_path.read_bytes()

                    from_range = current_position
                    f.write(binary_data)
                    to_range = f.tell()
                    current_position = f.tell()

                    # Example:
                    # {"StoryCharacter_ImageLocations": {"blue rectangle": "7338-9837",
                    #                                    "yellow rectangle": "9838-10257"}

                    # First, check if we've already added one location range to
                    # the dictionary or not. For example, if we're adding
                    # "blue rectangle" (like in the example comment above),
                    # check if we've already added another item, like yellow
                    # rectangle.
                    existing_dict_value = detail_header.get(dict_name)

                    # The range that we want to add, regardless if there's
                    # existing data or not.
                    # Example: {"yellow rectangle": "9838-10257"}
                    new_location_dict = {item_name: [f"{from_range}-{to_range}", file_extension]}

                    # If we have an existing value, merge the new location dict
                    # with what we have in the dictionary so far.
                    # For example, it'll then become something like this:
                    # {"StoryCharacter_ImageLocations": {"blue rectangle": "7338-9837",
                    #                                    "yellow rectangle": "9838-10257"}
                    if existing_dict_value:
                        # Merge the existing dictionary with the new one
                        existing_dict_value = existing_dict_value | new_location_dict

                        # Update the dictionary with the new merged dictionary
                        # as the value.
                        detail_header[dict_name] = existing_dict_value
                    else:
                        # It's our first entry for this dictionary.
                        detail_header[dict_name] = new_location_dict

            detail_header["StoryStartScript"] = self.story_start_script_info
            detail_header["StoryReusables"] = self.story_reusables_dict
            detail_header["StoryScript"] = self.story_scripts_dict
            
            # Variables for the visual novel.
            detail_header["StoryVariables"] = ProjectSnapshot.variables

            # Font sprite letter assignments, rects, and other properties
            # Example: {"test_font": {'Width': 49, 'Height': 46,
            #                         'PaddingLetters': 0, 'PaddingLines': 0,
            #                        'Letters': {'A': LetterProperties object..)
            font_sprite_properties = FontSprite.get_all_font_properties()
            detail_header["FontSpriteProperties"] = font_sprite_properties

            general_header["StoryInfo"] = ProjectSnapshot.details
            general_header["StoryWindowSize"] = ProjectSnapshot.story_window_size
            general_header["StoryEngineVersion"] = ProjectSnapshot.EDITOR_VERSION
            general_header["StoryCompileMode"] = compile_mode

            # Get a dictionary of chapter names and scene names
            # (just the names, not the scripts)
            chapters_scenes = self._get_all_chapters_and_scenes()
            general_header["StoryChapterAndSceneNames"] = chapters_scenes

            # Get the bytes version of the detail and general dictionaries
            detail_header = self._convert_dict_to_bytes(detail_header)
            general_header = self._convert_dict_to_bytes(general_header)

            # Write the detail header to the file.
            from_range = current_position
            f.write(detail_header)
            to_range = f.tell()
            current_position = f.tell()
            range_detail_header = f"{from_range}-{to_range}"

            # Write the general header to the file.
            from_range = current_position
            f.write(general_header)
            to_range = f.tell()

            range_general_header = f"{from_range}-{to_range}"

            # Get the padded locations of the detail and general headers.
            detail_header_range_padded = self._get_right_padded_text(text=range_detail_header).encode("utf-8")
            general_header_range_padded = self._get_right_padded_text(text=range_general_header).encode("utf-8")

            # Write the locations of the detail and general headers to the file
            # (this is the last thing we will add to the end of the file).
            f.write(detail_header_range_padded)   # 25 bytes
            f.write(general_header_range_padded)  # 25 bytes

        print("Done creating .lvna file.")

    @staticmethod
    def _get_right_padded_text(text: str, pad_character: str = "X", expected_length: int = 25) -> str:
        """
        Return a right-padded version of the provided text.

        For example: if the text 'hello' is provided,
                     this method will return: 'helloXXXXXXXXXXXXXXXXXXXX'

        :param pad_character: the character that will be used for padding
        :param expected_length: the overall length that the return string should be
        :return: padded string
        """
        
        length_text = len(text)
        if length_text < expected_length:
            text = text + (pad_character * (expected_length - length_text))

        return text

    @staticmethod
    def _get_all_chapters_and_scenes() -> Dict:
        """
        Get all the chapter names and all scene names.

        Purpose: for the general header, so when the story first opens up, we can show
                 the user all the chapters and scenes of the story.
                 We run this method when compiling a story.

        :return: Dict - key: chapter name (str), value: scene names (list of str)
        Example: {"First chapter": ["Scene name1", "Scene name2"],
                  "Second chapter": ["Another scene", "Cool scene"]}
        """

        chapters_scenes = {}

        for chapter_name, sub in ProjectSnapshot.chapters_and_scenes.items():
            scene_dict = sub[1]

            scene_list = []
            for scene_name in scene_dict:
                scene_list.append(scene_name)

            chapters_scenes[chapter_name] = scene_list.copy()

        return chapters_scenes

    def strip_comments_blank_lines(self, chapter_scene_dict: Dict) -> Dict:
        """
        Go through all the chapter scripts and scene scripts
        and remove comment lines and blank lines, because an lvna file
        should not contain comments or blank lines.
        
        Return a new dict with the comments and blank lines excluded.
        
        Arguments:
        
        - chapter_scene_dict: this dictionary will look like this:
        Key (str): chapter name, Value: [ chapter script,  another dict {Key: scene name (str): Value script (str)} ]
        """
    
        def _remove_comment_blank_lines(script_lines: List) -> str:
            """
            From the given list, return a string without lines starting with #
            and without empty lines.
            
            Example:
            ["#Test', 'This', 'is', 'ok', '', '']
            will return
            This
            is
            ok
            """
            
            # This will be a temporary list without comments and without blank lines.
            new_script_lines = []
            
            # The final filtered-string will be stored in this variable.
            new_script = ""
            
            for line in script_lines:
                
                # Exclude the line if it's a blank line
                # or if it's a comment line.
                if not line or line.startswith("#"):
                    continue
                else:
                    new_script_lines.append(line)
            
            if new_script_lines:
                new_script = "\n".join(new_script_lines)
                
            return new_script    
        
        
        # This will be the new dict that will be returned
        new_dict = {}
        
        # Go through the chapter scripts and all the scenes in the chapters.
        for chapter_name, chapter_list in chapter_scene_dict.items():
            
            # The current chapter script
            chapter_script = chapter_list[0]
            
            # All the scenes in this chapter.
            scene_dict = chapter_list[1]
            
            # Filter out comments and blank lines for the chapter's script
            chapter_script_lines = chapter_script.splitlines()
            new_chapter_script =\
                _remove_comment_blank_lines(script_lines=chapter_script_lines)
            
            # The filtered scenes in this chapter will be stored in this variable.
            new_scene_dict = {}
            
            # Go through all the scenes in the current chapter.
            for scene_name, scene_script in scene_dict.items():
                
                # Filter out comments and blank lines for the current scene.
                scene_script_lines = scene_script.splitlines()
                new_scene_script = _remove_comment_blank_lines(script_lines=scene_script_lines)
    
                # Populate the new scenes dict that won't have comments or blank lines.
                new_scene_dict[scene_name] = new_scene_script
                
            # Populate the final new dict that will have 
            # no comments or blank lines in any of the scripts.
            # Key (str): chapter name, Value: [ chapter script,  another dict {Key: scene name (str): Value script (str)} ]
            new_dict[chapter_name] = [new_chapter_script, new_scene_dict]
            
        return new_dict

    def compile(self, compile_mode: CompileMode) -> bool:
        """
        Gather all the binary files (images, audio) that the script(s) need
        and save them to a file on the file system, including the scripts themselves.
        
        We only include binary files (images, audio) that have a <load-..>
        script for them in either a chapter script or scene script.
        For example <load_character: rave_happy, Rave>
        
        Arguments:
        
        - compile_mode: when the compile mode is set to Draft, the mouse pointer
        coordinates will be shown in the visual novel.

        :return: True if successful, False if the compilation was unsuccessful.
        """

        if self.compile_part == CompilePart.ALL_SCENES:
            analyze_script = ProjectSnapshot.get_all_chapters_and_scenes()
        else:
            chapter_script =\
                ProjectSnapshot.get_chapter_script_with_one_level_call(\
                    self.startup_chapter_name)
            
            scene_script = \
                ProjectSnapshot.get_scene_script(self.startup_chapter_name, self.startup_scene_name)

            analyze_script = chapter_script + "\n" + scene_script

        analyze_lines = analyze_script.splitlines()

        # Key: item name, value: full path (str) to file
        included_files_character_images = {}
        included_files_background_images = {}
        included_files_object_images = {}
        included_files_font_sprite_sheet_images = {}
        included_files_dialog_images = {}
        included_files_audio = {}
        included_music_audio = {}

        # Include files for commands that use files, such as:
        # <load_character> <load_background>

        # Paths to the files
        character_path = ProjectSnapshot.project_path / SubPaths.CHARACTER_IMAGE_FOLDER.value
        object_path = ProjectSnapshot.project_path / SubPaths.OBJECT_IMAGE_FOLDER.value
        background_path = ProjectSnapshot.project_path / SubPaths.BACKGROUND_IMAGE_FOLDER.value
        font_sprite_sheet_path = ProjectSnapshot.project_path / SubPaths.FONT_SPRITE_FOLDER.value
        dialog_path = ProjectSnapshot.project_path / SubPaths.DIALOG_IMAGE_FOLDER.value
        audio_path = ProjectSnapshot.project_path / SubPaths.SOUND_FOLDER.value
        music_path = ProjectSnapshot.project_path / SubPaths.MUSIC_FOLDER.value

        dict_refs = {"load_character": (ProjectSnapshot.character_images,
                                        character_path,
                                        ItemSection.CHARACTER_IMAGE),

                     "load_object": (ProjectSnapshot.object_images,
                                     object_path,
                                     ItemSection.OBJECT_IMAGE),

                     "load_background": (ProjectSnapshot.background_images,
                                         background_path,
                                         ItemSection.BACKGROUND_IMAGE),

                     "load_font_sprite": (ProjectSnapshot.font_sprites,
                                          font_sprite_sheet_path,
                                          ItemSection.FONT_SPRITE_SHEET),

                     "load_dialog_sprite": (ProjectSnapshot.dialog_images,
                                            dialog_path,
                                            ItemSection.DIALOG_SPRITE),

                     "load_audio": (ProjectSnapshot.sounds,
                                    audio_path,
                                    ItemSection.AUDIO),

                     "load_music": (ProjectSnapshot.music,
                                    music_path,
                                    ItemSection.MUSIC)


                     }

        # Compile a list of paths to images that the story needs.
        # We do this by looking for specific commands, such as <load_character>
        for script_line in analyze_lines:

            # Get the command and arguments of the current line, if there is a command.
            result = extract_arguments(script_line)
            if result:
                # A command was found on this line.

                command_name = result.get("Command")
                arguments = result.get("Arguments")

                # Is this a command that references an image or audio file?
                if command_name in dict_refs and arguments:
                    # It's a command that references an image or audio file,
                    # such as <load_character: rave_normal, rave>
                    
                    # We only want the item name (the first argument)
                    # so that we can find the file name from that.
                    if "," in arguments:
                        # Example: rave_normal, rave
                        # we only want 'rave_normal'
                        item_name = arguments.split(",")[0].strip()
                    else:
                        # Example: rave_normal (no extension)
                        item_name = arguments.strip()

                    # Example: {"load_character": (ProjectSnapshot.character_images, character_path)}
                    dict_item_and_path = dict_refs.get(command_name)
                    dict_ref = dict_item_and_path[0]
                    item_path = dict_item_and_path[1]
                    item_section: ItemSection = dict_item_and_path[2]

                    # Get the actual file name of the item (example: file.png)
                    file_name = dict_ref.get(item_name)
                    if file_name:

                        # Get the full path, including the file name
                        full_item_path: Path = item_path / file_name
                        if full_item_path.exists() and full_item_path.is_file():
                            full_item_path_string = str(full_item_path)

                            # Add the full path to the appropriate list

                            if item_section == ItemSection.CHARACTER_IMAGE:
                                if item_name not in included_files_character_images:
                                    included_files_character_images[item_name] = full_item_path_string
                                    
                            elif item_section == ItemSection.OBJECT_IMAGE:
                                if item_name not in included_files_object_images:
                                    included_files_object_images[item_name] = full_item_path_string

                            elif item_section == ItemSection.BACKGROUND_IMAGE:
                                if item_name not in included_files_background_images:
                                    included_files_background_images[item_name] = full_item_path_string
                                
                            elif item_section == ItemSection.FONT_SPRITE_SHEET:
                                if item_name not in included_files_font_sprite_sheet_images:
                                    included_files_font_sprite_sheet_images[item_name] = full_item_path_string
                                    
                            elif item_section == ItemSection.DIALOG_SPRITE:
                                if item_name not in included_files_dialog_images:
                                    included_files_dialog_images[item_name] = full_item_path_string

                            elif item_section == ItemSection.AUDIO:
                                if item_name not in included_files_audio:
                                    included_files_audio[item_name] = full_item_path_string
                                    
                            elif item_section == ItemSection.MUSIC:
                                if item_name not in included_music_audio:
                                    included_music_audio[item_name] = full_item_path_string

                        else:
                            messagebox.showerror(parent=editor_window.Passer.editor.mainwindow, 
                                                 title="File Not Found",
                                                 message=f"The visual novel cannot compile because a required file was not found:\n\n{full_item_path.name}\n\n" + str(full_item_path))
                            return False

        # Start creating the individual bytes data, so we can append it to a single file.

        # Story script
        if self.compile_part == CompilePart.CURRENT_SCENE:
            current_chapter_and_scene_script = {self.startup_chapter_name:
                                                ProjectSnapshot.chapters_and_scenes.get(self.startup_chapter_name)}

            self.story_scripts_dict = current_chapter_and_scene_script

        elif self.compile_part == CompilePart.ALL_SCENES:
            self.story_scripts_dict = ProjectSnapshot.chapters_and_scenes
            
        # Remove comment lines and blank lines from the final scripts
        # that get saved in the final .lvna file.
        self.story_scripts_dict =\
            self.strip_comments_blank_lines(self.story_scripts_dict)

        self._save_lvna(character_files=included_files_character_images,
                        background_files=included_files_background_images,
                        object_files=included_files_object_images,
                        font_sprite_files=included_files_font_sprite_sheet_images,
                        dialog_files=included_files_dialog_images,
                        sound_files=included_files_audio,
                        music_files=included_music_audio,
                        compile_mode=compile_mode)

        return True
    

# test = r"<load_character: rave_normal, yo here>"
# results = extract_arguments(test)
# print(results)