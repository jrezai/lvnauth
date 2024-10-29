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

import re
import tkinter as tk
from tkinter import ttk
from tkinter import font

"""
Used for showing parameter descriptions based on where the caret is
in the editor's text widget.
"""
class ParameterDescription:
    
    # Holds the .after iid
    # Purpose: so parameter descriptions are not searched with every single
    # quick change. Descriptions are shown a few milliseconds later because
    # of this variable.
    last_after_timer = None
    
    def __init__(self,
                 read_text_widget: tk.Text,
                 show_text_widget: tk.Text,
                 show_text_frame: ttk.Frame):
        """
        Arguments:
        
        - read_text_widget: the text widget to check the caret position from.
        """
        
        # Get a ttk frame's background color
        style = ttk.Style()
        frame_bg_color = style.lookup("TFrame", "background")
        label_fg_color = style.lookup("TLabel", "foreground")
        # print(frame_bg_color, label_fg_color)

        self.read_text_widget = read_text_widget
        self.show_text_widget = show_text_widget
        self.show_text_frame = show_text_frame
        
        root_name = show_text_widget.winfo_toplevel().winfo_parent()
        root_window = show_text_widget.nametowidget(root_name)
        self.root_window = root_window
        
        # Any time the text widget is changed (new text, deleted text, etc.), 
        # we should shrink or grow the text widget as-needed to make it fit
        # the new text. That's what this line does.
        self.show_text_widget.bind("<Configure>", self.refresh_height)
        
        self.show_text_widget.configure(background=frame_bg_color,
                                        foreground=label_fg_color)
        
        # Used for commands that end with '_stop_movement_condition',
        # such as <character_stop_movement_condition>
        # One variance of that command has 2 arguments instead of 3, which
        # doesn't have a side-to-check argument. We use this to find
        # the parameter description for that shorter version of the command.
        self.STOP_MOVEMENT_CONDITION_ENDING_SPECIAL = "_no_side_to_check"
        
        # The parameter descriptions are stored here.
        self.data = {"load_audio": ("Audio name",),
                     "load_music": ("Music name",), 
                     "play_music": ("Music name", "(optional) Loop playback"),
                     "play_sound": ("Sound name", ),
                     "play_voice": ("Voice sound", ),
                     "volume_fx": ("Volume (0 to 100)", ),
                     "volume_music": ("Volume (0 to 100)", ),
                     "volume_text": ("Volume (0 to 100)", ),
                     "volume_voice": ("Volume (0 to 100)", ),
                     "dialog_text_sound": ("Audio file", ),
                     
                     "load_background": ("Background name", ),
                     "background_show": ("Background name", ),
                     "background_hide": ("Background name", ),
                     
                     "load_character": ("Character sprite name", "Alias"),
                     "character_show": ("Sprite name (not alias)", ),
                     "character_hide": ("Alias", ),
                     "character_flip_both": ("Alias", ),
                     "character_flip_horizontal": ("Alias", ),
                     "character_flip_vertical": ("Alias", ),
                     "character_after_fading_stop": ("Alias", "Reusable script name"),
                     "character_fade_current_value": ("Alias", "Opacity (0 to 255)"),
                     "character_fade_delay": ("Alias", "Number of frames to skip"),
                     "character_fade_speed": ("Alias", "Fade speed (1 to 100)", "Fade direction"),
                     "character_fade_until": ("Alias", "Stop at opacity (0 to 255)",),
                     "character_start_fading": ("Alias",),
                     "character_stop_fading": ("Alias",),
                     "character_after_rotating_stop": ("Alias", "Reusable script name"),
                     "character_rotate_current_value": ("Alias", "Angle (0 to 359)"),
                     "character_rotate_delay": ("Alias", "Number of frames to skip"),
                     "character_rotate_speed": ("Alias", "Rotate speed (1 to 100)", "Rotate direction"),
                     "character_rotate_until": ("Alias", "Stop at angle (0 to 359)"),
                     "character_start_rotating": ("Alias", ),
                     "character_stop_rotating": ("Alias", ),
                     "character_after_scaling_stop": ("Alias", "Reusable script name"),
                     "character_scale_by": ("Alias", "Scale speed (1 to 100)", "Scale direction"),
                     "character_scale_current_value": ("Alias", "Scale value"),
                     "character_scale_delay": ("Alias", "Number of frames to skip"),
                     "character_scale_until": ("Alias", "Stop at scale value"),
                     "character_start_scaling": ("Alias",),
                     "character_stop_scaling": ("Alias",),
                     "character_after_movement_stop": ("Alias", "Reusable script name"),
                     
                     "character_stop_movement_condition": ("Alias", "Side of sprite to check", "Stop location"),
                     "character_stop_movement_condition_no_side_to_check": ("Alias", "Stop location"),
                     
                     "character_move": ("Alias", "Horizontal amount", "Horizontal direction", "Vertical amount", "Vertical direction"),
                     "character_move_delay": ("Alias", "Number of frames to skip (horizontal)", "Number of frames to skip (vertical)"),
                     "character_start_moving": ("Alias",),
                     "character_stop_moving": ("Alias",),
                     "character_set_position_x": ("Alias", "Horizontal position"),
                     "character_set_position_y": ("Alias", "Vertical position"),
                     "character_set_center": ("Alias", "Center of X (horizontal position)", "Center of Y (vertical position)"),
                     "character_center_x_with": ("Alias to move", "Sprite type to center with", "Sprite alias to center with"),
                     "character_on_mouse_click": ("Alias", "Reusable script name", "*(optional) Arguments to pass to the reusable script"),
                     "character_on_mouse_enter": ("Alias", "Reusable script name", "*(optional) Arguments to pass to the reusable script"),
                     "character_on_mouse_leave": ("Alias", "Reusable script name", "*(optional) Arguments to pass to the reusable script"),
                     "text_dialog_define": ("Width (pixels)", "Height (pixels)", "Animation speed (1 to 100)", "Intro animation", "Outro animation", "Anchor", "Background color (hex)", "X padding", "Y padding", "Opacity (0 to 255)", "Rounded corners", "Reusable script name to run when intro animation starting", "Reusable script name to run when intro animation finishes", "Reusable script name to run when outro animation starting", "Reusable script name to run when outro animation finishes", "Reusable script name to run when <halt> is used", "Reusable script name to run when the story unhalts after using <halt>", "Border color (hex)", "Border opacity (0 to 255)", "Border thickness"),
                     "halt_auto": ("Number of frames to halt the dialog",), 
                     "continue": ("(optional) Manual Y position",),
                     
                     "load_dialog_sprite": ("Character sprite name", "Alias"),
                     "dialog_sprite_show": ("Sprite name (not alias)", ),
                     "dialog_sprite_hide": ("Alias", ),
                     "dialog_sprite_flip_both": ("Alias", ),
                     "dialog_sprite_flip_horizontal": ("Alias", ),
                     "dialog_sprite_flip_vertical": ("Alias", ),
                     "dialog_sprite_after_fading_stop": ("Alias", "Reusable script name"),
                     "dialog_sprite_fade_current_value": ("Alias", "Opacity (0 to 255)"),
                     "dialog_sprite_fade_delay": ("Alias", "Number of frames to skip"),
                     "dialog_sprite_fade_speed": ("Alias", "Fade speed (1 to 100)", "Fade direction",),
                     "dialog_sprite_fade_until": ("Alias", "Stop at opacity (0 to 255)",),
                     "dialog_sprite_start_fading": ("Alias",),
                     "dialog_sprite_stop_fading": ("Alias",),
                     "dialog_sprite_after_rotating_stop": ("Alias", "Reusable script name"),
                     "dialog_sprite_rotate_current_value": ("Alias", "Angle (0 to 359)"),
                     "dialog_sprite_rotate_delay": ("Alias", "Number of frames to skip"),
                     "dialog_sprite_rotate_speed": ("Alias", "Rotate speed (1 to 100)", "Rotate direction"),
                     "dialog_sprite_rotate_until": ("Alias", "Stop at angle (0 to 359)"),
                     "dialog_sprite_start_rotating": ("Alias", ),
                     "dialog_sprite_stop_rotating": ("Alias", ),
                     "dialog_sprite_after_scaling_stop": ("Alias", "Reusable script name"),
                     "dialog_sprite_scale_by": ("Alias", "Scale speed (1 to 100)", "Scale direction"),
                     "dialog_sprite_scale_current_value": ("Alias", "Scale value"),
                     "dialog_sprite_scale_delay": ("Alias", "Number of frames to skip"),
                     "dialog_sprite_scale_until": ("Alias", "Stop at scale value"),
                     "dialog_sprite_start_scaling": ("Alias",),
                     "dialog_sprite_stop_scaling": ("Alias",),
                     "dialog_sprite_after_movement_stop": ("Alias", "Reusable script name"),
                     
                     "dialog_sprite_stop_movement_condition": ("Alias", "Side of sprite to check", "Stop location"),
                     "dialog_sprite_stop_movement_condition_no_side_to_check": ("Alias", "Stop location"),
                     
                     "dialog_sprite_move": ("Alias", "Horizontal amount", "Horizontal direction", "Vertical amount", "Vertical direction"),
                     "dialog_sprite_move_delay": ("Alias", "Number of frames to skip (horizontal)", "Number of frames to skip (vertical)"),
                     "dialog_sprite_start_moving": ("Alias",),
                     "dialog_sprite_stop_moving": ("Alias",),
                     "dialog_sprite_set_position_x": ("Alias", "Horizontal position"),
                     "dialog_sprite_set_position_y": ("Alias", "Vertical position"),
                     "dialog_sprite_set_center": ("Alias", "Center of X (horizontal position)", "Center of Y (vertical position)"),
                     "dialog_sprite_center_x_with": ("Alias to move", "Sprite type to center with", "Sprite alias to center with"),
                     "dialog_sprite_on_mouse_click": ("Alias", "Reusable script name", "*(optional) Arguments to pass to the reusable script"),
                     "dialog_sprite_on_mouse_enter": ("Alias", "Reusable script name", "*(optional) Arguments to pass to the reusable script"),
                     "dialog_sprite_on_mouse_leave": ("Alias", "Reusable script name", "*(optional) Arguments to pass to the reusable script"),
                     
                     "load_object": ("Object sprite name", "Alias"),
                     "object_show": ("Sprite name (not alias)", ),
                     "object_hide": ("Alias", ),
                     "object_flip_both": ("Alias", ),
                     "object_flip_horizontal": ("Alias", ),
                     "object_flip_vertical": ("Alias", ),
                     "object_after_fading_stop": ("Alias", "Reusable script name"),
                     "object_fade_current_value": ("Alias", "Opacity (0 to 255)"),
                     "object_fade_delay": ("Alias", "Number of frames to skip"),
                     "object_fade_speed": ("Alias", "Fade speed (1 to 100)", "Fade direction"),
                     "object_fade_until": ("Alias", "Stop at opacity (0 to 255)",),
                     "object_start_fading": ("Alias",),
                     "object_stop_fading": ("Alias",),
                     "object_after_rotating_stop": ("Alias", "Reusable script name"),
                     "object_rotate_current_value": ("Alias", "Angle (0 to 359)"),
                     "object_rotate_delay": ("Alias", "Number of frames to skip"),
                     "object_rotate_speed": ("Alias", "Rotate speed (1 to 100)", "Rotate direction"),
                     "object_rotate_until": ("Alias", "Stop at angle (0 to 359)"),
                     "object_start_rotating": ("Alias", ),
                     "object_stop_rotating": ("Alias", ),
                     "object_after_scaling_stop": ("Alias", "Reusable script name"),
                     "object_scale_by": ("Alias", "Scale speed (1 to 100)", "Scale direction"),
                     "object_scale_current_value": ("Alias", "Scale value"),
                     "object_scale_delay": ("Alias", "Number of frames to skip"),
                     "object_scale_until": ("Alias", "Stop at scale value"),
                     "object_start_scaling": ("Alias",),
                     "object_stop_scaling": ("Alias",),
                     "object_after_movement_stop": ("Alias", "Reusable script name"),
                     
                     "object_stop_movement_condition": ("Alias", "Side of sprite to check", "Stop location"),
                     "object_stop_movement_condition_no_side_to_check": ("Alias", "Stop location"),
                     
                     "object_move": ("Alias", "Horizontal amount", "Horizontal direction", "Vertical amount", "Vertical direction"),
                     "object_move_delay": ("Alias", "Number of frames to skip (horizontal)", "Number of frames to skip (vertical)"),
                     "object_start_moving": ("Alias",),
                     "object_stop_moving": ("Alias",),
                     "object_set_position_x": ("Alias", "Horizontal position"),
                     "object_set_position_y": ("Alias", "Vertical position"),
                     "object_set_center": ("Alias", "Center of X (horizontal position)", "Center of Y (vertical position)"),
                     "object_center_x_with": ("Alias to move", "Sprite type to center with", "Sprite alias to center with"),
                     "object_on_mouse_click": ("Alias", "Reusable script name", "*(optional) Arguments to pass to the reusable script"),
                     "object_on_mouse_enter": ("Alias", "Reusable script name", "*(optional) Arguments to pass to the reusable script"),
                     "object_on_mouse_leave": ("Alias", "Reusable script name", "*(optional) Arguments to pass to the reusable script"),
                     
                     "load_font_sprite": ("Font sprite name", ),
                     "font": ("Font name", ),
                     "font_x": ("Horizontal position (x)", ),
                     "font_y": ("Vertical position (y)", ),
                     "font_text_delay": ("Number of frames to delay (0 to 600)", ),
                     "font_text_delay_punc": ("Previous letter", "Number of frames to skip (0 to 120)"),
                     "font_text_fade_speed": ("Fade speed (1 to 10)",),
                     "font_intro_animation": ("Animation type",),
                     "sprite_font": ("Sprite type", "Sprite alias", "Font name"),
                     "sprite_font_x": ("Sprite type", "Sprite alias", "Horizontal position value (x)"),
                     "sprite_font_y": ("Sprite type", "Sprite alias", "Vertical position value (x)"),
                     "sprite_font_delay": ("Sprite type", "Sprite alias", "Delay frames (0 to 600)"),
                     "sprite_font_delay_punc": ("Sprite type", "Sprite alias", "Previous letter", "Number of frames to skip (0 to 120)"),
                     "sprite_font_fade_speed": ("Sprite type", "Sprite alias", "Fade speed (1 to 10)"),
                     "sprite_font_intro_animation": ("Sprite type", "Sprite alias", "Starting animation type"),
                     "sprite_text": ("Sprite type", "Sprite alias", "Sprite text"),
                     "sprite_text_clear": ("Sprite type", "Sprite alias"),
                     
                     "scene_with_fade": ("Background color (hex)", "Fade-in speed (1 to 100)", "Fade-out speed (1 to 100)", "Number of frames to hold", "Chapter name", "Scene name"),
                     "rest": ("Number of frames to pause",),
                     "after": ("Number of frames to elapse", "Reusable script name", "*(optional) Arguments to pass to the reusable script"),
                     "after_cancel": ("Reusable script name",),
                     "call": ("Reusable script name", "*(optional) Arguments to pass to the reusable script"),
                     "scene": ("Chapter name", "Scene name"),
                     "wait_for_animation": ("Sprite type", "Alias", "Animation type"),
                     
                     "variable_set": ("Variable name", "Variable value"),
                     
                     "case": ("Value 1", "Comparison operator", "Value 2", "(optional) Condition name"),
                     "or_case": ("Value 1", "Comparison operator", "Value 2", "Condition name to compare with")
                     
                     }
    
    def get_parameter_description(self,
                                 command_name: str,
                                 number_of_commas_before: int) -> str | None:
        """
        Return a parameter's description based on where the caret is currently
        located in the text widget.
        
        Arguments:
        
        - command_name: the case-sensitive command name to lookup the
        description for.
        
        - number_of_commas_before: the number of commas that exist
        to-the-left-of the current position of the blinking caret, on the same
        line. This is how we determine which parameter the blinking caret is on.
        """
        
        # Find the parameter descriptions for the given command name.
        descriptions = self.data.get(command_name)
        if not descriptions:
            return
        
        # If the requested command name ends with a special string, that means
        # it was for a command that can have multiple arguments (for example
        # <character_stop_movement_condition>. Change it back to the normal
        # command name so we can display it to the user.)
        if command_name.endswith("_stop_movement_condition" + \
                                self.STOP_MOVEMENT_CONDITION_ENDING_SPECIAL):
            command_name = command_name.\
                removesuffix(self.STOP_MOVEMENT_CONDITION_ENDING_SPECIAL)
        
        # Generate a single string from a tuple of parameter descriptions.
        # Remove the asterisk if it exists in the description. An asterisk
        # is used for showing that an unlimited number of parameters can be
        # passed at that position.
        displayable_descriptions = \
            ", ".join([item[1:] if item.startswith("*") else item for item
                       in descriptions])
        
        # The command with a description of all its parameters.
        # This is used for showing the command and its parameter descriptions
        # to the user in a read-only text widget.
        command_with_all_parameter_descriptions = \
            fr"<{command_name}: {displayable_descriptions}>"
        
        self.show_text_widget.configure(state="normal")
        self.show_text_widget.delete("0.0", "end")
        self.show_text_widget.insert("0.0",
                                     command_with_all_parameter_descriptions)
        
        # Adjust the height of the text widget as-needed based on the
        # newly displayed text in the text widget. Shrink or grow as needed.
        self.refresh_height()
        
        self.show_text_widget.configure(state="disabled")
        
        try:
            
            # If the last parameter is an asterisk, that means there is no limit
            # to the number of parameters that can be passed in at this caret
            # location. This type of parameter is used for passing keys and 
            # values to a reusable script. So we will have one type of 
            # description for this type of parameter.
            if number_of_commas_before >= len(descriptions) - 1 \
               and descriptions[-1].startswith("*"):
                
                # Get the last parameter description so we can
                # remove the asterisk shortly after.
                last_description = descriptions[-1]
                
                # Get the last description without the starting asterisk *
                # Example: *test becomes test
                info = last_description[1:]
            else:
                # A regular positioned parameter.
                info = descriptions[number_of_commas_before]
                
        except IndexError:
            # We can't find the parameter description for the given command
            # based on the current caret's position.
            info = None
        
        return info
    
    def refresh_height(self, event=None):
        """
        Determine what the height of the text widget should be based on
        the number of lines.
        """
        new_height = self.root_window.call((self.show_text_widget,
                                "count", "-update", "-displaylines", "1.0",
                                "end"))
        self.show_text_widget.configure(height=new_height)
        
    def hide_description_frame(self):
        """
        Hide (ungrid) the frame that shows the parameter textbox.
        Purpose: when there is nothing to show.
        """
        
        # Prevents flickering. Without this, when the frame is gridded,
        # it will flicker the first time it's gridded.
        self.show_text_frame.update_idletasks()
        
        self.show_text_frame.grid_remove()
        
    def bold_words(self, words: str):
        """
        Bold the given words in the text widget.

        Arguments:
        
        - words: the description text to bold.
        """
        
        # No words to bold? The caret is not on a parameter location,
        # so delete the suggestive text.
        if not words:
            # self.show_text_widget.tag_delete("bld")
            self.show_text_widget.configure(state="normal")
            self.show_text_widget.delete("0.0", "end")
            self.show_text_widget.configure(state="disabled")
            
            # The caret could be on an empty line, or
            # the cursor/caret is on a line with a command that needs no 
            # parameters.
            # Hide the description frame because there is nothing to show.
            self.hide_description_frame()
            
            return
        
        # Show the description frame
        self.show_text_frame.grid()
        
        # Search for the word, starting at the beginning of the first line.
        index = self.show_text_widget.search(words, "1.0")
        if not index:
            return         
        # An index looks something like this: 1.56
        
        # Get the column position as an integer so that
        # we can find out where the word ends later.
        line, column_position = index.split(".")
        column_position = int(column_position)
        
        # Find out where the description text ends.
        end_column = column_position + len(words)
        
        # Record the ending index position of the words.
        end_index = f"{line}.{end_column}"
        
        # Get the default TkFixedFont info, so that we can read
        # the default font size and use that to set the text to bold,
        # without changing the font name.
        default_text_widget_font = font.nametofont("TkFixedFont")
        font_details = default_text_widget_font.actual()
        default_font_size = font_details.get("size")
        
        # Optional other configs:
        # underline=True,
        # underlinefg="blue",        
        self.show_text_widget.tag_configure("bld",
                                            font=("TkFixedFont",
                                                  default_font_size, "bold"))        
        
        # Set the description text to bold.
        self.show_text_widget.tag_add("bld", index, end_index)

        # To get the current tag configuration, run it without
        # passing in any extra parameters.
        #info = self.show_text_widget.tag_config("bld")
        #print(info)
        
    
    def start_timer(self, event):
        """
        Attempt to show the parameter's description after a few milliseconds.
        We put a short delay to prevent a lookup for every keystroke or mouse
        click, to help prevent slow downs on big scripts.
        """
        
        # If there's an existing timer, cancel it.
        if ParameterDescription.last_after_timer:
            self.read_text_widget.after_cancel(ParameterDescription.last_after_timer)
            
        # Start the timer and have it run a specific method.
        ParameterDescription.last_after_timer =\
            self.read_text_widget.after(400,
                                        self.start_get_parameter_description)
    
    def start_get_parameter_description(self):
        """
        Determine where the blinking cursor/caret is and then use that
        to determine the command name and parameter position that it's on.
        """
        
        # Reset the timer variable, we're done with it.
        ParameterDescription.last_after_timer = None
        
        # To look for a command name-only.
        pattern = r"^<(?P<Command>[a-z]+[_]*[\w]+):*"

        # Get the position of the caret
        position = self.read_text_widget.index(tk.INSERT)
        
        # Get the text from the beginning of the line that the caret is on
        # up to the caret position.
        line_text = self.read_text_widget.get("insert linestart",
                                              index2=position)
        
        result = re.search(pattern=pattern,
                           string=line_text)
        
        if result:
            command_name = result.groupdict().get("Command")
        else:
            self.hide_description_frame()
            return
        
        # The 'stop movement condition' command, such as: 
        # <character_stop_movement_condition> can have 3 arguments or 2.
        # Check for the 2-argument version.
        # The 3 argument version is the default.
        if command_name.endswith("_stop_movement_condition"):
            
            # Get the whole line so we can count the number of commas.
            entire_line_text = \
                self.read_text_widget.get("insert linestart",
                                          index2="insert lineend")
            
            # 1 comma means it's the non-default 2 argument version
            # of the command.
            if entire_line_text.count(",") == 1:
             
                # This is the non-default 2-argument version of the command.
                # Add a special string so we can find the 2-argument description
                # in the lookup dictionary.
                command_name += self.STOP_MOVEMENT_CONDITION_ENDING_SPECIAL
                
        # Don't allow a special command name that's meant to be used internally 
        # in-code, such as: <character_stop_movement_condition_no_side_to_check>
        elif command_name.endswith(self.STOP_MOVEMENT_CONDITION_ENDING_SPECIAL):
            return
        
        comma_count = line_text.count(",")
        
        description = \
            self.get_parameter_description(command_name=command_name,
                                           number_of_commas_before=comma_count)
        
        self.bold_words(description)
            
# print(get_parameter_description("character_show", 0))


if __name__ == "__main__":
    
    root = tk.Tk()
    
    text_widget = tk.Text(root)
    text_widget.pack(fill=tk.BOTH, expand=True)
    
    desc_text_widget = tk.Text(root, height=1, wrap=tk.WORD)
    desc_text_widget.pack(fill=tk.X, anchor=tk.S, expand=True)
    
    parameter_desc = ParameterDescription(read_text_widget=text_widget,
                                          show_text_widget=desc_text_widget)
    
    text_widget.insert("0.0", "<character_show: theo, second part, third part, name=theo, age=45>\n<exit>")
    
    # When a mouse button is released or when a key is released on the keyboard,
    # then find where the cursor is and show the parameter's description based
    # on where the cursor is.
    text_widget.bind("<ButtonRelease>", parameter_desc.start_timer)
    text_widget.bind("<KeyRelease>", parameter_desc.start_timer)
    
    root.mainloop()
