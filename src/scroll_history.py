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
import tkinter as tk
from dataclasses import dataclass
from typing import List, Dict



@dataclass
class ScrollPosition:
    xview: float
    yview: float
    
    # Such as "10.4" (line 10, column 4)
    cursor_position: str
    
    

class ScrollHistory:
    """
    Save and restore the scrollbar and cursor positions in a text widget.
    
    The scrollbar position saving does not occur on the file system,
    it's just during runtime.
    """
    def __init__(self, text_widget: tk.Text):
        
        self.text_widget = text_widget
        
        # {chapter_name: [scroll_data, {scene_name: {scroll_data}}] }
        
        # Records scroll positions for chapters and scenes
        # Key: str chapter name, case sensitive
        # Value: dict of scene names with scroll_data as the value.
        # { chapter_name: [scroll_data, {scene_name: scroll_data}] }
        self.scroll_positions = {}
        
        # Scroll positions for reusable scripts
        # Key: reusuable script name (case-sensitive)
        # Value: ScrollPosition object
        # { reusable script name: ScrollPosition object }
        self.scroll_positions_reusables = {}
        
    def rename_chapter_name_scroll_data(self,
                                        old_chapter_name: str,
                                        new_chapter_new: str):
        """
        Find the old chapter name in the scroll history and rename it.

        This gets used when the user renames a chapter in the editor.
        We need to also make sure the scroll history for that chapter
        references the new chapter name.

        Arguments:

        - old_chapter_name: the previous name of the chapter, case-sensitive.

        - new_chapter_new: the new name of the chapter, case-sensitive.

        This is what the historical scroll data dictionary looks like:
        { chapter_name: [scroll_data, {scene_name: scroll_data}] }
        """

        # Make sure the scroll history exists for the old name.
        if old_chapter_name in self.scroll_positions:

            # .pop() will return the value *and* delete the key.
            # We're creating a new key (new chapter name) with the old value.
            self.scroll_positions[new_chapter_new] =\
                self.scroll_positions.pop(old_chapter_name)
        
    def rename_scene_name_scroll_data(self,
                                      chapter_name: str,
                                      old_scene_name: str,
                                      new_scene_name: str):
        """
        Find the old scene name in the scroll history and rename it.

        This gets used when the user renames a scene in the editor.
        We need to also make sure the scroll history for that scene
        references the new scene name.

        Arguments:

        - chapter_name: the chapter that the scene is in.

        - old_scene_name: the previous name of the scene, case-sensitive

        - new_scene_name: the new name of the scene, case-sensitive.

        This is what the historical scroll data dictionary looks like:
        { chapter_name: [scroll_data, {scene_name: scroll_data}] }
        """

        # Make sure scroll history exists for the given chapter.
        value = self.scroll_positions.get(chapter_name)
        if not value:
            return

        # Get the scroll history for the 
        scene_scroll_history: Dict
        scene_scroll_history = value[1]

        # Find the old scene name in the scene scroll history
        if old_scene_name in scene_scroll_history:

            # .pop() will return the value *and* delete the key.
            # We're creating a new key (new scene name) with the old value.            
            scene_scroll_history[new_scene_name] =\
                scene_scroll_history.pop(old_scene_name)
        
    def rename_reusable_name_scroll_data(self,
                                         old_reusable_name: str,
                                         new_reusable_name: str):
        """
        Find the old reusable name in the scroll history and rename it.

        This gets used when the user renames a reusable script in the editor.
        We need to also make sure the scroll history for that reusable script
        references the new reusable script name.

        Arguments:

        - old_reusable_name: the previous name of the reusable script,
        case-sensitive.

        - new_reusable_name: the new name of the reusable script,
        case-sensitive.

        This is what the historical scroll data dictionary looks like:
        # { reusable script name: ScrollPosition object }
        """

        # Make sure the scroll history exists for the old name.
        if old_reusable_name in self.scroll_positions_reusables:

            # .pop() will return the value *and* delete the key.
            # We're creating a new key (new reusable script name) with 
            # the old value.
            self.scroll_positions_reusables[new_reusable_name] =\
                self.scroll_positions_reusables.pop(old_reusable_name)
        
    def delete_chapter_scroll_history(self, chapter_name: str):
        """
        Delete the scroll history of a given chapter name.
        
        This is used when a chapter name is renamed or deleted.
        
        Arguments:
        
        - chapter_name: the chapter name that should have its scroll
        history deleted. This is case-sensitive.
        
        If the chapter has no scroll history, no error will occur.
        
        This is what a scroll history dictionary looks like:
        # { chapter_name: [scroll_data, {scene_name: scroll_data}] }
        """
        if chapter_name in self.scroll_positions:
            del self.scroll_positions[chapter_name]
            
    def delete_scene_scroll_history(self, chapter_name: str, scene_name: str):
        """
        Delete the scroll history of a given scene name.
        
        This is used when a scene name is renamed or deleted.
        
        Arguments:
        
        - chapter_name: a scene is always part of a chapter. This is the
        name of the chapter that the scene is in. Case-sensitive.
        
        - scene_name: the scene name to delete the scroll history for.
        This is case-sensitive.
        
        If the scene has no scroll history, no error will occur.
        
        This is what a scroll history dictionary looks like:
        { chapter_name: [scroll_data, {scene_name: scroll_data}] }
        """
        value = self.scroll_positions.get(chapter_name)
        if value:
            scenes_dict = value[1]
            if scene_name in scenes_dict:
                del scenes_dict[scene_name]
        
    def delete_reusable_scroll_history(self, reusable_script_name: str):
        """
        Delete the scroll history of a given reusable script.
        
        This is used when a reusable script is renamed or deleted.
        
        Arguments:
        
        - reusable_script_name: the name of the reusable script that should
        should have its scroll history deleted. This is case-sensitive.
        
        If the reusable name has no scroll history, no error will occur.
        
        This is what a scroll history dictionary looks like:
        { reusable script name: ScrollPosition object }
        """
        if reusable_script_name in self.scroll_positions_reusables:
            del self.scroll_positions_reusables[reusable_script_name]
        
    def save_scroll_data_chapter_scene(self,
                                       source_chapter_name: str,
                                       source_scene_name: str|None = None):
        """
        Save the current scroll positions (x and y) and the current cursor
        position of the current chapter or scene script.
        
        This is not used for reusable scripts.
        
        Arguments:
        
        - source_chapter_name: the chapter name that the current script is on.
        This is case-sensitive
        
        - source_scene_name: an optional scene name when the user is currently
        on a scene. It's optional because the user might be on a chapter
        script. Leave as None if the user is currently on a chapter script.
        This is case-sensitive.
        
        This is what the historical scroll data dictionary looks like:
        { chapter_name: [scroll_data, {scene_name: scroll_data}] }
        """
        
        
        # Save the current scroll position before leaving.
        # xview() and yview() return a tuple like (0.2, 0.5); 
        # but we only need the first number.
        # 
        # The first number is the top edge of the visible area.
        # The second number is the bottom edge of the visible area.
        # For example (0.2, 0.5), the distance is 0.3, meaning 30% of the
        # script is currently visible. We only need the starting top position.
        pos_x = self.text_widget.xview()[0]
        pos_y = self.text_widget.yview()[0]
        
        # Get the cursor position as a string
        # Example: "10.4" means line 10, column 4
        cursor_pos = self.text_widget.index(tk.INSERT)
        
        # Use an object to store the saved scroll info.
        save_scroll_data = ScrollPosition(xview=pos_x,
                                          yview=pos_y,
                                          cursor_position=cursor_pos)
        
        # Is the user currently on a chapter script?
        if not source_scene_name:
            # Yes, the user is currently on a chapter script.
            # { chapter_name: [scroll_data, {scene_name: scroll_data}] }
            
            # Get the value for the current chapter.
            value: List
            value = self.scroll_positions.get(source_chapter_name)
            
            if value:
                # Update the existing value
                
                # [scroll_data, {scene_name: scroll_data}]
                value[0] = save_scroll_data
            
            else:
                # This chapter has no scenes and no previous scroll history.
                # Create a new value with an empty dict of scenes
                value = [save_scroll_data, {}]
                

            # Update the scroll info for the chapter that's being parted.
            self.scroll_positions[source_chapter_name] = value
        
        else:    
            # The user currently on a scene script.
            # { chapter_name: [scroll_data, {scene_name: scroll_data}] }
            
            # Get the value for the current chapter.
            value: List
            value = self.scroll_positions.get(source_chapter_name)
            
            # Get a dictionary of all the scenes and scroll data
            # in the chapter.
            # {scene_name: scroll_data}
            scenes: dict
            scenes = value[1]
            
            # Update the scroll data for this scene.
            # This will directly update the scroll_positions dict
            scenes[source_scene_name] = save_scroll_data
            
            
            # self.scroll_positions[source_chapter_name] = scenes
            
    def save_scroll_data_reusable(self, reusable_script_name: str):
        """
        Save the current scroll positions (x and y) and the current cursor
        position of the current reusable script.
        
        This is not used for chapters or scenes.
        
        Arguments:
        
        - reusable_script_name: the reusable script name that the current
        script is on. This is case-sensitive
        
        This is what the historical scroll data dictionary looks like:
        { reusable script name: ScrollPosition object }
        """
        
        
        # Save the current scroll position before leaving.
        # xview() and yview() return a tuple like (0.2, 0.5); 
        # but we only need the first number.
        # 
        # The first number is the top edge of the visible area.
        # The second number is the bottom edge of the visible area.
        # For example (0.2, 0.5), the distance is 0.3, meaning 30% of the
        # script is currently visible. We only need the starting top position.
        pos_x = self.text_widget.xview()[0]
        pos_y = self.text_widget.yview()[0]
        
        # Get the cursor position as a string
        # Example: "10.4" means line 10, column 4
        cursor_pos = self.text_widget.index(tk.INSERT)
        
        # Use an object to store the saved scroll info.
        save_scroll_data = ScrollPosition(xview=pos_x,
                                          yview=pos_y,
                                          cursor_position=cursor_pos)
        

        # Update the scroll info for the chapter that's being parted.
        self.scroll_positions_reusables[reusable_script_name] =\
            save_scroll_data
            
    def restore_scroll_data_chapter_scene(self,
                                          dest_chapter_name: str,
                                          dest_scene_name: str = None):
        """
        Get the scroll history data for the given chapter and/or scene.
        
        This is not used for reusable scripts.
        
        Arguments:
        
        - dest_chapter_name: the chapter name that the user wants to go to.
        This is case-sensitive. Even if we're trying to get history for
        a scene script, a chapter name must always be provided.
        
        - dest_scene_name: an optional scene scene name when the destination
        is going to be a scene script. It's optional because the user might
        want to go to a chapter script. Leave as None if the destination
        will be a chapter script. This is case-sensitive.
        
        This is what the historical scroll data dictionary looks like:
        { chapter_name: [scroll_data, {scene_name: scroll_data}] }
        """
    
        # Restore the scroll data for the destination script.
        
        # Initialize
        scroll_data = None

        # Do we have the destination chapter in the scroll history?
        if dest_chapter_name in self.scroll_positions:
            
            # Yes, we have the saved data for the destination chapter.
            
            # Are we getting the scene scroll history or the chapter itself?
            if not dest_scene_name:
                
                # We're getting the scroll history for the chapter itself.
                # Not the scene.
            
                # Get the saved scroll data for the destination script.
                scroll_data: ScrollPosition =\
                    self.scroll_positions[dest_chapter_name][0]
                
            else:
                # We're getting the scroll history for the scene.
                
                # { chapter_name: [scroll_data, {scene_name: scroll_data}] }
                scroll_data: ScrollPosition =\
                    self.scroll_positions[dest_chapter_name][1].get(dest_scene_name)
                
        # Set the text widget xview and yview, and the cursor position
        self._set_scroll(scroll_data=scroll_data)   
            
    def restore_scroll_data_reusable(self, reusable_script_name: str):
        """
        Get the scroll history data for the given reusable script.
        
        This is not used for chapters or scenes.
        
        Arguments:
        
        - reusable_script_name: the reusable script name that the user wants
        to go to. This is case-sensitive.
        
        This is what the historical scroll data dictionary looks like:
        { reusable script name: ScrollPosition object }
        """
    
        # Restore the scroll data for the destination script.
        
        # Attempt to get the saved scroll data for the destination script.
        scroll_data: ScrollPosition =\
            self.scroll_positions_reusables.get(reusable_script_name)

        # Set the text widget xview and yview, and the cursor position
        self._set_scroll(scroll_data=scroll_data)      

    def _set_scroll(self, scroll_data: ScrollPosition):
        """
        Set the text widget xview and yview to the specified scroll data
        values. Also set the cursor position.
        
        Arguments:
        
        - scroll_data: the scroll values that should be set on the text
        widget, along with the cursor position. If None, then the scroll
        position will default to the top.
        """
        
        if scroll_data:
            
            # Restore the scroll positions
            self.text_widget.xview_moveto(scroll_data.xview)
            self.text_widget.yview_moveto(scroll_data.yview)
        
            # Restore the cursor position.
            self.text_widget.mark_set(tk.INSERT,
                                      scroll_data.cursor_position)
            # self.text_widget.see(tk.INSERT)            
            
        else:
            
            # We don't have the scroll data for this script.
            # The script is being viewed for the first time.
            # Start at the top.
            self.text_widget.xview_moveto(0.0)
            self.text_widget.yview_moveto(0.0)
