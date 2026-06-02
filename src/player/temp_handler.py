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

import os
import tempfile
from pathlib import Path
from enum import Enum, auto


class TempContentType(Enum):
    MUSIC_FILE = "M"
    ALL = auto()


class TempHandler:
    """
    Handles getting the temporary directory, either in a Snap package, Flatpak
    or outside a container (regular /tmp folder).
    
    Also handles cleaning up temporary files.
    """
    
    @staticmethod
    def cleanup_temp_files(content_type: TempContentType):
        """
        Scan the temporary directory and delete LVNAuth temp files.
        
        Arguments:

        - content_type: the type of temporary files to delete. For example, if
        it's set to TempContentType.MUSIC, then only music temp files are
        deleted.
        """
        
        # Get the right temporary directory, depending on if we're running
        # inside a Snap or Flatpak or neither.
        temp_dir = TempHandler.get_proper_temp_dir()
        if not temp_dir or not temp_dir.is_dir():
            return
    
        # Find matching files
        if content_type == TempContentType.ALL:
            # All LVNAuth temp files
            pattern_search = "lvnauth_tmp_*"
        else:
            # Specific types of LVNAuth temp files
            pattern_search = f"lvnauth_tmp_{content_type.value}_*"
            
        # Find LVNAuth temp files.
        temp_files = temp_dir.glob(pattern_search)

        file_path: Path
        for file_path in temp_files:
            try:
                file_path.unlink(missing_ok=True)
            except OSError:
                # Skip silently. It could be a permission issue or the file
                # could be locked by another process.
                pass

    @staticmethod
    def get_proper_temp_dir() -> Path:
        """
        Return the temporary directory to use depending on whether
        LVNAuth is running in a Snap, or Flatpak, or neither.
        """
        
        # Try to get the Snap user data directory.
        snap_user_data = os.environ.get("SNAP_USER_DATA")
        
        # Try to get the Flatpak runtime directory
        flatpak_runtime = None
        if Path("/.flatpak-info").exists():
            flatpak_runtime = os.environ.get("XDG_RUNTIME_DIR")
            
        # Snap, Flatpak, or neither?
        custom_temp_dir = snap_user_data or flatpak_runtime
        
        if not custom_temp_dir:
            # System default temp directory
            custom_temp_dir = tempfile.gettempdir()
            
        return Path(custom_temp_dir)
