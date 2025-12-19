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

import pygame
import story_reader
import font_handler
import file_reader
import draft_rectangle
import sprite_definition as sd
from file_reader import ContentType
from audio_player import AudioPlayer
from typing import Tuple, List
from shared_components import MouseActionsAndCoordinates
from player_config_handler import PlayerConfigHandler
from enum import Enum, auto
from pathlib import Path
from dialog_rectangle import DialogRectangle, \
     RectangleIntroAnimation, \
     RectangleOutroAnimation, \
     AnchorRectangle
from cover_screen_handler import CoverScreenHandler



class ActiveStory:
    """
    Holds loaded story data, such as sprites and chapter/scene scripts and names.
    """
    
    def __init__(self,
                 screen_size: Tuple,
                 data_requester: file_reader.FileReader,
                 main_surface: pygame.Surface,
                 draft_mode: bool = False):
        
        """
        Arguments:
        
        - screen_size: the width/height of the player window.
        
        - data_requester: so we can load sprites and audio.
        
        - main_surface: the main pygame surface
        
        - draft_mode: used for knowing whether to show the draft rectangle
        or not, and whether to allow some keyboard shortcuts or not.
        """
        
        # For example: (640, 480)
        self.screen_size = screen_size
        
        # Keeps track of the current pygame Event in
        # the current frame so any part of the project can read it if needed.
        # This was added for sprite mouse events.
        self.current_event = None
        
        # FileReader object
        self.data_requester = data_requester

        self.main_surface = main_surface

        self.reader = story_reader.StoryReader(story=self,
                                               data_requester=self.data_requester,
                                               background_reader_name=None)

        self.story_running = True

        #self.dialog_rectangle = DialogRectangle(main_screen=self.main_surface,
                                           #width_rectangle=400,
                                           #height_rectangle=400,
                                           #animation_speed=7.5,
                                           # intro_animation=RectangleIntroAnimation.SCALE_UP_WIDTH_AND_HEIGHT,
                                           #outro_animation=RectangleOutroAnimation.GO_LEFT,
                                           #anchor=AnchorRectangle.MID_BOTTOM,
                                           # bg_color_rgb=Color(50, 50, 50))

        self.dialog_rectangle: DialogRectangle
        self.dialog_rectangle = None

        # For complete-screen fade-ins and fade-outs (used primarily for scene transitions)
        self.cover_screen_handler = CoverScreenHandler(main_surface=self.main_surface)

        # Used for storing the rect of the dialog rect (after all its
        # animations are complete), so that when we add letters to the dialog,
        # we don't have to use .get_rect() for each letter.
        self.dialog_rectangle_rect: pygame.Rect
        self.dialog_rectangle_rect = None
        
        # Story details (author, license, etc.)
        # Key (str): 'Author', Value (str): 'Name Here'
        self.details = {}

        # Used for showing the draft rectangle (mouse x/y coordinates)
        # at the top of the player window.
        self.draft_rectangle = draft_rectangle.DraftRectangle(main_surface)

        # Used for knowing whether to show the draft rectangle or not,
        # and whether to allow some keyboard shortcuts or not.
        self.draft_mode = draft_mode

        # Key (str): font name, Value: FontScript object
        self.font_sprite_sheets = {}

        # Main story scripts
        # Key (str): chapter name, Value: [ chapter script,  another dict {Key: scene name (str): Value script (str)} ]
        chapters_and_scenes = {}

        # Reusable scripts
        # Key (str): function name, value: script (str)
        reusables = {}
        
        # Used for playing all audio.
        # The audio channels will be initialized automatically as needed.
        self.audio_player = AudioPlayer()

        ## Key: item name, Value: pygame image (converted and ready for use)
        ## The dictionaries below will only be populated as-requested by the story script(s).
        #self.dialog_images = {}
        #self.character_images = {}
        #self.background_images = {}
        #self.object_images = {}
        #self.font_sprites = {}

        # Key: item name, Value: byte data
        # The dictionaries below will only be populated as-requested by the story script(s).
        self.sounds = {}
        self.music = {}

    def get_visible_sprite(self,
                           content_type: ContentType,
                           general_alias: str = None,
                           sprite_name: str = None) -> sd.SpriteObject | None:
        """
        Get the first sprite instance that is visible or flagged to become
        visible and that has the given general_alias.
        
        Purpose: to get a sprite based on the general alias.
        This method is not used for spawning a new sprite - it returns an
        existing sprite that is currently being displayed on the screen.

        Used for loading character and object sprites with a general alias.
        Name sprites can be loaded here too, but without an alias.
        For name sprites, the sprite_name must be specified.
        
        Arguments:
        
        - content_type: specify whether it's a character or object sprite.
        
        - general_alias: (str) the general alias we need to find a character
        or object sprite that is visible. This is not used for name sprites
        because name sprites don't have aliases.
        
        - sprite_name: (str) the name (not alias) of a sprite. Use this
        for name sprites, not for character or object sprites.
        """

        if content_type == ContentType.CHARACTER:
            group_to_check = sd.Groups.character_group

        elif content_type == ContentType.OBJECT:
            group_to_check = sd.Groups.object_group
            
        elif content_type == ContentType.DIALOG_SPRITE:
            group_to_check = sd.Groups.dialog_group

        else:
            return
        
        # Make sure we have a general alias or name, depending
        # on the sprite's content type.
        if content_type in (ContentType.CHARACTER, ContentType.OBJECT, ContentType.DIALOG_SPRITE):
            if not general_alias:
                raise ValueError(f"No general alias provided {ContentType.name}.")

        sprite: sd.SpriteObject
        for sprite in group_to_check.sprites.values():
            if any((sprite.visible, sprite.pending_show)) and \
               not sprite.pending_hide:

                # Look for the general alias if one has been
                # provided in this method (used for finding characters and objects).
                if general_alias:
                    if sprite.general_alias == general_alias:
                        return sprite

                # Look for the sprite name if one has been
                # provided in this method (used for finding name objects).
                elif sprite_name:
                    if sprite.name == sprite_name:
                        return sprite

    def add_font(self,
                 font_name: str,
                 font_sprite: font_handler.FontSprite):
        """
        Add a font name and a font sprite object to the main
        font dictionary that keeps track of all the loaded fonts.
        
        That way, when there's dialog text and we need to use a specific font,
        the main font dictionary will have access to all the font sprite objects
        to get a subsurface of a letter.
        
        Arguments:
        
        - font_name: (str) the font name, case-sensitive.
        
        - font_sprite: (FontSprite object) a font sprite object has the full
        size font sprite sheet. It can also spawn individual subsurface letters.
        """

        self.font_sprite_sheets[font_name] = font_sprite

    def draw_draft_rectangle(self):
        """
        Draw draft rectangle text, if it's set to be visible.
        """

        # Is there temporary text to show? Such as 'Copied sprite locations!'
        draft_text = self.draft_rectangle.get_temporary_text()
        if not draft_text:
            # No temporary text, so show the usual mouse co-ordinates.
            mouse_x, mouse_y = MouseActionsAndCoordinates.MOUSE_POS
            draft_text = f"x:{mouse_x}   y:{mouse_y}"

        # Draw the rectangle on the screen.
        self.draft_rectangle.draw(draft_text)

    def on_event(self, event):
        """
        Handle events like left button click to unhalt story or to speed up
        gradual text display.
        """

        # Record mouse position and mouse clicks (if any) for
        # sprite mouse interactions (hovers, clicks)
        if event.type == pygame.MOUSEBUTTONDOWN:
            MouseActionsAndCoordinates.MOUSE_DOWN = True
            
        if event.type == pygame.MOUSEBUTTONUP:
            MouseActionsAndCoordinates.MOUSE_UP = True
            
        if event.type == pygame.MOUSEMOTION:
            MouseActionsAndCoordinates.MOUSE_POS = pygame.mouse.get_pos()
            
        
        # In non-automated halt-mode? Look for a mouse click to advance the story.
        if self.reader.halt_main_script \
           and not self.reader.halt_main_script_auto_mode_seconds_reach:
            
            # Advance the story if a mouse button was clicked.
            if event.type == pygame.MOUSEBUTTONDOWN:

                
                # If dialog text is currently being animated/shown
                # (ie: gradual text or fading in), then speed it up.
                if self.reader.go_faster_text_mode():
                    return

                # Run a reusable script for when <unhalt> is used?

                # # (We don't have this check in the unhalt() method because
                # # the unhalt method also gets used for automated unhalt,
                # # so we shouldn't run a reusable script on automated unhalt.)
                # if self.dialog_rectangle.reusable_on_unhalt:
                #     self.reader.spawn_new_background_reader(reusable_script_name=self.dialog_rectangle.reusable_on_unhalt)
                #

                # unhalt story
                self.reader.unhalt()

                # # Re-draw the dialog rectangle shape so that any previous text
                # # gets blitted over with the new rectangle.
                # self.reader.story.dialog_rectangle.clear_text()
                

    def on_loop(self):
        """
        Handle movements
        """
        self.reader.read_all_scripts()

        sd.Groups.background_group.update()
        sd.Groups.object_group.update()
        sd.Groups.character_group.update()

        if self.dialog_rectangle and self.dialog_rectangle.visible:
            self.dialog_rectangle.update()

            # Dialog sprites should only animate if the dialog is visible.
            sd.Groups.dialog_group.update()
            
        # Consider the mouse not clicked anymore, just in case if it was
        # seen as clicked in the current frame. All the sprite group update()
        # methods above have now already dealt with the mouse click, if any,
        # so we'll reset it here until the next time the mouse is clicked again.
        MouseActionsAndCoordinates.MOUSE_UP = False

    def on_render(self):
        """
        Handle drawing
        :return:
        """

        sd.Groups.background_group.draw(self.main_surface)
        sd.Groups.object_group.draw(self.main_surface)
        sd.Groups.character_group.draw(self.main_surface)


        if self.dialog_rectangle and self.dialog_rectangle.visible:

            # Note: The sequence is important here.
            # We need to draw the text *before* drawing the dialog box.
            self.reader.active_font_handler.draw()

            # Draw the dialog rectangle on the main surface.
            self.dialog_rectangle.draw()

            # Note: again, the sequence is important here.
            # We need to draw any dialog sprites *before* drawing the dialog box.
            # Groups.dialog_group.draw(self.dialog_rectangle.surface)
            sd.Groups.dialog_group.draw(self.main_surface)

            
            # Is this the last dialog rectangle outro animation update?
            if self.dialog_rectangle.next_rect_update_hide_dialog:

                # This is the last outro animation of this dialog rectangle.
                # Set the visibility of the dialog to False here.
                
                # We set it to False here because if we set it to False earlier
                # then the last outro animation won't update, and it'll appear
                # stuck on the very last outro frame.
                self.dialog_rectangle.next_rect_update_hide_dialog = False

                self.dialog_rectangle.visible = False

        self.cover_screen_handler.update()
        self.cover_screen_handler.draw()

        # Draft rectangle (to show x/y coordinates of the mouse pointer)
        if self.draft_mode:
            self.draw_draft_rectangle()
            
            