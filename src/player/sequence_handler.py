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
import sprite_definition as sd
from animation_speed import AnimationSpeed
from typing import List, Set, Tuple
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
        
        # The sprite name to show after the sequence has stopped.
        # This is optional.
        self.sprite_name_after_stop:str = None
        
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
        
        Return: True if the sequence was created successfully.
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
                
        # There has to be 2 or more frames to create an animation.
        if len(self.frame_image_names) <= 1:
            return                

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
        
        # Now that the sequence has stopped, is there a final frame that
        # we should settle on? This is optional.
        if self.sprite_name_after_stop:
            
            # Yes, there is a specific sprite name we should show.
            
            # Get the main story reader
            main_reader =\
                Passer.active_story.reader.get_main_story_reader()
            
            # Show the sprite that needs to be shown now that the 
            # sequence has stopped.
            main_reader._sprite_show(arguments=self.sprite_name_after_stop,
                                     sprite_type=self.sprite_type)             
        
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


class SequenceGroup:
    def __init__(self):
        
        # Key: sequence name
        # Value: SequenceHandler object.
        self.sequences = {}
        
    def update(self):
        """
        Run the update method in all sequences.
        Sequences that are not active will return None in their update methods.
        """
        for sequence in self.sequences.values():
            sequence.update()
            
    def _get_aliases_in_sequence(self, sequence_name: str) -> Set:
        """
        Return a set of unique aliases that are associated with the sprite
        names in the given sequence name.
        
        Purpose: this method is used in the process of making sure a sequence
        that *wants to* be played, doesn't have sprite aliases that are already
        being played in a different sequence. Having multiple sequences playing
        the same aliases would not be straight-forward for the visual novel
        author when writing a visual novel.
        """
        
        # Get the sequence object that we need to check, by name.
        sequence: SequenceHandler
        sequence = self.sequences.get(sequence_name)
        if not sequence:
            return
        
        # A sequence is tied to a sprite type.
        # Use this mapping to find the sprite group for us to search aliases in.
        sprite_group_mapping = {ContentType.CHARACTER: sd.Groups.character_group,
                        ContentType.OBJECT: sd.Groups.object_group,
                        ContentType.DIALOG_SPRITE: sd.Groups.dialog_group,}
        
        # Get the sprite group depending on the sprite type.
        sprite_group: SpriteGroup
        sprite_group = sprite_group_mapping.get(sequence.sprite_type)
        if not sprite_group:
            return
        
        # We're interested in the sprites that are in the given sequence.
        unique_sprite_names = set(sequence.frame_image_names)
        
        # We're going to append general aliases to this set.
        # As we append aliases to this set, duplicates are not added.
        unique_aliases = set()

        # Enumerate through all the sprites in the given sprite group
        # and keep track of aliases for sprites that are in the given sequence.
        sprite_object: sd.SpriteObject
        for sprite_name, sprite_object in sprite_group.sprites.items():
            
            # Is the current sprite name one of the sprites in the sequence?
            if sprite_name in unique_sprite_names:
                
                # Yes, this is one of the sprite names in the given sequence.
                
                # Add the alias to the set.
                # Duplicates are not added because it's a set, not a list.
                unique_aliases.add(sprite_object.general_alias)
                
        return unique_aliases
    
    def _aliases_exist_in_other_playing_sequences(self,
                                          unique_aliases: Set,
                                          sprite_type: ContentType, 
                                          exclude_sequence_name: str) -> Tuple[Set, str]:
        """
        Determine if any of the aliases in the set, unique_aliases, exist
        in any other sequences that are currently playing.
        
        Arguments:
        
        - unique_aliases: a set of unique alias names.
        
        - sprite_type: so we can search the right sprite dictionary.
        
        - exclude_sequence_name: the sequence name to not check because
        this is the sequence name that wants to be played from another method,
        and it's the reason we're doing this check.
        
        Return: a tuple, considering of a set of the aliases that exist in
        any *other* sequences that are currently playing (if any), and the
        sequence name where the aliases are currently being used.
        """
        
        # Holds aliases that are in sequences, as we enumerate through other
        # sequences down below.
        other_aliases = set()
        
        # If the given unique aliases (unique_aliases) has items that exist in
        # one of the other sequences of the same sprite type, the shared
        # aliases will be populated in this set.
        sets_share_aliases = set()

        # Enumerate through all other sequences that match the type (character,
        # object, or dialog sprite) of the given sequence in the argument. 
        other_sequence: SequenceHandler
        other_seq_name: str = None
        for other_seq_name, other_sequence in self.sequences.items():
            
            # Make sure we're enumerating on a different sequence than the 
            # given sequence name in the argument, so that we're sure it's a 
            # different sequence altogether.            
            if other_seq_name == exclude_sequence_name:
                continue
            
            # The sprite type of the given sequence has to match the other
            # sequence that we're checking against. For example, character 
            # sequences must be compared to other character sequences, not 
            # objects or dialog sprites.            
            elif other_sequence.sprite_type != sprite_type:
                continue
            
            # We're only interested in comparing against other actively
            # *playing* sequences. If the other sequence is not being played,
            # there is no need to check the other sequence.
            elif not other_sequence.is_playing:
                continue
            
            # Get the unique aliases of the sprites in the other sequence.
            other_aliases =\
                self._get_aliases_in_sequence(sequence_name=other_seq_name)
                        
            # Make sure we have a value here, which should always be the case.
            if not other_aliases:
                continue
                        
            # Does the given unique aliases (in the argument) have aliases
            # that match with aliases in the other sequence that we're
            # enumeratong on? If so, populate this variable with the shared 
            # aliases, if any.
            sets_share_aliases = unique_aliases & other_aliases
            
            if sets_share_aliases:
                # One or more aliases are being used in the other sequence that
                # we're currently enumerating on. There is no point in checking
                # more sequences, so break here.
                break
            
        # Return the shared alias(es), if any, along with the sequence
        # name where the alias(es) are being used, if at all.
        return (sets_share_aliases, other_seq_name)

    def play(self, sequence_name: str, play_number_of_times: int):
        """
        Play a specific sequence. If the given sequence name is already
        playing, the request will be ignored.
        
        Arguments:
        
        - sequence_name: case-sensitive sequence name.
        
        - play_number_of_times: the number of times to play the sequence
        animation. -1 means repeat.
        """
        
        """
        We need to ensure that no other playing sequences are set up to show
        a sprite alias in the sequence name that wants to be played
        in this method. The reason is: two different sequences trying to
        animate sprites with overlapping aliases will not make sense.
        """

        # The sequence that wants to be played must already be configured.
        # Try to find it.
        sequence: SequenceHandler
        sequence = self.sequences.get(sequence_name)
        
        if sequence:
            # The sequence exists.
            
            # Is the sequence already playing? return.
            if sequence.is_playing:
                return
            
            # Get all unique aliases in the sequence we want to play.
            aliases_this_sequence =\
                self._get_aliases_in_sequence(sequence_name=sequence_name)
            
            # Check if any of the sprites in the given sequence 
            # (in the argument) are already being animated in a different 
            # sequence.
            aliases_already_in_use, other_sequence_name = \
                self._aliases_exist_in_other_playing_sequences(
                unique_aliases=aliases_this_sequence,
                sprite_type=sequence.sprite_type,
                exclude_sequence_name=sequence_name)            
            
            # Show the actively animating aliases, if any, so the visual novel
            # author is aware that two sequences can't play simultaneously, if
            # both sequences want to show the same aliases for the same 
            # sprite type (character, object, dialog sprite).
            if aliases_already_in_use:
                raise ValueError(f"Error: An attempt was made to play the sequence, '{sequence_name}'. However, a different sequence that is currently playing ('{other_sequence_name}') is already using the following aliases: {aliases_already_in_use}.")
            else:
                # There are no actively animating aliases that are in the
                # sequence that wants to be played.
                # Go ahead and play the sequence.
                sequence.play(play_num_of_times=play_number_of_times)
            
    def stop(self, sequence_name: str):
        """
        Stop a specific sequence from playing.
        
        This will also cause the sequence to show the 'final frame',
        if a final frame has been defined for the sequence.
        """
        sequence: SequenceHandler
        sequence = self.sequences.get(sequence_name)
        if sequence:
            if sequence.is_playing:
                sequence.stop()
            
    def stop_all(self):
        """
        Stop all sequences that are currently playing.
        
        This will also cause the sequences to show the 'final frame',
        if a final frame has been defined for the sequences.
        """
        
        sequence: SequenceHandler
        for sequence in self.sequences.values():
            if sequence.is_playing:
                sequence.stop()

    def create_sequence(self,
                        sequence_name:str,
                        sprite_type: str,
                        image_names: List,
                        default_delay: float,
                        play_number_of_times=1) -> bool | None:
        """
        Create a sequence name if it doesn't already exist and initialize it.
        
        Arguments:
        
        - sequence name: a unique (case-sensitive) name to represent this new
        sequence animation. This name will be used to interact with the
        sequence after it's been created.
        
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
        
        # Make sure a sequence name has been specified.
        if not sequence_name:
            return
        
        # Make sure the sequence name doesn't already exist.
        if sequence_name in self.sequences:
            return
        
        # Instantiate a new single sequence handler.
        sequence = SequenceHandler()
        created_successfully =\
            sequence.configure_sequence(
                sprite_type=sprite_type,
                image_names=image_names,
                default_delay=default_delay,
                play_number_of_times=play_number_of_times)

        # Was the sequence created successfully with the arguments we
        # provided it above?
        if created_successfully:
            
            # Add the newly created sequence to the queue list.
            self.sequences[sequence_name] = sequence

