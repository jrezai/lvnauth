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

from enum import Enum, auto
from typing import Tuple
from animation_speed import AnimationSpeed



class TintStyle(Enum):
    REGULAR = auto()
    GLOW = auto()


class TintDirection(Enum):
    HIGHER = auto()
    LOWER = auto()


class TintStatus(Enum):
    """
    Used for knowing what tint status a sprite is in.
    """
    ANIMATING = auto()
    ORIGINAL_UNTINTED = auto()
    REACHED_DEST_TINT = auto()



class TintHandler:
    """
    Gradually tints a sprite.
    The speed is user-definable.
    """
    
    def __init__(self):

        self.status = TintStatus.ORIGINAL_UNTINTED
        
        self.tint_style = TintStyle.REGULAR
        
        self.direction:TintDirection
        self.direction = None
        
        """
        If applying a regular tint, this value will decrease.
        If applying a glow tint, this value will start at zero and increase
        gradually.
        """
        
        self.reach_tint_value = None
        
        self.current_tint_value = None
        self.calculated_tint_value = None
        
        self.applied_tint_value = None
        
        self.speed = None
        
    def is_dirty_with_tint(self) -> bool:
        """
        Return whether the sprite has a non-default tint status.

        Purpose: before applying a fade effect, this method gets used
        to determine whether the image needs to be tinted first,
        before a fade effect is used.
        """
        
        # Has a tint status that is not ORIGINAL_UNTINTED (original)?
        # Consider it dirty with a tint effect.
        if self.status in (TintStatus.ANIMATING,
                           TintStatus.REACHED_DEST_TINT):
            return True
            
        else:
            return False
        
    def is_tint_animation_needed(self) -> bool:
        """
        Return whether the applied tint value is the same as the expected
        tint value.
        
        Purpose: to know whether a tint effect is required on self.image
        """
        
        # -------
        # Tint check
        
        # Tint check #1
        # Animating a tint or finished tinting but it now needs to stay tinted?
        reapply_tint = self.is_dirty_with_tint()
        
        # Tint check #2 - continued challenge
        # Is the 'applied' tint value different from the calculated 
        # tint value?
        if reapply_tint:
            
            # Tint the sprite if the 'applied' tint is different from the 
            # calculated tint value.
            reapply_tint =\
                (self.applied_tint_value is None \
                or \
                self.applied_tint_value != self.current_tint_value)
            
        return reapply_tint
        
    def start_tint_regular(self, speed: int, destination_tint: int):
        """
        Start animating a regular (darken) tint effect by changing the status.
        
        Arguments:
        
        - speed: An int speed value can, which affects how quickly the tint
        animation reaches the final tint value. A speed value such as 775 is
        normal. 

        - destination_tint: the tint value that needs to be reached (animated
        towards).
        """

        """
        Regular tint - make darker - decrease RGB from 255 to around 100
        Regular tint - go back to normal - increase RGB back to 255
        """
        
        # The starting tint value (no tint) is 255.
        # Or if the sprite's tint is being switched from Glow to Regular,
        # also start with 255.
        if self.status == TintStatus.ORIGINAL_UNTINTED \
           or self.tint_style != TintStyle.REGULAR:
            self.current_tint_value = 255

        # Regular tint, make darker?
        if self.current_tint_value > destination_tint:
            self.direction = TintDirection.LOWER
            
        # Regular tint, go back to normal?
        elif self.current_tint_value < destination_tint:
            self.direction = TintDirection.HIGHER
        
        else:
            # The calculated tint value is the same as the destination tint,
            # so there is nothing left to do.
            return
        
        
        # Reset
        self.applied_tint_value = None
        
        # Set the calculated speed for the tint animation
        self.speed = speed
        
        # The tint style is used for us to find out whether we need to blit
        # the sprite has BLEND_RGB_ADD (Glow) or BLEND_RGB_MULT (Regular tint)
        self.tint_style = TintStyle.REGULAR
        
        # Record the tint value that needs to be reached.
        self.reach_tint_value = destination_tint
        
        # Initialize the calculated tint value that we're starting with.
        # This will be calculated on each frame.
        self.calculated_tint_value = self.current_tint_value
            
        # Set flag to indicate that a tint animation has started.
        self.status = TintStatus.ANIMATING
        
    def start_tint_glow(self, speed: int, destination_tint: int):
        """
        Start animating a glow tint effect by changing the status.
        
        Arguments:
        
        - speed: An int speed value can, which affects how quickly the tint
        animation reaches the final tint value. A speed value such as 775 is
        normal. 

        - destination_tint: the tint value that needs to be reached (animated
        towards).
        """

        """
        Glow tint - make brighter - increase RGB from 0 to around 100
        Glow tint - go back to normal - decrease RGB back to 0
        """
        
        # The starting tint value (no glow) is 0.
        # Or if the sprite's tint is being switched from Regular to Glow,
        # also start with 0.
        if self.status == TintStatus.ORIGINAL_UNTINTED \
           or self.tint_style != TintStyle.GLOW:
            self.current_tint_value = 0

        # Glow tint, make brighter?
        if self.current_tint_value < destination_tint:
            self.direction = TintDirection.HIGHER
            
        # Glow tint, go back to normal?
        elif self.current_tint_value > destination_tint:
            self.direction = TintDirection.LOWER
        
        else:
            # The calculated tint value is the same as the destination tint,
            # so there is nothing left to do.
            return
        
        
        # Reset
        self.applied_tint_value = None
        
        # Set the calculated speed for the tint animation
        self.speed = speed        
        
        # The tint style is used for us to find out whether we need to blit
        # the sprite has BLEND_RGB_ADD (Glow) or BLEND_RGB_MULT (Regular tint)
        self.tint_style = TintStyle.GLOW
        
        # Record the tint value that needs to be reached.
        self.reach_tint_value = destination_tint
        
        # Initialize the calculated tint value that we're starting with.
        # This will be calculated on each frame.
        self.calculated_tint_value = self.current_tint_value
            
        # Set flag to indicate that a tint animation has started.
        self.status = TintStatus.ANIMATING
        
    def get_tint_values(self) -> Tuple | None:
        """
        Return a tuple with the current RGB tint values.
        
        Return None if the original (non-tinted) image is being displayed.
        """
        
        if self.status == TintStatus.ORIGINAL_UNTINTED:
            # Regular, untinted
            return
        
        return (self.current_tint_value,
                self.current_tint_value,
                self.current_tint_value)
        
    def animate_tint(self) -> bool | None:
        """
        Check if a tint is in an animation-state and whether it's reached
        its destination tint value.
        """
        
        if self.status != TintStatus.ANIMATING:
            return
        
        # SPEED = 775
        SPEED = self.speed

        if self.tint_style == TintStyle.REGULAR:
            
            # Have we reached the final tint?
            if self.direction == TintDirection.LOWER:
            
                if self.current_tint_value <= self.reach_tint_value:
                    
                    # We've reached the final tint value.
                    
                    # The sprite should now be a dimmed state.
                    self.status = TintStatus.REACHED_DEST_TINT
                    
                else:
                    
                    # The final tint value has not been reached yet.
                    self.calculated_tint_value -= SPEED * AnimationSpeed.delta                    
                    
                    # Clamp the value so it doesn't go below the 
                    # tint-reach value.
                    self.calculated_tint_value =\
                        max(self.reach_tint_value, self.calculated_tint_value)                      
                    
            elif self.direction == TintDirection.HIGHER:
                
                if self.current_tint_value >= self.reach_tint_value:
                    
                    # We've reached the final less-dim value.
                    
                    # Are we back to the 'original' untinted state?
                    if self.reach_tint_value >= 255:
                        
                        # The tint is 255, which is the same as not having
                        # a tint, so set the status to 'original'.
                        self.status = TintStatus.ORIGINAL_UNTINTED
                    else:
                        # The tint animation has reached its destination,
                        # but it's still tinted. It's not back to its original
                        # untinted state, so set the status to 
                        # 'reached destination'.
                        self.status = TintStatus.REACHED_DEST_TINT
                        
                else:
                    
                    # The final tint value has not been reached yet.
                    self.calculated_tint_value += SPEED * AnimationSpeed.delta
                    
                    # Clamp the value so it doesn't go above the 
                    # tint-reach value.
                    self.calculated_tint_value =\
                        min(self.reach_tint_value, self.calculated_tint_value)                      

                
            # Was the tint value reached? If so, set the current tint value
            # to match the destination tint value so it's exact.
            if self.status != TintStatus.ANIMATING:
                    
                # Make the current tint value match the final tint value.
                self.current_tint_value = self.reach_tint_value
                

        elif self.tint_style == TintStyle.GLOW:
            
            
            # Have we reached the final tint?
            if self.direction == TintDirection.HIGHER:
            
                if self.current_tint_value >= self.reach_tint_value:
                    
                    # We've reached the final tint value.
                    
                    # The sprite should now be a glow state.
                    self.status = TintStatus.REACHED_DEST_TINT
                    
                else:
                    
                    # The final tint value has not been reached yet.
                    self.calculated_tint_value += SPEED * AnimationSpeed.delta
                    
                    # Clamp the value so it doesn't go above the 
                    # tint-reach value.
                    self.calculated_tint_value =\
                        min(self.reach_tint_value, self.calculated_tint_value)                    
                    
                    
            elif self.direction == TintDirection.LOWER:
                
                if self.current_tint_value <= self.reach_tint_value:
                    
                    # We've reached the final less-glow value.
                    
                    # Are we back to the 'original' untinted state?
                    if self.reach_tint_value <= 0:
                        
                        # The tint is 0, which is the same as not having
                        # a glow tint, so set the status to 'original'.
                        self.status = TintStatus.ORIGINAL_UNTINTED
                    else:
                        # The tint animation has reached its destination,
                        # but it's still tinted. It's not back to its original
                        # untinted state, so set the status to 
                        # 'reached destination'.
                        self.status = TintStatus.REACHED_DEST_TINT
                        
                else:
                    
                    # The final tint value has not been reached yet.
                    self.calculated_tint_value -= SPEED * AnimationSpeed.delta
                    
                    # Clamp the value so it doesn't go below the 
                    # tint-reach value.
                    self.calculated_tint_value =\
                        max(self.reach_tint_value, self.calculated_tint_value)
                    
                
        ## Was the tint value reached? If so, set the current tint value
        ## to match the destination tint value so it's exact.
        #if self.status != TintStatus.ANIMATING:
                
            ## Make the current tint value match the final tint value.
            #self.current_tint_value = self.reach_tint_value


        # Make sure the tint value is an integer, not a float.
        self.current_tint_value = int(self.calculated_tint_value)

        # For debugging
        # print("Calculated tint:", self.calculated_tint_value, self.status)
        
        

        # Don't allow the tint value to go over 255 or below 0.
        if self.current_tint_value > 255:
            self.current_tint_value = 255

        elif self.current_tint_value < 0:
            self.current_tint_value = 0

        # Animating/calculating tint was required.
        return True
    