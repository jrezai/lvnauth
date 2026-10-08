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
from pygubu import builder
import editor_window
import tkinter as tk
from project_snapshot import ProjectSnapshot
from new_project_window import ProjectFolderWindow
from container_handler import ContainerHandler
from temp_handler import TempHandler, TempContentType
from tkinter import messagebox
PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "startup_window.ui"


class StartupWindow:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow: tk.Toplevel
        self.mainwindow = builder.get_object("startup_window", master)
        
        # Clean-up any LVNAuth temp files that might be in the temporary 
        # directory. Under normal circumstances, there shouldn't be any
        # unless LVNAuth quit unexpectedly and wasn't able to clean up the
        # temp files.
        TempHandler.cleanup_temp_files(TempContentType.ALL)

        if (
            ContainerHandler.is_in_snap_package()
            or ContainerHandler.is_in_flatpak_package()
        ):
            app_icon_path = ContainerHandler.get_lvnauth_editor_icon_path()
        else:
            app_icon_path = ContainerHandler.get_absolute_path("app_icon.png")
        
        # App icon
        app_icon = tk.PhotoImage(file=app_icon_path)
        self.mainwindow.app_icon = app_icon
        self.mainwindow.iconphoto(True, self.mainwindow.app_icon)
        
        # Edit details image
        editor_image = tk.PhotoImage(data=editor_window.Icons.EDIT_DETAILS_24_F.value)
        
        self.menu_editor = builder.get_object("menu_editor")
        

        self.btn_editor = builder.get_object("btn_editor")
        self.btn_editor.image = editor_image
        self.btn_editor.configure(image=self.btn_editor.image,
                                  menu=self.menu_editor)

        play_image = tk.PhotoImage(data=editor_window.Icons.PLAY_24_F.value)
        self.btn_play_file = builder.get_object("btn_play_file")
        self.btn_play_file.image = play_image
        self.btn_play_file.configure(
            command=self.on_play_button_clicked, image=self.btn_play_file.image
        )

        self.lbl_version = builder.get_object("lbl_version")
        self.lbl_version.configure(
            text=f"Version {ProjectSnapshot.EXACT_EDITOR_VERSION} ({ProjectSnapshot.RELEASE_DATE})"
        )

        builder.connect_callbacks(self)

        self.populate_recently_opened_projects()

    def populate_recently_opened_projects(self):
        """
        Dynamically populate the menus with recently opened projects.
        """

        # Load the list of recently opened projects from the configuration
        # file, if available.
        recent_projects = ProjectSnapshot.config.get_recent_projects()

        # Add each recent project to the menu with a command to open it.
        for project_path in recent_projects:
            self.menu_editor.add_command(
                label=project_path,
                command=lambda path=project_path: self.on_open_project_menu_clicked(
                    path
                ),
            )

        self.menu_editor.add_command(
            label="Clear Recent List",
            command=self.on_clear_recent_projects_menu_clicked,
        )

        # No recent projects to display, so disable the clear menu and return.
        if not recent_projects:
            self.menu_editor.entryconfig("Clear Recent List", state="disabled")

            return

    def on_clear_recent_projects_menu_clicked(self):
        """
        Clear the list of recently opened projects.
        """
        # Clear the recent projects list in the configuration
        ProjectSnapshot.config.remove_all_recent_projects()

        # Clear menu indexes 3 and onward, which are the recent project entries.
        # This will remove the Clear Recent List menu item as well, but we'll
        # re-add it below.
        self.menu_editor.delete(3, "end")

        # Re-add the "Clear Recent List" menu item to the end of the menu
        # but disable it since there are no recent projects to clear.
        self.menu_editor.add_command(
            label="Clear Recent List",
            command=self.on_clear_recent_projects_menu_clicked,
            state="disabled",
        )

    def on_new_project_menu_clicked(self):

        project_folder_window = ProjectFolderWindow(master=self.mainwindow)
        if project_folder_window.new_project_created_successfully:
            editor_app = editor_window.EditorMainApp(self.mainwindow)
            editor_window.Toolbar.save_project()

            open_manager = editor_window.OpenManager(self.mainwindow)
            open_manager.open(lvnap_file_path=ProjectSnapshot.save_full_path)

            self.mainwindow.withdraw()

    def on_open_project_menu_clicked(self, existing_project_path=None):
        """
        Open an existing project. If the existing_project_path is provided,
        it will open that project directly. Otherwise, it will prompt the user
        to select a project file.
        """
        if not existing_project_path:
            file_types = [("Visual Novel Project", (".lvnap"))]
            file_full_path = tk.filedialog.askopenfilename(
                parent=self.mainwindow, filetypes=file_types
            )
            if not file_full_path:
                return
        else:
            file_full_path = existing_project_path

        # Make sure the file_full_path is a pathlib.Path object
        if isinstance(file_full_path, str):
            file_full_path = pathlib.Path(file_full_path)

        # Check if the project file exists before trying to open it
        if not file_full_path.exists():
            messagebox.showerror(
                "File Not Found",
                f"The project file '{file_full_path}' does not exist.",
                parent=self.mainwindow,
            )
            return

        # Hide the startup window, because we're about to play the visual novel.
        self.mainwindow.withdraw()

        editor_app = editor_window.EditorMainApp(self.mainwindow)
        open_manager = editor_window.OpenManager(self.mainwindow)
        open_manager.open(lvnap_file_path=file_full_path)

        # Add the opened project to the recent projects list
        # in the configuration
        ProjectSnapshot.config.add_recent_project(file_full_path)
        
        self.mainwindow.withdraw()        
    
    def on_play_button_clicked(self):
        
        file_types = [("Visual Novel", (".lvna"))]
        file_full_path = tk.filedialog.askopenfilename(parent=self.mainwindow,
                                                       filetypes=file_types)
        if not file_full_path:
            return
        
        # Hide the startup window, because we're about to play the visual novel.
        self.mainwindow.withdraw()
        
        # Attempt to play the visual novel.
        editor_window.EditorMainApp.\
            play_lvna_file(lvna_file_path=file_full_path,
                           error_window_master=self.mainwindow, 
                           show_launch_window=True,
                           regular_play_mode=True)
        
        # Re-show the startup window because the visual novel has closed.
        self.mainwindow.deiconify()

    def run(self):
        self.mainwindow.mainloop()


if __name__ == "__main__":
    app = StartupWindow()
    app.run()
