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


from enum import Enum, auto


class StartOrStop(Enum):
    START = auto()
    STOP = auto()


class MovementStops(Enum):
    """
    The side of the rectangle that is going to be checked to see
    if it has reached the destination co-ordinates or not.
    """
    RIGHT = auto()
    LEFT = auto()
    TOP = auto()
    BOTTOM = auto()


class ImagePositionX(Enum):
    START_OF_DISPLAY = auto()
    END_OF_DISPLAY = auto()
    BEFORE_START_OF_DISPLAY = auto()
    AFTER_END_OF_DISPLAY = auto()


class ImagePositionY(Enum):
    TOP_OF_DISPLAY = auto()
    ABOVE_TOP_OF_DISPLAY = auto()
    BOTTOM_OF_DISPLAY = auto()
    BELOW_BOTTOM_OF_DISPLAY = auto()


def str_to_position_type(position: str):
    """
    Take a string position name and return the Enum version of it.

    Example: "start of display" will return ImagePositionX.START_OF_DISPLAY
    :param position: str
    :return: ImagePositionX or ImagePositionY
    """
    matches = {"start of display": ImagePositionX.START_OF_DISPLAY,
               "end of display": ImagePositionX.END_OF_DISPLAY,
               "before start of display": ImagePositionX.BEFORE_START_OF_DISPLAY,
               "after end of display": ImagePositionX.AFTER_END_OF_DISPLAY,
               "top of display": ImagePositionY.TOP_OF_DISPLAY,
               "above top of display": ImagePositionY.ABOVE_TOP_OF_DISPLAY,
               "bottom of display": ImagePositionY.BOTTOM_OF_DISPLAY,
               "below bottom of display": ImagePositionY.BELOW_BOTTOM_OF_DISPLAY}

    return matches.get(position)


def rect_section_to_type(rect_section: str) -> MovementStops:
    """
    Convert a string section, such as 'top' to MovementStops.TOP
    :param rect_section: str such as left, top, right, left
    :return: MovementStops class object.
    """
    matches = {"left": MovementStops.LEFT,
               "right": MovementStops.RIGHT,
               "top": MovementStops.TOP,
               "bottom": MovementStops.BOTTOM}

    section = matches.get(rect_section)

    return section
