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

import configparser
import pathlib
import pygubu
import tkinter as tk
from tkinter import ttk
from tkinter import colorchooser
from tkinter import messagebox
from project_snapshot import ProjectSnapshot
from input_string_window import InputStringWindow
PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "edit_colors_window.ui"


class EditColorsWindow:
    def __init__(self, master, refresh_colors_method):
        """
        Open the color settings window.
        
        Arguments:
        
        - master: the parent window of this toplevel widget.
        
        - refresh_colors_method: the method to run when the OK button is
        clicked, so the colour changes get applied to the text widget.
        """
        
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow = builder.get_object("colors_window", master)
        builder.connect_callbacks(self)
        
        # The method that will apply the colour changes
        # to the text widget.
        self.refresh_colors_method = refresh_colors_method
        
        lbl_editor_background = builder.get_object("lbl_editor_background")
        lbl_editor_background.label_name = "lbl_editor_background"
        
        lbl_non_dialog_forecolor = builder.get_object("lbl_non_dialog_forecolor")
        lbl_non_dialog_forecolor.label_name = "lbl_non_dialog_forecolor"
        
        lbl_highlighted_text_bg_color = builder.get_object("lbl_highlighted_text_bg_color")
        lbl_highlighted_text_bg_color.label_name = "lbl_highlighted_text_bg_color"
        
        lbl_blinking_cursor = builder.get_object("lbl_blinking_cursor")
        lbl_blinking_cursor.label_name = "lbl_blinking_cursor"
        
        lbl_command_forecolor = builder.get_object("lbl_command_forecolor")
        lbl_command_forecolor.label_name = "lbl_command_forecolor"
        
        lbl_arguments_forecolor = builder.get_object("lbl_arguments_forecolor")
        lbl_arguments_forecolor.label_name = "lbl_arguments_forecolor"
        
        lbl_comments_forecolor = builder.get_object("lbl_comments_forecolor")
        lbl_comments_forecolor.label_name = "lbl_comments_forecolor"
        
        lbl_character_text_forecolor = builder.get_object("lbl_character_text_forecolor")
        lbl_character_text_forecolor.label_name = "lbl_character_text_forecolor"
        
        lbl_character_text_bg = builder.get_object("lbl_character_text_bg")
        lbl_character_text_bg.label_name = "lbl_character_text_bg"
        
        lbl_current_row_bg = builder.get_object("lbl_current_row_bg")
        lbl_current_row_bg.label_name = "lbl_current_row_bg"
        
        self.v_no_background_dialogue_text: tk.BooleanVar
        self.v_no_background_dialogue_text = builder.get_variable("v_no_background_dialog_text")
        
        # So we can disable the checkbox when the 'Default' 
        # preset is selected (because changing the Default preset is not allowed).
        self.chk_no_dialog_text_bg = builder.get_object("chk_no_dialog_text_bg")
        
        self.btn_save_as = builder.get_object("btn_save_as")
        self.btn_delete = builder.get_object("btn_delete")
        
        self.btn_ok = builder.get_object("btn_ok")
        self.btn_cancel = builder.get_object("btn_cancel")
        self.mainwindow.bind("<Escape>", self.on_cancel_button_clicked)
        
        self.color_labels =\
            {"editor.background": lbl_editor_background,
             "editor.foreground": lbl_non_dialog_forecolor,
             "editor.select.background": lbl_highlighted_text_bg_color,
             "editor.insert.background": lbl_blinking_cursor,
             "editor.commands": lbl_command_forecolor,
             "editor.after.colon": lbl_arguments_forecolor,
             "editor.comments": lbl_comments_forecolor,
             "editor.dialog.text.forecolor": lbl_character_text_forecolor,
             "editor.dialog.text.backcolor": lbl_character_text_bg,
             "editor.highlight.row.background": lbl_current_row_bg}
        
        self.checkbox_options = {"editor.dialog.text.backcolor.disable": 
                                 self.v_no_background_dialogue_text}        
        
        # Bind labels to mouse left-click
        label_widget: ttk.Label
        for name, label_widget in self.color_labels.items():
            label_widget.name = name
            label_widget.bind("<Button-1>", self.on_label_color_clicked)
            
        # Presets combobox.
        self.cb_presets: ttk.Combobox
        self.cb_presets = builder.get_object("cb_presets")
        self.cb_presets.bind("<<ComboboxSelected>>", self.show_options_in_widgets)

        
        self.populate_presets()
        
        self.mainwindow.transient(master)
        self.mainwindow.wait_visibility()
        self.mainwindow.grab_set()


        self.mainwindow.wait_window(self.mainwindow)        
            
    def populate_presets(self):
        """
        Populate the combobox with a list of preset names, including 'Default'
        and choose the active preset and show the colors of that preset.
        """
        config = ProjectSnapshot.config.config
        
        self.cb_presets.configure(state="normal")
        self.cb_presets.delete(0, "end")
        self.cb_presets.configure(values="")
        
        presets = ["Default"]
        
        # Get the preset names without the prefix of 'colorpreset.'
        # For example: colorpreset.Light should just populate as Light
        loaded_presets = [section[12:] for section in config.sections()
                          if section.startswith("colorpreset.")]
        presets += loaded_presets
        
        # Populate the combobox
        self.cb_presets.configure(values=presets)
        
        # Choose the selected preset.
        if config.has_section("selected.color.preset"):
            selected_preset = config.get("selected.color.preset",
                                         "selected.color.preset")
        else:
            selected_preset = "Default"
        
        # The chosen preset.
        self.cb_presets.insert(0, selected_preset)

        self.cb_presets.configure(state="readonly")
        
        # Show the colors of the selected preset.
        self.show_options_in_widgets()
        
    def is_default_preset(self) -> bool:
        """
        Return whether the default preset ('Default') is selected
        in the combobox or not.
        """
        preset_name = self.cb_presets.get()
        if not preset_name:
            return False
        
        return preset_name.lower() == "default"
        
    def show_options_in_widgets(self, *args):
        """
        Show the option values in widgets (label backgrounds, checkboxes).
        
        Change the background of the labels to the color definitions
        of the selected preset.
        
        Also, if the preset is 'Default', disable the Save and Delete buttons,
        leaving only the 'Save As...' button enabled.
        """
        
        config = ProjectSnapshot.config.config
        
        preset_name = self.cb_presets.get()
        if not preset_name:
            return
        
        if self.is_default_preset():
            self.btn_save_as.state(["!disabled"])
            self.btn_delete.state(["disabled"])
            
            preset_address = "DEFAULT"
            
            # Don't allow the checkbutton to be checked/changed.
            # because the 'Default' preset is now selected.
            self.chk_no_dialog_text_bg.state(["disabled"])
            
        else:
            self.btn_save_as.state(["!disabled"])
            self.btn_delete.state(["!disabled"])
            
            preset_address = f"colorpreset.{preset_name}"
            
            # Allow the checkbutton to be checked/change
            # because the a custom preset has been selected.
            self.chk_no_dialog_text_bg.state(["!disabled"])
            
            
        # Combine the color options and checkbox options into
        # one dictionary so we can enumerate through the options.            
        options_to_check = self.color_labels | self.checkbox_options

        setting_key: str # Such as 'editor.dialog.text.backcolor'
        # option_widget is either a ttk.Label or ttk.BooleanVar
        for setting_key, option_widget in options_to_check.items():
        
            try:
                
                # For string config values, use config.get
                # Otherwise, use config.getboolean (for checkboxes)
                if isinstance(option_widget, ttk.Label):
                    get_method = config.get
                else:
                    get_method = config.getboolean
                
                # Get the value of the key.
                setting_value = get_method(preset_address, setting_key)
                
            except configparser.NoOptionError:
                messagebox.showerror(parent=self.mainwindow,
                                     title="Config File Error", 
                                     message=f"Could not find setting: '{setting_key}' in '{preset_address}'")
                return
            
            # Show the color value in the label widget
            # that represents the current option.
            if isinstance(option_widget, ttk.Label):
                option_widget.configure(background=setting_value)
            else:
                # TkBoolean variable
                option_widget.set(setting_value)
            
    def on_cancel_button_clicked(self, *args):
        """
        Close the Edit Colors window.
        """
        self.mainwindow.destroy()
        
    def on_ok_button_clicked(self):
        """
        Apply the colors to the text widget.
        """
        
        # Save any changes to the config file.
        self.save_selected_preset()
        
        # Apply the colour changes to the text widget.
        self.refresh_colors_method()
        
        self.mainwindow.destroy()
        
    def on_label_color_clicked(self, event: tk.Event):
        """
        Open the color dialog and if a color gets selected,
        change the background color of the clicked label.
        """
        
        # Don't allow the colors to change for the default preset.
        # Instead, the user should create a copy of the default preset
        # under a new name.
        if self.is_default_preset():
            messagebox.showwarning(parent=self.mainwindow, 
                                   title="Default Preset",
                                   message="The default preset cannot be modified.\n\n"
                                   "Click 'Save As...' to create a copy of the default preset "
                                   "and make changes to the copy.")
            return
        
        current_color_hex = event.widget.cget("background")
        current_color_rgb = event.widget.winfo_rgb(current_color_hex)

        # winfo_rgb() returns a maximum value of 65535 instead of 255,
        # for some reason, we need to divide each color (rgb) by 256
        # to get a max 255 value.
        red, green, blue = current_color_rgb

        if red > 0:
            red = red // 256
        if green > 0:
            green = green // 256
        if blue > 0:
            blue = blue // 256

        # Record the new max-255 color values
        current_color_rgb = (red, green, blue)

        color = colorchooser.askcolor(parent=self.mainwindow.winfo_toplevel(),
                                      title="Colour",
                                      initialcolor=current_color_rgb)

        # The return value will be like this if a colour is chosen:
        # ((0, 153, 0), '#009900')
        
        # Or like this if no color is chosen
        # (None, None)
        hex_new_color = color[1]

        if not hex_new_color:
            return
        
        event.widget.configure(background=hex_new_color)
        
    def on_delete_button_clicked(self):
        """
        Delete the selected preset and change the active preset to 'Default'.
        """
        # Get the selected preset name.
        preset_name = self.get_selected_preset_name()
        
        # Ask the user if they want to proceed.
        result =\
            messagebox.askokcancel(parent=self.mainwindow, 
                                   title="Confirm",
                                   message=f"Preset '{preset_name}' will be deleted.\n\nNote: this cannot be undone.")
        if not result:
            return
        
        config = ProjectSnapshot.config.config
        
        # Get the active preset section (for example: 'colorpreset.Blue')
        preset_section = self.get_selected_preset_section()
        
        # Remove the preset section from the configuration.
        # Example: 'colorpreset.Blue'
        config.remove_section(preset_section)
        
        # By removing the selected preset section, it will
        # cause the active preset to be set to the Default.
        config.remove_section("selected.color.preset")
        
        # Save the updated configuration to 'lvnauth.config'.
        ProjectSnapshot.config.save_config_to_file()
            
        # Apply the 'Default' preset colours to the text widget.
        self.refresh_colors_method()
        
        self.mainwindow.destroy()

    def on_save_as_button_clicked(self, prefill_preset_name=None):
        """
        Prompt for a new preset name and copy the current preset color values
        to the new preset.
        """
        input_window = InputStringWindow(self.mainwindow,
                                         title="Save As...",
                                         msg="Enter a new preset name:",
                                         prefill_entry_text=prefill_preset_name)
        
        new_preset_name = input_window.user_input
        
        # No name provided by the user? return
        if not new_preset_name:
            return
        else:
            new_preset_name = new_preset_name.strip()
            
        # No name after use .strip()? return.
        if not new_preset_name:
            return
        
        # Don't allow the new preset name to be 'default', 
        # because it's reserved.
        if new_preset_name.lower() == "default":
            messagebox.showwarning(parent=self.mainwindow, 
                                   title="Preset Name",
                                   message=f"'{new_preset_name}' is a reserved name.\n\n"
                                   "Please choose a different name.")
            self.on_save_as_button_clicked(prefill_preset_name=new_preset_name)
            return
        
        # Generate the section address, such as: colorpreset.Light
        new_preset_section = f"colorpreset.{new_preset_name}"
        
        # Does the preset name already exist? don't allow it.
        existing_sections =\
            [item.lower() for item in ProjectSnapshot.config.config.sections()
             if item.startswith("colorpreset.")]
        
        # Preset already exists? tell the user.
        if new_preset_section.lower() in existing_sections:
            messagebox.showwarning(parent=self.mainwindow, 
                                   title="Already Exists",
                                   message=f"The preset name '{new_preset_name}' already exists.\n\n"
                                   "Please choose a different name.")
            self.on_save_as_button_clicked(prefill_preset_name=new_preset_name)
            return            
        
        # Add the new preset section (example: colorpreset.Light)
        ProjectSnapshot.config.config.add_section(new_preset_section)
        
        # Add the new preset to the combobox
        combobox_values = list(self.cb_presets.cget("values"))
        combobox_values.append(new_preset_name)
        self.cb_presets.configure(values=combobox_values)
        
        # Select the new preset in the combobox.
        self.cb_presets.configure(state="normal")
        self.cb_presets.delete(0, tk.END)
        self.cb_presets.insert(0, new_preset_name)
        self.cb_presets.configure(state="readonly")
        
        # Save the selected preset to the config file.
        self.save_selected_preset(is_new_preset=True)
        
        # Causes the Delete button and 'No background' checkbox
        # to be enabled; the same as selecting the new preset's name
        # in the combobox.
        self.show_options_in_widgets()
        
    def get_selected_preset_section(self) -> str:
        """
        Return the section name of the section.
        For example: colorpreset.Light (case-sensitive).
        """
        selected_preset = self.cb_presets.get()
        
        if selected_preset.lower() == "default":
            return "DEFAULT"
        else:
            return f"colorpreset.{selected_preset}"
    
    def get_selected_preset_name(self) -> str:
        """
        Return the preset name, without the section.
        For example: BluePreset
        or if it's the default, it will return all caps as DEFAULT
        """
        selected_preset = self.cb_presets.get()
        
        if selected_preset.lower() == "default":
            selected_preset = "DEFAULT"
            
        return selected_preset
        
    def save_selected_preset(self, is_new_preset: bool = False):
        """
        Save the selected preset to the config file.
        Only save keys/values that have different values
        from the default values.
        
        The preset section is expected to already exist
        before calling this method (example: colorpreset.Light)
        
        Arguments:
        
        - is_new_preset: if True, the config file will be saved
        even if all the color values are the same as the default color values.
        The reason is: if we don't save the config, the [section] won't save.
        
        If all the color values are the same as the default, then the config
        will contain an empty section, such as 'colorpreset.mynew_preset',
        which is fine.
        
        When False, the config file will be saved only if the new option values
        (such as color values) are different from the current config values
        for the same section - or if, for example, the new color values are the
        same as the default values.
        """
        save_config_file = False
        
        # Shortcut for easier typing
        config = ProjectSnapshot.config.config
        
        # Save the active preset name
        preset_name = self.get_selected_preset_name()
        
        # Add a custom preset as the active preset?
        if preset_name.lower() != "default" \
           and not config.has_section("selected.color.preset"):
            
            # A custom preset has been set as the default preset.
            config.add_section("selected.color.preset")
            save_config_file = True
            
            # Set the custom preset as the defualt in the config file.
            config["selected.color.preset"]["selected.color.preset"] = preset_name
            
        # The 'Default' preset has been selected but a section for
        # 'selected.color.preset' exists? Delete that section.
        elif preset_name.lower() == "default" \
             and config.has_section("selected.color.preset"):
 
            # Delete the section, 'selected.color.preset', because the
            # default section already contains that section; no need to have it
            # in the config file twice.
            config.remove_section("selected.color.preset")
            save_config_file = True

        # A non-factory default preset has been selected?
        elif preset_name.lower() != "default":
            # If the previous active preset is different from the newly
            # selected preset, then set it to active.
            
            # Is the selected preset different than before?
            previous_selected_preset = config.get("selected.color.preset",
                                                  "selected.color.preset")
            
            if previous_selected_preset != preset_name:
                # A new preset has been selected that is not the default.
                
                save_config_file = True

                # Save the name of the active preset
                config["selected.color.preset"]["selected.color.preset"] = preset_name
                
                
        # Has a non-default (non-factory preset) been selected?
        if self.get_selected_preset_name().lower() != "default":
            # A non-default (non-factory preset) has been selected.
            
            # Remove options that have values that match the default values.
            # However, only delete options for non-default presets, 
            # not the default preset (which is why we have the if-statement
            # above).              
            
            # Get a dictionary of default keys and values.
            # Example:
            # {'editor.background': '#1c2733', 'editor.foreground': '#ebcdcd'}
            defaults = config.defaults()

            # Combine the color options and checkbox options into
            # one dictionary so we can enumerate through the options.
            options_to_check = self.color_labels | self.checkbox_options
            
            # Remove keys (options) that have values that are the same as
            # the default. For example, if 'editor.background' has a value of 
            # #1c2733, which at the time of writing, is the default hex color value,
            # then delete 'editor.background' from the custom preset.
            setting_key: str # such as 'editor.background'
            # option_widget: either a ttk.Label or tk.BooleanVar
            for setting_key, option_widget in options_to_check.items():

                # We should only save the preset key/value if the default is
                # different.
                # 
                # If the preset value for a specific setting is
                # the same as the default, make sure the preset color is not
                # present.
                
                # Get the label's backcolor
                if isinstance(option_widget, ttk.Label):
                    widget_value = str(option_widget.cget("background"))                 
                    
                    # The value as it currently is in the config
                    # file (if the option is there), for the selected preset.
                    old_preset_value_in_config =\
                        config.get(self.get_selected_preset_section(),
                                   setting_key)                       
                    
                else:
                    # It's going to be a TkBoolean type
                    widget_value = option_widget.get()
                    
                    # The value as it currently is in the config
                    # file (if the option is there), for the selected preset.
                    old_preset_value_in_config =\
                        config.getboolean(self.get_selected_preset_section(),
                                          setting_key)                   

    
                # So we can compare the new value with the default value.
                default_value = defaults.get(setting_key)
                if default_value == "True":
                    default_value = True
                elif default_value == "False":
                    default_value = False

                # Is the new preset color the same as the default value?
                if widget_value == default_value:
                    # The new preset color is the same as the default value.
                    
                    # Delete the option for this preset, because it's the
                    # same as the default.
                    if config.has_option(self.get_selected_preset_section(),
                                         setting_key):
                        
                        # has_option will return True even if the setting
                        # doesn't exist in a non-default section, such as
                        # 'color-reset.Light', because it'll find the default
                        # section (that's just the way ConfigParser works.)
                        
                        # However, strangely enough, remove_option() will 
                        # return False if it can't find the option in a 
                        # non-default section.
                        
                        # Remove the option for the current preset.
                        option_removed =\
                            config.remove_option(self.get_selected_preset_section(),
                                                 setting_key)
                        
                        # Did the option actually get deleted? (was it found?)
                        if option_removed:
                            # Yes, the option was actually removed (from
                            # a non-default section).
                        
                            # Flag to indiciate that we should save the config file
                            # because a change has occurred in the config.
                            save_config_file = True
                    
                # Is the label's backcolor the same as the config?
                elif old_preset_value_in_config == widget_value:
                    # No change from the config file for this color option.
                    continue
            
                else:
        
                    # The new preset color option is different from the 
                    # default color and different from the current config 
                    # value (if any).
                    
                    # Update/add the color option
                    config[self.get_selected_preset_section()][setting_key] = str(widget_value)
                
                    # Flag to indiciate that we should save the config file
                    # because a change has occurred in the config.
                    save_config_file = True
                
                
        if save_config_file or is_new_preset:
            # Save the updated configuration to 'lvnauth.config'.
            ProjectSnapshot.config.save_config_to_file()

    def run(self):
        self.mainwindow.mainloop()


if __name__ == "__main__":
    app = EditColorsWindow()
    app.run()
