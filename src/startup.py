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
import editor_window
import tkinter as tk
from project_snapshot import ProjectSnapshot
from new_project_window import ProjectFolderWindow
from snap_handler import SnapHandler
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
        
        
        if SnapHandler.is_in_snap_package():
            app_icon_path = SnapHandler.get_lvnauth_editor_icon_path()
        else:
            app_icon_path = "app_icon.png"
        
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
        self.btn_play_file.configure(command=self.on_play_button_clicked,
                                  image=self.btn_play_file.image)
        
        builder.connect_callbacks(self)

    def on_new_project_menu_clicked(self):
        
        project_folder_window = ProjectFolderWindow(master=self.mainwindow)
        if project_folder_window.new_project_created_successfully:

            editor_app = editor_window.EditorMainApp(self.mainwindow)
            editor_window.Toolbar.save_project()

            open_manager = editor_window.OpenManager(self.mainwindow)
            open_manager.open(lvnap_file_path=ProjectSnapshot.save_full_path)

            self.mainwindow.withdraw()
            
    def on_open_project_menu_clicked(self):
        
        file_types = [("Visual Novel Project", (".lvnap"))]
        file_full_path = tk.filedialog.askopenfilename(parent=self.mainwindow,
                                                       filetypes=file_types)
        if not file_full_path:
            return
        
        # Hide the startup window, because we're about to play the visual novel.
        self.mainwindow.withdraw()

        editor_app = editor_window.EditorMainApp(self.mainwindow)
        open_manager = editor_window.OpenManager(self.mainwindow)
        open_manager.open(lvnap_file_path=file_full_path)
        
        
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
