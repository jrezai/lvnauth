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
from rect_object import RectObject
PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "rect_options_window.ui"



class RectOptionsWindowApp:
    def __init__(self,
                 master,
                 edit_rect: RectObject,
                 update_func):
        
        """
        A rect options window which allows the user to edit
        the manual vertical settings (top and bottom), and the line number,
        and whether to automatically detect the vertical top and bottoms
        settings based on other letters on the same line number.
        
        Arguments:
        
        - master: the main window to associated this window with.
        
        - edit_rect: the current rect settings of the rect being edited.
        
        - update_func: a reference to _update_rect which takes in a new
        rect object and then updates the main rect options dictionary with
        the newly updated rect object after the user makes changes in
        this window.
        """

        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow = builder.get_object("rect_options_window", master)

        self.v_line_number = builder.get_variable("v_line_number")
        self.v_use_manual_top = builder.get_variable("v_use_manual_top")
        self.v_manual_top_value = builder.get_variable("v_manual_top_value")
        self.v_fixed_position = builder.get_variable("v_fixed_position")

        # Default the vertical position radio button to 'Top'
        self.rb_top = builder.get_object("rb_top")
        self.rb_top.invoke()

        self.cancel_values =\
            {"v_line_number": self.v_line_number.get(),
            "v_use_manual_top": self.v_use_manual_top.get(),
            "v_manual_top_value": self.v_manual_top_value.get(),
            "v_fixed_position": self.v_fixed_position.get()}

        self.update_func = update_func

        # The rect id that is being edited.
        self.edit_rect = edit_rect

        self.spinbox_manual_top = self.builder.get_object("spinbox_manual_top")
        self.lbl_top_most_info = self.builder.get_object("lbl_top_most_info")
        self.rb_top = self.builder.get_object("rb_top")
        self.rb_middle = self.builder.get_object("rb_middle")
        self.rb_bottom = self.builder.get_object("rb_bottom")

        # Load current rect settings
        self.v_fixed_position.set(edit_rect.fixed_position)
        self.v_line_number.set(edit_rect.line_number)
        self.v_manual_top_value.set(edit_rect.top_value)
        self.v_use_manual_top.set(edit_rect.use_manual_top)

        builder.connect_callbacks(self)

        # Enable/disabled widgets depending on the checkbox check-state
        # for 'Use manual top'.
        self._determine_widget_states()
        
    def on_manual_checkbox_changed(self):
        """
        The checkbox, 'Use manual top', has changed its state.
        It's either checked or unchecked.
        
        Enable or disable related widgets as needed.
        """

        # Enable or disable widgets depending on the checkbox's value.
        self._determine_widget_states()
        
    def _determine_widget_states(self):
        """
        Determine whether the 'top', 'middle', 'bottom'
        radio buttons should be enabled or not, based on whether
        the checkbox, 'Use manual top' is checked or not.
        """

        use_manual_top = self.v_use_manual_top.get()
        if use_manual_top:
            self.lbl_top_most_info.state(["!disabled"])
            self.spinbox_manual_top.state(["!disabled"])
            state = "disabled"
        else:
            self.lbl_top_most_info.state(["disabled"])
            self.spinbox_manual_top.state(["disabled"])

            state = "!disabled"

        self.rb_top.state([state])
        self.rb_middle.state([state])
        self.rb_bottom.state([state])

    def run(self):
        self.mainwindow.mainloop()

    def on_ok_button_clicked(self):
        """
        Save the rect settings and close the rect settings window.
        """
        self.edit_rect.top_value = self.v_manual_top_value.get()
        self.edit_rect.use_manual_top = self.v_use_manual_top.get()
        self.edit_rect.fixed_position = self.v_fixed_position.get()
        self.edit_rect.line_number = self.v_line_number.get()

        # Update the main rect object dictionary because
        # the user clicked OK to confirm updates.
        self.update_func(self.edit_rect)
        
        self.mainwindow.destroy()
        
    def on_cancel_button_clicked(self):
        """
        Restore the rect options tk variables
        and close the rect options window.
        """

        # Restore the tk variables
        self.v_line_number = self.cancel_values.get("v_line_number")
        self.v_fixed_position = self.cancel_values.get("v_fixed_position")
        self.v_manual_top_value = self.cancel_values.get("v_manual_top_value")
        self.v_use_manual_top = self.cancel_values.get("v_use_manual_top")
        
        self.mainwindow.destroy()


if __name__ == "__main__":
    app = RectOptionsWindowApp()
    app.run()
