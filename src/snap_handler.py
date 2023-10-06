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
        
        if snap_name:
            return True
        else:
            return False
    
    def get_snap_common_folder() -> Path:
        """
        Return a path to the snap common folder.
            
        The snap common folder is unversioned and the data
        is not copied when upgrading or rolling back.
        
        return a string path or None if the snap common path
        was not found.
        """
        
        snap_common_folder = os.environ.get("SNAP_COMMON")
        
        if not snap_common_folder:
            return
        
        snap_common_folder = Path(snap_common_folder)
        
        return snap_common_folder
        
    def get_lvnauth_editor_icon_path() -> Path:
        """
        Return a snap path to LVNAuth editor's icon png file.
        
        Example: /snap/lvnauth/x1/lvnauth/src/app_icon.png
        """
        
        # /snap/lvnauth/x1
        snap_directory = os.environ["SNAP"]
        
        if not snap_directory:
            return
        
        snap_directory = Path(snap_directory)
        
        full_path: Path
        full_path = snap_directory / "lvnauth" / "src" / "app_icon.png"

        return full_path
    