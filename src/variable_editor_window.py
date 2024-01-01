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
from tkinter import messagebox

import pygubu
import tkinter as tk
from treeview_edit_widget import TreeviewEdit
from project_snapshot import ProjectSnapshot
from input_string_window import InputStringWindow


PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "variable_editor_window.ui"


class VariableEditorWindow:
    def __init__(self, master):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)

        self.master = master

        # Main widget
        self.mainwindow = builder.get_object("variable_editor_window", master)
        builder.connect_callbacks(self)
        
        self.treeviewedit1: TreeviewEdit
        self.treeviewedit1 = builder.get_object("treeviewedit1")
        
        # Vertical scrollbar widget
        self.sb_vertical = builder.get_object("sb_vertical")
        
        # Connect the vertical scrollbar to the treeview widget.
        self.sb_vertical.configure(command=self.treeviewedit1.yview)
        self.treeviewedit1.configure(yscrollcommand=self.sb_vertical.set)
        
        # The method that the treeview widget will use to validate
        # new values being edited when a cell is double-clicked.
        self.treeviewedit1.validation_method = self.validate_variable_name
        
        # Create and show the treeview columns
        column_names = ("variable_name", "value")
        self.treeviewedit1.configure(columns=column_names,
                                     show="headings")
        self.treeviewedit1.heading("variable_name", text="Variable Name")
        self.treeviewedit1.heading("value", text="Value")
        
        # Set the max length limits for both the Variable name column ("#0")
        # and the variable value column (column name: "value")
        self.treeviewedit1.column_set_value_length_limit(column_name="variable_name",
                                                         max_length=40)
        
        self.treeviewedit1.column_set_value_length_limit(column_name="value",
                                                         max_length=500)
        
        # Don't allow blank variable names
        self.treeviewedit1.column_add_disallow_blank_values(column_name="variable_name")
        
        self.populate_treeview()
        
        self.mainwindow.transient(self.master)
        self.mainwindow.grab_set()

        self.mainwindow.wait_window(self.mainwindow)
        
    def validate_variable_name(self,
                               column_name: str,
                               variable_name: str,
                               original_name: str = None) -> bool:
        """
        Check whether the variable name contains any disallowed letters
        and check whether the variable name already exists in the treeview.
        
        Arguments:
        
        - column_name: the internal column name to check rules for,
        such as "#0" or "products", etc.
        
        - value: the string to check (new text wanting to be inserted).
        
        - original_name: the text that was there prior to being edited (if any).
        If it's a new insert, this will be None. We use this to compare
        to the new text, so that if they're both the same, it will
        automatically validate it.
        
        Return True if the validation passes, or False if otherwise.
        """
        
        # Is the new variable name the same as the old variable name?
        # Consider it as OK to use.
        
        # Is there an old name (there may not be, because it
        # could be a new variable being made)
        if original_name:
            # There is an old name.
            if variable_name == original_name.lower():
                return True
        
        # Key: internal column name, such as "#0" or "products"
        # Value: string of characters to disallow or None
        columns_disallow_characters = {"variable_name": r"\/,()$:<> "}        
        
        # Any letters to disallow in the given column?
        disallow_in_column = columns_disallow_characters.get(column_name)

        if disallow_in_column:
            for letter_disallowed in disallow_in_column:
                if letter_disallowed in variable_name:
                    
                    # For the sentence.
                    if letter_disallowed == " ":
                        letter_disallowed = "A space"
                    else:
                        letter_disallowed = f"'{letter_disallowed}'"
                    
                    messagebox.showwarning(parent=self.mainwindow, 
                                           title="Invalid Value",
                                           message=f"{letter_disallowed} cannot be used in a variable name.")
    
                    return False
        
        # Does the variable name already exist in the treeview widget?
        # (do a case sensitive search)
        for item_iid in self.treeviewedit1.get_children():
            item_detail = self.treeviewedit1.item(item=item_iid)
            
            # Get the current variable name in the treeview.
            treeview_variable_name = item_detail.get("values")[0]
            
            # Does the variable name already exist?
            if treeview_variable_name == variable_name:
  
                # Tell the user that the variable already exists.
                messagebox.showwarning(parent=self.mainwindow,
                                       title="Already exists",
                                       message=f"Variable '{variable_name}' already exists.")
                    
                return False

        return True    
        
    def on_new_variable_button_clicked(self):
        """
        Ask for a new variable name in a pop-up input window
        and add the variable to a new row in the treeview widget.
        """

        existing_text = None
        keep_checking = True
        
        while keep_checking:
            user_input_window =\
                InputStringWindow(master=self.master,
                                  max_character_length=40,
                                  title="New Variable",
                                  msg="Enter a new variable name below:",
                                  prefill_entry_text=existing_text)
            
            
            if user_input_window.user_input is not None:
                # Remove surrounding spacing
                user_input_window.user_input =\
                    user_input_window.user_input.strip()
            
            if not user_input_window.user_input:
                return

            new_variable_name = user_input_window.user_input
            
            allow_name =\
                self.validate_variable_name(column_name="variable_name",
                                            variable_name=new_variable_name)                
            
            if allow_name:
                keep_checking = False
            else:
                existing_text = user_input_window.user_input
            
        item_iid =\
            self.treeviewedit1.insert(parent="",
                                      index=tk.END,
                                      values=(user_input_window.user_input, ""))
 
        # Select the newly-added variable in the treeview widget.
        self.treeviewedit1.see(item=item_iid)
        self.treeviewedit1.selection_set(item_iid)
        
        # So we know that the user has made changes in the treeview widget
        # and it needs saving if the OK button is clicked.
        self.treeviewedit1.is_dirty = True
        
    def on_remove_variable_button_clicked(self):
        """
        Remove the selected variables from the treeview item
        and mark the treeview as dirty so we know that the
        contents have been changed by the user.
        """
        selected_items = self.treeviewedit1.selection()
        if not selected_items:
            return
        
        self.treeviewedit1.delete(*selected_items)
        
        # So we know that the user has made changes in the treeview widget
        # and it needs saving if the OK button is clicked.        
        self.treeviewedit1.is_dirty = True
        
    def on_cancel_button_clicked(self):
        """
        Close the variable editor window without saving the treeview's contents.
        """
        self.mainwindow.destroy()
        
    def on_ok_button_clicked(self):
        """
        Save the treeview's contents if its been changed by the user
        and then close the variable editor window.
        """
        
        # No changes made in the treeview widget? Just close the window
        # without re-saving the variables.
        if not self.treeviewedit1.is_dirty:
            self.mainwindow.destroy()
            return
        
        # Changes were made to the treeview widget
        # by the user. So save the changes to the 'variables' dictionary.
        
        ProjectSnapshot.variables.clear()
        
        # Iterate the treeview widget.
        for item_iid in self.treeviewedit1.get_children():
            item_details = self.treeviewedit1.item(item_iid)
            variable_name, variable_value = item_details.get("values")
        
            ProjectSnapshot.variables[variable_name] = variable_value
            
        # Sort the variables dictionary by key
        # so that it's sorted alphabetically when the treeview shows the 
        # variables the next time the variables window is shown.
        ProjectSnapshot.sort_variables_dictionary()
        
        self.master.event_generate("<<SaveNeeded>>")
        
        self.mainwindow.destroy()
        
    def populate_treeview(self):
        """
        Populate the treeview with variable names and values.
        """
        if not ProjectSnapshot.variables:
            return
    
    
        for variable_name, variable_value in ProjectSnapshot.variables.items():
            
            self.treeviewedit1.insert(parent="",
                                      index=tk.END,
                                      values=(variable_name, variable_value))
        
        