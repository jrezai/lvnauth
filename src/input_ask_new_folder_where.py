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

import pathlib
import pygubu

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "ask_create_folder_where.ui"


class WhereNewFolderWindow:
    def __init__(self, master, in_sub_folder_name):

        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)

        self.user_input = None
        self.in_sub_folder_name = in_sub_folder_name

        # Main widget
        self.mainwindow = builder.get_object("ask_where_folder_window", master)
        self.radiobutton_in_sub = builder.get_object("radiobutton_in_sub")
        builder.connect_callbacks(self)

        self.v_folder_where = builder.get_variable("v_folder_where")
        self.radiobutton_in_sub.configure(text=f"In '{self.in_sub_folder_name}'")

        self.mainwindow.bind("<Escape>", self.on_cancel_button_clicked)
        self.mainwindow.bind("<Return>", self.on_ok_button_clicked)
        self.mainwindow.bind("<KP_Enter>", self.on_ok_button_clicked)

        self.mainwindow.transient(master)
        self.mainwindow.grab_set()
        self.mainwindow.wait_window(self.mainwindow)

    def on_ok_button_clicked(self, event=None):
        self.user_input = self.v_folder_where.get()
        self.mainwindow.destroy()

    def on_cancel_button_clicked(self, event=None):
        self.user_input = None
        self.mainwindow.destroy()

    def on_validate(self, p_entry_value):

        if len(p_entry_value) > self.max_character_length:
            return False

        return True

