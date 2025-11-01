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

import pathlib
import pygubu
import tkinter as tk
import json
PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "fixed_font_size_converter_window.ui"
from tkinter import filedialog
from PIL import Image, ImageTk
from enum import Enum, auto
from tkinter import ttk
from typing import Dict, List, Tuple
from rect_options_window import RectOptionsWindowApp
from rect_object import RectObject
from tkinter import messagebox
from functools import partial
from pathlib import Path



class Direction(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()



class GenerateSpriteSheet:

    # The generated Image will be stored here so the
    # user can optionally save it to disk.
    generated_image: Image = None
    
    def __init__(self,
                 rects: Dict,
                 source_letter_image: Image.Image,
                 x_offset: int,
                 y_offset: int,
                 lbl_generated_image: ttk.Label,
                 lbl_letter_dimensions: ttk.Label,
                 func_show_trace_tab,
                 v_manual_height_increase):

        # Key: rectangle iid
        # Value: RectObject
        self.rects = rects

        self.source_letter_image = source_letter_image
        self.x_offset = x_offset
        self.y_offset = y_offset

        # Amount of padding to apply for generated letters
        # so that the letters don't appear to close to each other.
        # Used for debugging, don't use in production.
        self.x_padding_generated = 0
        self.y_padding_generated = 0
        
        self.lbl_generated_image = lbl_generated_image
        self.lbl_letter_dimensions = lbl_letter_dimensions
        self.func_show_trace_tab = func_show_trace_tab
        self.v_manual_height_increase = v_manual_height_increase

        self.generate_sprite_sheet()

    def get_max_sprite_sheet_width_height(self,
                                          rects: Dict,
                                          letter_box_width: int,
                                          letter_box_height: int,
                                          ) -> Tuple:
        """
        Get the maximum overall font sprite sheet width/height.
        
        Algorithm of width: get the combined width of rects on line number
        that has the most letters in it.
        
        Algorithm of height: get the combined height of rects, but only
        one rect per line number.
        """

        rect_object: RectObject

        width_so_far = 0
        height_so_far = 0

        # Key: line number
        # Value: count
        line_number_counts = {}
        max_count_in_line = 0

        """
        Get line number that has the most rects
        We will then use that line number to get the longest width
        that we need for the width of the full image.
        """
        for rect_object in rects.values():

            # Get the current count that we have for this line number.
            line_count = line_number_counts.get(rect_object.line_number, 0)
            
            # Increment 1 for this line number.
            line_count += 1
            line_number_counts[rect_object.line_number] = line_count
            
        # Find the line number that contains the highest number of rects.
        for line_number, count in line_number_counts.items():
            if count > max_count_in_line:
                max_count_in_line = count

        # The width we need to show all letters going across (horizontal)
        # The -1 (minus one) part in (max_count_in_line - 1) is used
        # to prevent a right-padding from showing for the last letter.
        required_width = (letter_box_width * max_count_in_line) \
            + (self.x_padding_generated * (max_count_in_line - 1))
        
        #required_height = (len(line_number_counts) * letter_box_height) + \
            #(self.y_padding_generated * (len(line_number_counts) - 1))

        required_height = (len(line_number_counts) * letter_box_height)
        required_height += self.y_padding_generated * (len(line_number_counts) - 1)

        return required_width, required_height

    def get_max_letter_width_height(self) -> Tuple:
        """
        Return the maximum width and height that will be
        needed for a letter.
        
        The width will be the widest letter.
        
        The height will be the highest rectangle.
        To determine the highest rectangle, the rectangles will be compared
        to other rectangles with the same line numbers. For example: a rectangle
        on line number 1 will be compared to other rectangles on line number 1.

        For example:
        Let's say we have:
        - the letter 'i':
        -    top: 15
        -    bottom: 25
        -    on line 1
        and also
        - the letter 'g':
        -    top: 5
        -    bottom: 35
        
        Between those two letters, the height will become:
        top: 5, bottom: 35 (the lowest-numbered top, and the highest
        numbered bottom)
        
        All other line numbers will be evaluated too and if another line
        number contains rectangles with higher values, the max record
        will be overwritten with the new values until no other higher values
        are found.
        """
        max_width_so_far = 0
        max_height_so_far = 0

        checked_line_numbers = []

        # Value: RectObject
        rect_object: RectObject
        for rect_id, rect_object in self.rects.items():

            # The line number this rectangle is on.
            line_number = rect_object.line_number
            
            # Make sure all rects have a line number.
            # Line number 0 (zero) is not considered to be a valid line number.
            if not line_number:
                messagebox.showerror(parent=self.lbl_letter_dimensions.winfo_toplevel(), 
                                     title="Line Number Missing",
                                     message="One or more letters is missing a line number value.\n\n" +
                                     "To fix this, double-click on each traced letter and make sure there is a line number.")
                self.func_show_trace_tab()
                return

            # Have we already checked all rectangles in this line number?
            # proceed to the next rectangle.
            if line_number in checked_line_numbers:
                continue

            # Get all rectangles on the line number that we're on.
            line_specific_rects = {key: value for key, value in self.rects.items()
                                   if value.line_number == line_number}

            # Consider this line number already checked so we don't check
            # this line number again in the next loop.
            checked_line_numbers.append(line_number)

            min_top_so_far = None
            max_bottom_so_far = 0

            # Loop through all rectangles on this line number.
            rect: RectObject
            for rect in line_specific_rects.values():

                # (x0, y0, x1, y1)
                # The width of this rect
                width = rect.coordinates[2] - rect.coordinates[0]

                # Is this the widest rectangle so far?
                if width > max_width_so_far:
                    # Yes, this is the widest rectangle we've found.
                    # Set a new max width record.
                    max_width_so_far = width

                # Now calculate the height
                
                # y0 - check if it's the lowest top
                # for this line number so far.
                top = rect.coordinates[1]
                
                # Does this rect have the lowest top value (most upper) so far?
                if min_top_so_far is None or top < min_top_so_far:
                    # Yes, this is the lowest top value we've seen so far,
                    # which means its the most 'upper' rect on this line.
                    # Record the top.
                    min_top_so_far = top

                # y1 - check if it's the higest bottom
                # for this line number so far.
                bottom = rect.coordinates[3]
                if bottom > max_bottom_so_far:
                    max_bottom_so_far = bottom

                # The difference (gives us the height)
                height = max_bottom_so_far - min_top_so_far

                # New maximum height?
                if height > max_height_so_far:
                    max_height_so_far = height

        """
        Now that we know the maximum width and height that a letter needs,
        we need to make letter 'boxes' to house each of the letters.
        The boxes will all be the same size - the size of the max letter width
        and max letter height.
        """

        # Used if the user wants to increase the height of the letter box
        # by a specific number of pixels. The purpose of this is if
        # a short letter is on line 1 and a long letter is on line 2,
        # we can't automatically determine what the height should be, because
        # one letter might be 'i' the other might be 'g' (that has a long tail)
        # so we allow the user to fine-tune the height manually.
        manual_increase_letter_box_height_by = \
            self.v_manual_height_increase.get()

        # Record the max width/height of a letter box so we can use them
        # in this method.
        max_box_height = max_height_so_far + manual_increase_letter_box_height_by
        max_box_width = max_width_so_far

        # Key: rectangle id
        # Value: RecObject
        for rect_id, rect_object in self.rects.items():

            # No need to evaluate the invisible space character
            # because it's not a real letter.
            if rect_id == "space":
                continue

            # Get the coordinates of the letter we're looping on.
            # We're only interested in y0 and y1.
            x0, y0, x1, y1 = rect_object.coordinates

            # Should we use a fixed anchor top for this letter?
            if not rect_object.use_manual_top:
                # Use a fixed anchor top
                
                # Calculate where the top should be based on the anchor
                # of 'top', 'middle', 'bottom'
                if rect_object.fixed_position == "top":
                    new_y0 = 0
                    
                elif rect_object.fixed_position == "middle":
                    new_y0 = int((max_box_height / 2) - ((y1 - y0) / 2))
                    
                elif rect_object.fixed_position == "bottom":
                    new_y0 = int(max_box_height - (y1 - y0))
                    
            else:
                # Use manual top for this rect
                new_y0 = rect_object.top_value

            # The new top
            rect_object.top_value = new_y0

            # Update the dictionary to reflect the new top
            self.rects[rect_id] = rect_object

        return max_box_width, max_box_height
        
    def generate_sprite_sheet(self):
        """
        Crop the traced letters and paste them on a new image
        with fixed spacing.
        """


        # Get the left-to-right sorted rectangle coordinates.
        # Key: rectangle id
        # Value: (x0, y0, x1, y1)
        sorted_rects: Dict
        sorted_rects = self._get_sorted_rectangles()
        
        # Get the biggest width/height of a letter, in pixels
        max_values = self.get_max_letter_width_height()
        if not max_values or max_values == (0, 0):
            return
        else:
            max_letter_width, max_letter_height = max_values

        # Can be used for debugging
        # letter_box_opacity = 150
        letter_box_opacity = 0

        # Create a new 'box' image that will fit 1 letter.
        # We will make copies of this image in a loop later.
        letter_box_image: Image.Image
        letter_box_image = Image.new(mode="RGBA",
                                     size=(max_letter_width,
                                           max_letter_height),
                                     color=(0, 0, 0, letter_box_opacity))
        
        # Ge the full size image dimensions
        full_width, full_height =\
            self.get_max_sprite_sheet_width_height(rects=sorted_rects,
                                                   letter_box_width=max_letter_width,
                                                   letter_box_height=max_letter_height)

        # Debug
        # full_height = 500

        # Create a blank image
        full_image: Image.Image
        full_image = Image.new(mode="RGBA",
                              size=(full_width, full_height),
                              color=(0, 0, 0, 150))

        # Copy a new blank (for the space character) letter box
        new_letter_box: Image.Image
        new_letter_box = letter_box_image.copy()
        

        current_x = 0

        recorded_line_number = 0

        rect_object: RectObject
        for rect_id, rect_object in sorted_rects.items():

            # Are we now on a new line?
            if rect_object.line_number != recorded_line_number:
                # Yes, we're on a new line.
                # Record the new line so we know when we're on a
                # different line again later on.
                recorded_line_number = rect_object.line_number

                # Set the invisible 'cursor' position to the left-most side.
                current_x = 0

            # Get the coordinates of the image itself, not the position
            # of the image in the canvas widget. The image in the canvas
            # widget has been offset a little bit.
            x0, y0, x1, y1 = rect_object.coordinates
            x0 -= self.x_offset
            y0 -= self.y_offset
            x1 -= self.x_offset
            y1 -= self.y_offset
            
            # The "space" rect_id might have negative coordinates
            # because in the coordinates are all zero, so in the code above
            # we subtracted zero by the offset values, so set to zero here.
            if x0 < 0:
                x0 = 0
            if y0 < 0:
                y0 = 0
            if x1 < 0:
                x1 = 0
            if y1 < 0:
                y1 = 0
            
            coordinates = (x0, y0, x1, y1)

            # Copy a new blank letter box
            new_letter_box: Image.Image
            new_letter_box = letter_box_image.copy()

            # Get the letter image
            letter_image: Image.Image
            letter_image =\
                self.source_letter_image.crop(coordinates)

            # Get the letter's dimensions
            letter_width = letter_image.width
            # letter_height = letter_image.height

            # Paste letter horizontally centered onto blank letter box
            center_x = (letter_box_image.width - letter_width) // 2
            new_letter_box.paste(letter_image, (center_x, rect_object.top_value))


            # Paste letter box into full image
            # Set the vertical position based on the line number.
            paste_y = (rect_object.line_number - 1) * letter_box_image.height

            # Apply vertical padding below every line except the first line.
            # Note: vertical padding is only used when debugging.
            if rect_object.line_number > 1:
                paste_y += self.y_padding_generated * (rect_object.line_number - 1)

            # Paste the letter box into full image.
            full_image.paste(new_letter_box, (current_x, paste_y))

            # full_image.paste(new_letter_box, (current_x, 0))

            current_x += new_letter_box.width + self.x_padding_generated

        # So we can use it with a ttk label.
        photo_image = ImageTk.PhotoImage(image=full_image)
        
        # Save a reference to the image so the user can save it
        # to the hard disk if needed.
        GenerateSpriteSheet.generated_image = full_image

        # Show the image so the user can see it.
        self.lbl_generated_image.image = photo_image
        self.lbl_generated_image.configure(image=photo_image)
        
        # Show the user the dimensions of each letter box.
        self.lbl_letter_dimensions.\
            configure(text=f"{max_letter_width}x{max_letter_height}")

    def _get_sorted_rectangles(self) -> Dict:
        """    
        Return a sorted dictionary of rects.
        
        Sort from lowest line number to highest line number
        and left-most x0 to the right-most x0. 
        """
        
        sorted_line_numbers = []
        sorted_x = []
        
        # Key: rect_iid
        # Value: RectObject
        sorted_rects = {}

        # Get all the line numbers.
        rect_object: RectObject
        for rect_iid, rect_object in self.rects.items():
            if rect_object.line_number not in sorted_line_numbers:
                sorted_line_numbers.append(rect_object.line_number)

        # Get the line numbers in ascending order.
        sorted_line_numbers.sort()

        # Sort x0 from lowest value to highest value.
        rect_object: RectObject
        for rect_iid, rect_object in self.rects.items():

            # Get just the x0 coordinate of the rectangle
            x0 = rect_object.coordinates[0]

            # Keep a record of all the x0s
            sorted_x.append(x0)

        # Sort x0s in ascending order.
        sorted_x.sort()

        # Loop from the lowest line number to the highest line number.
        for line_number in sorted_line_numbers:

            # Loop from the left-most X to the right-most X
            # on the line number that we're on.
            for x in sorted_x:

                rect_object: RectObject
                for rect_iid, rect_object in self.rects.items():

                    # We're only interested in the line number
                    # that we're currently looping on.
                    if rect_object.line_number != line_number:
                        continue

                    # Find the rectangle that is its turn to be added
                    # so the sorted_rects dictionary.
                    if rect_object.coordinates[0] == x:
                        sorted_rects[rect_iid] = rect_object

        # Now we have a sorted dictionary of rects (from left to right),
        # starting with the lowest line number to the highest line number.
        return sorted_rects

class TraceToolApp:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow = builder.get_object("main_window", master)
        
        self.main_notebook: ttk.Notebook
        self.main_notebook = builder.get_object("main_notebook")
        self.lbl_generated_image = builder.get_object("lbl_generated_image")
        self.lbl_letter_dimensions = builder.get_object("lbl_letter_dimensions")
        self.v_manual_height_increase = builder.get_variable("v_manual_height_increase")
        self.v_dark_background = builder.get_variable("v_dark_background")
        self.v_dark_background.trace_add("write", self.on_dark_background_checkbutton_clicked)

        # Keep track of the image iid because we need to exclude it
        # when looking for overlapping rectangles.
        self.image_iid = None

        self.canvas_main: tk.Canvas
        self.canvas_main = builder.get_object("canvas_main")

        builder.connect_callbacks(self)

        self.mainwindow.bind("<Up>", self.on_move_up)
        self.mainwindow.bind("<Down>", self.on_move_down)
        self.mainwindow.bind("<Left>", self.on_move_left)
        self.mainwindow.bind("<Right>", self.on_move_right)
        self.mainwindow.bind("<Delete>", self.on_delete_key_pressed)
        self.canvas_main.bind("<Double-1>", self.on_double_click)

        # self.up_look_for_opaque = False

        self.x_offset = 25  # 25
        self.y_offset = 25  # 25

        self.active_rect_iid = None
        
        # Record the photo image here so it doesn't get
        # garbage collected prematurely
        self.photo_image: ImageTk.PhotoImage
        self.photo_image = None
        
        self.img: Image.Image
        self.img = None

        # Key: rect iid
        # Value: RectObject
        self.rects = {}

        # Debug
        # self.show_image(debug_path)

    def on_dark_background_checkbutton_clicked(self, *args):
        """
        Set the canvas to a light or dark background depending
        on the checkbox state.
        """
        if self.v_dark_background.get():
            self.canvas_main.configure(background="#111319")
        else:
            self.canvas_main.configure(background="#ccd9cc")
            

    def on_load_trace_clicked(self):
        """
        Load a JSON .trc file from the hard disk.
        """

        # Ask for a selected file.
        file_types = [("Trace file", ".trc")]
        selected_file_path = filedialog.askopenfilename(parent=self.mainwindow,
                                                        filetypes=file_types)
        if not selected_file_path:
            return

        # The supported trace file version that we can read.
        supported_trace_version = 1

        # Load the JSON file and convert it to a regular Python dict.
        load_path = Path(selected_file_path)
        file_data = load_path.read_text()
        load_data = json.loads(file_data)
        
        # These keys must exist in the loaded dictionary
        # to be considered a regular trace file.
        required_keys = ("Rects", "Version",
                         "SourceImageDimensions", "ManualHeightIncrease")

        for required_key in required_keys:
            if required_key not in load_data:
                messagebox.showerror(parent=self.mainwindow, 
                                     title="Invalid Data",
                                     message="Unexpected data. Could not read trace file.")
                return

        # Record the loaded data.
        loaded_version = load_data.get("Version")

        # A list of rects (no iids)
        loaded_rects: List[Dict]
        loaded_rects = load_data.get("Rects")
        
        loaded_image_dimensions = load_data.get("SourceImageDimensions")
        loaded_manual_height_increase = load_data.get("ManualHeightIncrease")
        
        
        if loaded_version != supported_trace_version:
            messagebox.showerror("Unsupported Trace File",
                                 "Unsupported trace file version.")
            return

        # If there is an existing project, confirm with the user that
        # it's OK to proceed.
        if self.rects:
            msg = "Load trace file? Unsaved traces will be lost."
            
            decision = messagebox.askquestion(parent=self.mainwindow, 
                                              title="Load Trace File?",
                                              message=msg)
            
            if decision == "No":
                return
            
        # Make sure there is a loaded source image.
        if not self.img:
            messagebox.showwarning(parent=self.mainwindow, 
                                   title="No Image",
                                   message="There is no image loaded.\n"
                                   "Open an image first")
            return

        loaded_source_image_width = loaded_image_dimensions.get("Width")
        loaded_source_image_height = loaded_image_dimensions.get("Height")
        
        if self.img.width != loaded_source_image_width or \
           self.img.height != loaded_source_image_height:
            messagebox.showerror(parent=self.mainwindow, 
                                 title="Image Dimensions",
                                 message=f"The expected image dimensions for this trace file are: "
                                 f"{loaded_source_image_width}x{loaded_source_image_height}\n\n"
                                 f"However, the current image is: {self.img.width}x{self.img.height}")
            return


        self.rects.clear()
        self.active_rect_iid = None
        loaded_rect_objects = []
        
        # Delete any existing rectangles on the canvas.
        existing_rects = [item for item in self.canvas_main.find_all()
                          if self.canvas_main.type(item) == "rectangle"]
        for item_id in existing_rects:
            self.canvas_main.delete(item_id)

        # Loop through the rects that we need to load.
        # These rects have no ids. They are just a list of dictionaries
        # that contain rectobject details.
        for rect_object_details in loaded_rects:
            load_coordinates = rect_object_details.get("Coordinates")
            load_line_number = rect_object_details.get("LineNumber")
            load_use_manual_top = rect_object_details.get("UseManualTop")
            load_fixed_position = rect_object_details.get("FixedPosition")
            load_top_value = rect_object_details.get("TopValue")

            new_rectangle = \
                RectObject(coordinates=load_coordinates,
                           line_number=load_line_number,
                           use_manual_top=load_use_manual_top,
                           fixed_position=load_fixed_position,
                           top_value=load_top_value)
            
            loaded_rect_objects.append(new_rectangle)

        self.v_manual_height_increase.set(loaded_manual_height_increase)

        """
        Now that we have a list of RectObject rects, draw the rectangles.
        """
        rect_object: RectObject
        for rect_object in loaded_rect_objects:
            coordinates = rect_object.coordinates

            iid = \
                self.canvas_main.create_rectangle(
                    (coordinates[0],
                     coordinates[1],
                     coordinates[2],
                     coordinates[3]),
                    fill="",
                    outline=self.get_deselect_outline_color())

            self.rects[iid] = rect_object

    def on_save_trace_clicked(self):
        """
        Save a JSON .trc file to the hard disk.
        """
        
        # Make sure there are rects to save.
        if not self.rects:
            messagebox.showwarning(parent=self.mainwindow, 
                                   title="Nothing to Save",
                                   message="There are no areas traced.")
            return

        save_data = {}
        save_rects = []

        save_coordinates = {}
        save_manual_height = self.v_manual_height_increase.get()
        
        img_width = self.img.width
        img_height = self.img.height

        # Loop through all the rectangles, excluding the special
        # "space" letter box.
        rect_object: RectObject
        for rect_id, rect_object in self.rects.items():

            if rect_id == "space":
                continue
            
            save_id = rect_id
            save_coordinates = rect_object.coordinates
            save_line_number = rect_object.line_number
            save_use_manual_top = rect_object.use_manual_top
            save_fixed_position = rect_object.fixed_position
            save_top_value = rect_object.top_value
            
            save_rects.append({"Coordinates": save_coordinates,
                                  "LineNumber": save_line_number,
                                  "UseManualTop": save_use_manual_top,
                                  "FixedPosition": save_fixed_position,
                                  "TopValue": save_top_value}
                              )

        save_data["Rects"] = save_rects
        save_data["Version"] = 1
        save_data["SourceImageDimensions"] = {"Width": img_width,
                                              "Height": img_height}
        save_data["ManualHeightIncrease"] = save_manual_height

        save_json = json.dumps(obj=save_data,
                               indent=2)

        # Show the save file dialog
        file_types = [("Trace file", ".trc")]
        file_name_path = filedialog.asksaveasfilename(parent=self.mainwindow,
                                                      filetypes=file_types)

        if not file_name_path:
            return
        
        save_path = Path(file_name_path)
        save_path.write_text(save_json)

    def on_save_as_button_clicked(self):
        """
        Save the generated image to disk.
        """
        GenerateSpriteSheet.generated_image: Image

        if not GenerateSpriteSheet.generated_image:
            return

        file_types = [("Portable Network Graphics", ".png")]
        save_full_path = filedialog.asksaveasfilename(parent=self.mainwindow,
                                                      filetypes=file_types)

        if not save_full_path:
            return

        GenerateSpriteSheet.generated_image.save(save_full_path, "PNG")

    def _update_rect(self, new_rect_object: RectObject):
        """
        Update the rect object in the dictionary for the active rect id.
        
        This is used when a rect setting has been changed and we need
        to update the rect options dictionary.
        """
        self.rects[self.active_rect_iid] = new_rect_object

    def on_double_click(self, event):
        # Make sure there is a rectangle selected.
        if not self.active_rect_iid:
            return

        # Get the rec object for the active rectangle,
        # because the rect options window needs it.
        rect_object = self.rects.get(self.active_rect_iid)
        
        rect_window: tk.Toplevel
        rect_window = RectOptionsWindowApp(master=self.mainwindow,
                                           edit_rect=rect_object,
                                           update_func=self._update_rect)
        rect_window = rect_window.mainwindow

        rect_window.transient(self.mainwindow)
        rect_window.update_idletasks()
        rect_window.grab_set()
        rect_window.wait_window(rect_window)

    def on_delete_key_pressed(self, event):
        """
        Delete the selected rectangle.
        """

        # No selected rectangle? Return
        if not self.active_rect_iid:
            return
        
        self.canvas_main.delete(self.active_rect_iid)
        del self.rects[self.active_rect_iid]
        self.active_rect_iid = None

    def on_move_up(self, event):
        self.move_rect(event=event,
                       direction=Direction.UP)

    def on_move_down(self, event):
        self.move_rect(event=event,
                       direction=Direction.DOWN)

    def on_move_left(self, event):
        self.move_rect(event=event,
                       direction=Direction.LEFT)

    def on_move_right(self, event):
        self.move_rect(event=event,
                       direction=Direction.RIGHT)

    def run(self):
        self.mainwindow.mainloop()

    def on_mouse_motion(self, event):
        x = event.x - self.x_offset
        y = event.y - self.y_offset
        # info = self.img.getpixel((x, y))

        # print(info, f"{x}x{y}")

    def on_canvas_button_press(self, event):
        """
        The left mouse button has been held down on the canvas widget.
        """
        
        # No font image loaded yet? return
        if not self.img:
            return
        
        self.draw_rectangle(event.x, event.y)

    def on_canvas_mouse_move(self, event):
        """
        The mouse point is moving over the canvas.
        """
        pass

    def on_canvas_button_released(self, event):
        """
        The left mouse button is no longer
        being held down on the canvas widget.
        """
        pass
    
    def _get_lowest_top(self):
        """
        Get the top-most y0 value of all the rects.
        Purpose: so we can make the "space" rect match the lowest top.
        We don't just want to maket the space rect y0 of zero, because
        the top-most actual letter rect ma not be at zero.
        """
        
        lowest_y0 = None

        rect_object: RectObject
        for rect_id, rect_object in self.rects.items():

            # We shouldn't evaluate the invisible space character
            # because all its coordinates are zero and it's not a real letter.
            if rect_id == "space":
                continue
            
            # x0, y0, x1, y1
            y0 = rect_object.coordinates[1]
            
            if lowest_y0 is None:
                lowest_y0 = y0
            else:
                if y0 < lowest_y0:
                    lowest_y0 = y0
                    
        return lowest_y0
            
    def on_notebook_tab_changed(self, event):
        tab_id = self.main_notebook.index("current")
        
        if tab_id == 0:
            # Set focus to the main window so that the key arrows
            # will respond (for moving rectangle edges).
            self.mainwindow.focus()
        
        elif tab_id == 1:
            
            func_show_trace_tab = partial(self.main_notebook.select, tab_id=0)

            self._create_space_letter_box()
            
            test = GenerateSpriteSheet(rects=self.rects,
                                       source_letter_image=self.img,
                                       x_offset=self.x_offset,
                                       y_offset=self.y_offset,
                                       lbl_generated_image=self.lbl_generated_image,
                                       lbl_letter_dimensions=self.lbl_letter_dimensions,
                                       func_show_trace_tab=func_show_trace_tab,
                                       v_manual_height_increase=self.v_manual_height_increase)

    def _create_space_letter_box(self):
        """
        Create a space letter box based on the lowest top value.
        
        Default the space character to line 1 so it appears at the beginning
        of the generated image.
        """

        # Remove any existing space letter box because the lowest top
        # value might have changed since the last time we added a space
        # character to the dictionary.
        if "space" in self.rects:
            del self.rects["space"]

        # Get the rect that has the lowest y0 value, because
        # we need to set the invisible space letter to match that y0.
        # We can't assume that the lowest y0 is zero, because it might
        # be higher, so we need the space letter to match the 'top' value
        # of the lowest (top-most) y0 value.
        lowest_y0 = self._get_lowest_top()

        # lowest_y0 will be None if there are no rectangles,
        # so check for it to avoid an exception.
        if lowest_y0 is None:
            return

        self.rects["space"] = RectObject(coordinates=(0,
                                                      lowest_y0,
                                                      0,
                                                      lowest_y0),
                                         line_number=1)

    def _set_rect_outline_to_black(self, rect_iid: int = None):
        """
        Deselect one or all rectangles by changing the outline to black.
        
        If an argument is specified (rect_iid), only the given's rectangle
        outline is set to black. Otherwise, all rectangles' outlines are
        set to black.
        
        Arguments:
        
        - rect_iid: the unique identifier for a rectangle. If this is set to
        None, then all the rectangles will have their outlines set to black.
        """
        
        if rect_iid is not None:
            
            # Deselect one specific rectangle.
            self.canvas_main.itemconfig(rect_iid, outline=self.get_deselect_outline_color())
            
        else:
            # Deselect all rectangles by changing the outlines to black.
            
            # Get rectangle item iids.
            all_rects = [item for item in self.canvas_main.find_all()
                         if self.canvas_main.type(item) == "rectangle"]            
            
            rect_iid: int
            for rect_iid in all_rects:
                
                # Deselect this rectangle, before it's evaluated.
                self.canvas_main.itemconfig(rect_iid, outline=self.get_deselect_outline_color())                

    def get_deselect_outline_color(self) -> str:
        """
        Get the outline color of rectangles when they are not selected.
        
        If we're in dark mode, set the outline color to purple.
        Otherwise, set the outline color to black.
        """
        dark_mode = self.v_dark_background.get()
        
        if dark_mode:
            return "green"
        else:
            return "black"
    

    def set_active_rectangle(self, x, y) -> int | None:
        """
        Select the rectangle that is within the given mouse pointer
        coordinates by changing its color.
        """

        # We no longer have a focussed rectangle because we're going
        # to determine which rectangle should have the focus or if
        # no rectangle will end up having focus for various reasons, then
        # don't have an active selected rectangle.
        self.active_rect_iid = None

        # Get rectangle item iids.
        all_rects = [item for item in self.canvas_main.find_all()
                     if self.canvas_main.type(item) == "rectangle"]

        found_rect = False

        # Go through the rectangle iids and select
        # the rect that contains the mouse pointer, but don't stop there.
        # Deselect all the other rectangles.
        rect_iid: int
        for rect_iid in all_rects:

            # Deselect this rectangle, before it's evaluated.
            self._set_rect_outline_to_black(rect_iid=rect_iid)

            # Is the mouse pointer within this rectangle?
            item = self.canvas_main.coords(rect_iid)
            x0, y0, x1, y1 = item
            if x >= x0 and x <= x1 \
               and y >= y0 and y <= y1:
                # The mouse pointer is within this rectangle.
                
                # Set flag that will be returned
                found_rect = True

                # So the other parts of the code will know
                # which rect is currently selected.
                self.active_rect_iid = rect_iid

                # So the selected rectangle stands out.
                self.canvas_main.itemconfig(rect_iid, outline="blue")

        return found_rect

    def draw_rectangle(self, x, y):
        """
        Create a rectangle around the pixel that has just been clicked
        or if the mouse is inside a rectangle, select that rectangle.
        """

        found_iid = self.set_active_rectangle(x=x, y=y)
        if found_iid:
            # An existing rectangle was clicked; no need for a new rectangle.
            return

        # Get the coordinates that match the actual
        # spritesheet image coordinates, not the 
        # canvas widget with the offsets.
        x_check = x - self.x_offset
        y_check = y - self.y_offset

        # Create a rectangle around the pixel that has just been clicked.
        self._get_bounding_box(x=x_check,
                               y=y_check)
        
    def is_transparent_pixel(self, x, y) -> bool:
        """
        Return whether a pixel with alpha 0 (100% transparent)
        has been clicked (True) or not (False).
        
        Arguments:
        
        - x: the x coordinate of where the mouse pointer is
        - y: the y coordinate of where the mouse pointer is
        
        Return: bool
        """
        
        pixel = self.img.getpixel((x, y))

        length = len(pixel)
        if length == 4:
            # Example: (120,120,120,0)
            if pixel[3] == 0:
                return True
            
        else:
            return False

    def _get_bounding_box(self,
                         x: int,
                         y: int,
                         left_stops: int = 1,
                         top_stops: int = 1,
                         right_stops: int = 1,
                         bottom_stops: int = 1):
        
        """
        Look for the nearest transparent pixels around the pixel
        that has just been clicked. Then form a rectangle around the
        transparent areas.
        
        Changes:
        Nov 7, 2023 (Jobin Rezai) - Show a message if the loaded image
        is not in RGBA mode.
        """
        
        img_width, img_height = self.img.size
        
        x_pos = x
        y_pos = y

        img_mode = self.img.mode
        if img_mode != "RGBA":
            messagebox.showerror(parent=self.mainwindow,
                                 message="Only RGBA images with transparency can be traced.\n"
                                         f"The image you have selected is of mode: {img_mode}.",
                                 title="No Transparency")
            return

        pixel = self.img.getpixel((x, y))
        if pixel[3] == 0:
            print("Nothing selected")
            return

        # Get the left stop (alpha pixel)
        transparent = False
        while not transparent:
            x_pos -= 1
            transparent = self.is_transparent_pixel(x_pos, y_pos)
            if x_pos == 0:
                break
        pixel_left = x_pos

        x_pos = x
        y_pos = y

        # Get the top stop (alpha pixel)
        transparent = False
        while not transparent:
            y_pos -= 1
            transparent = self.is_transparent_pixel(x_pos, y_pos)
            if y_pos == 0:
                break            
        pixel_top = y_pos
        
        x_pos = x
        y_pos = y

        # Get the right stop (alpha pixel)
        transparent = False
        while not transparent:
            x_pos += 1
            if x_pos == img_width - 1:
                break
            transparent = self.is_transparent_pixel(x_pos, y_pos)


        pixel_right = x_pos
    
        x_pos = x
        y_pos = y

        # Get the bottom stop (alpha pixel)
        transparent = False
        while not transparent:
            y_pos += 1
            if y_pos >= img_height - 1:
                break            
            transparent = self.is_transparent_pixel(x_pos, y_pos)

        pixel_bottom = y_pos
            
            
        # print(f"{pixel_left=},{pixel_top=},{pixel_right=},{pixel_bottom=}")

        x0, y0, x1, y1 = (pixel_left + self.x_offset,
                          pixel_top + self.y_offset,
                          pixel_right + self.x_offset,
                          pixel_bottom + self.y_offset)

        # Check to see if the new rectangle will overlap with
        # any existing rectangles.
        item_iids = self.canvas_main.find_overlapping(x1=x0, y1=y0, x2=x1,
                                                      y2=y1)


        # Exclude the loaded-image's item iid from the list of overlapping
        # items that it found, if any, because we're not concerned about
        # the canvas image's iid.
        item_iids = [iid for iid in item_iids
                     if iid != self.image_iid]
        
        if item_iids:
            # This new rectangle will overlap with an existing rectangle,
            # so return.
            return

        # Create the new rectangle and show it as being selected.
        iid = self.canvas_main.create_rectangle(x0, y0, x1, y1,
                                                fill="",
                                                outline="blue")

        # Record the iid of the new rectangle so if we need to change
        # its size later, we can just access this dictionary.
        new_rect = RectObject(coordinates=(x0, y0, x1, y1))
        self.rects[iid] = new_rect

        # Set the new rectangle as the selected rectangle.
        self.active_rect_iid = iid
        
    def move_rect(self, event, direction: Direction):
        """
        Move the rectangle up by one pixel in a loop
        until the entire top part of the rectangle reaches
        alpha 0 (transparency).
        """

        # Make sure there is a rectangle selected.
        if not self.active_rect_iid:
            return

        # Get the coordiantes of the selected rectangle.
        rect_object: RectObject = self.rects.get(self.active_rect_iid)
        x0, y0, x1, y1 = rect_object.coordinates

        # Get the rectangle coordinates relative to the image
        # (and not the canvas widget).
        x0 -= self.x_offset
        y0 -= self.y_offset
        x1 -= self.x_offset
        y1 -= self.y_offset


        # Determine which rectangle X and rectangle Y we need to
        # iterate through to find the pixels we want.

        # 'check_from' is the position to start pixel checking.
        # 'check_to' is the last position to pixel check.
        # 'move_y' will be either y0 or y1, which will move the rectangle up or down.
        # 'move_x' will be either x0 or x1, and will be used for moving the rectangle left or right.
        if direction == Direction.UP:
            
            # Is the rectangle already at the top of the image? return.
            if y0 <= 0:
                return

            check_from = x0
            check_to = x1  # + 2
            move_y = y0
            
        elif direction == Direction.DOWN:
            
            # Is the rectangle already at the bottom of the image? return.
            if y1 >= self.img.height:
                return
            
            check_from = x0
            check_to = x1 # + 2
            move_y = y1
            
        elif direction == Direction.LEFT:
            
            # Is the rectangle already at the left of the image? return.
            if x0 <= 0:
                return

            check_from = y0
            check_to = y1  # - 2
            move_x = x0
            
        elif direction == Direction.RIGHT:
            
            # Is the rectangle already at the right of the image? return.
            if x1 >= self.img.width:
                return              
            
            check_from = y0
            check_to = y1 # + 2

            # We're going to be moving 'x1' if the current
            # vertical right side doesn't satisfy.
            move_x = x1
            
        
       # self.up_look_for_opaque = True

        opaque_found = False


        # Look for a row (when going up/down) that has at least one opaque pixel.
        # Look for a column (when going left/right) that has at least one opaque pixel.

        # By 'opaque', we really mean an alpha greater than 0.

        """
        The reason we look for an opaque pixel *before* looking for 
        all-transparent pixels is because we want to 'start' from where an
        opaque pixel is. Take for instance the lower case letter 'i'.
        When we click on the bottom part of 'i', it'll highlight the whole
        letter without the point. Then when we press 'up' on the keyboard,
        we want it to stop at the top of the dot, so we need to look for
        the start of the opaque part of the dot before we can start looking
        for the transparent ending at the very top of 'i'.
        """

        # Look for a starting opaque position.
        while not opaque_found:
            
            for i in range(check_from, check_to):

                if direction in (Direction.UP, Direction.DOWN):
                    pixel = self.img.getpixel((i, move_y))

                elif direction in (Direction.LEFT, Direction.RIGHT):
                    pixel = self.img.getpixel((move_x, i))
                    
  
                # Is the pixel not fully transparent?
                if pixel[3] > 0:
                    # The pixel is not fully transparent.
                    
                    opaque_found = True
                    
                   # self.up_look_for_opaque = False
                    break
                
            else:
                # We haven't found an opaque pixel on this row.

                if direction == Direction.UP:
                    # Move the rectangle up and try again.
                    y0 -= 1
                    move_y = y0

                    # Checking for an opaque pixel up (y-coordinate) into
                    # the negatives? Return, because this image doesn't have
                    # an opaque row at the top.
                    if y0 < 0:
                        return

                elif direction == Direction.DOWN:
                    # Move the rectangle down and try again.
                    y1 += 1
                    move_y = y1

                    # Checking for an opaque pixel past the last row? Return.
                    # An image starts at pixel 1, but the y-coordinate
                    # of a canvas starts at 0, which is why y1==img.height is
                    # the same as being one pixel *after* the bottom of the image.
                    if y1 == self.img.height:
                        return                    
                                        
                elif direction == Direction.LEFT:
                    # Move the rectangle left and try again.
                    x0 -= 1
                    move_x -= 1
                    
                    # Checking for an opaque pixel before the start of
                    # the image? Return.
                    # This image doesn't have an opaque pixel to the left.
                    if x0 < 0:
                        return

                elif direction == Direction.RIGHT:
                    # Move the rectangle right and try again.
                    x1 += 1
                    move_x += 1

                    # Checking for an opaque pixel beyond the right of
                    # the image? Return.
                    # This image doesn't have an opaque pixel to the right.


                    # An image starts at pixel 1, but the x-coordinate
                    # of a canvas starts at 0, which is why x1==img.width is
                    # the same as being one pixel *after* the right of the image.
                    if x1 == self.img.width:
                        return



        opaque_found = True
            


        # Look for a row that is all transparent across the top.
        while opaque_found:

            if direction == Direction.UP:
                # Have we reached the top of the image?
                # If so, that means the letter is touching the top of the image,
                # so technically there likely is no transparent top.
                # We can stop here since we're already at the top of the image.
                if y0 == 0:
                    break

            elif direction == Direction.DOWN:
                # Have we reached the bottom of the image?
                # If so, that means the letter is touching the bottom of the image,
                # so technically there likely is no transparent bottom.
                # We can stop here since we're already at the bottom of the image.
                if y1 == self.img.height:
                    break
            
            elif direction == Direction.LEFT:
                # Have we reached the left-most side of the image?
                # If so, that means the letter is touching the left of the image,
                # so technically there likely is no transparent left.
                # We can stop here since we're already at the left of the image.
                if x0 == 0:
                    break
                
            elif direction == Direction.RIGHT:
                # Have we reached the right-most side of the image?
                # If so, that means the letter is touching the right of the image,
                # so technically there likely is no transparent right.
                # We can stop here since we're already at the right of the image.
                print(self.img.width)
                if x1 == self.img.width:
                    break            
            
        
            for i in range(check_from, check_to):

                if direction in (Direction.UP, Direction.DOWN):
                    pixel = self.img.getpixel((i, move_y))

                elif direction in (Direction.LEFT, Direction.RIGHT):
                    pixel = self.img.getpixel((move_x, i))

                print(pixel)

                # Is the pixel non-transparent?
                if pixel[3] > 0:
                    # We've reached a non-transparent pixel

                    if direction == Direction.UP:
                        # Move the rectangle's top higher.
                        y0 -= 1
                        move_y = y0
                        break
                    
                    elif direction == Direction.DOWN:
                        # Move the rectangle's bottom lower
                        y1 += 1
                        move_y = y1
                        break

                    elif direction == Direction.LEFT:
                        # Move the rectangle more to the left
                        x0 -= 1
                        move_x = x0
                        break
                    

                    elif direction == Direction.RIGHT:
                        # Move the rectangle more to the right
                        x1 += 1
                        move_x = x1
                        break                
                    
            else:
                # We've reached a row with all transparency
                opaque_found = False
                    

        x0 += self.x_offset
        y0 += self.y_offset
        x1 += self.x_offset
        y1 += self.y_offset
        
        # Are the new coordinates overlapping with another rectangle? Return.
        item_iids = self.canvas_main.find_overlapping(x1=x0, y1=y0, x2=x1, y2=y1)

        # Remove the image iid (which is the loaded image) from the
        # overlapping check and remove the selected rectangle from the check.
        item_iids = [iid for iid in item_iids
                     if iid not in (self.image_iid, self.active_rect_iid)]
        
        # If we have any iids left over, that means the rectangle's new
        # coordinates will overlap with another rectangle if we continue,
        # so return.
        if item_iids:
            return

        # Update the selected rectangle's coordinates.
        self.canvas_main.coords(self.active_rect_iid,
                                x0, y0, x1, y1)

        # Update the coordinates in the dictionary so we have them
        # the next time they need to be updated.
        rect_object.coordinates = (x0, y0, x1, y1)
        self.rects[self.active_rect_iid] = rect_object

    def on_load_sprite_sheet_clicked(self):
        
        # A sprite sheet should only be a .png
        file_types = [("PNG files", ".png")]

        # Ask for one file
        selected_file = filedialog.askopenfilename(parent=self.mainwindow,
                                                   filetypes=file_types)

        if not selected_file:
            return
        
        self.show_image(selected_file)

    def show_image(self, image_path: str):


        self.img = Image.open(image_path)
        self.photo_image = ImageTk.PhotoImage(self.img)

        # Load and show the image, while keeping track of its canvas item iid.
        # We need the iid so we can exclude the image from rectangle checks,
        # because rectangles only need to be checked against other rectangles.
        self.image_iid =\
            self.canvas_main.create_image(self.x_offset, self.y_offset,
                                          image=self.photo_image,
                                          anchor=tk.NW)

if __name__ == "__main__":
    app = TraceToolApp()
    app.run()
