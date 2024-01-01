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
