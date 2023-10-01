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

class Passer:
    active_story = None
    
    # Used for a constant move speed of all objects
    # regardless of the FPS    
    seconds_elapsed = 0
    
    # Used for specifying a custom chapter/scene
    # to play from the Launch window.
    # {chapter_name: scene_name}
    manual_startup_chapter_scene = None

    # If the user clicks the 'X' in the launch window,
    # we set this flag to indicate to the ActiveStory object
    # that the application should close (because the user clicked the 'X')
    close_after_launch_window = False