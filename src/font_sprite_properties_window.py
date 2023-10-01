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

import pathlib
import pygubu
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from project_snapshot import ProjectSnapshot, SubPaths, FontSprite, LetterProperties
from input_trim_values_window import InputTrimValuesWindow
from entrylimit import EntryWithLimit
from pathlib import Path
from PIL import Image, ImageTk
from typing import Tuple, List
from enum import Enum, auto


PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "font_sprite_window.ui"




class IndividualSprite(ttk.Frame):
    """
    Holds the information for one font sprite (for example a single letter).
    Detailed example: the letter 'A', its rect size (not pygame rect, just
    our own defined rect, which is: left, upper, right, lower)
    """
    def __init__(self, master, image, rect_position: Tuple, text: str, **kw):
        """
        Arguments:
        
        image: a Pillow-style image (not PhotoImage)
        
        rect_position: a tuple like this (5,5,5,5), which means:
        (left, upper, right, lower). This represents the 'cut-out' size
        of the sprite from the full-size image.
        
        text: the text that the entry should display (if any)
        
        This is used in the font spritesheet window. Each font letter
        that gets displayed in the font spritesheet window will have
        this object displayed.
        """

        super().__init__(master, **kw)
        self.frame_inner = ttk.Frame(self, name="frame_inner")
        self.frame_inner.configure(height=200, width=200)
        self.lbl_letter_image = ttk.Label(self.frame_inner)
        self.lbl_letter_image.configure(font="TkDefaultFont", compound="image")
        self.lbl_letter_image.grid(column=0, row=0)
        self.entry_letter = EntryWithLimit(master=self.frame_inner,
                                           max_length=1)

        if text and len(text) == 1:
            self.entry_letter.insert(0, text)
            
        self.entry_letter.configure(width=2)
        self.entry_letter.grid(column=0, row=1)

        self.frame_inner.grid(column=0, pady="0 10", row=0, sticky="nsew")
        self.frame_inner.columnconfigure(0, weight=1)

        # Show the font letter
        self.lbl_letter_image.image = ImageTk.PhotoImage(image)
        self.lbl_letter_image.configure(image=self.lbl_letter_image.image)

        # (left, upper, right, lower) position of the sprite,
        # relative to the full size font spritesheet.
        self.rect_position = rect_position
        
    def get_text(self) -> str | None:
        """
        Return the text that's in the entry widget or None
        if there is no text. 
        """
        text = self.entry_letter.get()

        if not text:
            return

        return text
    
    def get_rect(self) -> Tuple | None:
        """
        Return the tuple contains the 'cut-out' size of this individual sprite
        in the format of: (left, upper, right, lower).
        """
        return self.rect_position


class RuleCheckResult(Enum):
    PREVIOUS_LETTER_ALREADY_EXISTS = auto()
    REGARDLESS_RULE_ALREADY_EXISTS = auto()
    RULE_NOT_FOUND = auto()
    

