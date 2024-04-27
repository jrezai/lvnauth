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
import pygame
from typing import List
from screeninfo import screeninfo


class ManualUpdate:
    manual_queue: List[pygame.Rect]
    manual_queue = []

    @staticmethod
    def queue_for_update(rect_to_update: pygame.Rect):
        """
        Queue a rect to be updated on the screen.

        Purpose: some commands which are not animation-related, such as
        <character_set_position_x>, don't update the screen automatically.

        This method was created so that any non-animation related changes
        can call this method to update the changes on the screen.
        """

        if not rect_to_update:
            return

        # Go through all the rects that are queued for updating (if any)
        # to see if the new rect that we want to add is already contained
        # in the existing rects that are queued.

        for rect in ManualUpdate.manual_queue:

            # Check if the given rect is already inside a rect that's queued.
            # If so, if there is no point in queueing the new rect.
            if rect.contains(rect_to_update):
                return

            # Check if a rect that's already queued is bigger than
            # the rect that is requesting to be queued.
            # If so, there is no point in queuing the new rect.
            elif rect_to_update.contains(rect):
                return

        ManualUpdate.manual_queue.append(rect_to_update)

    @staticmethod
    def remove_queue_if_rect_exists(rect_list: List[pygame.Rect]):
        """
        Loop through the given rect list and remove rects from the
        queue if already in the given rect list.

        Arguments:

        - rect_list: a list of rects to check. This is the rect list
        that is destined to be used for updating the screen.
        """

        # List of queue indexes that we need to remove later.
        remove_queue_index = []

        # Loop through the given update list
        for rect in rect_list:

            # Loop through the manual queue list.
            for i, queue_rect in enumerate(ManualUpdate.manual_queue):

                # Does the given update list already include the queued rect?
                # If so, remove that rect from the queue list because it will
                # already get updated from a different update list.
                if rect.contains(queue_rect):
                    remove_queue_index.insert(0, i)
                    continue

        ## Remove the queued rects that we found above.
        # for i in remove_queue_index:
        # ManualUpdate.manual_queue.pop(i)

    @staticmethod
    def get_updated_rects(existing_update_list: List[pygame.Rect]) -> List[pygame.Rect] | None:
        """
        Return any rects that need updating.
        """
        updated_rects = ManualUpdate.manual_queue.copy()

        # Remove queued rects that are already set to be updated.
        ManualUpdate.remove_queue_if_rect_exists(existing_update_list)

        ManualUpdate.manual_queue.clear()
        return updated_rects


# Used for sprite mouse clicks and mouse hovers
class MouseActionsAndCoordinates:
    MOUSE_POS = tuple()
    MOUSE_DOWN = False
    MOUSE_UP = False


class Passer:
    active_story = None
    
    # Used for specifying a custom chapter/scene
    # to play from the Launch window.
    # {chapter_name: scene_name}
    manual_startup_chapter_scene = None

    # If the user clicks the 'X' in the launch window,
    # we set this flag to indicate to the ActiveStory object
    # that the application should close (because the user clicked the 'X')
    close_after_launch_window = False
    

    @staticmethod
    def center_window_active_monitor(window) -> bool:
        """
        Center the given window (root or toplevel) on the monitor that it's on.
        
        For example: if the given window is opened on the second monitor,
        then it will be centered on the second monitor.
        
        This has been tested successfully on X (in Linux).
        It hasn't been tested in Windows.
        
        Arguments:
        
        - window: a root or toplevel window
        
        Returns: bool 
        (True if the center calculations were done successfully and the window
        has been centered on a monitor)
        
        (False) if for some reason the window wasn't found in any of the
        monitors (shouldn't happen).
        """
        
        # We need to call the root or toplevel's update() method before we 
        # try and get the window's size, because if the window hasn't been 
        # drawn on the screen yet, we won't get the proper dimensions
        # when we try and use winfo_width() and winfo_height().
        # 
        # When we run .update(), then winfo_width() and winfo_height()
        # will work as expected.
    
        window.update_idletasks()
        
        # Hide the toplevel window for now (it will help to minimize 
        # flickering when it moves to its center position later on)
        window.withdraw()
        
        # Get a list of monitors
        monitors = screeninfo.get_monitors()
        
        mon_sizes = []
        combined_width_so_far = 0
        
        #if len(monitors) == 1:
            #mon_sizes.append((_from, _to, monitors[0].height))
            
        #else:
    
        # Get a list of widths for each monitor.
        # For example, if there are 2 monitors (each 1920x1080), 
        # then find out the width of each (incrementing over to the next).
        # Example: first monitor: 0 to 1920 (width), second monitor: 1921x3840
        
        # We will need to create a tuple that looks like this:
        # (from_x, to_x, center_x, center_y)
        
        # 'from_x' and 'to_x' represent a monitor's width 
        # from 'from_x' to 'to_x'.
        
        # For example: if the first monitor is 1920 pixels wide, 
        # then 'from_x' will be 0, and 'to_x' will be 1920.
        # Then, if the second monitor is also 1920 pixels wide, 
        # then for the second monitor, 'from_x' will be 1921, to_x' will be 3840.
        
        # So if the window's X (not width, but X) is within that monitor's 
        # 'from_x' to 'to_x', then we will consider the
        # window to be inside that monitor (because the window's X was 
        # inside the 'from_x' and 'to_x' of that monitor's tuple value).
        
        # center_x, center_y are the center width and center height, 
        # respectivly, of the single monitor that the window is in.
        
        # Enumerate over each monitor
        for idx, m in enumerate(monitors):
            
            # If it's the first monitor, then we don't need to add +1 for the first '_from_x'
            if idx == 0:
                _from = 0
                _to = m.width
            else:
                # Add a +1 so that it continues 1 pixel more for the next monitor, so that two monitors don't overlap.
                _from = combined_width_so_far + 1
                _to = combined_width_so_far + m.width
                
            # Get the center x and y of the current monitor we're looping on.
            center_x = combined_width_so_far + (m.width // 2)
            center_y = m.height // 2
            
            # We will use this later to find out which of these monitors the specified window is in.
            mon_sizes.append((_from, _to, center_x, center_y))
            
            # As we continue enumerating over each monitor, the 'from_x' has to continue where the last monitor's width left off.
            # So we keep summing up the width of each monitor that we enumerate so the next monitor can start its 'from_x',
            # where the last monitor's width ended, + 1.
            combined_width_so_far += m.width            
            
        # Find out which monitor (width-range) the X of the window is on, then center it based on that.
        for size_range in mon_sizes:
            
            # Is the window inside the current loop monitor?
            if window.winfo_x() >= size_range[0] and window.winfo_x() <= size_range[1]:
                win_x_center = size_range[2] - (window.winfo_width() // 2)
                win_y_center = size_range[3] - (window.winfo_height() // 2)
                
                # Center the window
                window.geometry(f"+{win_x_center}+{win_y_center}")
                
                # Now show the toplevel window, because we're done centering it.
                window.deiconify()
                
                return True
        else:
            return False
    