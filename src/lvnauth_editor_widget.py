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

"""
Changes:

- Nov 24, 2023 (Jobin Rezai) - Prevent middle mouse button from pasting
text into the text widget.
"""


import tkinter as tk
from project_snapshot import ProjectSnapshot


class LVNAuthEditorWidget(tk.Text):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tags = ["command_tag", "after_command", "comment_tag", "dialog_text"]

        self.bind("<KeyRelease>", self.on_key_release)
        self.bind("<<Paste>>", self._on_pasted_text)
        
        # To prevent middle-button pasting text.
        self.bind("<<PasteSelection>>", self.on_middle_button_clicked)
        
        self.configure(exportselection=False)

        # So the keypress method gets ignored when pasting text.
        self.pasted = False
        
        # Read the color values from the config file and apply them
        # to the text widget.        
        self.refresh_colors()

        # Highlight the row that the insert cursor is currently on.
        self.highlight_insert_row()
        
    def refresh_colors(self):
        """
        Read the color values from the config file and apply them
        to the text widget.
        """
        
        config = ProjectSnapshot.config.config
        config.read(ProjectSnapshot.config.config_file_path)

        # Get the selected preset, so we can read its color values.
        selected_preset_section = ProjectSnapshot.config.get_selected_color_preset_section()
        
        editor_background = config.get(selected_preset_section,
                                       "editor.background")
        
        editor_foreground = config.get(selected_preset_section,
                                       "editor.foreground")
        
        select_background = config.get(selected_preset_section,
                                       "editor.select.background")
        
        insert_background = config.get(selected_preset_section,
                                       "editor.insert.background")
        
        editor_commands = config.get(selected_preset_section,
                                     "editor.commands")
        
        editor_after_colon = config.get(selected_preset_section,
                                        "editor.after.colon")
        
        editor_comments = config.get(selected_preset_section,
                                     "editor.comments")
        
        dialog_text = config.get(selected_preset_section,
                                 "editor.dialog.text.forecolor")
        
        dialog_text_bg = config.get(selected_preset_section,
                                    "editor.dialog.text.backcolor")
        
        # Checkbox value, so read it as a boolean.
        dialog_text_bg_disable =\
            config.getboolean(selected_preset_section,
                              "editor.dialog.text.backcolor.disable")
        
        # Disable the dialog text background color?
        if dialog_text_bg_disable:
            # Yes, disable the dialog text background color.
            dialog_text_bg = ""
        
        highlight_row_bg = config.get(selected_preset_section,
                                      "editor.highlight.row.background")          
                
        self.configure(background=editor_background)
        self.configure(foreground=editor_foreground)
        self.configure(selectbackground=select_background)
        self.configure(insertbackground=insert_background)

        self.tag_configure(\
            tagName="command_tag", foreground=editor_commands)
        
        self.tag_configure(\
            tagName="after_command", foreground=editor_after_colon)
        
        self.tag_configure(\
            tagName="comment_tag", foreground=editor_comments)
        
        self.tag_configure(\
            tagName="dialog_text",
            foreground=dialog_text,
            background=dialog_text_bg)

        self.tag_configure(\
            tagName="highlight_row",
            background=highlight_row_bg)
        
        self.tag_raise(tagName="highlight_row")
        
    def on_middle_button_clicked(self, event):
        """
        Prevent the middle mouse button from pasting text.
        """
        return "break"

    def _on_pasted_text(self, event):
        """
        After half a second, iterate over every line
        in the text widget and reapply the tags.
        """

        # So the keypress method gets ignored.
        # Reason: we're going to reevaluate the entire text widget any way,
        # so there is no point is colorizing just one line, which is why
        # we have this flag.
        self.pasted = True

        # Colorize all the contents in the text widget.
        self.after(500, self.reevaluate_entire_contents)

    def reevaluate_current_line(self):
        """
        Colorize the line the insert cursor is currently on.
        """
        self.on_key_release(None)

    def reevaluate_entire_contents(self):
        """
        Go through all the lines in the text widget then
        remove the tags and reapply them.
        
        Purpose: used when text is pasted into the text widget
        and also when loading a script.
        """

        # Get the total number of lines in the text widget.
        # Example: 10.0 (we just want the 10 part)
        total_lines = int(self.index("end").split(".")[0])

        # Go through all the lines in the text widget
        # and colorize them.
        for line in range(1, total_lines):
            start = f"{line}.0"
            end = f"{line}.0 lineend"

            self.colorize_line(start=start, end=end)

        # So that the keyrelease method will not be ignored.
        self.pasted = False

    def highlight_insert_row(self):
        """
        Highlight the row that the insert cursor is currently on.
        """

        ms_delay = 150

        self.tag_remove("highlight_row", "1.0", tk.END)

        # If any text is selected, don't highlight the insert row.
        tag_range_selection = self.tag_ranges(tk.SEL)
        if tag_range_selection:
            # Some text is selected, so don't highlight the row.
            self.after(ms_delay, self.highlight_insert_row)
            return

        self.tag_add("highlight_row", "insert linestart", "insert lineend +1c")

        self.after(ms_delay, self.highlight_insert_row)

    def colorize_line(self, start, end):
        """
        Colorize the given line.
        
        Arguments:
        
        - start: text widget start position, such 3.0 (line 3, character 0)
        - end: text widget end position, such as 3.0 lineend (end of line 3)
        """

        # Get the text of the current line.
        line_text = self.get(start, end)

        # Remove all the tags of the current line,
        # so we can re-colorize it.
        self.remove_tags(start=start, end=end)

        # Add tags so the line shows up colorized based on the syntax.
        self.add_tags(text=line_text, start=start, end=end)

    def remove_tags(self, start, end):
        """
        Remove all the tags for the given range
        because each time a line changes, we clear all the tags for that line.
        """

        for tag in self.tags:
            self.tag_remove(tag, start, end)

    def add_tags(self, text, start, end):
        """
        Re-evaluate the line and apply tags.
        """

        if not text:
            return

        # Get the first non-whitespace character
        starting_char = text.lstrip()
        if not starting_char:
            return
        else:
            starting_char = starting_char[0]

        # Is it a comment line?
        if starting_char == "#":
            # Colorize the comment line

            self.search("#", start, stopindex="end")
            self.tag_add("comment_tag", start, end)

            return

        # Is it the beginning of a command line?
        elif starting_char == "<":
            # Colorize the command line

            start_bracket_location = self.search("<", start, stopindex=end)

            if start_bracket_location:
                end_bracket_location = self.search(">", start_bracket_location, stopindex=end)

                if end_bracket_location:
                    colon_position = self.search(":", start, stopindex=end)

                    # Did we have a : colon character?
                    if colon_position:
                        self.tag_add("command_tag", start + "+1c", colon_position)
                        self.tag_add("after_command", colon_position + "+1c", end_bracket_location)

                    else:
                        # No colon found, but a ending bracket was found.
                        # This is used for commands with no parameters.
                        # Example <halt>
                        self.tag_add("command_tag", start + "+1c", end_bracket_location)

        else:
            # Regular dialog text
            self.tag_add("dialog_text", start, end)

    def on_key_release(self, *args):
        """
        Colorize the current line.
        """

        if self.pasted:
            return

        # Get the current line number that the insert cursor is on.
        current_line_number = self.get_current_line_number()

        # Get the line range.
        start = f"{current_line_number}.0"
        end = f"{current_line_number}.0 lineend + 1c"

        self.colorize_line(start=start, end=end)

    def get_current_line_number(self) -> int:
        """
        Return the line number the insert cursor is on.
        Example: 3
        """
        # Get the current line number
        current_line_number = self.index(tk.INSERT)
        current_line_number = current_line_number.split(".")[0]

        return int(current_line_number)


if __name__ == "__main__":
    root = tk.Tk()

    test = LVNAuthEditorWidget(master=root, font=("TkDefaultText", 15, "normal"))
    test.pack()

    root.mainloop()
