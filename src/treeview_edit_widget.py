"""
Copyright 2023-2025 Jobin Rezai

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
from tkinter import ttk
from entry_limit import EntryWithLimit



class TreeviewEdit(ttk.Treeview):
    """
    A treeview widget with editable cells (by double-clicking the cells).
    
    Usage: like a regular ttk.Treeview widget, except the following
    new methods are available:
    
    - column_add_disallow_blank_values(column_name)
    Example: self.column_add_disallow_blank_values("#0")
    
    - column_set_value_length_limit(column_name, max_length)
    Example: self.column_set_value_length_limit("#0", 3)
    """
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        
        # This will eventually be the entry widget that will be used for 
        # editing treeview cells. Only one entry widget (the variable below)
        # will be shown at a time.
        self.entry_widget = EntryWithLimit(self)
        self.entry_widget.bind("<FocusOut>", self.on_focus_out)
        self.entry_widget.bind("<Escape>", self.on_escape_key_pressed)
        self.entry_widget.bind("<Return>", self.on_enter_pressed)
        self.entry_widget.bind("<KP_Enter>", self.on_enter_pressed)        
        
        # A method that will check whether a value is valid
        # to be added to a specific column in the treeview widget.
        # It takes 2 required parameters: the internal column name, 
        # and the value that wants to be added.
        self.validation_method = None
        
        # Cell values cannot be blank in these columns.
        self.columns_disallow_empty_cells = ["#0"]
        
        # Manual max lengths of values in a column (optional).
        # Key: column name (str) (not the displayable header text)
        # Value: max length (int)
        self.column_value_length_limits = {}

        # Double-click binding (left-mouse button)
        self.bind("<Double-1>", self.on_double_click)
        
        # Mouse wheel up binding
        self.bind_all("<Button-4>", self.on_focus_out)
        
        # Mouse wheel down binding
        self.bind_all("<Button-5>", self.on_focus_out)
        
        # Use the clean() method to reset this flag.
        self.is_dirty = False
        
    def clean(self):
        """
        Reset the 'is_dirty' flag.
        
        Purpose: to indiciate that the treeview's cells have not
        been modified by the user.
        """
        self.is_dirty = False
        
    def column_set_value_length_limit(self, column_name: str, max_length: int):
        """
        Set a maximum value of newly entered text for rows in a specific
        column.
        
        Arguments:
        
        - column_name: the internal column name (not the displayable header
        text) of the column we want to enforce a max length limit for.
        
        Example of column names: "#0" or "products", etc.
        
        - max_length: the max length allowed for new values.
        """
        self.column_value_length_limits[column_name] = max_length
        
    def column_add_disallow_blank_values(self, column_name: str):
        """
        Add a column name to the list of columns that should not
        allow blank cell values.
        
        Arguments:
        
        - column_name: the name of the column (not the displayable header text)
        """
        
        # Blank value? return
        if not column_name:
            return
        
        # Column already exists in the disallow list? return
        elif column_name in self.columns_disallow_empty_cells:
            return
        
        # Make sure the column name exists in the treeview widget.
        column_names = self.cget("columns")
        
        if column_name not in column_names:
            return
        
        # Add column to disallow blank values list.
        self.columns_disallow_empty_cells.append(column_name)

    def on_double_click(self, event):
        """
        Show an entry widget on top of the double-clicked cell,
        if a cell has been double-clicked in the treeview widget.
        """

        # Identify the region that was double-clicked
        region_clicked = self.identify_region(event.x, event.y)

        # We're only interested in tree and cell.
        if region_clicked not in ("tree", "cell"):
            return

        # Which item was double-clicked?
        # For example, "#0" is the first column, followed by "#1", "#2", etc.
        column = self.identify_column(event.x)
        
        # print(type(column))

        # For example, "#0" will become -1, "#1" will become 0, etc.
        column_index = int(column[1:]) - 1
        
        column_name =\
            self._get_column_name_from_index(column_index=column_index + 1)

        # For example: 001
        selected_iid = self.focus()
        
        # No selection? return
        if not selected_iid:
            return

        # This will contain both text and values from the given item iid
        selected_values = self.item(selected_iid)

        # Try to get the text of the Text column or Values column
        try:
            if column == "#0":
                selected_text = selected_values.get("text")
            else:
                selected_text = selected_values.get("values")[column_index]
        except IndexError:
            return
        
        # Make sure the selected value is a string because numbers
        # in the treeview widget are returned as int values.
        selected_text = str(selected_text)
        
        # Get the size/coordinates of the treeview cell.
        column_box = self.bbox(selected_iid, column)
        
        # Get the Y position of the treeview widget, because
        # the .bbox() method is relative to the widget itself, so
        # we need to add the Y position alongside .bbox() to make
        # the entry widget appear directly in a cell.
        # Do the same thing with the X position.
        treeview_x = self.winfo_x()
        treeview_y = self.winfo_y()
        
        max_limit = self.column_value_length_limits.get(column_name)      

        # Set the length limit in the entry widget
        self.entry_widget.configure(max_length=max_limit)
        
        # Delete any existing text from a possible previous edit.
        self.entry_widget.delete(0, tk.END)

        # Record the column index and item iid
        # so we'll know which item and column index to update
        # in the treeview widget.
        self.entry_widget.editing_column_index = column_index
        self.entry_widget.editing_item_iid = selected_iid
        
        # To compare if the newly entered value is different,
        # (to set the is_dirty flag)
        self.entry_widget.original_text = selected_text

        self.entry_widget.insert(0, selected_text)
        self.entry_widget.select_range(0, tk.END)

        # If we don't focus on the entry widget, the user won't
        # be able to type right away.
        self.entry_widget.focus()

        self.entry_widget.place(x=column_box[0] + treeview_x,
                                y=column_box[1] + treeview_y,
                                width=column_box[2],
                                height=column_box[3])

    def _get_column_name_from_index(self, column_index: int) -> str:
        """
        Return the name of the column from the index.
        
        Arguments:
        
        - column_index: numeric column number. For example, 0 (zero)
        means column "#0" (the tree column), and 1 will be the next column.
        
        Return value example: any string value, such as 'Names'.
        
        Purpsose: so we can find out whether the column cell value that is
        being edited allows blank values or not.
        """
        
        # Get the names of the columns in a list.
        # Example: ["#0", "names", "products"]
        column_names = ["#0"] + list(self.cget("columns"))
        
        try:
            # Get the column name based on the column index.
            name = column_names[column_index]
        except IndexError:
            return
        
        return name

    def on_enter_pressed(self, event):
        """
        Update the treeview cell with the value in the entry widget.
        """
        
        # Get the text in the entry widget.
        new_text = self.entry_widget.get().strip()
        
        # Get the item iid (row) that is being edited in the treeview widget,
        # such as I002
        selected_iid = self.entry_widget.editing_item_iid

        # Get the column index, which we need for updating the values list.
        # For example: index -1 (for the tree column), 
        # index 0 (first self-defined column), etc.
        column_index = self.entry_widget.editing_column_index
        
        # So that column -1 becomes column 0 (for the tree column)
        column_index_to_check = column_index + 1        
        
        # Get the column name (ie: 'products')
        column_name =\
            self._get_column_name_from_index(column_index=column_index_to_check)        
        
        # Blank new value?
        if not new_text:
            
            # Does the column that's being edited allow blank cell values?
            if column_name and column_name in self.columns_disallow_empty_cells:
                # Blank values are not allowed in the given column name,
                # so treat it like pressing the ESC key.
                self.on_escape_key_pressed(event)
                return
            
        else:
            # Do we need to validate the new value?
            if self.validation_method:
                # Yes, we need to validate the new value
                # to ensure it's valid to be inserted in the column.
                allow_value = self.validation_method(column_name,
                                                     new_text,
                                                     self.entry_widget.original_text)
                
                if not allow_value:
                    # There are invalid letters in the new variable name.
                    # Don't allow the new name to show up in the treeview widget.
                    self.on_escape_key_pressed(event)
                    return

        # Are we updating the Icon/Tree column?
        if column_index == -1:
            # Update the text column text
            self.item(selected_iid, text=new_text)
        else:
            # Update the values (one of the columns after the icon column)
            current_values = self.item(selected_iid).get("values")
            current_values[column_index] = new_text
            self.item(selected_iid, values=current_values)
            
        # Is the newly-entered text different from what was there before?
        # If so, set the 'is_dirty' flag, so we can know that
        # the treeview contents have been modified by the user.
        if new_text != self.entry_widget.original_text:
            self.is_dirty = True

        # Get it out of edit-mode.
        self._hide_entry_widget()

    def on_focus_out(self, event):
        """
        The user has clicked away from the cell is being edited.
        Apply the changes to the cell, as if enter was pressed.
        
        This method will also be called when using the scroll wheel
        on the mouse on the treeview widget (used for confirming
        the active entry edit, as if the enter key was pressed). But
        it's possible that the entry widget does not exist at all and
        that we're not in edit-mode, so we need to check whether the
        entry widget exists or not.
        """
        
        # The entry widget may not be visible, because this method
        # also runs when the scroll wheel is used on the mouse.
        if not self.entry_widget.winfo_viewable():
            return
            
        # Update the text on the cell being edited.
        self.on_enter_pressed(event)
        
    def on_escape_key_pressed(self, event):
        """
        The ESC key was pressed on the keyboard, so cancel edit-mode.
        """
        self._hide_entry_widget()

    def _hide_entry_widget(self):
        """
        Remove the text and place-forget the entry widget so it hides from view.
        """
        if self.entry_widget.winfo_viewable():
            self.entry_widget.delete(0, tk.END)
            self.entry_widget.place_forget()
        

if __name__ == "__main__":
    # For testing purposes.

    root = tk.Tk()

    column_names = ("fruit_name", "colour")

    treeview_food = TreeviewEdit(root, columns=column_names)

    treeview_food.heading("#0", text="Food Type")
    treeview_food.heading("fruit_name", text="Fruit Name")
    treeview_food.heading("colour", text="Colour")

    fruit_category = treeview_food.insert(parent="",
                                     index=tk.END,
                                     text="Fruit")

    treeview_food.insert(parent=fruit_category,
                         index=tk.END,
                         values=("Banana", "Yellow"))

    treeview_food.insert(parent=fruit_category,
                         index=tk.END,
                         values=("Apple", "Green"))
    

    btn_test = ttk.Button(root, text="Test")
    btn_test.pack()
    treeview_food.pack(fill=tk.BOTH, expand=True)
    
    treeview_food.column_set_value_length_limit("#0", 3)
    treeview_food.column_set_value_length_limit("fruit_name", 5)

    root.mainloop()
    