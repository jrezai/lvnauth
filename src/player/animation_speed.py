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

class AnimationSpeed:
    
    # Delta is time in seconds since last frame.
    # Used for FPS setting independent physics.
    delta = 0    

    @staticmethod
    def get_sequence_value(initial_value: float,
                           increment_by: float,
                           max_convenient_row: int, 
                           convenient_row_number: int) -> float:
        """
        Calculates the value in the sequence for a given row number, based on 
        a starting value and a specified increment.
    
        Purpose: to get a float value that can be used in an animation, such as
        fading, movement, scaling, rotating.
    
        Each type of animation will need its own initial value
        and incrementation.
    
        Arguments:
    
        - initial_value: the slowest animation value (example: 0.0002)
    
        - increment_by: by how much to increase the speed of an animation at
        each speed setting (example: 0.002).
        
        - max_convenient_value: the max allowed convenient value. Each
        type of animation will have its own max.
    
        - convenient_row_number: the convenient value from the editor to get the
        calculable value for. For example, a convenient row number of 1 means to
        get the slowest value. The max is 30000. Example value: 1
    
        Return: the calculated float value at the requested convenient row.
        """
        if convenient_row_number < 1:
            convenient_row_number = 1
        elif convenient_row_number > max_convenient_row:
            convenient_row_number = max_convenient_row
    
        # The sequence starts at 0
        num_increments = convenient_row_number - 1
    
        value = initial_value + (num_increments * increment_by)
    
        # Return the value rounded to 4 decimal places for clean output
        return round(value, 4)
