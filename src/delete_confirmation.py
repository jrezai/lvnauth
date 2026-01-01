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

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "delete_confirmation_window.ui"


class DeleteConfirmationWindow:
    def __init__(self, master, prompt_text: str, items_to_delete: str):

        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)

        self.user_answer = None

        # The main question text to show the user.
        self.prompt_text = prompt_text

        # The full paths to the images that will be deleted
        self.items_to_delete = items_to_delete

        # Main widget
        self.main_window = builder.get_object("delete_confirmation_window", master)
        builder.connect_callbacks(self)

        self.lbl_main_question = builder.get_object("lbl_main_question")
        self.text_path_listings = builder.get_object("text_path_listings")

        # Show the prompt text (for example: 'Remove item..?')
        self.lbl_main_question.configure(text=prompt_text)

        # Scrollbars
        self.sb_h = builder.get_object("sb_h")
        self.sb_v = builder.get_object("sb_v")

        self.sb_h.configure(command=self.text_path_listings.xview)
        self.sb_v.configure(command=self.text_path_listings.yview)

        self.text_path_listings.configure(yscrollcommand=self.sb_v.set,
                                          xscrollcommand=self.sb_h.set)

        self.text_path_listings.configure(state="normal")
        self.text_path_listings.insert("0.0", items_to_delete)
        self.text_path_listings.configure(state="disabled")

        self.main_window.bind("<Escape>", self.on_cancel_button_clicked)
        self.main_window.bind("<Return>", self.on_ok_button_clicked)
        self.main_window.bind("<KP_Enter>", self.on_ok_button_clicked)

        self.main_window.transient(master)
        self.main_window.grab_set()
        self.main_window.wait_window(self.main_window)

    def on_ok_button_clicked(self, event=None):
        self.user_answer = True
        self.main_window.destroy()

    def on_cancel_button_clicked(self, event=None):
        self.user_answer = None
        self.main_window.destroy()


