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
from animation_speed import AnimationSpeed
from typing import List
from sprite_definition import Groups, SpriteGroup
from shared_components import Passer
from file_reader import ContentType


class SequenceHandler:
    def __init__(self):
        
        # The delay that applies to all images.
        self.global_delay = 0.1
        
        # Image names
        self.frame_image_names = []
        
        # Delay list (list of floats)
        self.frame_delays = []
        
        # Key: image name (str)
        # Value: delay (float)
        # Used for images that have specific non-global delays.
        self.individual_delay = {}
        
        # To know where the images come from (characters, dialog sprites, etc.)
        self._sprite_type:ContentType
        self._sprite_type = None
        
        # Use -1 for forever
        self.play_number_of_times = 1
        
        # A counter that keeps track of the number of times the sequence
        # has reached the end.
        self.played_number_of_times_so_far = 0
        
        self.is_playing = False
        
        # To know which 'page' of image we're on.
        self.current_frame_index = 0
        
        # The time keeper.
        self.timer = 0.0

        # To know when to show the next image.
        self.current_target_time = 0.0
        
    @property
    def sprite_type(self) -> ContentType:
        return self._sprite_type
    
    @sprite_type.setter
    def sprite_type(self, value: str):
        """
        Take a string as a value, such as "character",
        but save the value as a ContentType enum.
        """
        
        lookup = {"character": ContentType.CHARACTER,
                  "object": ContentType.OBJECT,
                  "dialog sprite": ContentType.DIALOG_SPRITE,}
        
        set_value = lookup.get(value)
        self._sprite_type = set_value
        
    def configure_sequence(self,
                           sprite_type: str,
                           image_names: List,
                           default_delay: float,
                           play_number_of_times=1) -> bool | None:
        
        """
        Prepare the animation by specifying the image names that
        will be used in the sequence, along with a default delay setting.
        
        Arguments:
        
        - sprite_type (str): either 'character', 'object', or 'dialog sprite',
        so this method knows which image dictionary to check.
        
        - image_names: a list of image sprite names to load sequentially
        to make an animation. The order of the image file names is the sequence
        in which the images will be displayed.
        
        - default_delay: the global delay to apply to each image in the
        animation. Each sprite can have its own sequence delay, but that's
        set in a different method.
        
        - play_number_of_times: the number of times to play the sequence.
        Use -1 to play forever.
        """
        
        dict_source = {"character": Groups.character_group,
                       "object": Groups.object_group,
                       "dialog sprite": Groups.dialog_group,}
        
        # Find the sprite group dictionary to get the images from.
        # At this point, we just need to ensure to get the images
        # that actually exist.
        sprite_group: SpriteGroup
        sprite_group = dict_source.get(sprite_type)
        if not sprite_group:
            return
        
        # Clear any existing image names from a previous animation, 
        # we're starting new.
        self.frame_image_names.clear()
        self.frame_delays.clear()
        
        self.sprite_type = None
        
        self.global_delay = default_delay
        
        # Add the given image names (not aliases) to a list
        # so we can load the images by name dynamically during an animation.
        for image_name in image_names:
            
            if image_name in sprite_group.sprites:
                self.frame_image_names.append(image_name)
                self.frame_delays.append(self.global_delay)

        # Did we successfully at image names to the list?
        if self.frame_image_names:
            
            self.sprite_type = sprite_type
            
            return True
        
    def stop(self):
        """
        Set flag to stop the sequential animation.
        """
        self.is_playing = False
        
        # Reset the counter that holds the number of times 
        # the sequence was played.
        self.played_number_of_times_so_far = 0        
        
    def play(self, play_num_of_times: int):
        """
        Start showing images in sequence.
        
        Arguments:
        
        - play_num_of_times: the number of times to play the sequence animation.
        minus 1 (-1) means repeat. When it's on repeat, the stop() must be
        used to stop the animation.
        """
        
        # Make sure there are images to show.
        if not self.frame_image_names:
            return
        
        # There has to be a specific number of times to play the sequence
        # or -1 for repeat.
        elif not play_num_of_times:
            return
        
        
        # Set the initial delay (the first image the frame)
        # self.current_target_time = self.frame_delays[0]
        
        # -1 means play forever.
        self.play_number_of_times = play_num_of_times
        
        # Initialize. We start at 1 because this variable starts getting 
        # incremented after the current initial frame. If we start at zero,
        # it will play one extra sequence.
        self.played_number_of_times_so_far = 1
        
        self.is_playing = True

        # Play from the beginning, initialize timer variables.
        self._reset_sequence()
        
    def _reset_sequence(self):
        """
        Reset the image cursor (frame) position so its back to the beginning.
        
        Purpose: this gets called when the sequence animation is finished
        and needs to be 'rewinded'.
        """
        
        # Set to -1 so it'll be set to 0 in the update() method,
        # if the sequence is played again,
        self.current_frame_index = -1
        
        # Reset destination time
        self.current_target_time = 0
        
        # Reset elapsed time counter
        self.timer = 0.0
        
    def update(self):
        """
        Advance the frame based on delta time.
        Must be called once per pygame frame.
        """
        # Not playing? return.
        if not self.is_playing:
            return
        
        ## Debug
        #self.play_number_of_times = -1
        
        # Delta time in seconds that have elapsed since the last frame.
        dt = AnimationSpeed.delta

        # Add elapsed time
        self.timer += dt

        # Check if it's time to switch frames
        if self.timer >= self.current_target_time:
            
            # Subtract the target time because we've already met or exceeded
            # the target time. We do this instead of resetting the timer to 0
            # to keep the math accurate (preserves extra milliseconds for the 
            # next frame to catch up sooner on the next frame if it took longer 
            # this frame). This is useful for avoiding time drift over several 
            # frames.
            self.timer -= self.current_target_time
            
            # Advance index, making it ready to get the next image
            # in the sequence.
            self.current_frame_index += 1

            # Check if we've reached the end of the sequence
            if self.current_frame_index >= len(self.frame_image_names):
                
                # Yes, we've reached the end of the sequence animation.
                
                # Rewind the sequence, making it ready to be played
                # from the beginng.
                self._reset_sequence()                
                
                # Should we play the sequence animation all over again?
                # -1 means play in a loop.
                if self.play_number_of_times == -1:
                    
                    # Yes, play the sequence animation from the beginning.
                    return
                    
                # Have we played the required number of times?
                elif self.played_number_of_times_so_far < self.play_number_of_times:
                    
                    # No, we haven't played the required number of times yet.
                    
                    # Increment played counter
                    self.played_number_of_times_so_far += 1

                else:
            
                    # Finished playing, we should now stop the sequence
                    # animation.
                    
                    # self.current_frame_index = len(self.frame_image_names) - 1

                    self.stop()
                    return
                  

            else:
                # The sequence is not finished.
                
                # Update the target time for the new frame image.
                self.current_target_time =\
                    self.frame_delays[self.current_frame_index]
                
                # Get the new image name to display on the screen.
                new_image_name =\
                    self.frame_image_names[self.current_frame_index]
                
                # Show a character sprite by setting 
                # its visibility flag to True.
                main_reader =\
                    Passer.active_story.reader.get_main_story_reader()
                
                main_reader._sprite_show(arguments=new_image_name,
                                         sprite_type=self.sprite_type)            
