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
import pathlib
import tkinter as tk
from tkinter import messagebox

import pygubu
import queue_reader
from typing import Dict
from PIL import ImageTk, Image
from io import BytesIO
from pathlib import Path
from web_handler import WebKeys, WebHandler, WebLicenseType
from shared_components import Passer
from reply_post import ReplyPost
from response_code import ServerResponseReceipt, ServerResponseCode
PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / ".." / "ui" / "launch_window.ui"

# We need to add the parent directory so
# the container_handler module will be seen.
this_module_path = Path(__file__)
one_level_up_directory = str(Path(*this_module_path.parts[0:-2]))
sys.path.append(one_level_up_directory)
from container_handler import ContainerHandler


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

        # For reading secondary thread messages.
        self.queue_msg_handler = \
            queue_reader.QueueMsgReader(builder=self.builder)

        # Continuously check the queue for secondary thread messages.
        self.mainwindow: tk.Toplevel
        self.mainwindow.after(300, self.check_queue)

        # Get references to the widgets
        self.lbl_story_title = builder.get_object("lbl_story_title")
        self.lbl_author = builder.get_object("lbl_author")
        self.lbl_copyright = builder.get_object("lbl_copyright")
        self.lbl_license = builder.get_object("lbl_license")
        self.lbl_genre = builder.get_object("lbl_genre")
        self.lbl_version = builder.get_object("lbl_version")
        self.lbl_episode = builder.get_object("lbl_episode")
        self.txt_description = builder.get_object("txt_description")
        self.sb_vertical_description = builder.get_object("sb_vertical_description")

        self.lbl_poster = builder.get_object("lbl_poster")

        # Used for web-enabled visual novels.
        self.frame_license_key = builder.get_object("frame_license_key")

        self.treeview_chapter_scenes = builder.get_object("treeview_chapter_scenes")
        self.btn_play_selection = builder.get_object("btn_play_selection")
        
        # For getting the user inputted license key.
        self.entry_license_key = builder.get_object("entry_license_key")
        
        # So we know when the user has decided to 'X' out of the window.
        # That way, we can prevent the story from playing and exit the app.
        self.mainwindow.protocol("WM_DELETE_WINDOW", self.on_window_closing)
        
        # App icon
        # If the icon exists in the current folder, use it.
        # Otherwise, it might be one-directory up (depends on how the
        # player is launched - from the Editor or directly in an IDE.)
        icon_path = ContainerHandler.get_lvnauth_editor_icon_path()
        if not icon_path:
            # Not a Snap or Flatpak package.

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
        
        self.check_web_enabled()

    def check_queue(self):
        """
        Read the queue that was sent by a secondary thread.
        This method will run in the main GUI thread.
        """
        
        self.mainwindow.after(300, self.check_queue)
        
        if ReplyPost.the_queue.empty():
            return
        
        msg: ServerResponseReceipt = ReplyPost.the_queue.get()
        
        self.queue_msg_handler.read_msg(msg=msg)
        
    def check_web_enabled(self):
        """
        Initialize web_handler and show the license frame (so the viewer
        can enter a license key), if the visual novel is web-enabled.
        """
        
        # bool
        web_enabled = self.story_info.get(WebKeys.WEB_ACCESS.value)
        
        web_address = self.story_info.get(WebKeys.WEB_ADDRESS.value)
        
        # If it's a shared license key, get it here.
        # If it's a private license key, we don't have it yet; this will be None
        web_key = self.story_info.get(WebKeys.WEB_KEY.value)
        web_license_type = self.story_info.get(WebKeys.WEB_LICENSE_TYPE.value)
        if web_license_type == "private":
            web_license_type = WebLicenseType.PRIVATE
        else:
            web_license_type = WebLicenseType.SHARED
        
        # Initialize web_handler. This will be used throughout the visual
        # novel for interacting with flask and the database.
        Passer.web_handler = WebHandler(web_key,
                                        web_address,
                                        web_license_type,
                                        web_enabled,
                                        self.on_web_request_finished)
        
        # Don't show the license frame if the visual novel
        # is not web-enabled.
        if not web_enabled:
            self.frame_license_key.grid_forget()
            
    def on_web_request_finished(self, receipt: ServerResponseReceipt):
        """
        Read the response from the server.
        This method is in the GUI thread.
        """
        response_code = receipt.get_response_code()
        response_text = receipt.get_response_text()
        
        if response_code == ServerResponseCode.LICENSE_KEY_NOT_FOUND:
            # The provided license key is not a valid/known license key.
            try:
                msgbox = messagebox.showerror(master=self.mainwindow,
                                              title="License Key",
                                              message="The provided license key is invalid.")
            except tk.TclError:
                # If the parent window closes while the msgbox is open,
                # it'll raise a TclError, so we have this here to exit
                # gracefully.
                return

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
        If it's a web-enabled visual novel, verify the license
        and if it's valid, get the selected chapter and scene in the
        treeview widget and run it.
        
        If it's not a web-enabled visual novel, get the selected chapter
        and scene in the treeview widget and run it.
        """

        # Disable the button so the user doesn't repeatidly click it.
        self.btn_play_selection.state(["disabled"])
        
        if Passer.web_handler.web_enabled:
            
            # Get the user-typed license key,
            # if the license key type is private.
            if Passer.web_handler.web_license_type == WebLicenseType.PRIVATE:
                Passer.web_handler.web_key = self.entry_license_key.get().strip()
                
                # Make sure a license key was actually typed.
                if not Passer.web_handler.web_key:
                    try:
                        messagebox.showwarning(master=self.mainwindow,
                                               title="License Key",
                                               message="This visual novel requires a license key.\n\nPlease enter a license key.")
                        self.btn_play_selection.state(["!disabled"])
                        self.entry_license_key.focus()
                        return
                    except tk.TclError:
                        # Closing the parent window while a message box is open
                        # will raise a TclError, so we have this error 
                        # handler here.
                        return
                    
            
            # It's a web-enabled visual novel, check if the license is valid.
            Passer.web_handler.start_verify_license()
        else:
            # It's not a web-enabled visual novel, play the selection now.
            self._play_selection()
        
    def _play_selection(self):
        """
        Get the selected chapter and scene in the treeview widget and run it.
        
        """

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
        self.lbl_episode.configure(text=self.story_info.get("Episode"))
        
        self.txt_description.insert("end", self.story_info.get("Description", ""))
        self.txt_description.configure(state="disabled")
        
        # Connect the vertical scrollbar to the description text widget.
        self.sb_vertical_description.configure(command=self.txt_description.yview)
        self.txt_description.configure(yscrollcommand=self.sb_vertical_description.set)

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

