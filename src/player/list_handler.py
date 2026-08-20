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

    def list_add(self, list_name: str, text_to_add: str, comma_separated: bool = True):
        """
        Create a new list if it doesn't already exist and add the comma
        separated text to its sub-list.

        The list name is case sensitive.

        Arguments:

        - list_name: a new or existing list name

        - text_to_add: a single text or comma separated string of text
        to add to the list. Whether the commas are read as plain text or
        delimiters depends on the next argument.

        - comma_sparated: whether to read 'text_to_add' as comma separated
        text or as a single text (example: takes in commas as part of the
        text).
        """

        # Make sure there is text to add.
        if not text_to_add:
            return

        # Create the sub-list of text, trimming spaces.
        if comma_separated:
            # Comma separated strings
            words_list = [item.strip() for item in text_to_add.split(",")]
        else:
            # Non-comma separated text

            # Add the text as a single string of text.
            words_list = [text_to_add.strip()]

        # Does the list have existing items? Append.
        existing_list = self.lists.get(list_name)
        if existing_list:
            # Append to the existing list.
            existing_list.extend(words_list)
        else:
            # First time populating the list.
            self.lists[list_name] = words_list

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
