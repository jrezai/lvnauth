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

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "input_string_window.ui"


class InputStringWindow:
    def __init__(self, master=None, max_character_length=35,
                 title="Input",
                 msg="Enter a value below:",
                 prefill_entry_text=""):

        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)

        self.user_input = None
        self.max_character_length = max_character_length

        # Main widget
        self.mainwindow = builder.get_object("input_window", master)
        builder.connect_callbacks(self)

        self.lbl_msg = builder.get_object("lbl_msg")
        self.entry_input = builder.get_object("entry_input")

        if prefill_entry_text:
            self.entry_input.insert(0, prefill_entry_text)

        # Set the label message and window title
        self.lbl_msg.configure(text=msg)
        self.mainwindow.title(title)

        # Set the initial focus to the entry widget.
        self.entry_input.focus()
        self.mainwindow.bind("<Escape>", self.on_cancel_button_clicked)
        self.mainwindow.bind("<Return>", self.on_ok_button_clicked)
        self.mainwindow.bind("<KP_Enter>", self.on_ok_button_clicked)

        self.mainwindow.transient(master)
        self.mainwindow.grab_set()
        self.mainwindow.wait_window(self.mainwindow)

    def on_ok_button_clicked(self, event=None):
        self.user_input = self.entry_input.get()
        self.mainwindow.destroy()

    def on_cancel_button_clicked(self, event=None):
        self.user_input = None
        self.mainwindow.destroy()

    def on_validate(self, p_entry_value):

        if len(p_entry_value) > self.max_character_length:
            return False

        return True