class FontSpriteWindow:
    def __init__(self,
                 master,
                 font_sprite_name: str,
                 font_file_name: str,
                 font_sprite_details: FontSprite):

        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)

        self.master = master

        self.font_sprite_name = font_sprite_name
        self.font_file_name = font_file_name
        self.font_sprite_details = font_sprite_details

        self.window = builder.get_object("font_spritesheet_window",
                                         master=master)
        
        self.main_canvas = builder.get_object("main_canvas")
        
        self.treeview_trim: ttk.Treeview = builder.get_object("treeview_trim")
        self.frame_cutoff_buttons: ttk.Frame = builder.get_object("frame_cutoff_buttons")

        self.sb_v: ttk.Scrollbar
        self.sb_h: ttk.Scrollbar
        
        self.sb_v = builder.get_object("sb_v")
        self.sb_h = builder.get_object("sb_h")

        self.builder.connect_callbacks(self)
        

        self.v_width = self.builder.get_variable("v_width")
        self.v_height = self.builder.get_variable("v_height")
        
        self.v_padding_letters = self.builder.get_variable("v_padding_letters")
        self.v_padding_lines = self.builder.get_variable("v_padding_lines")
        self.v_detect_letter_edges = self.builder.get_variable("v_detect_letter_edges")

        self.main_canvas.configure(yscrollcommand=self.sb_v.set)
        self.sb_v.configure(command=self.main_canvas.yview)
        
        self.main_canvas.configure(xscrollcommand=self.sb_h.set)
        self.sb_h.configure(command=self.main_canvas.xview)

        self._set_variables()

        # When the individual sprite objects are added to the canvas widget
        # using .create_window(), a unique ID is returned & added to this list.
        # This is how we know which object is which when we're enumerating
        # the canvas' widgets.
        self.canvas_window_ids = []

        # Disable the widgets related to letter trim settings
        # because the font spritesheet must be split first using
        # trim settings.
        self.disable_enable_trim_letter_widgets(enable=False)
        
        # Populate individual letter trim values, if any.
        self._populate_treeview_trim_values()
        
        # Bind double-click to treeview widget so when it's double-clicked,
        # we'll assume the user wants to edit the selected row.
        self.treeview_trim.bind("<Double-1>", self.on_treeview_double_clicked)
        
        self.window.transient(self.master)
        self.window.wait_visibility()
        self.window.grab_set()


        self.window.wait_window(self.window)

    def on_treeview_double_clicked(self, event):
        element_double_clicked = self.treeview_trim.identify_region(event.x, event.y)
        
        if element_double_clicked in ("tree", "cell"):
            self.on_edit_letter_trim_button_clicked()
        

    def disable_enable_trim_letter_widgets(self, enable: bool):
        """
        Disable or enable the trim treeview widget and the buttons
        used for adding/removing trim values.
        
        Purpose: the trim widgets should only be available
        after the font spritesheet has been split because
        otherwise the letters' trim settings won't save properly.
        
        Arguments:
        
        - enable: (bool) set to True to enable the widgets or False to
        disable the widgets related to letter trim settings.
        """
        
        if enable:
            state_value = ["!disabled"]
        else:
            state_value = ["disabled"]

        # Disable or enable the treeview widget.
        self.treeview_trim.state(state_value)

        # Disable or enable the buttons, 'Add, Edit, Remove'
        for w in self.frame_cutoff_buttons.winfo_children():
            w.state(state_value)
        
    def _populate_treeview_trim_values(self):
        """
        Populate the treeview with the previous letters
        and trim values.
        """

        self.treeview_trim.delete(*self.treeview_trim.get_children())
        
        # Get the font properties for this entire font spritesheet
        # The font properties will have info like letters and rects
        font_properties: FontSprite
        font_properties = ProjectSnapshot.font_sprite_properties\
            .get(self.font_sprite_name)
        
        letter: str
        letter_properties: LetterProperties
        for letter, letter_properties in font_properties.letters.items():
            # letter_properties contains the crop_rect and the previous letter
            # rules and trim values.

            # Insert just the letter row for now, if there are any
            # kerning rules for it.
            if not letter_properties.kerning_rules:
                continue
            
            icon_column_iid =\
                self.treeview_trim.insert(parent="",
                                          index=tk.END,
                                          text=letter)

            
            # Now go through all the letter properties for this letter
            # and add the previous letter rules.
            # Example: [("abcd", -3, 0), ("efgh", -5, 3)]
            for kerning_rules in letter_properties.kerning_rules:

                previous_letters = kerning_rules[0]
                left_trim = kerning_rules[1]
                right_trim = kerning_rules[2]

                # Add sub-items (previous letters, left_trim, right_trim)
                self.treeview_trim.insert(parent=icon_column_iid,
                                          index=tk.END,
                                          values=(previous_letters,
                                                  left_trim,
                                                  right_trim))
                
    def add_letter_to_trim_treeview(self,
                                    parent: str,
                                    letter: str,
                                    left_trim: int = None,
                                    right_trim: int = None,
                                    disregard_previous_letter: bool = False,
                                    previous_letters: str = None):
        """
        Add the given letter and trim values to the trim treeview widget.
        
        Arguments:
        
        - letter: (str) a single letter, such as 'A'
        - left_trim: (int) a negative or positive numeric value
        - right_trim: (int) a negative or positive numeric value
        - disregard_previous_letter: (bool) whether to have previous rules
        (False) or not (True)
        - previous_letters: (str) characters (such as 'lmnop', no delimiter)
        """

        # First time we're adding this letter? Add the parent item first.
        if not parent:
            parent = self.treeview_trim.insert(parent="",
                                               text=letter,
                                               index=tk.END)

        if disregard_previous_letter:
            previous_letters = "(Any)"

        # Add the sub-item with the previous letter details.
        self.treeview_trim.insert(parent=parent,
                                  index=tk.END,
                                  values=(previous_letters,
                                          str(left_trim),
                                          str(right_trim)))

    def previous_letter_rule_exists(
            self,
            letter: str,
            new_previous_letters: str,
            disregard_previous_letters: bool,
            ignore_specific_item_iid: str = None) -> RuleCheckResult:
        """
        Based on the given letter in this method, check if the letter's
        previous letter rules (in the font's letters dictionary)
        already contains any of the given previous letters
        (if previous letters is supplied).
        
        If we don't need to look at the previous letter rules
        (when disregard_previous_letters == True), then check
        if this rule already exists for this letter. Return True
        if this rule already exists.
        
        Arguments:
        
        - letter: (str) the single string character that we're looking at.
        
        - new_previous_letters: (str) or None - the previous letters that are
        requested to be added to this letter. We need to check if any of
        the previous letters already exist (letter by letter).
        
        - disregard_previous_letters: (bool) - True if the user wants to
        create a rule that the trim settings for this letter should apply
        regardless of what the previous letters are.
        
        Return: True if we're requesting to add the rule, 'Regardless of
        previous letter', but that rule already exists for the given letter.
        
        Return: a single string character that already exists if at least one
        of the given previous letters already exists in the previous letter
        rules for this letter.
        
        ignore_specific_item_iid: the selected treeview item iid when a rule is
        being edited. We should ignore this item iid in the previous-rule checks
        so that we don't check against itself.
        
        Return: (tuple) - (RuleCheckResult, individual letter that already exists).
        
        """
        # Check the treeview for the existence of the new rule,
        # because the user might have added a rule which hasn't been saved
        # to the rules dictionary yet (ie: the user may not have clicked
        # 'OK' yet to save all the rule changes).
        
        # Iterate through top-level item ids
        # The top levels item ids don't have sub-items.
        for item_id in self.treeview_trim.get_children():
            
            # Get the 'text' value of the item we're on.
            item_details = self.treeview_trim.item(item=item_id)
            text = item_details.get("text")
            
            # Not the letter we're looking for? Check the next iteration.
            if text != letter:
                continue
            
            # Check the sub-items of the current item we're on.
            # We're specifically interested in the Previous Letters column.
            for sub_item_iid in self.treeview_trim.get_children(item=item_id):

                # Is the user editing an existing rule? If so,
                # the selected item in the treeview widget will be
                # in 'ignore_specific_item_iid', so don't check the item
                # for previous rules, because otherwise we'd be checking
                # against itself.
                if ignore_specific_item_iid:
                    # We should ignore this item.

                    # Are we iterating over the item iid that should be
                    # ignored?
                    if sub_item_iid == ignore_specific_item_iid:
                        continue

                # Get a dictionary which contains the sub-item values.
                sub_item_details = self.treeview_trim.item(item=sub_item_iid)

                # Get the sub-item rules for the item to see if any of the
                # new rules already exist in the previous rules.
                existing_previous_letters = sub_item_details.get("values")[0]

                # Should the trim rules apply regardless of the previous letter?
                if disregard_previous_letters:
                    # Yes, apply the trim rules regardless of the previous letter.

                    # Check if there is already a 'regardless' rule for this letter.
                    if existing_previous_letters == "(Any)":
                        return (RuleCheckResult.REGARDLESS_RULE_ALREADY_EXISTS, None)

                else:
                    # There are specific previous letter rules to follow.

                    # Iterate individual letters in the new letters.
                    for individual_letter in new_previous_letters:
    
                        # Does at least one of the new letters already exist?
                        if individual_letter in existing_previous_letters:
                            return (RuleCheckResult.PREVIOUS_LETTER_ALREADY_EXISTS, individual_letter)
                        
        return (RuleCheckResult.RULE_NOT_FOUND, None)

    def letter_exists_in_treeview(self, letter: str) -> str:
        """
        Check whether the given single letter exists in the trim treeview
        or not.
        
        Arguments:
        - letter: (str) a single letter, such as 'A'
        
        Return: the item iid if the letter exists in the trim treeview widget,
        specifically in the icon column or return an empty string if not found.
        """

        if not letter:
            return

        # Enumerate over all parent (root) item iids.
        for item_iid in self.treeview_trim.get_children():

            # Get the text of the tree column (the first column)
            item_text = self.treeview_trim.item(item_iid).get("text")
            
            if item_text == letter:
                return item_iid
            
        else:
            return ""

    def _set_variables(self):
        """
        Set the Tk variables from the font sprite details so that
        the font sprite details reflect in the GUI.
        """
        self.v_width.set(self.font_sprite_details.width)
        self.v_height.set(self.font_sprite_details.height)
        self.v_padding_letters.set(self.font_sprite_details.padding_letters)
        self.v_padding_lines.set(self.font_sprite_details.padding_lines)
        self.v_detect_letter_edges.set(self.font_sprite_details.detect_letter_edges)

    def on_add_letter_trim_button_clicked(self):
        """
        Add a letter and its trim values to the treeview widget,
        but only if the letter isn't already in the treeview widget.
        """

        letter_width = self.v_width.get() - 1

        keep_asking = True
        letter = ""
        left = 0
        right = 0
        previous_letters = ""
        check_previous_letter = False
        
        while keep_asking:
            trim_window = InputTrimValuesWindow(master=self.window,
                                                _from=-letter_width,
                                                _to=letter_width,
                                                prefill_previous_letters=previous_letters,
                                                prefill_check_previous_letter=check_previous_letter,
                                                prefill_left_value=left,
                                                prefill_right_value=right,
                                                prefill_letter_value=letter)

            letter = trim_window.user_input_letter
            left = trim_window.user_input_left
            right = trim_window.user_input_right
            previous_letters = trim_window.user_input_previous_letters
            check_previous_letter = trim_window.user_input_check_previous_letter

            # No letter given? return
            # (a blank space will be evaluated as True,
            # which is OK in our case)
            if not letter:
                break

            # Get the letter's iid in the treeview widget (if it's there).
            letter_item_iid = self.letter_exists_in_treeview(letter=letter)

            if not check_previous_letter:
                disregard_previous_letters = True
            else:
                disregard_previous_letters = False

            # Does the new rule already exist for the letter? Continue the loop
            if self._rule_has_issues(letter=letter,
                                 new_previous_letters=previous_letters,
                                 disregard_previous_letters=disregard_previous_letters,
                                 left_trim=left,
                                 right_trim=right):
                continue

            # The rule is new and doesn't already exist.
            keep_asking = False

            self.add_letter_to_trim_treeview(parent=letter_item_iid,
                                             letter=letter,
                                             left_trim=left,
                                             right_trim=right,
                                             disregard_previous_letter=disregard_previous_letters, 
                                             previous_letters=previous_letters)
            
    def _rule_has_issues(self,
                     letter: str,
                     new_previous_letters: str,
                     disregard_previous_letters: bool,
                     left_trim: int,
                     right_trim: int,
                     ignore_specific_item_iid: str = None,) -> bool:
        """
        Make sure previous letter(s) have been specified if the radio button
        for checking previous letters is set.
        
        Then check whether the given new-previous-rules already exist
        for the given letter or not.
        
        Also check whether the new rule contains duplicate new previous letters.
        For example: if the new previous-letters are "test", there are 2 t's
        so don't allow that.
        
        Arguments:
        
        - letter: single character parent letter (such as 'a')
        
        - new_previous_letters: string of previous letters to check (ie: 'abc')
        
        - disregard_previous_letters: if True, it means to apply the trim
        rules regardless of the previous letter.
        
        - left_trim: the left kerning value (int). We need this to check
        for both zero left/right.
        
        - right_trim: the right kerning value (int). We need this to check
        for both zero left/right.
        
        - ignore_specific_item_iid: (optional) item iid of the selected item in
        the treeview widget. This will have a value if an existing item iid
        rule is being edited.
        
        Return: True if the rule already exists, otherwise False.
        """

        # Type-hints
        result: RuleCheckResult
        letter_that_exists: str
        
        # If the option, 'Only when the previous letter is...' is selected,
        # make sure previous letters have been typed.
        if not disregard_previous_letters:
            if not new_previous_letters:
                title = "Previous letter(s) missing"
                msg = "Type one or more letters in the text field."
                messagebox.showerror(parent=self.window, title=title,
                                     message=msg)

                return True

        # Are any of the new previous-letters duplicated?
        # For example: 'aba', there are 2 a's, so don't allow that.
        previous_letters_set = set(new_previous_letters)

        if len(previous_letters_set) != len(new_previous_letters):
            messagebox.showwarning(
                parent=self.window,
                title=f"Duplicate Letter(s)",
                message=f"One or more previous letters is repeated.\n"
                "Only unique letters are allowed.")
            return True

        # Make sure the left and right trims are not zero,
        if not any((left_trim, right_trim)):
            messagebox.showwarning(
                parent=self.window,
                title=f"Missing left/right values",
                message=f"No left/right kerning values have been specified.")
            return True

        # Do any of the single characters in the new-previous-rules
        # already exist?
        result, letter_that_exists =\
            self.previous_letter_rule_exists(
                letter=letter,
                new_previous_letters=new_previous_letters,
                disregard_previous_letters=disregard_previous_letters,
                ignore_specific_item_iid=ignore_specific_item_iid)

        if result == RuleCheckResult.PREVIOUS_LETTER_ALREADY_EXISTS:
            messagebox.showwarning(
                parent=self.window, 
                title=f"{letter_that_exists} Already Exists",
                message=f"'{letter_that_exists}' already exists as a previous-letter rule for letter: {letter}")
            return True

        elif result == RuleCheckResult.REGARDLESS_RULE_ALREADY_EXISTS:
            messagebox.showwarning(
                parent=self.window,
                title="Rule Already Exists",
                message="A rule to disregard previous letters already exists.")
            return True

        else:
            return False
        
    def _delete_rule_item(self, item_iid: str):
        """
        Delete the specified item_iid (rule) from the rules treeview widget.
        
        If the parent (letter) of this rule has more than 1 rule,
        just delete the specified rule.
        
        If the parent of this rule (letter) has only 1 rule, delete
        the parent, which will delete the specified rule too.
        """
        
        # Is it a sub-item (rules row) or a parent (letter)
        parent_iid = self.treeview_trim.parent(item_iid)

        if parent_iid:
            # It's a sub-item
            sub_item = True
        else:
            # It's a parent row
            sub_item = False

        if sub_item:
            # If it's a sub-item being deleted, delete the parent too if this
            # is the only sub-item.
            children_count = len(self.treeview_trim.get_children(parent_iid))

            # If the item has more than 1 child (so the item is a parent)
            # then just delete this one sub-item (don't delete the parent).
            if children_count > 1:
                # Just delete the single sub-item
                self.treeview_trim.delete(item_iid)
            else:
                # Delete the parent, because the sub-item is the only child.
                self.treeview_trim.delete(parent_iid)
        else:
            # Delete the selected item (which is a parent),
            # because that's what is highlighted.
            self.treeview_trim.delete(item_iid)

    def on_edit_letter_trim_button_clicked(self):
        """
        A treeview cell has been double-clicked.
        
        Edit the highlighted letter's trim values in the treeview widget
        by opening an edit window.
        """

        # Get the currently selected item
        item_iid = self.treeview_trim.selection()

        # Nothing selected? return
        if not item_iid:
            return

        # Get the first selection
        item_iid = item_iid[0]

        # Get the parent of the item
        parent_iid = self.treeview_trim.parent(item_iid)

        # Don't allow a root/letter row to be edited
        # It might be something worth adding in the future.
        if not parent_iid:
            # The selected item is a parent, don't allow it to be edited.
            return

        # Get the parent iid's details dictionary
        # so we can get the letter.
        parent_item_details = self.treeview_trim.item(parent_iid)
            
        # Get the text (letter) of the selected item
        letter = parent_item_details.get("text")

        # Get the list of sub-item values
        details = self.treeview_trim.item(item_iid)
        item_values = details.get("values")
        
        previous_letters = item_values[0]
        if previous_letters == "(Any)":
            previous_letters = ""
            check_previous_letters = False
        else:
            check_previous_letters = True
            
        left = item_values[1]
        right = item_values[2]

        letter_width = self.v_width.get() - 1

        keep_asking = True

        while keep_asking:
            trim_window = InputTrimValuesWindow(master=self.window,
                                                _from=-letter_width,
                                                _to=letter_width,
                                                prefill_left_value=left,
                                                prefill_right_value=right,
                                                prefill_letter_value=letter,
                                                prefill_previous_letters=previous_letters,
                                                prefill_check_previous_letter=check_previous_letters,
                                                edit_mode=True)

            new_previous_letters = trim_window.user_input_previous_letters
            check_previous_letters = trim_window.user_input_check_previous_letter
            left = trim_window.user_input_left
            right = trim_window.user_input_right
            

            # The user cancelled the edit?
            if new_previous_letters is None:
                return
            
            # If the left/right are both zero, remove the rule from
            # the treeview, because it's the same as not having a rule.
            if left == 0 and right == 0:
                self._delete_rule_item(item_iid=item_iid)
                return
            
            if not check_previous_letters:
                disregard_previous_letters = True
            else:
                disregard_previous_letters = False

            # Does the new edited rule already exist?
            rule_has_issues =\
                self._rule_has_issues(letter=letter,
                                  new_previous_letters=new_previous_letters,
                                  disregard_previous_letters=disregard_previous_letters,
                                  left_trim=left,
                                  right_trim=right, 
                                  ignore_specific_item_iid=item_iid)

            if rule_has_issues:
                continue

            if disregard_previous_letters:
                new_previous_letters = "(Any)"
            
            # Edit the row/item.
            self.treeview_trim.item(item_iid,
                                    values=(new_previous_letters, left, right))

            keep_asking = False

    def on_remove_letter_trim_button_clicked(self):
        """
        Remove the selected trim letter setting in the treeview widget.
        """

        # Get the selected item
        selected_item_iid = self.treeview_trim.selection()

        # Nothing selected? return
        if not selected_item_iid:
            return

        # Confirm with the user
        result = messagebox.askyesno(parent=self.window,
                                     title=f"Delete row?",
                                     message=f"Delete the selected row?")
        
        if not result:
            return

        # Delete the selected row
        self._delete_rule_item(selected_item_iid)

    def on_cancel_button_clicked(self):

        self.window.destroy()

    def on_ok_button_clicked(self):
        """
        Make sure each letter is assigned to an image just once.
        
        Then get the rect sizes of the images and the kerning values
        and save them to the font's properties.
        """

        try:
            width = self.v_width.get()
            height = self.v_height.get()
            padding_letters = self.v_padding_letters.get()
            padding_lines = self.v_padding_lines.get()
            detect_letter_edges = self.v_detect_letter_edges.get()

        except tk.TclError:
            messagebox.showwarning(parent=self.window,
                                   title="Check Fields",
                                   message="There seems to be a problem with"
                                   " the given number(s).\n\nPlease check to"
                                   " make sure they are actual numbers.")
            return
        
                

        font_properties = FontSprite(width=width, height=height,
                                     padding_letters=padding_letters,
                                     padding_lines=padding_lines,
                                     detect_letter_edges=detect_letter_edges)

        final_letters = []
        final_rects = []
        final_kerning_rules = []
        
        # Get all the inputted letters and their rects
        for idx, window_id in enumerate(self.canvas_window_ids):

            # Get the widget name (str)
            individual_sprite: str = self.main_canvas.itemcget(window_id,
                                                               "window")

            # Get the object from the name
            individual_sprite: IndividualSprite
            individual_sprite = \
                self.main_canvas.nametowidget(individual_sprite)

            letter = individual_sprite.get_text()
            rect = individual_sprite.get_rect()
            
            if not letter:
                continue

            # Make sure the letter is assigned to an image just once.
            if letter in final_letters:
                messagebox.showwarning(parent=self.window,
                                       title=f"'{letter}' Already Assigned",
                                       message=f"'{letter}' is already " \
                                       "assigned.\n\n"\
                                       "Each letter can only be assigned once.")
                return

            # Get the previous letters and left and right trims of the letter.
            # Will be returned as a list of tuples.
            # Example: [('abc', -4, -2), ('efg', -1, 0)]
            trim_values = self._get_trim_values(letter=letter)

            # Append the left/right trim to the rect, specifically the left
            # and right of the rect.
            # Reminder: a rect looks like this:
            # (left, upper, right, lower)
            # So the final rect will look like this:
            # (left, upper, right, lower, left_trim, right_trim, previous_letters_to_trim_for)
            #rect = (rect[0],
                    #rect[1],
                    #rect[2],
                    #rect[3],
                    #left_trim,
                    #right_trim,
                    #previous_letters)

            # Append the previous_letters and left/right trim to the rect.
            # Reminder: a rect looks like this:
            # (left, upper, right, lower, [(previous letters, left_trim, right_trim]), (previous_letters, left_trim, right_trim)]
            rect = (rect[0],
                    rect[1],
                    rect[2],
                    rect[3])

            final_letters.append(letter)
            final_rects.append(rect)
            final_kerning_rules.append(trim_values)

        # Add the letters to the properties dictionary,
        # including the crop size and any kerning rules.
        for letter, rect, kerning_rules in zip(final_letters, final_rects, final_kerning_rules):

            # Update the property
            font_properties.add_letter(letter=letter,
                                       rect_crop=rect,
                                       kerning_rules=kerning_rules)

            # Add or Update the property for the font sprite.
            ProjectSnapshot.font_sprite_properties[self.font_sprite_name] = \
                font_properties
        
        self.window.destroy()


    def _get_trim_values(self, letter: str) -> List[Tuple]:
        """
        Get the left and right trim values of the specified letter
        from the treeview widget, including the previous letters to trim for.
        
        Arguments:
        
        - letter: (str) a single letter to find in the treeview widget.
        
        Return: a list of tuples
        Example: [('abc', -4, -2), ('efg', -5, 0)]
        or an empty list if the letter is not found in the treeview widget.
        """

        # Iterate the toplevel items.
        # The toplevel items don't have trimming left/right values.
        trim_values = []
        for item_iid in self.treeview_trim.get_children():

            details = self.treeview_trim.item(item_iid)

            text = details.get("text")

            if text != letter:
                continue

            for sub_item_iid in self.treeview_trim.get_children(item=item_iid):

                sub_item_details = self.treeview_trim.item(item=sub_item_iid)

                previous_letters = sub_item_details.get("values")[0]
                left_trim = sub_item_details.get("values")[1]
                right_trim = sub_item_details.get("values")[2]
                
                trim_values.append((previous_letters, left_trim, right_trim))
                
        # Previous letters, left trim, right trim
        return trim_values

    def on_split_button_clicked(self):
        
        self.main_canvas.delete(tk.ALL)
        self.canvas_window_ids.clear()

        # Get the full path to the font spritesheet image
        # on the file system.
        full_path = ProjectSnapshot.project_path / SubPaths.FONT_SPRITE_FOLDER.value / self.font_file_name
        
        if not full_path.exists():
            messagebox.showerror(parent=self.main_canvas.winfo_toplevel(), 
                                 title="File Not Found",
                                 message=f"Font spritesheet not found in:\n"
                                 f"{full_path}")
            return

        width = self.v_width.get()
        height = self.v_height.get()

        # Pillow needs this for the crop method.
        left = 0
        right = width
        upper = 0
        lower = height

        # Type-hints.
        img: Image.Image
        image_section: Image.Image
        self.main_canvas: tk.Canvas

        # Keeps track of where to place the 'windows' in the canvas widget.
        last_sprite_widget_x = 0
        last_sprite_widget_y = 0

        # Needed when doing the math for the widget/window positions
        # in the canvas widget.
        canvas_width = self.main_canvas.winfo_width()

        # Get the font properties for this entire font spritesheet
        # The font properties will have info like letters and rects
        font_properties: FontSprite = ProjectSnapshot.font_sprite_properties \
            .get(self.font_sprite_name)
        
        # Key: tuple rect_crop (0,0,0,0)
        # which is: (left, upper, right, lower)
        
        # Value: letter (str), such as 'A'
        sizes_and_letters = {}
        if font_properties and font_properties.letters:
            # font_properties.letters has the letter assignments,
            # with the letters as the key, and rect_crop as the values.
            

            # Reverse it by getting the rect_crops as the keys and letters as
            # the values. This is used for populating the entry widgets.
            # However, leave out the trim values because we're not going to
            # use them in this method, since the .crop method of the pillow
            # library can't use left/right trims (.crop is used in this method).
            sizes_and_letters = {(value.rect_crop[0], value.rect_crop[1], value.rect_crop[2], value.rect_crop[3]): key
                                 for key, value in font_properties.letters.items()
                                 if value not in sizes_and_letters}
            
        # Open the full sprite image and split the characters.
        # The width and height tell us how big each split should be.
        with Image.open(full_path) as img:

            # The full dimensions of the font spritesheet.
            full_image_width = img.width
            full_image_height = img.height

            keep_splitting = True
            while keep_splitting:

                # The 'cut-out' dimensions of this sprite/letter.
                rect_position = (left, upper, right, lower)
                
                # Get the letter assignment for the above rect position
                # (if there is a letter assignment)
                letter = sizes_and_letters.get(rect_position)
                
                # Crop the sprite from the full spritesheet
                image_section = img.crop(rect_position)

                # Create the frame and entry widget that will get shown
                # to the user so the user can type a letter assignment
                # for each sprite.
                individual_sprite = \
                    IndividualSprite(master=self.main_canvas,
                                     rect_position=rect_position,
                                     image=image_section,
                                     text=letter)

                # Show the above widget inside the canvas widget.
                widget_id = self.main_canvas.create_window(last_sprite_widget_x,
                                                           last_sprite_widget_y,
                                                           window=individual_sprite)

                # Keep a record of the window IDs so we can enumerate
                # over them later if the user clicks the OK button.
                self.canvas_window_ids.append(widget_id)

                # winfo_reqwidth() and winfo_reqheight() won't return
                # the correct values without updating idle tasks first.
                individual_sprite.update_idletasks()

                # Needed for the math to find out how much space is required
                # for the widget/window that's about to be added.
                widget_width = individual_sprite.winfo_reqwidth()
                widget_height = individual_sprite.winfo_reqheight()

                """
                Determine the position of the widget that's about to be added
                to the canvas widget.
                """
                # Is there enough horizontal room for this widget?
                if last_sprite_widget_x + (widget_width * 2) > canvas_width:
                    # There's not enough horizontal room, move it down a line.
                    last_sprite_widget_x = 0
                    last_sprite_widget_y += widget_height
                else:
                    # Yes, there is enough horizontal room.
                    last_sprite_widget_x += widget_width


                """
                Determine the next crop size in the font spritesheet
                """
                # Can we proceed by cropping another sprite towards the right?
                if full_image_width >= right + width:
                    # We can crop another sprite towards the right
                    left = right
                    right += width

                # Can we proceed down?
                elif full_image_height >= lower + height:
                    # We can crop another sprite starting on the next line.
                    upper = lower
                    lower += height
                    left = 0
                    right = width

                else:
                    # There is no more room in the full image
                    # to split, so stop splitting.
                    keep_splitting = False

        # Set the scroll region of the canvas to all so that the scroll
        # bars will detect the new area (widgets were finished being added)
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox(tk.ALL))
        
        # When it finishes adding the widgets, the positioning of the
        # horizontal scrollbar won't be exactly at the top, so this will
        # move the scrollbar position to the top.
        self.main_canvas.yview_moveto(0)

        # Enable the widgets related to trim value settings because
        # now the font spritesheet has been split.
        self.disable_enable_trim_letter_widgets(enable=True)
