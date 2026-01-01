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
- Nov 23, 2023 (Jobin Rezai) - Added get_snap_user_data_folder()

- February 24, 2024 (Jobin Rezai) - Renamed to container_handler.py,
to begin Flatpak recognition.

- July 12, 2025 (Jobin Rezai) - Use an absolute path when playing a draft visual 
novel instead of a relative path.
"""

import os
from pathlib import Path


class ContainerHandler:
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
    def is_in_flatpak_package() -> bool:
        """
        Check whether LVNAuth is inside a Linux Flatpak package or not.
        
        return: True if running inside a Flatpak or False if otherwise.
        """
        container = os.environ.get("container")
        if container and container == "flatpak":
            return True
        else:
            return False
        
    @staticmethod
    def get_flatpak_app_directory() -> Path | None:
        """
        Return the path to the /app/bin folder of the flatpak.
        This is where the main Python scripts are.
        """
        if ContainerHandler.is_in_flatpak_package():

            app_folder = Path("/app/bin")
            
            return app_folder
        
    @staticmethod
    def get_flatpak_config_directory() -> Path | None:
        """
        Return the path to the config folder of the flatpak,
        which is something like:
        /home/username/.var/app/org.lvnauth.LVNAuth/config
        
        This is where the non-edited default version of lvnauth.config is.
        """
        if ContainerHandler.is_in_flatpak_package():
            config_folder = os.environ.get("XDG_CONFIG_HOME")
            if not config_folder:
                return
            
            config_folder = Path(config_folder)
            
            return config_folder
    
    @staticmethod
    def get_snap_user_common_folder() -> Path | None:
        """
        Return a path to the snap user common folder.
            
        The snap common folder is unversioned and the data
        is not copied when upgrading or rolling back.
        
        return a string path or None if the snap common path
        was not found.
        """

        if ContainerHandler.is_in_snap_package():
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

        if ContainerHandler.is_in_snap_package():
            snap_user_data_folder = os.environ.get("SNAP_USER_DATA")

            if not snap_user_data_folder:
                return

            snap_user_data_folder = Path(snap_user_data_folder)

            return snap_user_data_folder
    
    @staticmethod
    def get_draft_path() -> Path:
        """
        Get the path for saving and playing a .lvna draft file
        and if the draft folder doesn't exist, create it.
        """
        full_path = None
        
        if ContainerHandler.is_in_snap_package():
            snap_common = ContainerHandler.get_snap_user_common_folder()
            if snap_common:
                full_path = snap_common / "draft" / "draft.lvna"
                
        elif ContainerHandler.is_in_flatpak_package():
            draft_directory = os.environ.get("XDG_CACHE_HOME")
            if draft_directory:
                full_path = Path(draft_directory) / "draft" / "draft.lvna"
                
        else:
            full_path = Path(__file__).parent / "draft" / "draft.lvna"
            
        # Do we have a full path to draft.lvna?
        if full_path:
            
            # Make sure the draft folder exists.
            draft_folder = full_path.parents[0]
            draft_folder.mkdir(parents=True, exist_ok=True)
            
            # Return a full path to draft.lvna
            return full_path
        
    @staticmethod
    def get_lvnauth_player_python_file() -> Path | None:
        """
        Return a snap or flatpak path to LVNAuth's main.py player Python file.
        If we're not in a snap, return the regular path to main.py
        
        Example for snap: /snap/lvnauth/x1/lvnauth/src/player/main.py
        Example for flatpak: /app/bin/player/main.py
        """
        
        # /snap/lvnauth/x1
        if ContainerHandler.is_in_snap_package():
            snap_directory = os.environ.get("SNAP")

            snap_directory = Path(snap_directory)

            full_path: Path
            full_path = snap_directory / "src" / "player" / "main.py"

            return full_path
        
        # /app/bin
        elif ContainerHandler.is_in_flatpak_package():
            app_directory = ContainerHandler.get_flatpak_app_directory()
            
            full_path: Path
            full_path = app_directory / "player" / "main.py"

            return full_path            
        else:
            # Not in a Snap package; return a regular path.
            return Path(__file__).parent / "player" / "main.py"

    @staticmethod
    def get_lvnauth_editor_icon_path() -> Path | None:
        """
        Return a snap path or flatpak path to LVNAuth editor's icon png file.

        Example for snap: /snap/lvnauth/x1/lvnauth/src/app_icon.png
        Example for flatpak: /app/bin/app_icon.png
        """

        if ContainerHandler.is_in_snap_package():
            # /snap/lvnauth/x1
            snap_directory = os.environ.get("SNAP")

            if not snap_directory:
                return

            snap_directory = Path(snap_directory)

            full_path: Path
            full_path = snap_directory / "src" / "app_icon.png"

            return full_path
        
        elif ContainerHandler.is_in_flatpak_package():
            # /app/bin/
            flatpak_directory = ContainerHandler.get_flatpak_app_directory()
            if not flatpak_directory:
                return
            
            full_path: Path
            full_path = flatpak_directory / "app_icon.png"

            return full_path            

    @staticmethod
    def get_lvnauth_editor_icon_path_small() -> Path | None:
        """
        Return a snap or flatpak path to LVNAuth player's small icon png file.

        Example for snap: /snap/lvnauth/x1/lvnauth/src/player/app_icon_small.png
        Example for flatpak: /app/bin/player/app_icon_small.png
        """
        
        if ContainerHandler.is_in_snap_package():

            # /snap/lvnauth/x1
            snap_directory = os.environ.get("SNAP")
    
            if not snap_directory:
                return
    
            snap_directory = Path(snap_directory)
    
            full_path: Path
            full_path = snap_directory / "src" / "player" / "app_icon_small.png"
    
            return full_path
        
        elif ContainerHandler.is_in_flatpak_package():
            
            # /app/bin
            app_directory = ContainerHandler.get_flatpak_app_directory()
            if not app_directory:
                return
            
            full_path: Path
            full_path = app_directory / "player" / "app_icon_small.png"
    
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
