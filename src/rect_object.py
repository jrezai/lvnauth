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

from typing import Tuple



class RectObject:
    """
    Defines a rectangle that is the size of the largest letter
    in a font sprite sheet.
    
    Arguments:
    
    - coordinates: the size of the rectangle (x0, y0, x1, y1)
    
    - line_number: the line number the rect is on. We use the line numbers
    to figure out what the longest (max height) of a letter box needs to be.
    
    - use_manual_top: a bool variable used for knowing whether we need
    to set the top manually with a value that the user has set or whether
    we need to set the position with an anchored (fixed) position.
    
    - fixed_position: a str variable used for which vertical position
    to anchor the rectangle. Possible values are: 'top', 'middle', 'bottom'.
    
    - top_value: the manual top value (y0) for where the letter should be
    vertically positioned. This value is ignored if use_manual_top is False. 
    """
    def __init__(self,
                 coordinates: Tuple,
                 line_number: int = 0,
                 use_manual_top: bool = False,
                 fixed_position: str = "top",
                 top_value: int = 0):

        self.coordinates = coordinates
        self.line_number = line_number
        self.use_manual_top = use_manual_top
        self.fixed_position = fixed_position
        self.top_value = top_value
