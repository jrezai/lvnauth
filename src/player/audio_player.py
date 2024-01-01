"""
Copyright 2023, 2024 Jobin Rezai

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

        # Limit it to 3 audio channels (excluding the music channel)
        # (built-in pygame music channel) - Music channel
        # 0 - Sound FX channel
        # 1 - Voice channel
        # 2 - Text (letter) channel
        pygame.mixer.set_num_channels(3)

        self.channel_fx: pygame.mixer.Channel
        self.channel_fx = pygame.mixer.Channel(0)

        self.channel_voice: pygame.mixer.Channel
        self.channel_voice = pygame.mixer.Channel(1)

        self.channel_text: pygame.mixer.Channel
        self.channel_text = pygame.mixer.Channel(2)

        self.loaded_music = None
        self.loaded_fx = None
        self.loaded_voice = None
        self.loaded_text = None

        # Volume is 0 to 1 (ie: 0.5 means 50% volume)
        self._volume_music = 1
        self._volume_sound = 1
        self._volume_voice = 1
        self._volume_text = 1
        
    def stop_audio(self, audio_channel: AudioChannel):
        """
        Stop the audio on a specific channel,
        if the channel has been initialized.
        """

        if audio_channel == AudioChannel.MUSIC:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()

        elif audio_channel == AudioChannel.FX:
            if self.channel_fx:
                self.channel_fx.stop()

        #elif audio_channel == AudioChannel.TEXT:
            #if self.channel_text:
                #self.channel_text.stop()
                
        elif audio_channel == AudioChannel.VOICE:
            if self.channel_voice.get_busy():
                self.channel_voice.stop()
                
        elif audio_channel == AudioChannel.ALL:
            if self.channel_voice.get_busy():
                self.channel_voice.stop()

            if self.channel_fx.get_busy():
                self.channel_fx.stop()

            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()

    @property
    def volume_text(self):
        return self._volume_text

    @volume_text.setter
    def volume_text(self, value: float):
        self._volume_text = value

        # Set the volume for the channel.
        self.channel_text.set_volume(value)

    @property
    def volume_sound(self):
        return self._volume_sound

    @volume_sound.setter
    def volume_sound(self, value: float):
        self._volume_sound = value

        # Set the volume for the channel
        self.channel_fx.set_volume(value)
          
    @property
    def volume_voice(self):
        return self._volume_voice

    @volume_voice.setter
    def volume_voice(self, value: float):
        self._volume_voice = value

        # Set the volume for the channel
        self.channel_voice.set_volume(value)
    
    @property
    def volume_music(self):
        return self._volume_music

    @volume_music.setter
    def volume_music(self, value: float):
        self._volume_music = value

        # Set the volume for the channel
        pygame.mixer.music.set_volume(value)

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

        else:
            return

        # Get the bytes of the sound
        sound_bytes =\
            Passer.active_story.data_requester.get_audio(content_type=content_type,
                                                         item_name=audio_name)

        if not sound_bytes:
            return

        elif audio_channel == AudioChannel.MUSIC:

            self._play_music(audio_name=audio_name,
                             bytes_data=sound_bytes,
                             loop_music=loop_music)

        else:
            self._play_audio_in_channel(audio_channel=audio_channel,
                                        audio_name=audio_name,
                                        bytes_data=sound_bytes)

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

        # If the requested music is different than what's playing, stop the music.
        if pygame.mixer.music.get_busy() and self.loaded_music != audio_name:
            pygame.mixer.music.stop()

        # If the music channel is playing something, it's the same as what is being requested,
        # so don't interrupt it.
        # The music will need to be stopped first if the music needs to start from the beginning.
        elif pygame.mixer.music.get_busy():
            return

        # pygame works well with BytesIO
        # Convert the bytes sound to a BytesIO stream
        io_bytes_data = BytesIO(bytes_data)

        pygame.mixer.music.set_volume(self.volume_music)

        # Play the music data
        pygame.mixer.music.load(io_bytes_data, namehint=audio_name)

        # Save the filename of the loaded .wav/.ogg
        self.loaded_music = audio_name

        if loop_music:
            # Continuously loop the music.
            pygame.mixer.music.play(loops=-1)
        else:
            # Play the music with no loop.
            pygame.mixer.music.play()

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

    def _play_audio_in_channel(self, audio_channel: AudioChannel, audio_name: str, bytes_data: bytes):
        """
        Play an audio file from bytes data, in a specific audio channel.

        Music is not played in this method; music is using pygame's built-in music module.

        Arguments:

        - audio_channel: the audio channel to play bytes_data in.
        
        - audio_name: the resource/item name of the sound to be played.
        
        - bytes_data: the bytes representation of the wav/ogg data.
        """

        if audio_channel == AudioChannel.FX:
            channel = self.channel_fx
            volume = self.volume_sound

        elif audio_channel == AudioChannel.VOICE:
            channel = self.channel_voice
            volume = self.volume_voice

        elif audio_channel == AudioChannel.TEXT:
            channel = self.channel_text
            volume = self.volume_text

        else:
            return

        # If the requested audio is different than what's playing, stop the existing audio.
        if channel.get_busy() and self.loaded_text != audio_name:
            channel.stop()

        # pygame works well with BytesIO
        # Convert the bytes sound to a BytesIO stream
        io_bytes_data = BytesIO(bytes_data)

        # Initialize a new sound object.
        sound = pygame.mixer.Sound(file=io_bytes_data)

        # Save the filename of the loaded .wav/.ogg
        self.loaded_text = audio_name

        channel.set_volume(volume)
        channel.play(sound)
