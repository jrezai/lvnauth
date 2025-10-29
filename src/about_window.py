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

import pathlib
import webbrowser
import pygubu
from PIL import Image, ImageTk
from project_snapshot import ProjectSnapshot
from linklabel_widget import LinkLabel
from container_handler import ContainerHandler
PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "about_window.ui"
PROJECT_LVN_LICENSE_UI =  PROJECT_PATH / "ui" / "lvnauth_license_window.ui"
PROJECT_LIBRARIES_ICONS_LICENSE_UI = PROJECT_PATH / "ui" / "about_libraries_window.ui"


class LVNAuthLicenseWindow:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_LVN_LICENSE_UI)
        # Main widget
        self.mainwindow = builder.get_object("lvnauth_license_window", master)
        builder.connect_callbacks(self)
        
        self.connect_scrollbars()
        
        # So the user can close the window with the Esc key
        self.mainwindow.bind("<Escape>", self.on_ok_button_clicked)
        
        self.mainwindow.focus()
        self.mainwindow.transient(master)
        self.mainwindow.grab_set()
        self.mainwindow.wait_window(self.mainwindow)        

    def connect_scrollbars(self):
        
        # LVNAuth license
        text_lvnauth = self.builder.get_object("text_lvnauth")
        sb_vertical_lvnauth = self.builder.get_object("sb_vertical_lvnauth")
        sb_vertical_lvnauth.configure(command=text_lvnauth.yview)
        text_lvnauth.configure(yscrollcommand=sb_vertical_lvnauth.set)  

    def run(self):
        self.mainwindow.mainloop()

    def on_ok_button_clicked(self, *args):
        self.mainwindow.destroy()

        
class AboutLibrariesWindow:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_LIBRARIES_ICONS_LICENSE_UI)
        # Main widget
        self.mainwindow = builder.get_object("about_libraries_window", master)
        builder.connect_callbacks(self)
        
        self.connect_scrollbars()

        # So the user can press the Esc key to close the window.
        self.mainwindow.bind("<Escape>", self.on_esc_key_pressed)

        self.mainwindow.focus()
        self.mainwindow.transient(master)
        self.mainwindow.grab_set()
        self.mainwindow.wait_window(self.mainwindow)
                
    def on_esc_key_pressed(self, *args):
        self.mainwindow.destroy()
        
    def connect_scrollbars(self):
        
        # Pygame-ce
        text_pygame = self.builder.get_object("text_pygame")
        sb_vertical_pygame = self.builder.get_object("sb_vertical_pygame")
        sb_vertical_pygame.configure(command=text_pygame.yview)
        text_pygame.configure(yscrollcommand=sb_vertical_pygame.set)
        
        # Pillow
        text_pillow = self.builder.get_object("text_pillow")
        sb_vertical_pillow = self.builder.get_object("sb_vertical_pillow")
        sb_vertical_pillow.configure(command=text_pillow.yview)
        text_pillow.configure(yscrollcommand=sb_vertical_pillow.set)
        
        # Pygubu
        text_pygubu = self.builder.get_object("text_pygubu")
        sb_vertical_pygubu = self.builder.get_object("sb_vertical_pygubu")
        sb_vertical_pygubu.configure(command=text_pygubu.yview)
        text_pygubu.configure(yscrollcommand=sb_vertical_pygubu.set)              

        # Ionic
        text_ionic = self.builder.get_object("text_ionic")
        sb_vertical_ionic = self.builder.get_object("sb_vertical_ionic")
        sb_vertical_ionic.configure(command=text_ionic.yview)
        text_ionic.configure(yscrollcommand=sb_vertical_ionic.set)
        
        # screeninfo
        text_screeninfo = self.builder.get_object("text_screeninfo")
        sb_vertical_screeninfo = self.builder.get_object("sb_vertical_screeninfo")
        sb_vertical_screeninfo.configure(command=text_screeninfo.yview)
        text_screeninfo.configure(yscrollcommand=sb_vertical_screeninfo.set)

class AboutWindow:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow = builder.get_object("about_window", master)
        builder.connect_callbacks(self)
        
        # LVNAuth logo image
        if ContainerHandler.is_in_snap_package():
            lvnauth_snap_directory = ContainerHandler.get_lvnauth_src_folder()
            lvnauth_logo_path = lvnauth_snap_directory / "lvnauth_logo.png"
        
        elif ContainerHandler.is_in_flatpak_package():
            lvnauth_flatpak_directory = ContainerHandler.get_flatpak_app_directory()
            lvnauth_logo_path = lvnauth_flatpak_directory / "lvnauth_logo.png"
        else:
            # Not a Snap or Flatpak package; get the regular path (same folder as this script.)
            lvnauth_logo_path = "lvnauth_logo.png"

        self.lvnauth_image = Image.open(lvnauth_logo_path)
        self.lvnauth_image = ImageTk.PhotoImage(image=self.lvnauth_image)
        self.lbl_lvnauth = builder.get_object("lbl_lvnauth")
        self.lbl_lvnauth.configure(image=self.lvnauth_image)
        
        self.frame_version_info = builder.get_object("frame_version_info")
        
        self.lbl_version = builder.get_object("lbl_version")
        self.lbl_version.configure(text=f"Version {ProjectSnapshot.EXACT_EDITOR_VERSION}")
        
        self.lbl_website = LinkLabel(self.frame_version_info,
                                     text="https://lvnauth.org",
                                     command=self.visit_website)
        self.lbl_website.grid(row=1, column=0, sticky="w")
        
        # So the user can press the Esc key to close the window.
        self.mainwindow.bind("<Escape>", self.on_ok_button_clicked)

        self.connect_scrollbars()

        self.mainwindow.focus()
        self.mainwindow.transient(master)
        self.mainwindow.grab_set()
        self.mainwindow.wait_window(self.mainwindow)      
        
    def visit_website(self):
        webbrowser.open_new(r"https://lvnauth.org")
        
    def connect_scrollbars(self):
        
        # LVNAuth license
        text_license = self.builder.get_object("text_license")
        
        sb_vertical = self.builder.get_object("sb_vertical")
        sb_vertical.configure(command=text_license.yview)
        
        sb_horizontal = self.builder.get_object("sb_horizontal")
        sb_horizontal.configure(command=text_license.xview)
        
        text_license.configure(yscrollcommand=sb_vertical.set,
                               xscrollcommand=sb_horizontal.set)  
        
    def on_ok_button_clicked(self, *args):
        self.mainwindow.destroy()
        
    def on_view_license_button_clicked(self):
        license_window = LVNAuthLicenseWindow(self.mainwindow)
        
    def on_libraries_button_clicked(self):
        libraries_window = AboutLibrariesWindow(self.mainwindow)
        

    def run(self):
        self.mainwindow.mainloop()




if __name__ == "__main__":
    app = AboutWindow()
    app.run()
