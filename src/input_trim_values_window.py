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
PROJECT_UI = PROJECT_PATH / "ui" / "input_trim_values_window.ui"


class InputTrimValuesWindow:
    def __init__(self,
                 master=None,
                 _from=0,
                 _to=100,
                 title="Input",
                 msg="Trim Values",
                 prefill_previous_letters="",
                 prefill_check_previous_letter=False,
                 prefill_left_value=0,
                 prefill_right_value=0,
                 prefill_letter_value="",
                 edit_mode=False):

        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)

        self.user_input_left = None
        self.user_input_right = None
        self.user_input_letter = None
        self.user_input_previous_letters = None
        self.user_input_check_previous_letter = None

        self._from = _from
        self._to = _to
        
        # Main widget
        self.mainwindow = builder.get_object("input_window", master)
        builder.connect_callbacks(self)

        self.frame_title = builder.get_object("frame_title")
        self.lbl_letter = builder.get_object("lbl_letter")
        self.entry_letter = builder.get_object("entry_letter")
        self.spinbox_left = builder.get_object("spinbox_left")
        self.spinbox_right = builder.get_object("spinbox_right")
        self.entry_previous_letters = builder.get_object("entry_previous_letters")

        # Set the maximums for the spinbox widgets
        self.spinbox_left.configure(from_=_from,
                                    to=_to)
        self.spinbox_right.configure(from_=_from,
                                     to=_to)
        
        self.v_letter = builder.get_variable("v_letter")
        self.v_left = builder.get_variable("v_left")
        self.v_right = builder.get_variable("v_right")
        self.v_previous_letters = builder.get_variable("v_previous_letters")
        self.v_check_previous_letter = builder.get_variable("v_check_previous_letter")

        # Trace when this variable gets changed
        # so that we can enable/disable the 'previous letters' radio button.
        self.v_check_previous_letter.trace_add("write", self.on_rule_type_changed)

        self.v_left.set(prefill_left_value)
        self.v_right.set(prefill_right_value)

        # The letter
        if prefill_letter_value:
            self.entry_letter.insert(0, prefill_letter_value)

        # Previous letters rule
        # Show the previous letters (if any), as long as the rule,
        # 'regardless of previous letter' is not enabled, because otherwise
        # it would show '(Any)' in the entry.
        if prefill_previous_letters and prefill_check_previous_letter:
            self.entry_previous_letters.insert(0, prefill_previous_letters)
            
        # Should we check previous letters?
        # (There is a trace for the variable below.)
        self.v_check_previous_letter.set(prefill_check_previous_letter)
            
        
        # Set the label message and window title
        self.frame_title.configure(text=msg)
        self.mainwindow.title(title)

        # Set the initial focus to the entry widget.
        self.spinbox_left.focus()
        self.mainwindow.bind("<Escape>", self.on_cancel_button_clicked)
        self.mainwindow.bind("<Return>", self.on_ok_button_clicked)
        self.mainwindow.bind("<KP_Enter>", self.on_ok_button_clicked)

        # Don't allow the letter to be changed if we're in edit-mode.
        if edit_mode:
            self.lbl_letter.state(["disabled"])
            self.entry_letter.state(["disabled"])
        else:
            # The letter entry should have the first focus
            self.entry_letter.focus()

        self.mainwindow.transient(master)
        
        # In some cases, we may need to update idle tasks below.
        # Otherwise, grab_set() may show an exception. One situation
        # where this is needed is when double-clicking the treeview widget
        # to edit the trim values.
        self.mainwindow.update_idletasks()

        self.mainwindow.grab_set()
        self.mainwindow.wait_window(self.mainwindow)

    def on_rule_type_changed(self, *args):
        """
        The variable, v_check_previous_letter, has changed its value.
        
        Disable the previous-letter entry widget if the variable,
        v_check_previous_letter, has changed to False, otherwise enable
        the entry widget.
        """
        if not self.v_check_previous_letter.get():
            self.entry_previous_letters.state(["disabled"])
        else:
            self.entry_previous_letters.state(["!disabled"])

    def on_ok_button_clicked(self, event=None):
        self.user_input_left = self.v_left.get()
        self.user_input_right = self.v_right.get()
        self.user_input_letter = self.v_letter.get()
        self.user_input_previous_letters = self.v_previous_letters.get()
        self.user_input_check_previous_letter = self.v_check_previous_letter.get()
        self.mainwindow.destroy()

    def on_cancel_button_clicked(self, event=None):
        self.user_input_left = None
        self.user_input_right = None
        self.user_input_letter = None
        self.user_input_previous_letters = None
        self.mainwindow.destroy()

    def on_validate(self, p_entry_value):
        """
        Validate spinbox value to make sure it's an integer.
        """
        try:

            test_value = int(p_entry_value)

        except ValueError:

            return False
            
        return True
    
    def on_validate_letter(self, p_entry_value):
        """
        Validate letter entry to make sure there is a single character.
        """
        if len(p_entry_value) > 1:
            return False

        return True

if __name__ == "__main__":
    app = InputTrimValuesWindow()
    app.mainwindow.mainloop()
