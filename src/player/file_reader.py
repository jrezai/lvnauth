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

from enum import Enum
from io import BytesIO
from pathlib import Path
from re import search
from typing import NamedTuple
#from font_handler import FontSprite
import font_handler
import json
import pygame
import sprite_definition as sd


class ContentType(Enum):
    CHARACTER = "StoryCharacter_ImageLocations"
    OBJECT = "StoryObject_ImageLocations"
    BACKGROUND = "StoryBackground_ImageLocations"
    FONT_SPRITE_SHEET = "StoryFontSprite_ImageLocations"
    DIALOG_SPRITE = "StoryDialog_ImageLocations"
    AUDIO = "StoryAudio_Locations"
    MUSIC = "StoryMusic_Locations"


class BytesRange(NamedTuple):
    """
    Used for holding a 'from' bytes and 'to' bytes int values.
    """
    from_bytes: int
    to_bytes: int


def extract_header_size_ranges(range_part: str):
    """
    Return the size ranges of the detail header and general header from a .lvna file.
    :param range_part: example: 374520-375235XXXXXXXXXXXX375236-375570XXXXXXXXXXXX

    :return: Dict
    """
    pattern = r"^(?P<FromDetail>\d+)[-](?P<ToDetail>\d+)X+(?P<FromGeneral>\d+)[-](?P<ToGeneral>\d+)X+$"

    result = search(pattern=pattern,
                    string=range_part)

    if result:
        return result.groupdict()


