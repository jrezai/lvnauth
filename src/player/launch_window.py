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
import pathlib
import tkinter as tk
from tkinter import messagebox

import pygubu
from typing import Dict
from PIL import ImageTk, Image
from io import BytesIO
from pathlib import Path
from shared_components import Passer
PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / ".." / "ui" / "launch_window.ui"

# We need to add the parent directory so
# the snap_handler module will be seen.
this_module_path = Path(__file__)
one_level_up_directory = str(Path(*this_module_path.parts[0:-2]))
sys.path.append(one_level_up_directory)
from snap_handler import SnapHandler


class LaunchWindow:
    def __init__(self,
                 story_info: Dict,
                 poster_file_object: BytesIO,
                 chapter_and_scene_names: Dict):
        """
        Initialize a window which shows story information,
        such as author, copyright, description, and a poster image.
        
        Arguments:

        - story_info: a dictionary which looks like this:
        {'Author': '', 'Copyright': '', 'Description': '', 'Genre': '',
        'License': '', 'StoryTitle': 'New Story...', 'Version': ''}
        
        - poster_file_object: the poster of the visual novel as a BytesIO
        object, ready to be converted to a PhotoImage.
        
        - chapter_and_scene_names: a dict of chapter names and scene names.
        Example: {'My First Chapter': ['My First Scene', 'Second scene'],
                  'My second Chapter': ['My First Scene', 'Second scene']}
        """

        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow = builder.get_object("launch_window")
        builder.connect_callbacks(self)

        # Get references to the widgets
        self.lbl_story_title = builder.get_object("lbl_story_title")
        self.lbl_author = builder.get_object("lbl_author")
        self.lbl_copyright = builder.get_object("lbl_copyright")
        self.lbl_license = builder.get_object("lbl_license")
        self.lbl_genre = builder.get_object("lbl_genre")
        self.lbl_version = builder.get_object("lbl_version")
        self.txt_description = builder.get_object("txt_description")

        self.lbl_poster = builder.get_object("lbl_poster")

        self.treeview_chapter_scenes = builder.get_object("treeview_chapter_scenes")
        self.btn_play_selection = builder.get_object("btn_play_selection")
        
        # So we know when the user has decided to 'X' out of the window.
        # That way, we can prevent the story from playing and exit the app.
        self.mainwindow.protocol("WM_DELETE_WINDOW", self.on_window_closing)
        
        # App icon
        # If the icon exists in the current folder, use it.
        # Otherwise, it might be one-directory up (depends on how the
        # player is launched - from the Editor or directly in an IDE.)
        icon_path = SnapHandler.get_lvnauth_editor_icon_path()
        if not icon_path:
            # Not a Snap package.

            icon_path = Path(r"app_icon.png")
            if not icon_path.exists():
                # The icon is likely in a directory one level up.
                icon_path = Path(r"../app_icon.png")
            
        app_icon = tk.PhotoImage(file=icon_path)
        self.mainwindow.app_icon = app_icon
        self.mainwindow.wm_iconphoto(True, self.mainwindow.app_icon)        

        # The dictionary that holds info about the story, such as name, author,
        # copyright, etc.
        self.story_info: Dict
        self.story_info = story_info

        # Dict of chapter and scene names.
        # We'll populate the treeview from this dict later.
        self.chapter_and_scene_names = chapter_and_scene_names

        # Keep a reference to the poster bytes IO object.
        self.poster_file_object = poster_file_object

        self.populate_story_info()

    def on_window_closing(self):
        """
        The launch window is closing. Set a shared variable
        flag to indicate that once the launch window closes, the entire
        app should close. The default story shouldn't play, because
        the user has clicked the 'X' to close the launch window.
        """
        Passer.close_after_launch_window = True
        
        self.mainwindow.destroy()

    def on_play_selection_button_clicked(self):
        """
        Get the selected chapter and scene in the treeview widget.
        
        Return: a dict (key: chapter name, value: scene name)
        Example: {chapter_name: scene_name}
        """

        # Disable the button so the user doesn't repeatidly click it.
        self.btn_play_selection.state(["disabled"])        
        
        selection = self.treeview_chapter_scenes.selection()

        # If the user hasn't selected a chapter/scene to play,
        # or if the user has selected the first item (I001),
        # play the story's default startup chapter/scene,
        # by just closing the launch window.
        if not selection or selection[0] == "I001":
            self.mainwindow.destroy()
            return

        selected_item_iid = selection[0]

        """
        If the selected row is a chapter, play the first scene in that chapter.
        If the selected row is a scene, play the scene in that chapter.
        """

        # Example:
        # {'text': 'My First Chapter', 'image': '', 'values': '', 'open': 0, 'tags': ''}
        row_details = self.treeview_chapter_scenes.item(selected_item_iid)

        chapter_name = row_details.get("text")
        if chapter_name:
            # A chapter row is selected.

            first_scene_name = None
            
            # Get the first scene in the selected chapter.
            for scene_item_iid in \
                    self.treeview_chapter_scenes.get_children(selected_item_iid):

                # Get the scene row item details, so we can later get the
                # scene name
                scene_item_details =\
                    self.treeview_chapter_scenes.item(scene_item_iid)

                first_scene_name = scene_item_details.get("values")[0]
                break

            # Make sure both a chapter and scene is selected.
            # We might have a chapter with no scenes in it.
            if not first_scene_name:
                messagebox.showerror(
                    parent=self.mainwindow,
                    title="No Scenes",
                    message="This chapter has no scenes.")
                
                # Re-enable the Play button
                self.btn_play_selection.state(["!disabled"])
                return

            # Set the shared variable so ActiveStory will read it later
            # and know to set a custom startup chapter/scene.
            Passer.manual_startup_chapter_scene = {chapter_name: first_scene_name}

        else:
            # A scene row is selected.
            
            # Get the parent of the selection (which will be the chapter name).

            # Record the scene name
            scene_name = row_details.get("values")[0]

            # Get the parent iid (this will be the chapter name's item iid)
            chapter_item_iid =\
                self.treeview_chapter_scenes.parent(selected_item_iid)

            # Get the chapter row details as a dictionary
            chapter_row_details =\
                self.treeview_chapter_scenes.item(chapter_item_iid)

            # Get the chapter name
            chapter_name = chapter_row_details.get("text")

            # Set the shared variable so ActiveStory will read it later
            # and know to set a custom startup chapter/scene.
            Passer.manual_startup_chapter_scene = {chapter_name: scene_name}       

        # Close the launch window so the story can start playing.
        self.mainwindow.destroy()

    def populate_story_info(self):
        """
        Populate the labels that show the story's info (such as author,
        copyright, etc.)
        """
        self.lbl_story_title.configure(text=self.story_info.get("StoryTitle"))
        self.lbl_author.configure(text=self.story_info.get("Author"))
        self.lbl_copyright.configure(text=self.story_info.get("Copyright"))
        self.lbl_license.configure(text=self.story_info.get("License"))
        self.lbl_genre.configure(text=self.story_info.get("Genre"))
        self.lbl_version.configure(text=self.story_info.get("Version"))
        
        self.txt_description.insert("end", self.story_info.get("Description", ""))
        self.txt_description.configure(state="disabled")

        # Show the story's poster image.
        self.show_poster_image()
        
        # Show the chapter names and scene names
        self._populate_treeview()
        
    def _populate_treeview(self):
        """
        Populate the treeview with chapter names and scenes
        from the dict: self.chapter_and_scene_names
        
        Example: {'My First Chapter': ['My First Scene', 'Second scene'],
                  'My second Chapter': ['My First Scene', 'Second scene']}
        """

        # A selection option to play the story's default startup chapter/scene.
        self.treeview_chapter_scenes.insert(parent="",
                                            index=0,
                                            text="(Play from beginning)")
        
        # Iterate through the chapter names that contain scene lists.
        for chapter_name, scene_list in self.chapter_and_scene_names.items():

            # Add the chapter name
            chapter_item_iid = self.treeview_chapter_scenes.insert(parent="",
                                                                   index="end",
                                                                   text=chapter_name)

            # Add all the scenes in the current chapter.
            for scene_name in scene_list:
                # Don't add scene names starting with a period, because
                # these are hidden scenes.
                if scene_name.startswith("."):
                    continue

                # Add the scene
                self.treeview_chapter_scenes.insert(parent=chapter_item_iid,
                                                    index="end",
                                                    values=(scene_name, ))

    def show_poster_image(self):
        """
        Show the poster of the visual novel in a label
        by converting it from a BytesIO object to a PhotoImage.
        """
        
        # No poster image? return.
        if not self.poster_file_object:
            return
        
        # Convert the BytesIO object of the poster image to a PhotoImage
        # that tkinter can use.
        with Image.open(self.poster_file_object) as img:
            poster_image = ImageTk.PhotoImage(img)

        # Keep a reference to the photoimage
        self.lbl_poster.image = poster_image

        # Show the poster image in the poster label.
        self.lbl_poster.configure(image=self.lbl_poster.image)

    def run(self):
        self.mainwindow.mainloop()

