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
import tkinter as tk
PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "play_error_window.ui"

"""
Used for showing Python exceptions to the user if an exception
is raised during the playback of a visual novel.
"""
class PlayErrorWindow:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow = builder.get_object("play_error_window", master)
        builder.connect_callbacks(self)
        
        self.sb_horizontal = builder.get_object("sb_horizontal")
        self.sb_vertical = builder.get_object("sb_vertical")
        
        self.text1: tk.Text
        self.text1 = builder.get_object("text1")
        
        self.connect_scroll_bars()
        
    def show_text(self, text: str):
        """
        Delete the current text in the text widget and
        show the given text string instead.
        
        Make the text widget read-only after the text
        has been inserted.
        """
        self.text1.configure(state="normal")
        self.text1.delete(1.0, tk.END)
        self.text1.insert(1.0, text)
        self.text1.configure(state="disabled")
        
    def connect_scroll_bars(self):
        """
        Connect the horizontal and vertical scrollbars
        to the text widget.
        """
        self.sb_horizontal.configure(command=self.text1.xview)
        self.sb_vertical.configure(command=self.text1.yview)
        
        self.text1.configure(xscrollcommand=self.sb_horizontal.set,
                             yscrollcommand=self.sb_vertical.set)
        
    def on_ok_button_clicked(self):
        """
        The OK button has been clicked, so close the window.
        """
        self.mainwindow.destroy()

    def run(self):
        self.mainwindow.mainloop()


if __name__ == "__main__":
    app = PlayErrorWindow()
    app.run()
