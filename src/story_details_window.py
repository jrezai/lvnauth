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

import pathlib
import pygubu
import tkinter as tk
from tkinter import filedialog, PhotoImage
from tkinter import ttk, messagebox
from typing import Dict
from shutil import copy2
from project_snapshot import ProjectSnapshot, SubPaths
from pathlib import Path
from web_handler import WebKeys


PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "story_details_window.ui"


class StoryDetailsWindow:
    def __init__(self, master, existing_details: Dict):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)

        self.master = master

        self.existing_details = existing_details
        self.details = {}

        # Main widget
        self.story_details_window = builder.get_object("story_details_window", master)
        builder.connect_callbacks(self)

        self.entry_story_title = builder.get_object("entry_story_title")
        self.entry_author = builder.get_object("entry_author")
        self.entry_copyright = builder.get_object("entry_copyright")
        self.entry_license = builder.get_object("entry_license")
        self.entry_genre = builder.get_object("entry_genre")
        self.entry_version = builder.get_object("entry_version")
        self.entry_episode = builder.get_object("entry_episode")
        self.txt_description = builder.get_object("txt_description")
        
        # Web related
        self.v_allow_web_access = builder.get_variable("v_allow_web_access")
        self.v_license_key_type = builder.get_variable("v_license_key_type")
        self.entry_shared_key = builder.get_object("entry_shared_key")
        self.entry_web_address = builder.get_object("entry_web_address")
        
        # Connect the description's vertical scrollbar
        self.sb_vertical_description =\
            builder.get_object("sb_vertical_description")
        self.sb_vertical_description.configure(command=self.txt_description.yview)
        self.txt_description.configure(yscrollcommand=self.sb_vertical_description.set)
        

        self.lbl_poster_image = builder.get_object("lbl_poster_image")
        self.lbl_poster_image.image = None

        self.btn_change_image = builder.get_object("btn_change_image")
        self.new_poster_full_path = None

        # This flag gets set when the 'Clear poster' button is clicked.
        # Then, if the user clicks OK, we'll know to delete the poster file.
        self.delete_poster_file = None

        # If there is a post image, show it in the label.
        poster_full_path = ProjectSnapshot.project_path / SubPaths.POSTER_IMAGE_PATH.value
        if poster_full_path.exists() and poster_full_path.is_file():
            self.lbl_poster_image.image = PhotoImage(file=str(poster_full_path))
            self.lbl_poster_image.configure(image=self.lbl_poster_image.image)

        # Get the spinbox widgets for the story window size.
        self.sb_width: ttk.Spinbox
        self.sb_height: ttk.Spinbox
        self.sb_width = builder.get_object("sb_width")
        self.sb_height = builder.get_object("sb_height")

        # Get the story project's current window size
        width, height = ProjectSnapshot.story_window_size

        # Show the story's window size in the spinbox widgets.
        self.sb_width.delete(0, "end")
        self.sb_width.insert(0, width)
        
        self.sb_height.delete(0, "end")
        self.sb_height.insert(0, height)

        self.widget_mappings = {"StoryTitle": self.entry_story_title,
                                "Author": self.entry_author,
                                "Copyright": self.entry_copyright,
                                "License": self.entry_license,
                                "Genre": self.entry_genre,
                                "Version": self.entry_version,
                                "Episode": self.entry_episode,
                                "Description": self.txt_description,
                                
                                WebKeys.WEB_KEY.value: self.entry_shared_key,
                                WebKeys.WEB_ADDRESS.value: self.entry_web_address,
                                WebKeys.WEB_ACCESS.value: self.v_allow_web_access,
                                WebKeys.WEB_LICENSE_TYPE.value: self.v_license_key_type}

        self._get_details()

        self.story_details_window.transient(self.master)
        self.story_details_window.grab_set()

        self.story_details_window.wait_window(self.story_details_window)

    def on_change_image_button_clicked(self):
        """
        Ask the user to select an image file.

        The 'Change Image' button has been clicked.
        :return: None
        """

        file_types = [("PNG image", ".png")]
        selected_file = filedialog.askopenfilename(parent=self.story_details_window,
                                                   filetypes=file_types)
        if not selected_file:
            return

        # Set the path of the source poster image, so if the user clicks OK
        # we'll copy the image from this path to the project's path.
        self.new_poster_full_path = Path(selected_file)

        photo_file = PhotoImage(file=selected_file)

        self.lbl_poster_image.image = photo_file
        self.lbl_poster_image.configure(image=photo_file)

        # Reset flag to indicate that we're not going to delete
        # the poster file if the user clicks OK (this flag
        # is used when clearing a poster image, when the user doesn't
        # want to user a poster image at all)
        self.delete_poster_file = False

    def on_clear_poster_button_clicked(self):
        """
        Clear the poster image in the label and set a flag variable
        so when the user clicks OK in this dialog, we will know to delete
        the poster image file, if there is a poster file in the project's folder.
        :return: None
        """
        self.lbl_poster_image.configure(image="")
        self.lbl_poster_image.image = None

        # Set the delete flag for when the user clicks OK button.
        # That's where the actual deletion takes place.
        self.delete_poster_file = True

        # Reset the new poster variable, so the OK button knows
        # that we're not going to copy a new poster image file.
        self.new_poster_full_path = None

    def _get_details(self):
        """
        Show the current details to the user by populating the widgets.
        :return: None
        """
        if self.existing_details:
            for detail_name, widget in self.widget_mappings.items():
                text_to_show = self.existing_details.get(detail_name, "")
                
                # If the key was found with a value of None, it won't
                # default to "" from the line above. We can't insert None
                # into an entry widget.
                if text_to_show is None:
                    text_to_show = ""
                
                # string tk variable? set the text.
                if isinstance(widget, tk.StringVar):
                    widget.set(text_to_show)
                    
                # bool tk variable? set the bool flag from a string value.
                elif isinstance(widget, tk.BooleanVar):
                    widget.set(bool(text_to_show))

                elif widget.winfo_class() == "Text":
                    widget.insert("1.0", text_to_show)
                else:
                    widget.insert(0, text_to_show)
                    
    def on_default_size_button_clicked(self):
        """
        Set the default window size to 640x480 by changing
        the spinbox widget values.
        """

        self.sb_width.delete(0, "end")
        self.sb_height.delete(0, "end")

        self.sb_width.insert(0, "640")
        self.sb_height.insert(0, "480")

    def on_cancel_button_clicked(self):
        self.story_details_window.destroy()

    def on_ok_button_clicked(self):
        """
        Save the data to an instance dictionary so that the main details
        dictionary for the project will be updated from the instance
        dictionary later.
        """

        # Iterate through the entry widgets and the description text widget.
        for detail_name, widget in self.widget_mappings.items():

            if hasattr(widget, "winfo_class") and widget.winfo_class() == "Text":
                self.details[detail_name] = widget.get("1.0", "end-1c")
            else:
                
                # If the web license type is private (not shared), don't record 
                # any typed-in shared web key, because the visual novel is set 
                # to a private user key.
                if self.v_license_key_type.get() == "private" and \
                   detail_name == WebKeys.WEB_KEY.value:
                    # Set the shared key to None, because the web license type
                    # is private. Without this, we'll end up saving any
                    # typed-in shared key, even if not in shared-key mode.
                    self.details[detail_name] = None
                    continue
                
                self.details[detail_name] = widget.get()
                
        # Save the window size.
        width = self.sb_width.get().strip()
        height = self.sb_height.get().strip()

        # Make sure the given story window size
        # width and height are numeric.
        try:
            width = int(width)
            height = int(height)
        except ValueError:
            messagebox.showerror(
                parent=self.story_details_window,
                title="Window Size",
                message="The window size value is not numeric.")
            self.sb_width.focus()
            
            # By clearing this dictionary, the caller of this
            # window will know not to modify the main details dictionary.
            self.details.clear()
            
            # Don't continue - the width or height is incorrect.
            return
        else:
            
            # Make sure the width and height value is between 320 and 9999.
            if width < 320 or width > 9999 or height < 320 or height > 9999:
                messagebox.showerror(window=self.story_details_window, 
                                     title="Window Size",
                                     message="The minimum window size is 320 pixels\n\n"
                                     "The maximum window size is 9999 pixels.")
                
                # Don't continue - the width or height is incorrect
                return

            # The window size appears OK, save it.
            ProjectSnapshot.story_window_size = (width, height)

        # Set the full save path for a poster image.
        destination_poster_path = ProjectSnapshot.project_path / SubPaths.POSTER_IMAGE_PATH.value

        # Has the poster been changed?
        if self.new_poster_full_path:
            # The poster has been changed, so copy the new poster image
            # to the project's folder.
            if self.new_poster_full_path.exists() and self.new_poster_full_path.is_file():
                copy2(src=str(self.new_poster_full_path), dst=str(destination_poster_path),
                      follow_symlinks=False)

        elif self.delete_poster_file:
            destination_poster_path.unlink(missing_ok=True)

        # Close the detail window
        self.story_details_window.destroy()
