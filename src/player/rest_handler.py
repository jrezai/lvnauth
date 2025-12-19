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
from animation_speed import AnimationSpeed


class RestHandler:
    """
    Pauses the main reader (not background readers).
    This is used with the <rest> command.
    
    <rest> works almost like <halt>, with the difference being that
    a mouse click will not work with <rest>, so it forces the main story
    reader to pause.
    
    Another difference is that <rest> can specify the number of seconds
    to pause the main story reader, whereas <halt> can't specify a timeframe.
    
    Usage:
    The setup() method is used to initialize the rest handler.
    The tick() method is used to check if we should pause the main reader (True)
    or not (False)
    """
    
    def __init__(self):
        
        # Increments on each frame
        self.rest_seconds_counter = 0
        
        # The frame count we need to reach
        self.rest_seconds_reach = 0
        
    def setup(self, seconds_reach: int):
        """
        Initialize the counter so we can start counting.
        
        If there is a rest counter already counting, then add
        more time to rest - because it's possible to run <rest> from
        a reusable script multiple times, so in a case like that, it will
        just increment the existing wait timer.
        """
        
        # Is there an existing rest timer currently active?
        if all((self.rest_seconds_reach, self.rest_seconds_counter)) and \
           self.rest_seconds_counter <= self.rest_seconds_reach:
            
            # Yes, there's an active rest timer already,
            # so add to the current wait time.
            
            self.rest_seconds_reach += seconds_reach
        else:
            # New rest timer; initialize.
            
            self.rest_seconds_reach = seconds_reach
            self.rest_seconds_counter = 0
            
    def pause_required(self) -> bool:
        """
        Check if we need to pause the main reader or not.
        
        Return: True if we need to pause the main story reader
        or False if we should not pause the main story reader.
        """
        return self.rest_seconds_reach > 0
        
    def tick(self):
        """
        Check if we need to pause the main reader or not
        and if we need to pause, then increment the rest-counter.
        
        Return: True if we need to pause the main story reader
        or False if we should not pause the main story reader.
        """
        
        # Counter not active? return False (which means don't pause)
        if not self.rest_seconds_reach:
            return False
        
        # Has the counter reached the number that it needs to reach?
        # Reset the counter and return False, there is no need to pause anymore.
        elif self.rest_seconds_counter >= self.rest_seconds_reach:
            self.rest_seconds_counter = 0
            self.rest_seconds_reach = 0
            return False
        else:
            # The counter is active. Increment 
            # and return True (which means Pause)
            self.rest_seconds_counter += AnimationSpeed.delta
            return True
        