class FileReader:
    """
    Reads a compiled .lvna file and stores the story's scripts,
    image names, general info in dictionaries.
    """
    def __init__(self, full_path_lvna: str):

        self.full_path_lvna = Path(full_path_lvna)
        self.file_data = self.full_path_lvna.read_bytes()

        stream_file = BytesIO(self.file_data)
        self.view = stream_file.getbuffer()

        self.detail_header = None
        self.general_header = None

        self._get_headers()

    def _get_headers(self):
        """
        Get the detail and general dictionaries and record them as dictionaries.
        :return:
        """

        # The last 25 bytes will be the padded size of the general header
        # 25 bytes before that will be the padded size of the detail header

        # So both headers together will look something like this:
        # 374520-375235XXXXXXXXXXXX375236-375570XXXXXXXXXXXX
        if not self.full_path_lvna.exists():
            raise FileNotFoundError("Story file not found.")

        elif not self.full_path_lvna.is_file():
            raise TypeError("Expected a story file, got a directory instead.")

        header_ranges = self.view[-50:].tobytes().decode("utf-8")
        # Now we'll have something like this as a string:
        # '374520-375235XXXXXXXXXXXX375236-375570XXXXXXXXXXXX'

        header_size_ranges = extract_header_size_ranges(header_ranges)
        if not header_size_ranges:
            raise ValueError("Invalid or corrupted visual novel file.")

        # Record the detail and general headers.
        from_detail = int(header_size_ranges.get("FromDetail"))
        to_detail = int(header_size_ranges.get("ToDetail"))

        from_general = int(header_size_ranges.get("FromGeneral"))
        to_general = int(header_size_ranges.get("ToGeneral"))

        detail_header = self.view[from_detail:to_detail].tobytes()
        self.detail_header = json.loads(detail_header)

        general_header = self.view[from_general:to_general].tobytes()
        self.general_header = json.loads(general_header)

        # print(self.detail_header)
        # print(self.general_header)

    @staticmethod
    def _extract_range(data_range: str) -> BytesRange:
        """
        Given a string like this: '8-3000', it will return a namedtuple
        like this: 'bytes_from: 8', 'bytes_to: 3000'

        :param data_range: (str) bytes range (such as 8-3000)
        :return: namedtuple (from_bytes: 8, to_bytes: 3000)
        """

        pattern = r"^(?P<FromRange>\d+)[-](?P<ToRange>\d+)$"

        result = search(pattern=pattern,
                        string=data_range)

        if result:
            # Get the regex results as a dictionary
            dict_results = result.groupdict()

            # Read the regex results as integers
            from_range = int(dict_results.get("FromRange"))
            to_range = int(dict_results.get("ToRange"))

            # BytesRange is a namedtuple
            bytes_range = BytesRange(from_range, to_range)

            return bytes_range

    def get_audio(self,
                  content_type: ContentType,
                  item_name: str):
        """
        Return the bytes of a specific audio, based on a given name.
        """

        # Audio names and byte ranges
        data_dict = self.detail_header.get(content_type.value)
        

        # Example: {'StoryCharacter_ImageLocations': {'rave_normal': ['157434-217093', '.png']}
        if data_dict:

            # Example: ['157434-217093', '.png']
            reader = data_dict.get(item_name)

            if reader:
                data_range, file_extension = reader

                # Convert the string-format of the bytes range
                # such as '157434-217093', to a namedtuple with int values.
                data_range = self._extract_range(data_range=data_range)

                # Get the audio as bytes
                bytes_audio =\
                    self.view[data_range.from_bytes:data_range.to_bytes].tobytes()

                return bytes_audio

    def get_sprite(self,
                   content_type: ContentType,
                   item_name: str,
                   general_alias: str = None,
                   load_item_as_name: str = None):
        """
        Return a sprite object (which is meant to be eventually added to a sprite group)
        or a font sprite (FontSprite object)

        Arguments:
         - content_type: based on the ContentType class.
         - item_name: the item name without an extension (for example: 'rave_normal')
         - general_alias: the category name to give to the newly spawned sprite.
         this only gets used for character sprite objects, not background sprites
         and not font sprites.
         - load_item_as_name: the name to load the sprite as. This is used if we
         want to load multiple copies of the same sprite but with different
         sprite names (for example: when wanting to show multiple button sprites).
         
        Return: sprite object (SpriteObject) or font sprite (FontSprite object) or None
        """

        # Example of data that it will search:
        # {'StoryCharacter_ImageLocations': {'rave_normal': ['157434-217093', '.png']}

        # In the example above, the item name is 'rave_normal', and the content type
        # is 'StoryCharacter_ImageLocations'

        data_dict = self.detail_header.get(content_type.value)

        # Example: {'StoryCharacter_ImageLocations': {'rave_normal': ['157434-217093', '.png']}
        if data_dict:

            # Example: ['157434-217093', '.png']
            reader = data_dict.get(item_name)
            if reader:
                data_range, file_extension = reader

                # Convert the string-format of the bytes range
                # such as '157434-217093', to a namedtuple with int values.
                data_range = self._extract_range(data_range=data_range)

                bytes_sprite = self.view[data_range.from_bytes:data_range.to_bytes].tobytes()

                file_sprite = BytesIO(bytes_sprite)

                # Load image
                if file_extension.lower() in (".png", ".gif"):
                    surface_image = pygame.image.load(file_sprite,
                                                     "any_name" + file_extension).convert_alpha()
                else:
                    surface_image = pygame.image.load(file_sprite,
                                                     "any_name" + file_extension).convert()
                    


                sprite_group = None
                create_sprite_method = None
                
                if content_type == ContentType.CHARACTER:

                    # Set the dictionary
                    sprite_group = sd.Groups.character_group
                    create_sprite_method = sd.Character
                
                elif content_type == ContentType.OBJECT:

                    sprite_group = sd.Groups.object_group
                    create_sprite_method = sd.SpriteObject

                elif content_type == ContentType.DIALOG_SPRITE:

                    sprite_group = sd.Groups.dialog_group
                    create_sprite_method = sd.DialogSprite


                if sprite_group:
                    existing_sprite: sd.SpriteObject
                    existing_sprite = None

                    # If the sprite is already loaded, return
                    # the sprite from the sprite's group instead of the 
                    # .lvna file.
                    
                    # If we're loading the sprite with a new name (not using
                    # the sprite's original name), then don't return an
                    # already-loaded sprite - load the sprite from the .lvna.
                    # There's no technical reason for this aside from being
                    # able to start from scratch, that way the new sprite's
                    # settings are reset and original.
                    if not load_item_as_name:
                        # We're loading the sprite using the original name,
                        # so look for a cached/already-loaded sprite
                        # that has the same name as the one we're trying to load.
                        
                        existing_sprite = sprite_group.sprites.get(item_name)
                        if existing_sprite:
                            return existing_sprite

                    # The sprite hasn't been instantiated yet.
                    # Instantiate it here. The returned sprite
                    # will get added to the characters dictionary elsewhere.
                    new_sprite = create_sprite_method(name=item_name,
                                                      image=surface_image,
                                                      general_alias=general_alias)
                    
                    # Loading the sprite as a new/different name?
                    # Set the new name here.
                    if load_item_as_name:
                        new_sprite.name = load_item_as_name
                    
                    return new_sprite

                elif content_type == ContentType.BACKGROUND:

                    existing_sprite = sd.Groups.background_group.sprites.get(item_name)
                    if existing_sprite:
                        return existing_sprite

                    new_sprite = sd.Background(name=item_name,
                                               image=surface_image,
                                               general_alias="fixed_alias")
                    return new_sprite
                

                elif content_type == ContentType.FONT_SPRITE_SHEET:

                    # Get the letter properties for this font sprite sheet.
                    # ie: letter rects, padding values
                    all_font_properties = \
                        self.detail_header.get("FontSpriteProperties")
                    
                    if not all_font_properties:
                        return
                    
                    font_properties = all_font_properties.get(item_name)
                    
                    if not font_properties:
                        return

                    new_font = \
                        font_handler.FontSprite(font_name=item_name,
                                                full_font_spritesheet=surface_image,
                                                font_properties=font_properties)
                    return new_font
                
