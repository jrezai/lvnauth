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

from pathlib import Path
from configparser import ConfigParser, NoSectionError, NoOptionError

 
# Used for saving and loading visual novel data, such as the license key.
class PlayerConfigHandler:
    
    def __init__(self, vn_name: str, lvna_file_full_path: Path):
        
        """
        Arguments:
        
        - vn_name: the visual novel name. We use this in the config file as
        all visual novels in the same folder will share the same config file.
        Each visual novel will have its own section in the config file. We use
        the visual novel name (vn_name) for each section.
        
        - lvna_file_full_path: the full path to the visual novel file.
        We use this to get the path of the visual novel. The config file
        needs to be in the same folder as the lvna file, for simplicity.
        """
        
        if not lvna_file_full_path.is_file():
            raise FileNotFoundError(f".lvna file not found: {lvna_file_full_path}")
        
        # Get the path, without the file name.
        vn_path = lvna_file_full_path.parent
        
        # So know which category in the config file to save/load data.
        self.vn_name = vn_name
        
        self.config_file_path = Path(vn_path) / "vn_data"
        self.config = ConfigParser()
        self.config.read(self.config_file_path)
        
    def save_data(self, option_name: str, value: str):
        """
        Save data to a config file that's in the same folder as the
        visual novel.
        
        Arguments:

        - option_name: the option name under the category.
        
        - value: the value to save.
        """
        
        # The section has to exist, it won't be made automatically.
        if not self.config.has_section(self.vn_name):
            self.config.add_section(self.vn_name)
        
        # The option, however, will be created automatically 
        # if it doesn't already exist.
        self.config[self.vn_name][option_name] = value
        
        self.config_file_path: Path
        with self.config_file_path.open("w") as f:
            self.config.write(f)
        
        # Reload the config parser.
        self.config.read(self.config_file_path)        
        
    def get_data(self, option_name: str) -> str:
        """
        Get a value from the config file.
        
        Arguments:
        
        - option_name: the option under the visual novel to get the data for.
        """
        
        try:
            data = self.config.get(self.vn_name, option_name)
            
        except (NoSectionError, NoOptionError):
            return
        
        return data
        
        