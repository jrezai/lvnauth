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

import tkinter as tk
import tkinter.ttk as ttk
from string import ascii_letters, digits


class EntryWithLimit(ttk.Entry):
    """
    An entry widget that can:
    - Allow a max length limit
    - Allow only specific characters
    - Disallow numbers before text (useful for usernames)
    """
    
    def __init__(self, master=None, widget=None, 
                 max_length=None, characters_allowed=None, 
                 disallow_numbers_before_text=False,
                 auto_caps=False, **kw):
        """
        An entry widget that can:
        - Allow a max length limit
        - Allow only specific characters
        - Automatically change text to all-caps
        - Disallow numbers before text (useful for usernames)
        
        Arguments:
        
        - max_length: self-explanitory
        
        - characters_allowed: expects a tuple of strings with individual characters. Numbers are expected to be represented as strings too,
        such as: ("a", "b", "c", "1", "2", "3")
        You may also pass the following strings:
        - "letters_digits" to automatically allow just ascii letters and digits (no spaces).
        - "letters" to automatically allow just ascii letters with spaces
        - "digits" to allow numbers only
        
        - disallow_numbers_before_text: bool value to specify whether numbers should be allowed before text (such as 123username).
        Set to True to disallow.
        
        - auto_caps: bool value to indicate whether the newly inserted text should automatically be set to uppercase.
        """
        
        ttk.Entry.__init__(self, master, **kw)
        
        # If characters_allowed is None, then all characters will be allowed.
        
        
        # From: https://stackoverflow.com/questions/4140437/interactively-validating-entry-widget-content-in-tkinter
        
        # valid percent substitutions (from the Tk entry man page)
        # note: you only have to register the ones you need; this
        # example registers them all for illustrative purposes
        #
        # %d = Type of action (1=insert, 0=delete, -1 for others)
        # %i = index of char string to be inserted/deleted, or -1
        # %P = value of the entry if the edit is allowed
        # %s = value of entry prior to editing
        # %S = the text string being inserted or deleted, if any
        # %v = the type of validation that is currently set
        # %V = the type of validation that triggered the callback
        #      (key, focusin, focusout, forced)
        # %W = the tk name of the widget
        
        self.max_length = max_length
        
        if characters_allowed == "letters_digits":
            characters_allowed = ascii_letters + digits
            
        elif characters_allowed == "letters":
            characters_allowed = ascii_letters + (" ") # All letters + a space
            
        elif characters_allowed == "digits":
            characters_allowed = digits
        
        
        # Specific types of characters allowed?
        self.characters_allowed = characters_allowed
    
        # Disallow numbers before text?
        self.disallow_numbers_before_text = disallow_numbers_before_text
        
        # Make sure the characters that are allowed are only specified as strings,
        # because when we use 'not in' or 'in', it can only check strings.
        if characters_allowed and isinstance(characters_allowed, tuple):
            for letter in characters_allowed:
                if not isinstance(letter, str):
                    raise ValueError(f"characters_allowed must contain only strings. An invalid value of {letter} was found.")            
            
        # If we're disallowing numbers before text (such as: 123username), then make sure
        # that the characters allowed contains at least one digit.
        if disallow_numbers_before_text and characters_allowed:
            for letter in characters_allowed:
                if letter in digits:
                    break
            else:
                raise ValueError("disallow_numbers_before_text is True, but characters_allowed does not contain any digits.")
            
            
        # Automatically set newly inserted text to uppercase? (bool)
        self.auto_caps = auto_caps
   
        self.v_entry = tk.StringVar(self.winfo_toplevel())
        self.configure(textvariable=self.v_entry)   
        self.v_entry.trace_add("write", self.set_uppercase)
   
        validation = (self.register(self.on_validate),
                      '%d', '%i', '%P', '%s', '%S', '%v', '%V', '%W')
        
        self.configure(validate="key", validatecommand=validation)
        
    def set_uppercase(self, *args):
        if self.auto_caps:
            self.v_entry.set(self.v_entry.get().upper())

        
    def on_validate(self, d, i, P, s, S, v, V, W):

        # If max_length has been specified, make sure what will be displayed
        # won't exceed the length limit. If it will exceed the limit, return False.
        if self.max_length and len(P) > self.max_length:
            return False
        
        
        elif self.disallow_numbers_before_text:
            
            # If a number will show up before any text, don't allow it.
            # Example: don't allow: 123username, but allow username123
            text_found = False
            for letter in P:
                if letter in ascii_letters:
                    text_found = True
                elif letter in digits and not text_found:
                    return False
                
                
        
        # Allow only specific characters?
        if self.characters_allowed:
            
            # 'S' might be a single string or a full word. It'll be a single string
            # if the user is typing in the widget. It'll be a full word if the .insert method was
            # used to insert a whole word. So either way, we loop through the characters, even if it's just one character.
            for new_char in S:
                
                if new_char not in self.characters_allowed:
                    return False        
        
        return True
        
    def configure(self, cnf=None, **kw):

        # We will merge cnf with **kw, so we must make sure
        # that cnf is not None when we're doing that.
        if not cnf:
            cnf = {}        
                 

        args_combined: Dict = {**cnf, **kw}
        
        
        
        max_length = args_combined.get("max_length")
        if max_length:
            max_length = int(max_length)
            
            self.max_length = max_length
            
            
    
        auto_caps = args_combined.get("auto_caps")
        if auto_caps:
            auto_caps = bool(auto_caps)
            
            self.auto_caps = auto_caps
            
    
        characters_allowed = args_combined.get("characters_allowed")    
        if characters_allowed:
            if characters_allowed == "letters_digits":
                characters_allowed = ascii_letters + digits
                
            elif characters_allowed == "letters":
                characters_allowed = ascii_letters + (" ") # All letters + a space
                
            elif characters_allowed == "digits":
                characters_allowed = digits
            
            
            if self.characters_allowed:
                self.characters_allowed += characters_allowed
            else:
                self.characters_allowed = characters_allowed
            
    
        additional_allowed_characters = args_combined.get("additional_allowed_characters")
        if additional_allowed_characters:
            
            if not self.characters_allowed:
                self.characters_allowed = additional_allowed_characters
            else:
                self.characters_allowed += additional_allowed_characters

        
    
        disallow_numbers_before_text = args_combined.get("disallow_numbers_before_text")
        if disallow_numbers_before_text:
            disallow_numbers_before_text = bool(disallow_numbers_before_text)
            
            self.disallow_numbers_before_text = disallow_numbers_before_text
            

        if "max_length" in args_combined.keys():
            del args_combined["max_length"]
        
        if "auto_caps" in args_combined.keys():
            del args_combined["auto_caps"]
            
        if "characters_allowed" in args_combined.keys():
            del args_combined["characters_allowed"]
            
        if "disallow_numbers_before_text" in args_combined.keys():
            del args_combined["disallow_numbers_before_text"]

        if "additional_allowed_characters" in args_combined.keys():
            del args_combined["additional_allowed_characters"]

        # Continue to run the standard configure method on the widget.
        return ttk.Entry.configure(self, args_combined)        
        
