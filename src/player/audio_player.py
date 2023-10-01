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

import pygame
import file_reader
from io import BytesIO
from enum import Enum, auto
from shared_components import Passer



class AudioChannel(Enum):
    FX = auto()
    MUSIC = auto()
    VOICE = auto()
    TEXT = auto()
    ALL = auto()



class AudioPlayer:

    def __init__(self):

        self.channel_text: pygame.mixer.Sound
        self.channel_text = None

        self.channel_fx: pygame.mixer.Sound
        self.channel_fx = None

        self.channel_voice: pygame.mixer.Sound
        self.channel_voice = None

        self.channel_music: pygame.mixer.Sound
        self.channel_music = None
        
        self.loaded_text = None
        self.loaded_voice = None
        self.loaded_fx = None
        self.loaded_music = None

        # Volume is 0 to 1 (ie: 0.5 means 50% volume)
        self._volume_text = 1
        self._volume_sound = 1
        self._volume_voice = 1
        self._volume_music = 1
        
    def stop_audio(self, audio_channel: AudioChannel):
        """
        Stop the audio on a specific channel,
        if the channel has been initialized.
        """

        if audio_channel == AudioChannel.MUSIC:
            if self.channel_music:
                self.channel_music.stop()

        elif audio_channel == AudioChannel.FX:
            if self.channel_fx:
                self.channel_fx.stop()

        #elif audio_channel == AudioChannel.TEXT:
            #if self.channel_text:
                #self.channel_text.stop()
                
        elif audio_channel == AudioChannel.VOICE:
            if self.channel_voice:
                self.channel_voice.stop()
                
        elif audio_channel == AudioChannel.ALL:
            if self.channel_voice:
                self.channel_voice.stop()
                
            if self.channel_fx:
                self.channel_fx.stop()
                
            if self.channel_music:
                self.channel_music.stop()        

    @property
    def volume_text(self):
        return self._volume_text

    @volume_text.setter
    def volume_text(self, value: float):
        self._volume_text = value

        # Set the volume for the channel, if it's initialized.
        if self.channel_text:
            self.channel_text.set_volume(value)

    @property
    def volume_sound(self):
        return self._volume_sound

    @volume_sound.setter
    def volume_sound(self, value: float):
        self._volume_sound = value

        # Set the volume for the channel, if it's initialized.
        if self.channel_fx:
            self.channel_fx.set_volume(value)
          
    @property
    def volume_voice(self):
        return self._volume_voice

    @volume_voice.setter
    def volume_voice(self, value: float):
        self._volume_voice = value

        # Set the volume for the channel, if it's initialized.
        if self.channel_voice:
            self.channel_voice.set_volume(value)
    
    @property
    def volume_music(self):
        return self._volume_music

    @volume_music.setter
    def volume_music(self, value: float):
        self._volume_music = value

        # Set the volume for the channel, if it's initialized.
        if self.channel_music:
            self.channel_music.set_volume(value)

    def play_audio(self,
                   audio_name: str,
                   audio_channel: AudioChannel,
                   loop_music=False):
        """
        Play an audio file through the specified channel.
        
        Arguments:
        
        - audio_name: the file name we want to play
        
        - audio_channel: the channel to use to play this audio.
        
        - loop_music: only used with <play_music>
        """
        
        if not audio_name:
            return
        
        if audio_channel in (AudioChannel.FX, AudioChannel.TEXT,
                             AudioChannel.VOICE):
            content_type = file_reader.ContentType.AUDIO

        elif audio_channel == AudioChannel.MUSIC:
            content_type = file_reader.ContentType.MUSIC

        # Get the bytes of the sound
        sound_bytes =\
            Passer.active_story.data_requester.get_audio(content_type=content_type,
                                                         item_name=audio_name)

        if not sound_bytes:
            return

        if audio_channel == AudioChannel.TEXT:
            
            self._play_text_sound(audio_name=audio_name,
                                 bytes_data=sound_bytes)
            
        elif audio_channel == AudioChannel.VOICE:

            self._play_voice(audio_name=audio_name,
                             bytes_data=sound_bytes)
            
        elif audio_channel == AudioChannel.FX:

            self._play_fx(audio_name=audio_name,
                          bytes_data=sound_bytes)
            
        elif audio_channel == AudioChannel.MUSIC:

            self._play_music(audio_name=audio_name,
                             bytes_data=sound_bytes,
                             loop_music=loop_music)

    def _play_music(self,
                    audio_name: str,
                    bytes_data: bytes,
                    loop_music: bool):
        """
        Play a music audio file from bytes data.
        
        Arguments:
        
        - audio_name: the resource/item name of the sound to be played.
        
        - bytes_data: the bytes representation of the wav/ogg data.
        """

        # Create a new text audio channel if not initialized
        # or if the last loaded audio is different than what needs to be played.
        if not self.channel_music or self.loaded_music != audio_name:

            # pygame works well with BytesIO
            # Convert the bytes sound to a BytesIO stream
            io_bytes_data = BytesIO(bytes_data)

            # Initialize a new audio channel.
            self.channel_music = pygame.mixer.Sound(file=io_bytes_data)

        # Save the filename of the loaded .wav
        self.loaded_music = audio_name

        # If we don't stop the existing, sound, the sound
        # won't play until the previous sound has stopped.
        self.channel_music.stop()

        self.channel_music.set_volume(self.volume_music)
        
        if loop_music:
            # Continuously loop the music.
            self.channel_music.play(-1)
        else:
            # Play the music with no loop.
            self.channel_music.play()

    def _play_fx(self, audio_name: str, bytes_data: bytes):
        """
        Play an FX audio file from bytes data.
        
        Arguments:
        
        - audio_name: the resource/item name of the sound to be played.
        
        - bytes_data: the bytes representation of the wav/ogg data.
        """

        # Create a new text audio channel if not initialized
        # or if the last loaded audio is different than what needs to be played.
        if not self.channel_fx or self.loaded_fx != audio_name:

            # pygame works well with BytesIO
            # Convert the bytes sound to a BytesIO stream
            io_bytes_data = BytesIO(bytes_data)

            # Initialize a new audio channel.
            self.channel_fx = pygame.mixer.Sound(file=io_bytes_data)

        # Save the filename of the loaded .wav
        self.loaded_fx = audio_name

        # If we don't stop the existing, sound, the sound
        # won't play until the previous sound has stopped.
        self.channel_fx.stop()

        self.channel_fx.set_volume(self.volume_sound)
        self.channel_fx.play()

    def _play_voice(self, audio_name: str, bytes_data: bytes):
        """
        Play a voice audio file from bytes data.
        
        Arguments:
        
        - audio_name: the resource/item name of the sound to be played.
        
        - bytes_data: the bytes representation of the wav/ogg data.
        """

        # Create a new text audio channel if not initialized
        # or if the last loaded audio is different than what needs to be played.
        if not self.channel_voice or self.loaded_voice != audio_name:

            # pygame works well with BytesIO
            # Convert the bytes sound to a BytesIO stream
            io_bytes_data = BytesIO(bytes_data)

            # Initialize a new audio channel.
            self.channel_voice = pygame.mixer.Sound(file=io_bytes_data)

        # Save the filename of the loaded .wav
        self.loaded_voice = audio_name

        # If we don't stop the existing, sound, the sound
        # won't play until the previous sound has stopped.
        self.channel_voice.stop()

        self.channel_voice.set_volume(self.volume_voice)
        self.channel_voice.play()

    def _play_text_sound(self, audio_name: str, bytes_data: bytes):
        """
        Play an audio file from bytes data.
        
        Arguments:
        
        - audio_name: the resource/item name of the sound to be played.
        
        - bytes_data: the bytes representation of the wav/ogg data.
        """

        # Create a new text audio channel if not initialized
        # or if the last loaded audio is different than what needs to be played.
        if not self.channel_text or self.loaded_text != audio_name:

            # pygame works well with BytesIO
            # Convert the bytes sound to a BytesIO stream
            io_bytes_data = BytesIO(bytes_data)

            # Initialize a new audio channel.
            self.channel_text = pygame.mixer.Sound(file=io_bytes_data)

        # Save the filename of the loaded .wav
        self.loaded_text = audio_name

        # If we don't stop the existing, sound, the sound
        # won't play until the previous sound has stopped.
        self.channel_text.stop()

        self.channel_text.set_volume(self.volume_text)
        self.channel_text.play()

