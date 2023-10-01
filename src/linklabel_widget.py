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

import tkinter as tk
from tkinter import ttk
from tkinter import font

class LinkLabel(ttk.Label):

    unique_style_counter = -1
    font_label_size = 8

    def __init__(self, master, smalltext=False, command=None, **kw):
        
       
        # Default font name
        self.default_font = font.nametofont("TkDefaultFont")
        
        # Default font object dictionary
        self.default_font_name = self.default_font.actual()

        font_size = self.default_font_name.get("size")

        self.custom_font_underlined = font.Font(family=self.default_font_name,
                                                size=font_size,
                                                underline=True)

        self.custom_font_not_underlined = font.Font(family=self.default_font_name,
                                                    size=font_size,
                                                    underline=False)

        LinkLabel.unique_style_counter += 1
        self.unique_style_name = f"LinkLabel{LinkLabel.unique_style_counter}.TLabel"


        self.s = ttk.Style()
        self.s.configure(self.unique_style_name, font=self.custom_font_underlined, foreground="blue")        
        kw["style"] = self.unique_style_name

        super().__init__(master, **kw)        

        self.func_id_mouse_enter = None
        self.func_id_mouse_leave = None
        self.func_id_mouse_down = None
        self.func_id_mouse_up = None

        # Bind to mouse hover events
        self.enable()

        # The function to run when the linklabel is clicked.
        self.command = command

        #print("Style is", self.configure("style"))

    def disable(self):
        if None in (self.func_id_mouse_enter,
                    self.func_id_mouse_leave,
                    self.func_id_mouse_down,
                    self.func_id_mouse_up):
            return

        self.configure(state=tk.DISABLED, cursor="arrow")

        # Simulate leaving the linklabel.

        # This was made so if the click causes the linklabel to get disabled,
        # The non-hover default underline will show.
        # Otherwise, the linklabel will get disabled without an underline
        # because the mouse pointer was on it before it was disabled.

        # If the current font of the linklabel is not underlined, it means
        # it's being hovered on, so reset its font/underline.
        font_internal_name = self.s.lookup(self.unique_style_name, "font")

        font_being_used = font.nametofont(font_internal_name)

        if font_being_used.cget("underline") == 0:
            self.on_mouse_leave(None)

        self.unbind("<Enter>", self.func_id_mouse_enter)
        self.unbind("<Leave>", self.func_id_mouse_leave)
        self.unbind("<Button-1>", self.func_id_mouse_down)
        self.unbind("<ButtonRelease-1>", self.func_id_mouse_up)

        self.func_id_mouse_enter = None
        self.func_id_mouse_leave = None
        self.func_id_mouse_down = None
        self.func_id_mouse_up = None

    def enable(self):
        self.configure(state=tk.NORMAL, cursor="hand2")

        self.func_id_mouse_enter = self.bind("<Enter>", self.on_mouse_enter)
        self.func_id_mouse_leave = self.bind("<Leave>", self.on_mouse_leave)
        self.func_id_mouse_down = self.bind("<Button-1>", self.on_mouse_down)
        self.func_id_mouse_up = self.bind("<ButtonRelease-1>", self.on_mouse_up)        

    def on_mouse_down(self, event):

        self.s.configure(self.unique_style_name, foreground="red")

    def on_mouse_up(self, event):

        self.s.configure(self.unique_style_name, foreground="blue")

        if self.command:
            self.command()

    def on_mouse_enter(self, event):

        self.s.configure(self.unique_style_name, font=self.custom_font_not_underlined, foreground="blue")   
        # print("Entered")

    def on_mouse_leave(self, event):
        self.s.configure(self.unique_style_name, font=self.custom_font_underlined, foreground="blue")   
        #print("left")