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

- Nov 24, 2023 (Jobin Rezai) - Changed default preset colors for:
editor.foreground, editor.commands, editor.select.background
"""

import os
import configparser
from typing import Dict
from pathlib import Path
from container_handler import ContainerHandler


class ConfigHandler:
    def __init__(self):
        
        # This dictionary is used to ensure all the sections and values
        # exist in the config file.
        self.latest_default_config_values =\
            {"editor.background": "#1c2733",
             "editor.foreground": "#ce9474",
             "editor.select.background": "#36411b",
             "editor.insert.background": "#b58a7a",
             "editor.commands": "#6cb1d9",
             "editor.after.colon": "#9e8c5a",
             "editor.comments": "#827145",
             "editor.dialog.text.forecolor": "lightgreen",
             "editor.dialog.text.backcolor": "#444953",
             "editor.dialog.text.backcolor.disable": True,
             "editor.highlight.row.background": "#13476b",
             "selected.color.preset": "DEFAULT"}
        
        # Keys that should be read as bool instead of str
        self.bool_config_keys = ("editor.dialog.text.backcolor.disable", )
        
        # Get the path to the config file if we're running in a snap package.
        
        self.config_file_path = ContainerHandler.get_snap_user_data_folder()
        if self.config_file_path:
            self.config_file_path = self.config_file_path / "lvnauth.config"
            
        elif ContainerHandler.is_in_flatpak_package():
            # /home/username/.var/app/org.lvnauth.LVNAuth/config
            self.config_file_path = ContainerHandler.get_flatpak_config_directory()
            self.config_file_path = self.config_file_path / "lvnauth.config"
            
        else:
            # Not a snap or flatpak package.
            
            # Set a default config file path (current directory)
            # The config path will be in App Data if it's running from Windows.
            self.config_file_path = self.get_config_path_absolute()
            # self.config_file_path = Path("lvnauth.config")
        
        # Read the config file and keep it ready for reading/updating/saving.
        self.config = configparser.ConfigParser()
        
        self.create_config_file_if_not_exists()
        
        self.config.read(self.config_file_path)
        

        
        self.ensure_config_file_is_up_to_date()
        
    def get_config_path_absolute(self) -> Path:
        """
        Return the full path to lvnauth.config depending on where LVNAuth
        is running from.
        
        The newest addition is Windows. If it's from that operating system,
        return the full path of the App Data directory, including the
        config file.
        """

        # Get the 'Roaming' AppData path from the environment variable.
        appdata_dir = os.environ.get("APPDATA")
        if not appdata_dir:
            # Running in Linux

            # Return the regular absolute path in the local directory.
            full_path = ContainerHandler.get_absolute_path("lvnauth.config")
        else:
            # Running Windows.
            
            # Define the app data LVNAuth directory.
            lvnauth_appdata_directory: Path
            lvnauth_appdata_directory = Path(appdata_dir) / "LVNAuth"
            
            # Create the LVNAuth app data directory if it doesn't exist yet.
            lvnauth_appdata_directory.mkdir(exist_ok=True)
                
            # Set the full path to the config file in app data
            full_path = lvnauth_appdata_directory / "lvnauth.config"
            
        return full_path
            
    def ensure_config_file_is_up_to_date(self):
        """
        Ensure all the default values exist under the DEFAULT section.
        
        Purpose: when a new version of LVNAuth is released with new config
        sections, this will ensure that the existing (older) config file
        is updated with the new sections and values that have been introduced
        in the new version. If a section already exists, it is skipped.
        """
        
        # Whether to update the 'DEFAULT' section of the config file.
        update_default_config_section = False
        
        # Enumerate the default keys/values and update them if they exist
        # and add new keys/values if the keys don't exist.
        config_default_keys_values: Dict
        config_default_keys_values = self.config.defaults()
        
        # No defaults found? Start the defaults from scratch.
        if not config_default_keys_values:
            config_default_keys_values = self.latest_default_config_values
            update_default_config_section = True
        else:
            
            # Defaults were found in the config file.
            # Make sure the default keys/values are up-to-update.
    
            key_option: str
            default_value: str
            
            # Loop through all the keys/values that need to exist
            # in the config file.
            for key_option, default_value in self.latest_default_config_values.items():
                
                try:
                    
                    if key_option in self.bool_config_keys:
                        get_method = self.config.getboolean
                    else:
                        get_method = self.config.get
                    
                    config_file_value = get_method("DEFAULT", key_option)
                    
                    # Does the default value need to be updated?
                    if config_file_value != default_value:
                        # Update the value for the default key.
                        # because the config file's default is different.
                        config_default_keys_values[key_option] = default_value
                        
                        # So we know to apply the new change to the config file later.
                        update_default_config_section = True                    
                    
                except configparser.NoOptionError:
                    # The default key was not found in the config file.
                    
                    # Add the key to a temporary dictionary which
                    # will eventually get updated in the config file.
                    config_default_keys_values[key_option] = default_value
                    
                    # So we know to apply the new change to the config file later.
                    update_default_config_section = True
                

        # Update the 'DEFAULT' section of the configuration file?
        if update_default_config_section:
            
            # Here, we return a copy of the dictionary. If we give it
            # the dictionary itself, for some reason it will clear 
            # the dictionary.
            self.config["DEFAULT"] = config_default_keys_values.copy()
            
            # Save the updated configuration to 'lvnauth.config'.
            self.save_config_to_file()
                
    def save_config_to_file(self):
        """
        Save the configuration to disk.
        """
        
        # Save the updated configuration to 'lvnauth.config'.
        with open(self.config_file_path, "w") as configfile:
            self.config.write(configfile)        
                
    def create_config_file_if_not_exists(self):
        """
        Create lvnauth.config if the file doesn't already exist.
        """
        if self.config_file_path.exists():
            return
        
        self.config["DEFAULT"] = self.latest_default_config_values
        
        # Save the updated configuration to 'lvnauth.config'.
        self.save_config_to_file()       
            
    def get_selected_color_preset_section(self) -> str:
        """
        Get the color preset section that is currently selected/active
        from the config file.
        
        Example: colorpreset.Light
        
        Purpose: used for loading the color values of the selected
        color preset.
        """
        
        # Is a custom preset selected?
        if self.config.has_section("selected.color.preset"):
            # A custom preset is selected.
            preset_section = self.config.get("selected.color.preset",
                                          "selected.color.preset")
            
            preset_section = f"colorpreset.{preset_section}"
        else:
            # The default preset is selected.
            preset_section = "DEFAULT"
            
        return preset_section
        
