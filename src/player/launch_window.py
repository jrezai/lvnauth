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

import traceback
import sys
import pathlib
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import pygubu
import queue_reader
from typing import Dict
from PIL import ImageTk, Image
from io import BytesIO
from pathlib import Path
from web_handler import WebHandler, WebLicenseType, WebRequestPurpose
from player_config_handler import PlayerConfigHandler
from shared_components import Passer
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
        
        self.mainwindow.report_callback_exception =\
            self.custom_tk_exception_handler

        # For reading secondary thread messages.
        self.queue_msg_handler = \
            queue_reader.QueueMsgReader(builder=self.builder)

        # Continuously check the queue for secondary thread messages.
        self.mainwindow: tk.Toplevel
        self.mainwindow.after(300, self.check_queue)
        
        self.style = ttk.Style()
        self.style.configure("Warning.TLabel",
                             background="red",
                             foreground="white")

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

        # Used for showing/hiding the 'License Key' tab for 
        # web-enabled visual novels.
        self.notebook_main = builder.get_object("notebook_main")

        self.treeview_chapter_scenes = builder.get_object("treeview_chapter_scenes")
        self.btn_play_selection = builder.get_object("btn_play_selection")
        
        # For focussing on the license key widget.
        self.entry_license_key = builder.get_object("entry_license_key")
        
        # For getting/setting the license key in the entry widget.
        self.v_license_key: tk.Variable
        self.v_license_key = builder.get_variable("v_license_key")
        self.v_license_key.trace_add("write", self.on_license_key_changed)
        
        # So we can change the text of the 'Get License Key' button
        # to 'Update License Key' if needed.
        self.btn_get_license = builder.get_object("btn_get_license")
        
        # So we can update the text of the labelframe, similar to the button
        # above.
        self.frame_redeem_or_update_license_key =\
            builder.get_object("frame_redeem_or_update_license_key")
        
        # For getting a transaction ID from the user.
        self.v_transaction_id = builder.get_variable("v_transaction_id")
        
        # Used for showing a warning if bypassing certificate verification.
        self.lbl_certificate_warning =\
            builder.get_object("lbl_certificate_warning")
        self.lbl_certificate_warning.configure(style="Warning.TLabel")
        
        # Load and show the license key from the config file (if available).
        self.populate_license_key()

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
        
    def show_certificate_warning(self, web_enabled: bool):
        """
        Show a certificate warning message to the viewer of the visual novel
        if the certificate check is set to be bypassed.
        
        Arguments:
        
        - web_enabled: bool to indicate whether it's a web-enabled
        visual novel or not.
        """
        bypass_certificate_check = self.story_info.get("WebBypassCertificate")
        if bypass_certificate_check and web_enabled:
            self.lbl_certificate_warning.configure(text="Warning: the SSL certificate will not be verified.\nThis visual novel is for TESTING only.")
        else:
            self.lbl_certificate_warning.grid_forget()
        
    def on_license_key_changed(self, name, index, mode):
        """
        If a license key is present (any text) in the entry widget,
        update the text to show 'Update License Key'.
        
        If there is no license key entered in the entry widget,
        update the text to show 'Redeem License Key'.
        """
        license_key = self.v_license_key.get()
        
        if license_key:
            self.btn_get_license.configure(text="Update License Key")
            self.frame_redeem_or_update_license_key.configure(text="Update the license key above")
        else:
            self.btn_get_license.configure(text="Get License Key")
            self.frame_redeem_or_update_license_key.configure(text="Redeem a new license key")
        
    def custom_tk_exception_handler(self, exception_class, exception_value,
                                    traceback_object):
        """
        Custom handle Tkinter exceptions.
        
        Purpose: without this, any time there is a tkinter exception, it will
        output the error to the console, but it won't close the app. We want it
        to close the player when a Tkinter exception occurs.
        
        Example: if a web-connected visual novel can't connect to the server,
        when the 'Play' button is clicked in tkinter, we want the visual novel
        to close so it could output the error to an exceptions window for the
        user to see.
        """
        
        # This is required to output the exception to the console.
        # Without this, the exception won't get outputted when the app closes.
        traceback.print_exception(exception_class, exception_value,
                                  traceback_object)
        
        # Close the player because a Tkinter exception has occurred.
        # 1 means not successful.
        sys.exit(1)  

    def check_queue(self):
        """
        Read the queue that was sent by a secondary thread.
        This method will run in the main GUI thread.
        
        This method polling check is for the Launch window-only.
        
        The in-pygame polling (for the <remote> command) gets checked in
        pygame's own loop, not here.
        """
        
        self.mainwindow.after(300, self.check_queue)
        
        if WebHandler.the_queue.empty():
            return
        
        msg: ServerResponseReceipt = WebHandler.the_queue.get()
        
        self.queue_msg_handler.read_msg(msg=msg)
        
    def check_web_enabled(self):
        """
        Don't show the license frame and the certificate warning label
        if the visual novel is not web-enabled.
        
        If it is web-enabled, consider showing the certificate warning label
        if the certificate is being bypassed.
        """

        if not Passer.web_handler.web_enabled:
            self.notebook_main.tab(tab_id=2, state=tk.HIDDEN)
            
        # Show a warning if bypassing certificate verification
        # if it's a web-connected visual novel
        self.show_certificate_warning(Passer.web_handler.web_enabled)               
            
    def on_web_request_finished(self, receipt: ServerResponseReceipt):
        """
        Read the response from the server.
        This method is in the GUI thread.
        """
        response_code = receipt.get_response_code()
        response_text = receipt.get_response_text()
        
        msgbox_func = messagebox.showerror
        
        match response_code:
            
            case ServerResponseCode.SUCCESS:
            
                # The license key is valid. Play the visual novel.
                self._play_selection()
                
                return
            
            case ServerResponseCode.UPDATED_LICENSE:
                # The given license key was updated using a transaction ID.
                
                msg_title = "Success!"
                msg = "Success!\n\nThe provided license key has been updated."
                
                # Disable the 'Update License' button because it's finished.
                self.btn_get_license.state(["disabled"])
                
                msgbox_func = messagebox.showinfo
            
            case ServerResponseCode.LICENSE_KEY_NOT_FOUND:
                # The provided license key is not a valid/known license key.
                
                msg_title = "License Key"
                msg = "The provided license key is invalid."
            
            case ServerResponseCode.CONNECTION_ERROR:
                # Could not connect to server
                
                msg_title = "Connection Error"
                msg = "Could not connect to the server."
                
            case ServerResponseCode.LICENSE_KEY_ASSOCIATION_MISMATCH:
                
                msg_title = "License Key Mismatch"
                msg = "The provided license key is not associated with this visual novel."
                
            case ServerResponseCode.LICENSE_KEY_LOCKED:
                
                msg_title = "License Key Locked"
                msg = "The license key is currently locked and cannot be used."
                
            case ServerResponseCode.LICENSE_KEY_OWING_BALANCE:
                
                msg_title = "License Key Unpaid"
                msg = "A payment is required to play this visual novel."
                
            case ServerResponseCode.SSL_ERROR:
                
                msg_title = "SSL Error"
                msg = "Could not securely connect to the server."
                
            case ServerResponseCode.ALREADY_REDEEMED:
                
                msg_title = "Already Redeemed"
                msg = "The license key has already been redeemed or updated using the provided transaction ID."
                
            case ServerResponseCode.LICENSE_KEY_NOT_PRIVATE:
                
                # The user is trying to update a public license key with a transaction ID.
                msg_title = "Private License Key"
                msg = "The provided license key is public. Only a private license key can be updated."
                
            case ServerResponseCode.TRANSACTION_ID_NOT_FOUND:
                
                msg_title = "Transaction ID Not Found"
                msg = "The provided transaction ID was not found.\n\nThe transaction ID should have been emailed to you after making a payment."
                
            case ServerResponseCode.VN_NOT_PART_OF_PACKAGE:
                
                msg_title = "Visual Novel Package"
                msg = "This visual novel is not part of the package (tier) that was paid for."
                
            case ServerResponseCode.UNKNOWN:
                
                msg_title = "Unknown Error"
                msg = response_text
            
        try:
            msgbox_func(master=self.mainwindow,
                        title=msg_title,
                        message=msg)
   
            self.entry_license_key.focus()
            
            # Enable the play button after 1 second.
            self.mainwindow.after(1000, self.enable_play_button)
            
            
            
        except tk.TclError:
            # If the parent window closes while the msgbox is open,
            # it'll raise a TclError, so we have this here to exit
            # gracefully.
            return
        

            
    def enable_play_button(self):
        """
        Enable the Play button.
        
        This method is used after an error message box is shown to the user,
        and we want to enable the play button using an .after timer.
        """
        self.btn_play_selection.state(["!disabled"])

    def on_window_closing(self):
        """
        The launch window is closing. Set a shared variable
        flag to indicate that once the launch window closes, the entire
        app should close. The default story shouldn't play, because
        the user has clicked the 'X' to close the launch window.
        """
        Passer.close_after_launch_window = True
        
        self.mainwindow.destroy()

    def on_get_license_key_button_clicked(self):
        """
        If a license key is provided, attempt to associate the provided
        transaction ID with the given license key.
        
        If no license key is provided, then it's probably the first time
        the user is buying a license, so let the web server generate a new
        license key based on the given transaction ID and put that license key
        into the license_key entry widget.
        """
        
        # Get the license key, if provided.
        Passer.web_handler.web_key = self.v_license_key.get().strip()
        
        # Get the transaction ID, which is mandatory.
        transaction_id = self.v_transaction_id.get().strip()
        
        if not transaction_id:
            messagebox.showerror(
                parent=self.mainwindow,
                title="Transaction ID",
                message="Please enter your transaction ID.\nIt should be in the email that was sent to you.")
            return
        
        # The license key and visual novel name will get added later
        # from Passer.web_handler.web_key
        # (if a license key is available)
        # in the web_handler itself, as part of keys that are always included
        # in each request.
        data = {"transaction_id": transaction_id}
        
        Passer.web_handler.\
            send_request(data=data,
                         purpose=WebRequestPurpose.REDEEM_OR_UPDATE_LICENSE_KEY,
                         callback_method=self.on_web_request_finished,
                         increment_usage_count=False)

    def save_license_key(self):
        """
        Get the license from from the entry widget and save it to the local
        config file. The purpose is to prevent having to enter a license key
        again after the visual novel is closed and re-opened.
        """
        
        # Get the license key.
        license_key = self.v_license_key.get().strip()
        
        Passer.player_config.save_data("LicenseKey", license_key)
        
    def populate_license_key(self):
        """
        Get the license key from the config file, if it's there.
        Show the license key in the entry widget if the license key is found.
        """
        
        license_key = Passer.player_config.get_data("LicenseKey")
        if not license_key:
            return
        
        license_key = license_key.strip()
        
        self.v_license_key.set(license_key)

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
                Passer.web_handler.web_key = self.v_license_key.get().strip()
                
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
            
            # Save the license key to the config file so when the visual novel
            # is restarted, the license key will be pre-populated.
            self.save_license_key()            
            
            Passer.web_handler.\
                send_request(data=None,
                             purpose=WebRequestPurpose.VERIFY_LICENSE,
                             callback_method=self.on_web_request_finished,
                             increment_usage_count=False)
            
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

