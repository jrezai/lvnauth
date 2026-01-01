"""
Copyright 2023-2026 Jobin Rezai

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

import pathlib
import pygubu
from tkinter import messagebox, filedialog

import project_snapshot
from project_snapshot import ProjectSnapshot


PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "project_folder_window.ui"


class ProjectFolderWindow:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        # Main widget
        self.project_folder_window = builder.get_object("project_folder_window", master)
        
        self.project_folder_window.bind("<Escape>", self.on_cancel_button_clicked)
        
        self.entry_project_name = builder.get_object("entry_project_name")
        self.entry_project_folder = builder.get_object("entry_project_folder")

        self.project_name = None
        self.project_folder = None
        
        # So the caller of this class will know whether
        # the project folder was created successfully or not.
        self.new_project_created_successfully = False
        
        builder.connect_callbacks(self)
                
        self.entry_project_name.focus()

        self.project_folder_window.transient(master)
        self.project_folder_window.grab_set()
        self.project_folder_window.wait_window(self.project_folder_window)
        

    def on_cancel_button_clicked(self, *args):
        self.project_folder_window.destroy()

    def on_browse_button_clicked(self):

        result = filedialog.askdirectory(parent=self.project_folder_window,
                                         title="Select Folder")
        if not result:
            return
        else:
            self.entry_project_folder.delete(0, "end")
            self.entry_project_folder.insert(0, result)

    def on_ok_button_clicked(self) -> bool:
        """
        Create the project's folder.
        """
        project_name = self.entry_project_name.get().strip()
        project_folder = self.entry_project_folder.get().strip()

        # Now generate a save path that includes the project name.
        project_path = pathlib.Path(project_folder) / project_name

        # Make sure a project name has been specified.
        if not project_name:
            messagebox.showerror(parent=self.project_folder_window,
                                 title="Missing Project Name",
                                 message="Please type a project name.")
            self.entry_project_name.focus()
            return

        # Make sure a project folder has been specified
        elif not project_folder:
            messagebox.showerror(parent=self.project_folder_window,
                                 title="Missing Project Save Folder",
                                 message="Please specify a folder to save the project in.")
            self.entry_project_folder.focus()
            return

        if not project_path.exists():
            result = messagebox.askyesno(parent=self.project_folder_window,
                                         title="Project Folder",
                                         message="The project folder does not exist.\n\n"
                                         "Would you like to create it?\n\n"
                                         f"{project_path}")
            if not result:
                return
            

        # Save the path to the new .lvnap file
        lvnap_path = project_path / (project_name + ".lvnap")        

        # Does the .lvnap file already exist? Warn the user.
        if lvnap_path.exists():
            result = messagebox.askyesno(parent=self.project_folder_window,
                                         title="Project Already Exists",
                                         message="The project file already exists.\n\n"
                                         "Would you like to overwrite it?\n\n"
                                         f"{str(lvnap_path)}")
            
            if not result:
                return

        # Make sure all the sub-paths (/images, /audio) are there.
        # If not, create them now.
        try:

            # Create the main project folder if it doesn't already exist.
            project_path.mkdir(parents=True, exist_ok=True)

            if not project_path.exists():
                messagebox.showerror(parent=self.project_folder_window,
                                     title="Could Not Create Folder",
                                     message="Could not create the project folder.")
                return

            # Loop through enum paths (the .value has the Path object)
            
            # Create the image sub-folders (ie: /images/font_sprites)
            for sub_path in project_snapshot.SubPaths:
                
                # Don't create a path to poster.png, because it's a file,
                # not a directory.
                if sub_path == project_snapshot.SubPaths.POSTER_IMAGE_PATH:
                    continue
                
                folder_path = project_path / sub_path.value
                folder_path.mkdir(parents=True, exist_ok=True)

        except OSError as e:
            messagebox.showerror(parent=self.project_folder_window,
                                 title="Create Folder Error",
                                 message="Could not create the project folder.\n\n"
                                 f"Details: {e}")
            return

        self.project_name = project_name
        self.project_folder = project_folder


        ProjectSnapshot.save_full_path = lvnap_path
        ProjectSnapshot.project_path = project_path
        
        # So the caller of this class will know that the project
        # was created successfully.
        self.new_project_created_successfully = True

        self.project_folder_window.destroy()
        
        


