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

"""
Changes:
- Nov 23, 2023 (Jobin Rezai) - Added get_snap_user_data_folder()
"""

import os
from pathlib import Path


class SnapHandler:
    @staticmethod
    def is_in_snap_package() -> bool:
        """
        Check whether LVNAuth is inside a Linux Snap package or not.
        
        return: True if in a snap package, or False if not in a snap package.
        """
        snap_name = os.environ.get("SNAP_NAME")
        
        if snap_name is not None and snap_name == "lvnauth":
            return True
        else:
            return False
    
    @staticmethod
    def get_snap_user_common_folder() -> Path | None:
        """
        Return a path to the snap user common folder.
            
        The snap common folder is unversioned and the data
        is not copied when upgrading or rolling back.
        
        return a string path or None if the snap common path
        was not found.
        """

        if SnapHandler.is_in_snap_package():
            snap_user_common_folder = os.environ.get("SNAP_USER_COMMON")

            if not snap_user_common_folder:
                return

            snap_user_common_folder = Path(snap_user_common_folder)

            return snap_user_common_folder
        
    @staticmethod
    def get_snap_user_data_folder() -> Path | None:
        """
        Return a path to the snap user data folder.
            
        The snap user data folder is versioned and the data
        is copied when upgrading.
        
        This directory is used for storing the latest config file.
        
        return a string path or None if the snap user data path
        was not found.
        """

        if SnapHandler.is_in_snap_package():
            snap_user_data_folder = os.environ.get("SNAP_USER_DATA")

            if not snap_user_data_folder:
                return

            snap_user_data_folder = Path(snap_user_data_folder)

            return snap_user_data_folder
    
    @staticmethod
    def get_draft_path() -> Path:
        """
        Get the path for saving and playing a .lvna draft file. 
        """
        if SnapHandler.is_in_snap_package():
            snap_common = SnapHandler.get_snap_user_common_folder()
            if snap_common:
                draft_path = snap_common / "draft" / "draft.lvna"
                
                return draft_path
        else:
            return Path(r"draft/draft.lvna")
        
    @staticmethod
    def get_lvnauth_player_python_file() -> Path | None:
        """
        Return a snap path to LVNAuth's main.py player Python file.
        If we're not in a snap, return the regular path to main.py
        
        Example: /snap/lvnauth/x1/lvnauth/src/player/main.py
        """
        
        # /snap/lvnauth/x1
        if SnapHandler.is_in_snap_package():
            snap_directory = os.environ.get("SNAP")

            snap_directory = Path(snap_directory)

            full_path: Path
            full_path = snap_directory / "src" / "player" / "main.py"

            return full_path
        else:
            # Not in a Snap package; return a regular path.
            return Path("player") / "main.py"

    @staticmethod
    def get_lvnauth_editor_icon_path() -> Path | None:
        """
        Return a snap path to LVNAuth editor's icon png file.

        Example: /snap/lvnauth/x1/lvnauth/src/app_icon.png
        """

        if SnapHandler.is_in_snap_package():
            # /snap/lvnauth/x1
            snap_directory = os.environ.get("SNAP")

            if not snap_directory:
                return

            snap_directory = Path(snap_directory)

            full_path: Path
            full_path = snap_directory / "src" / "app_icon.png"

            return full_path

    @staticmethod
    def get_lvnauth_editor_icon_path_small() -> Path | None:
        """
        Return a snap path to LVNAuth player's small icon png file.

        Example: /snap/lvnauth/x1/lvnauth/src/player/app_icon_small.png
        """

        # /snap/lvnauth/x1
        snap_directory = os.environ.get("SNAP")

        if not snap_directory:
            return

        snap_directory = Path(snap_directory)

        full_path: Path
        full_path = snap_directory / "src" / "player" / "app_icon_small.png"

        return full_path

    @staticmethod
    def get_lvnauth_src_folder() -> Path | None:
        """
        Return a snap path to the /src folder where all the main files are.
        Example: /snap/lvnauth/x1/lvnauth/src/
        :return: Path or None
        """

        # /snap/lvnauth/x1
        snap_directory = os.environ.get("SNAP")

        if not snap_directory:
            return

        snap_directory = Path(snap_directory)
        snap_directory = snap_directory / "src"

        return snap_directory
