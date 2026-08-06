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

import random
from typing import List, Dict


class ListHandler:
    def __init__(self):
        
        # Key: list name
        # Value: [list of strings]
        self.lists: Dict[str, List[str]]
        self.lists = {}
        
    def list_add(self, list_name: str, comma_separated_text: str):
        """
        Create a new list if it doesn't already exist and add the comma
        separated text to its sub-list.
        
        The list name is case sensitive.
        """

        # Make sure there is text to add.
        if not comma_separated_text:
            return
        
        # Create the list, with no text yet.
        self.lists[list_name] = list_name
        
        # Create the sub-list of text, trimming spaces.
        word_list = [item.strip() for item in comma_separated_text.split(",")]
        
        self.lists[list_name] = word_list
        
    def list_delete(self, list_name: str):
        """
        Delete the given dict key.
        
        The list name is case sensitive.
        """
        try:
            del self.lists[list_name]
        except KeyError:
            return
        
    def list_take_first(self, list_name: str) -> str | None:
        """
        Take the first item from the given list (index 0).
        
        The list name is case-sensitive.
        """

        try:
            list_values = self.lists[list_name]
        except KeyError:
            raise KeyError(f"List not found: {list_name}")
        
        if list_values:
            # Take the first item.
            return list_values.pop(0)
        
    def list_take_last(self, list_name: str) -> str | None:
        """
        Take the last item from the given list.
        The list name is case-sensitive.
        """

        try:
            list_values = self.lists[list_name]
        except KeyError:
            raise KeyError(f"List not found: {list_name}")
        
        if list_values:
            # Take the last item.
            return list_values.pop()
            
    def list_take_random(self,
                    list_name: str,
                    remove_after: bool = True) -> str | None:
        """
        Take a random item from the given list and return it.
        
        Arguments:
        
        - list_name: the list to take a random value from. Case-sensitive.
        
        - remove_after: whether to delete the item (True) or not (False).
        """
        try:
            list_values = self.lists[list_name]
        except KeyError:
            raise KeyError(f"List not found: {list_name}")
        
        if list_values:
            random_value = random.choice(list_values)
            
            # Remove the item from the list now that we found it?
            if remove_after:
                list_values.remove(random_value)
            
            return random_value
    
if __name__ == "__main__":
    
    test = ListHandler()
