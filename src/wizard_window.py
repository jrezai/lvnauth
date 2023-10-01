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

import pathlib
import tkinter as tk
import pygubu
from tkinter import messagebox
from tkinter import ttk
from tkinter import colorchooser
from typing import Dict
from enum import Enum, auto
from project_snapshot import ProjectSnapshot
from entrylimit import EntryWithLimit


PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "wizard.ui"
TEXT_CREATE_DIALOG_UI = PROJECT_PATH / "ui" / "text_create_dialog.ui"


class Purpose(Enum):
    BACKGROUND = auto()
    CHARACTER = auto()
    OBJECT = auto()
    FONT_SPRITE = auto()
    DIALOG = auto()
    ACTION = auto()  # such as <halt>
    AUDIO = auto()
    MUSIC = auto()
    REUSABLE_SCRIPT = auto() # such as <call> or <after>
    SCENE_SCRIPT = auto() # such as <scene>


class TextCreateDialogFrame:
    def __init__(self, master=None):
        
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(TEXT_CREATE_DIALOG_UI)
        # Main widget
        self.mainframe = builder.get_object("frame_text_create_dialog", master)
        self.master = master
        builder.connect_callbacks(self)


        # Intro animation frame in the Run tab
        
        # We use this for disabling or enabling all the widgets in this frame,
        # depending if an intro animation is set or not.
        self.frame_run_intro_animation_script: ttk.Frame
        self.frame_run_intro_animation_script =\
            self.builder.get_object("frame_run_intro_animation_script")
        
        # We use this for disabling or enabling all the widgets in this frame,
        # depending if an outro animation is set or not.
        self.frame_run_outro_animation_script: ttk.Frame
        self.frame_run_outro_animation_script =\
            self.builder.get_object("frame_run_outro_animation_script")

        """
        Size and Position tab
        """
        self.v_width = self.builder.get_variable("v_width")
        self.v_height = self.builder.get_variable("v_height")
        self.v_rounded_corners = self.builder.get_variable("v_rounded_corners")
        self.cb_dialog_position = self.builder.get_object("cb_dialog_position")

        # Default values
        self.v_width.set(400)
        self.v_height.set(200)
        
        self.cb_dialog_position.configure(state="normal")
        self.cb_dialog_position.insert(0, "mid bottom")
        self.cb_dialog_position.configure(state="readonly")

        
        """
        Animation tab
        """
        self.cb_intro_animation = self.builder.get_object("cb_intro_animation")
        self.cb_outro_animation = self.builder.get_object("cb_outro_animation")
        self.v_animation_speed = self.builder.get_variable("v_animation_speed")

        # Default values
        self.cb_intro_animation.configure(state="normal")
        self.cb_intro_animation.insert(0, "scale up width and height")
        self.cb_intro_animation.configure(state="readonly")

        self.cb_outro_animation.configure(state="normal")
        self.cb_outro_animation.insert(0, "fade out")
        self.cb_outro_animation.configure(state="readonly")

        self.v_animation_speed.set(5)


        """
        Colours tab
        """
        self.lbl_backcolor: ttk.Label
        self.lbl_backcolor = self.builder.get_object("lbl_backcolor")
        self.v_opacity = self.builder.get_variable("v_opacity")
        
        self.v_opacity.set(200)
        
        self.lbl_backcolor_border: ttk.Label
        self.lbl_backcolor_border =\
            self.builder.get_object("lbl_backcolor_border")
        
        self.v_opacity_border = self.builder.get_variable("v_opacity_border")
        self.v_opacity_border.set(200)
        
        self.v_border_width = self.builder.get_variable("v_border_width")
        self.v_border_width.set(0)
        
        
        
        """
        Padding tab
        """
        self.v_padding_x = self.builder.get_variable("v_padding_x")
        self.v_padding_y = self.builder.get_variable("v_padding_y")
        
        # Default values
        self.v_padding_x.set(0)
        self.v_padding_y.set(0)

        """
        Comboboxes in the Run tab (run reusable script on event)
        """
        self.cb_reusable_on_intro_starting =\
            builder.get_object("cb_reusable_on_intro_starting")

        self.cb_reusable_on_intro_finished =\
            builder.get_object("cb_reusable_on_intro_finished")

        self.cb_reusable_on_outro_starting =\
            builder.get_object("cb_reusable_on_outro_starting")
        
        self.cb_reusable_on_outro_finished =\
            builder.get_object("cb_reusable_on_outro_finished")
        
        
        """
        Halt tab
        """
        self.cb_resuable_on_halt = builder.get_object("cb_resuable_on_halt")
        self.cb_resuable_on_unhalt = builder.get_object("cb_resuable_on_unhalt")


        self._populate_run_comboboxes()

    def _populate_run_comboboxes(self):
        """
        Populate the comboboxes int he Run tab with all
        the reusable scripts.
        """
        combobox: ttk.Combobox
        for combobox in (self.cb_reusable_on_intro_finished,
                         self.cb_reusable_on_intro_starting,
                         self.cb_reusable_on_outro_finished,
                         self.cb_reusable_on_outro_starting,
                         self.cb_resuable_on_halt,
                         self.cb_resuable_on_unhalt):
            
            combobox.configure(values=tuple(ProjectSnapshot.reusables.keys()),
                               state="readonly")

    def on_intro_animation_changed(self, event):
        """
        The intro animation combobox selection has changed.
        
        If 'no animation' is selected, disable the 'Run' tab combobox,
        'When intro animation is starting'.
        """

        if self.cb_intro_animation.get() == "no animation":
            set_state = "disabled"
        else:
            set_state = "!disabled"

        # Disable or enable all the widgets in this frame.
        for w in self.frame_run_intro_animation_script.winfo_children():
            
            # We need to know whether this widget is a TCombobox or not.
            # If it is, set the state to 'readonly' when we're enabling it.
            widget_class =\
                self.frame_run_intro_animation_script.nametowidget(w).winfo_class()

            if widget_class == "TCombobox" and set_state == "!disabled":
                w.configure(state="readonly")
            else:
                w.configure(state=set_state)
            
    def on_outro_animation_changed(self, event):
        """
        The outro animation combobox selection has changed.
        
        If 'no animation' is selected, disable the 'Run' tab combobox,
        'When outro animation is starting'.
        """
        
        if self.cb_outro_animation.get() == "no animation":
            set_state = "disabled"
        else:
            set_state = "!disabled"

        # Disable or enable all the widgets in this frame.
        for w in self.frame_run_outro_animation_script.winfo_children():
            
            # We need to know whether this widget is a TCombobox or not.
            # If it is, set the state to 'readonly' when we're enabling it.
            widget_class =\
                self.frame_run_outro_animation_script.nametowidget(w).winfo_class()

            if widget_class == "TCombobox" and set_state == "!disabled":
                w.configure(state="readonly")
            else:
                w.configure(state=set_state)

    def on_change_color_clicked(self, widget_id):
        """
        Show the colour chooser dialog for the background or border.
        
        The 'Change Colour' button has been clicked.
        """
        
        if widget_id == "btn_change_border_color":
            # Border colour
            lbl_widget = self.lbl_backcolor_border
        else:
            # Background colour
            lbl_widget = self.lbl_backcolor
        
        current_color_hex = lbl_widget.cget("background")
        current_color_rgb = lbl_widget.winfo_rgb(current_color_hex)

        # winfo_rgb() returns a maximum value of 65535 instead of 255,
        # for some reason, we need to divide each color (rgb) by 256
        # to get a max 255 value.
        red, green, blue = current_color_rgb

        if red > 0:
            red = red // 256
        if green > 0:
            green = green // 256
        if blue > 0:
            blue = blue // 256

        # Record the new max-255 color values
        current_color_rgb = (red, green, blue)

        color = colorchooser.askcolor(parent=self.master.winfo_toplevel(),
                                      title="Background Colour",
                                      initialcolor=current_color_rgb)

        # The return value will be like this if a colour is chosen:
        # ((0, 153, 0), '#009900')
        
        # Or like this if no color is chosen
        # (None, None)
        hex_new_color = color[1]

        if not hex_new_color:
            return
        
        lbl_widget.configure(background=hex_new_color)

class WizardWindow:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow = builder.get_object("toplevel1", master)
        builder.connect_callbacks(self)
        
        self.sb_vertical = builder.get_object("sb_vertical")

        # The sub-frame will be put into the frame below.
        self.frame_contents_outer = builder.get_object("frame_contents_outer")
        
        self.lbl_header = builder.get_object("lbl_header")
        self.lbl_purpose = builder.get_object("lbl_purpose")

        self.treeview_commands: ttk.Treeview
        self.treeview_commands = builder.get_object("treeview_commands")
        
        # Connect treeview horizontal scrollbar
        self.sb_vertical.configure(command=self.treeview_commands.yview)
        self.treeview_commands.configure(yscrollcommand=self.sb_vertical.set)
        
        # The page that is currently being displayed.
        # We need to record it here so that we can ungrid it using this
        # varibable, before displaying a different page.
        self.active_page: WizardListing
        self.active_page = None

        # When the 'OK' button is clicked, this variable
        # will then contain the generated command which gets
        # read by the caller of this object.
        self.generated_command = None

        # Key: command name (ie: load_background)
        # Value: page (a WizardListing object)
        self.pages = {}

        default_page = DefaultPage(parent_frame=self.frame_contents_outer,
                                   header_label=self.lbl_header,
                                   purpose_label=self.lbl_purpose,
                                   treeview_commands=None,
                                   parent_display_text=None,
                                   sub_display_text=None,
                                   command_name="Wizard Command Window",
                                   purpose_line="This wizard will make it easier to use commands in your story.")


        page_audio_load =\
            AudioLoad(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="load_audio",
                         command_name="load_audio",
                         purpose_line="Prepare an audio file to be played.")

        page_music_load =\
            AudioLoad(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="load_music",
                         command_name="load_music",
                         purpose_line="Prepare a music file to be played.")

        page_audio_play_music =\
            AudioPlay(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="play_music",
                         command_name="play_music",
                         purpose_line="Play audio in the music channel.")
        
        page_audio_play_sound =\
            AudioPlay(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="play_sound",
                         command_name="play_sound",
                         purpose_line="Play a sound effect in the sound channel.")

        page_audio_play_voice =\
            AudioPlay(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="play_voice",
                         command_name="play_voice",
                         purpose_line="Play audio in the voice channel.")


        page_audio_stop_fx =\
            AudioStop(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="stop_fx",
                         command_name="stop_fx",
                         purpose_line="Stops the audio in the FX channel.",
                         when_to_use="When you want to stop playing an audio effect.")
        
        page_audio_stop_all_audio =\
            AudioStop(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="stop_all_audio",
                         command_name="stop_all_audio",
                         purpose_line="Stops playing the audio for: effects, voices, music.",
                         when_to_use="When you want to stop playing audio effects, voices, and music.\n"
                         "No error will occur if no audio is playing.")


        page_audio_stop_music =\
            AudioStop(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="stop_music",
                         command_name="stop_music",
                         purpose_line="Stops the audio in the music channel.",
                         when_to_use="When you want to stop playing music.")

        page_audio_stop_voice =\
            AudioStop(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="stop_voice",
                         command_name="stop_voice",
                         purpose_line="Stops the audio in the voice channel.",
                         when_to_use="When you want to stop playing audio in the voice channel.")


        page_audio_volume_fx =\
            Audio_Volume(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="volume_fx",
                         command_name="volume_fx",
                         purpose_line="Sets the sound effects volume.",
                         scale_from_value=0,
                         scale_to_value=100,
                         scale_instructions="Volume (0-100):\n"
                         "0 = muted  100 = max volume",
                         scale_default_value=100)

        page_audio_volume_music =\
            Audio_Volume(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="volume_music",
                         command_name="volume_music",
                         purpose_line="Sets the music volume.",
                         scale_from_value=0,
                         scale_to_value=100,
                         scale_instructions="Volume (0-100):\n"
                         "0 = muted  100 = max volume",
                         scale_default_value=100)

        page_audio_volume_text =\
            Audio_Volume(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="volume_text",
                         command_name="volume_text",
                         purpose_line="Sets the gradual letter-by-letter volume.\n\n"
                         "The audio gets chosen using <dialog_text_sound>",
                         scale_from_value=0,
                         scale_to_value=100,
                         scale_instructions="Volume (0-100):\n"
                         "0 = muted  100 = max volume",
                         scale_default_value=100)

        page_audio_volume_voice =\
            Audio_Volume(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="volume_voice",
                         command_name="volume_voice",
                         purpose_line="Sets the voice channel volume.",
                         scale_from_value=0,
                         scale_to_value=100,
                         scale_instructions="Volume (0-100):\n"
                         "0 = muted  100 = max volume",
                         scale_default_value=100)

        page_audio_dialog_text_sound =\
            DialogTextSound(parent_frame=self.frame_contents_outer,
                            header_label=self.lbl_header,
                            purpose_label=self.lbl_purpose,
                            treeview_commands=self.treeview_commands,
                            parent_display_text="Audio",
                            sub_display_text="dialog_text_sound",
                            command_name="dialog_text_sound",
                            purpose_line="Set audio to play for each gradually shown letter.\n"
                            "Only works for gradually-shown text (non-fading).")


        page_audio_dialog_text_sound_clear =\
            DialogTextSoundClear(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Audio",
                                 sub_display_text="dialog_text_sound_clear",
                                 command_name="dialog_text_sound_clear",
                                 purpose_line="Set no audio to play for each gradually shown letter.",
                                 when_to_use="When you no longer want to have any audio play\nfor each letter that is shown one by one.")


        page_load_background =\
            Background_LoadBackground(parent_frame=self.frame_contents_outer,
                                      header_label=self.lbl_header,
                                      purpose_label=self.lbl_purpose,
                                      treeview_commands=self.treeview_commands,
                                      parent_display_text="Background",
                                      sub_display_text="load_background",
                                      command_name="load_background",
                                      purpose_line="Load a background sprite into memory.")

        page_show_background =\
            BackgroundShow(parent_frame=self.frame_contents_outer,
                           header_label=self.lbl_header,
                           purpose_label=self.lbl_purpose,
                           treeview_commands=self.treeview_commands,
                           parent_display_text="Background",
                           sub_display_text="background_show",
                           command_name="background_show",
                           purpose_line="Show a specific a background sprite in the story.")

        page_hide_background =\
            BackgroundHide(parent_frame=self.frame_contents_outer,
                           header_label=self.lbl_header,
                           purpose_label=self.lbl_purpose,
                           treeview_commands=self.treeview_commands,
                           parent_display_text="Background",
                           sub_display_text="background_hide",
                           command_name="background_hide",
                           purpose_line="Hide a specific a background sprite in the story.")

        page_load_character =\
            Character_LoadCharacter(parent_frame=self.frame_contents_outer,
                                    header_label=self.lbl_header,
                                    purpose_label=self.lbl_purpose,
                                    treeview_commands=self.treeview_commands,
                                    parent_display_text="Character",
                                    sub_display_text="load_character",
                                    command_name="load_character",
                                    purpose_line="Load a character sprite into memory.")

        page_show_character =\
            CharacterShow(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Character",
                          sub_display_text="character_show",
                          command_name="character_show",
                          purpose_line="Shows the given sprite and it hides the currently visible\n"
                          "sprite with the same general alias as the one we’re about to show.")


        page_hide_character =\
            CharacterHide(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Character",
                          sub_display_text="character_hide",
                          command_name="character_hide",
                          purpose_line="Hides the given sprite.")


        page_character_flip_both =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Character",
                          sub_display_text="character_flip_both",
                          command_name="character_flip_both",
                          purpose_line="Flips the given sprite both horizontally and vertically.")


        page_character_flip_horizontal =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Character",
                          sub_display_text="character_flip_horizontal",
                          command_name="character_flip_horizontal",
                          purpose_line="Flips the given sprite horizontally.")


        page_character_flip_vertical =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Character",
                          sub_display_text="character_flip_vertical",
                          command_name="character_flip_vertical",
                          purpose_line="Flips the given sprite vertically.")
        

        page_character_after_fading_stop =\
            CharacterAfterFadingStop(parent_frame=self.frame_contents_outer,
                                    header_label=self.lbl_header,
                                    purpose_label=self.lbl_purpose,
                                    treeview_commands=self.treeview_commands,
                                    parent_display_text="Character",
                                    sub_display_text="character_after_fading_stop",
                                    command_name="character_after_fading_stop",
                                    purpose_line="Run a reusable script after a specific character sprite stops fading.")

        page_character_fade_current_value =\
            CharacterFadeCurrentValue(parent_frame=self.frame_contents_outer,
                                      header_label=self.lbl_header,
                                      purpose_label=self.lbl_purpose,
                                      treeview_commands=self.treeview_commands,
                                      parent_display_text="Character",
                                      sub_display_text="character_fade_current_value",
                                      command_name="character_fade_current_value",
                                      purpose_line="Set the opacity level of a specific character.\n"
                                      "Note: the character sprite must already be visible.",
                                      from_value=0,
                                      to_value=255,
                                      amount_usage_info="Opacity level:\n"
                                      "0=fully transparent  255=fully opaque",
                                      amount_name="opacity level")

        page_character_fade_delay =\
            CharacterFadeDelay(parent_frame=self.frame_contents_outer,
                               header_label=self.lbl_header,
                               purpose_label=self.lbl_purpose,
                               treeview_commands=self.treeview_commands,
                               parent_display_text="Character",
                               sub_display_text="character_fade_delay",
                               command_name="character_fade_delay",
                               purpose_line="Specify the number of frames to skip for a sprite's fade animation.\n"
                               "This is used to create an extra-slow fade effect.\n\n"
                               "Example: a value of 30 (frames) will delay the fade every 1 second.\n"
                               "Note: the character sprite must already be visible.",
                               from_value=1,
                               to_value=120,
                               amount_usage_info="Number of frames to skip:",
                               amount_name="number of frames to skip")

        page_character_fade_speed =\
            CharacterFadeSpeed(parent_frame=self.frame_contents_outer,
                               header_label=self.lbl_header,
                               purpose_label=self.lbl_purpose,
                               treeview_commands=self.treeview_commands,
                               parent_display_text="Character",
                               sub_display_text="character_fade_speed",
                               command_name="character_fade_speed",
                               purpose_line="Set the fade-speed of a character sprite.\n"
                               "Note: the character sprite must already be visible.",
                               radio_button_instructions="Fade direction:",
                               radio_button_text_1="Fade in",
                               radio_button_text_2="Fade out",
                               radio_button_value_1="fade in",
                               radio_button_value_2="fade out",
                               default_radio_button_value="fade in",
                               scale_default_value=5,
                               scale_from_value=1,
                               scale_to_value=100,
                               scale_instructions="Fade speed (1 to 100):")

        page_character_fade_until =\
            CharacterFadeUntil(parent_frame=self.frame_contents_outer,
                               header_label=self.lbl_header,
                               purpose_label=self.lbl_purpose,
                               treeview_commands=self.treeview_commands,
                               parent_display_text="Character",
                               sub_display_text="character_fade_until",
                               command_name="character_fade_until",
                               purpose_line="Indicate at what fade level a fade animation should stop.\n"
                               "Note: the character sprite must already be visible.",
                               scale_instructions="Stop fading when the opacity reaches... (0 to 255)\n"
                               "0 = fully transparent  255 = fully opaque",
                               scale_from_value=0,
                               scale_to_value=255,
                               scale_default_value=128)

        page_character_start_fading =\
            CharacterStartFading(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Character",
                                 sub_display_text="character_start_fading",
                                 command_name="character_start_fading",
                                 purpose_line="Starts a character sprite fading animation.\n"
                                 "Note: the character sprite must already be visible.")

        page_character_stop_fading =\
            CharacterStopFading(parent_frame=self.frame_contents_outer,
                                header_label=self.lbl_header,
                                purpose_label=self.lbl_purpose,
                                treeview_commands=self.treeview_commands,
                                parent_display_text="Character",
                                sub_display_text="character_stop_fading",
                                command_name="character_stop_fading",
                                purpose_line="Stops a character sprite fading animation.\n"
                                "Note: the character sprite must already be visible.")

        page_character_after_rotating_stop =\
            CharacterAfterRotatingStop(parent_frame=self.frame_contents_outer,
                                       header_label=self.lbl_header,
                                       purpose_label=self.lbl_purpose,
                                       treeview_commands=self.treeview_commands,
                                       parent_display_text="Character",
                                       sub_display_text="character_after_rotating_stop",
                                       command_name="character_after_rotating_stop",
                                       purpose_line="When a specific sprite image stops rotating, run a reusable script.\n"
                                       "Note: the character sprite must already be visible.")

        page_character_rotate_current_value =\
            CharacterRotateCurrentValue(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Character",
                                        sub_display_text="character_rotate_current_value",
                                        command_name="character_rotate_current_value",
                                        purpose_line="Immediately set a sprite's rotation value (no gradual animation).\n"
                                        "Note: the character sprite must already be visible.")

        page_character_rotate_delay =\
            CharacterRotateDelay(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Character",
                                 sub_display_text="character_rotate_delay",
                                 command_name="character_rotate_delay",
                                 purpose_line="Specify the number of frames to skip for this sprite's rotate animation.\n"
                                 "This is used to create an extra-slow rotating effect.\n\n"
                                 "Example: a value of 2 means to delay the rotation animation\n"
                                 "by 2 frames each time.\n\n"
                                 "Note: the character sprite must already be visible.",
                                 from_value=1,
                                 to_value=120,
                                 amount_usage_info="Number of frames to skip:",
                                 amount_name="number of frames to skip")

        page_character_rotate_speed =\
            CharacterRotateSpeed(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Character",
                                 sub_display_text="character_rotate_speed",
                                 command_name="character_rotate_speed",
                                 purpose_line="Set the rotation speed percentage of a character sprite.\n"
                                 "The speed range is 1 (slowest) to 100 (fastest).\n\n"
                                 "Note: the character sprite must already be visible.",
                                 radio_button_instructions="Rotate direction:",
                                 radio_button_text_1="Clockwise",
                                 radio_button_text_2="Counterclockwise",
                                 radio_button_value_1="clockwise",
                                 radio_button_value_2="counterclockwise",
                                 default_radio_button_value="clockwise",
                                 scale_default_value=5,
                                 scale_from_value=1,
                                 scale_to_value=100,
                                 scale_instructions="Rotation speed (1 to 100):")

        page_character_rotate_until =\
            CharacterRotateUntil(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Character",
                                 sub_display_text="character_rotate_until",
                                 command_name="character_rotate_until",
                                 purpose_line="Indicate at what degree a rotation animation should stop.\n"
                                 "Note: the character sprite must already be visible.",
                                 scale_instructions="Stop rotating when the angle reaches... (0 to 359)",
                                 scale_from_value=0,
                                 scale_to_value=359,
                                 scale_default_value=180)

        page_character_start_rotating =\
            CharacterStartRotating(parent_frame=self.frame_contents_outer,
                                   header_label=self.lbl_header,
                                   purpose_label=self.lbl_purpose,
                                   treeview_commands=self.treeview_commands,
                                   parent_display_text="Character",
                                   sub_display_text="character_start_rotating",
                                   command_name="character_start_rotating",
                                   purpose_line="Starts a character sprite rotation animation.\n"
                                   "Note: the character sprite must already be visible.")

        page_character_stop_rotating =\
            CharacterStopRotating(parent_frame=self.frame_contents_outer,
                                  header_label=self.lbl_header,
                                  purpose_label=self.lbl_purpose,
                                  treeview_commands=self.treeview_commands,
                                  parent_display_text="Character",
                                  sub_display_text="character_stop_rotating",
                                  command_name="character_stop_rotating",
                                  purpose_line="Stops a character sprite rotation animation.\n"
                                  "Note: the character sprite must already be visible.")

        page_character_after_scaling_stop =\
            CharacterAfterScalingStop(parent_frame=self.frame_contents_outer,
                                      header_label=self.lbl_header,
                                      purpose_label=self.lbl_purpose,
                                      treeview_commands=self.treeview_commands,
                                      parent_display_text="Character",
                                      sub_display_text="character_after_scaling_stop",
                                      command_name="character_after_scaling_stop",
                                      purpose_line="When a specific sprite image stops scaling using <character_scale_until>,\n"
                                      "run a specific reusable script.\n\n"
                                      "Note: the character sprite must already be visible.")

        page_character_scale_by =\
            CharacterScaleBy(parent_frame=self.frame_contents_outer,
                             header_label=self.lbl_header,
                             purpose_label=self.lbl_purpose,
                             treeview_commands=self.treeview_commands,
                             parent_display_text="Character",
                             sub_display_text="character_scale_by",
                             command_name="character_scale_by",
                             purpose_line="Sets the scale speed of a character sprite.\n"
                             "Note: the character sprite must already be visible.",
                             radio_button_instructions="Scale direction:",
                             radio_button_text_1="Scale up",
                             radio_button_text_2="Scale down",
                             radio_button_value_1="scale up",
                             radio_button_value_2="scale down",
                             default_radio_button_value="scale up",
                             scale_default_value=5,
                             scale_from_value=1,
                             scale_to_value=100,
                             scale_instructions="Scale speed (1 to 100):")

        page_character_scale_current_value =\
            CharacterScaleCurrentValue(parent_frame=self.frame_contents_outer,
                                       header_label=self.lbl_header,
                                       purpose_label=self.lbl_purpose,
                                       treeview_commands=self.treeview_commands,
                                       parent_display_text="Character",
                                       sub_display_text="character_scale_current_value",
                                       command_name="character_scale_current_value",
                                       purpose_line="Immediately set a sprite's scale value (no gradual animation).\n"
                                       "Note: the character sprite must already be visible.",
                                       from_value=0,
                                       to_value=100,
                                       amount_usage_info="Scale value:\n"
                                       "(example: 2 means twice as big as the original size)",
                                       amount_name="scale")

        page_character_scale_delay =\
            CharacterScaleDelay(parent_frame=self.frame_contents_outer,
                                header_label=self.lbl_header,
                                purpose_label=self.lbl_purpose,
                                treeview_commands=self.treeview_commands,
                                parent_display_text="Character",
                                sub_display_text="character_scale_delay",
                                command_name="character_scale_delay",
                                purpose_line="Specify the number of frames to skip for this sprite's scale animation.\n"
                                "This is used to create an extra-slow scaling effect.\n\n"
                                "Example: a value of 2 means to delay the scaling animation\n"
                                "by 2 frames each time.\n\n"
                                "Note: the character sprite must already be visible.",
                                from_value=1,
                                to_value=120,
                                amount_usage_info="Number of frames to skip:",
                                amount_name="number of frames to skip")

        page_character_scale_until =\
            CharacterScaleUntil(parent_frame=self.frame_contents_outer,
                                header_label=self.lbl_header,
                                purpose_label=self.lbl_purpose,
                                treeview_commands=self.treeview_commands,
                                parent_display_text="Character",
                                sub_display_text="character_scale_until",
                                command_name="character_scale_until",
                                purpose_line="Indicate at what scale a scaling animation should stop.\n"
                                "Note: the character sprite must already be visible.",
                                scale_instructions="Stop scaling when the scale reaches... (0 to 100)",
                                scale_from_value=0,
                                scale_to_value=100,
                                scale_default_value=2)

        page_character_start_scaling =\
            CharacterStartScaling(parent_frame=self.frame_contents_outer,
                                  header_label=self.lbl_header,
                                  purpose_label=self.lbl_purpose,
                                  treeview_commands=self.treeview_commands,
                                  parent_display_text="Character",
                                  sub_display_text="character_start_scaling",
                                  command_name="character_start_scaling",
                                  purpose_line="Starts a character sprite scaling animation.\n\n"
                                  "Note: the character sprite must already be visible.\n"
                                  "Also, <character_scale_until> should be used prior.")

        page_character_stop_scaling =\
            CharacterStopScaling(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Character",
                                 sub_display_text="character_stop_scaling",
                                 command_name="character_stop_scaling",
                                 purpose_line="Stops a character sprite scaling animation.\n\n"
                                 "The scale value is not lost. If the scaling is started again,\n"
                                 "it will resume from where it stopped last.\n\n"
                                 "Note: the character sprite must already be visible.")

        page_character_after_movement_stop =\
            CharacterAfterMovementStop(parent_frame=self.frame_contents_outer,
                                       header_label=self.lbl_header,
                                       purpose_label=self.lbl_purpose,
                                       treeview_commands=self.treeview_commands,
                                       parent_display_text="Character",
                                       sub_display_text="character_after_movement_stop",
                                       command_name="character_after_movement_stop",
                                       purpose_line="Run a reusable script after a specific character sprite stops moving.")
   
        page_character_stop_movement_condition =\
            CharacterStopMovementCondition(parent_frame=self.frame_contents_outer,
                                      header_label=self.lbl_header,
                                      purpose_label=self.lbl_purpose,
                                      treeview_commands=self.treeview_commands,
                                      parent_display_text="Character",
                                      sub_display_text="character_stop_movement_condition",
                                      command_name="character_stop_movement_condition",
                                      purpose_line="Add a condition that defines when to stop a moving sprite.\n\n"
                                      "Multiple stop conditions can be added for a single sprite by calling\n"
                                      "this command multiple times with different parameters.\n\n"
                                      "Once all the stop conditions have been satisfied, then the specified sprite\n"
                                      "will stop moving.")

        page_character_move =\
            CharacterMove(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Character",
                          sub_display_text="character_move",
                          command_name="character_move",
                          purpose_line="Sets the movement amount and direction of a character sprite.")

        page_character_move_delay =\
            CharacterMoveDelay(parent_frame=self.frame_contents_outer,
                               header_label=self.lbl_header,
                               purpose_label=self.lbl_purpose,
                               treeview_commands=self.treeview_commands,
                               parent_display_text="Character",
                               sub_display_text="character_move_delay",
                               command_name="character_move_delay",
                               purpose_line="Specify the number of frames to skip for a sprite's movement animation.\n"
                               "This is used to create an extra-slow movement.\n\n"
                               "The higher the values, the slower the animation.",
                               spinbox_1_instructions="Number of frames to skip\n"
                               "(horizontal movement):",
                               spinbox_2_instructions="Number of frames to skip\n"
                               "(vertical movement):",
                               spinbox_1_subject="horizontal",
                               spinbox_2_subject="vertical",
                               subject_sentence_1="the number of frames to skip for horizontal movements",
                               subject_sentence_2="the number of frames to skip for vertical movements",
                               spinbox_from_value=1,
                               spinbox_to_value=120)

        page_character_start_moving =\
            CharacterStartMoving(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Character",
                                 sub_display_text="character_start_moving",
                                 command_name="character_start_moving",
                                 purpose_line="Starts a movement animation on specific character sprite.")


        page_character_set_position_x =\
            CharacterSetPositionX(parent_frame=self.frame_contents_outer,
                                  header_label=self.lbl_header,
                                  purpose_label=self.lbl_purpose,
                                  treeview_commands=self.treeview_commands,
                                  parent_display_text="Character",
                                  sub_display_text="character_set_position_x",
                                  command_name="character_set_position_x",
                                  purpose_line="Sets the horizontal position of a specific character relative to the top-left\n"
                                  "corner of the sprite.\n\n"
                                  "Note: the character sprite must already be visible.",
                                  direction="horizontal")

        page_character_set_position_y =\
            CharacterSetPositionY(parent_frame=self.frame_contents_outer,
                                  header_label=self.lbl_header,
                                  purpose_label=self.lbl_purpose,
                                  treeview_commands=self.treeview_commands,
                                  parent_display_text="Character",
                                  sub_display_text="character_set_position_y",
                                  command_name="character_set_position_y",
                                  purpose_line="Sets the vertical position of a specific character relative to the top-left\n"
                                  "corner of the sprite.\n\n"
                                  "Note: the character sprite must already be visible.",
                                  direction="vertical")                                  

        page_character_set_center =\
            CharacterSetCenter(parent_frame=self.frame_contents_outer,
                               header_label=self.lbl_header,
                               purpose_label=self.lbl_purpose,
                               treeview_commands=self.treeview_commands,
                               parent_display_text="Character",
                               sub_display_text="character_set_center",
                               command_name="character_set_center",
                               purpose_line="Set the center point of the sprite.\n"
                               "corner of the sprite.\n\n"
                               "Note: the character sprite must already be visible.",
                               spinbox_1_instructions="Center of X (horizontal position):",
                               spinbox_2_instructions="Center of Y (vertical position):",
                               spinbox_1_subject="horizontal",
                               spinbox_2_subject="vertical",
                               subject_sentence_1="the horizontal center position",
                               subject_sentence_2="the vertical center position",
                               spinbox_from_value=-5000,
                               spinbox_to_value=9000)


        """
        Object
        """

        page_load_object =\
            Character_LoadCharacter(parent_frame=self.frame_contents_outer,
                                    header_label=self.lbl_header,
                                    purpose_label=self.lbl_purpose,
                                    treeview_commands=self.treeview_commands,
                                    parent_display_text="Object",
                                    sub_display_text="load_object",
                                    command_name="load_object",
                                    purpose_line="Load an object sprite into memory.")

        page_show_object =\
            CharacterShow(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Object",
                          sub_display_text="object_show",
                          command_name="object_show",
                          purpose_line="Shows the given sprite and it hides the currently visible\n"
                          "sprite with the same general alias as the one we’re about to show.")

        page_hide_object =\
            CharacterHide(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Object",
                          sub_display_text="object_hide",
                          command_name="object_hide",
                          purpose_line="Hides the given sprite.")
        
        
        page_object_flip_both =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Object",
                          sub_display_text="object_flip_both",
                          command_name="object_flip_both",
                          purpose_line="Flips the given sprite both horizontally and vertically.")


        page_object_flip_horizontal =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Object",
                          sub_display_text="object_flip_horizontal",
                          command_name="object_flip_horizontal",
                          purpose_line="Flips the given sprite horizontally.")


        page_object_flip_vertical =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Object",
                          sub_display_text="object_flip_vertical",
                          command_name="object_flip_vertical",
                          purpose_line="Flips the given sprite vertically.")
        

        page_object_after_fading_stop =\
            CharacterAfterFadingStop(parent_frame=self.frame_contents_outer,
                                    header_label=self.lbl_header,
                                    purpose_label=self.lbl_purpose,
                                    treeview_commands=self.treeview_commands,
                                    parent_display_text="Object",
                                    sub_display_text="object_after_fading_stop",
                                    command_name="object_after_fading_stop",
                                    purpose_line="Run a reusable script after a specific object sprite stops fading.")

        page_object_fade_current_value =\
            CharacterFadeCurrentValue(parent_frame=self.frame_contents_outer,
                                      header_label=self.lbl_header,
                                      purpose_label=self.lbl_purpose,
                                      treeview_commands=self.treeview_commands,
                                      parent_display_text="Object",
                                      sub_display_text="object_fade_current_value",
                                      command_name="object_fade_current_value",
                                      purpose_line="Set the opacity level of a specific object.\n"
                                      "Note: the object sprite must already be visible.",
                                      from_value=0,
                                      to_value=255,
                                      amount_usage_info="Opacity level:\n"
                                      "0=fully transparent  255=fully opaque",
                                      amount_name="opacity level")

        page_object_fade_delay =\
            CharacterFadeDelay(parent_frame=self.frame_contents_outer,
                               header_label=self.lbl_header,
                               purpose_label=self.lbl_purpose,
                               treeview_commands=self.treeview_commands,
                               parent_display_text="Object",
                               sub_display_text="object_fade_delay",
                               command_name="object_fade_delay",
                               purpose_line="Specify the number of frames to skip for a sprite's fade animation.\n"
                               "This is used to create an extra-slow fade effect.\n\n"
                               "Example: a value of 30 (frames) will delay the fade every 1 second.\n"
                               "Note: the character sprite must already be visible.",
                               from_value=1,
                               to_value=120,
                               amount_usage_info="Number of frames to skip:",
                               amount_name="number of frames to skip")

        page_object_fade_speed =\
            CharacterFadeSpeed(parent_frame=self.frame_contents_outer,
                               header_label=self.lbl_header,
                               purpose_label=self.lbl_purpose,
                               treeview_commands=self.treeview_commands,
                               parent_display_text="Object",
                               sub_display_text="object_fade_speed",
                               command_name="object_fade_speed",
                               purpose_line="Set the fade-speed of an object sprite.\n"
                               "Note: the object sprite must already be visible.",
                               radio_button_instructions="Fade direction:",
                               radio_button_text_1="Fade in",
                               radio_button_text_2="Fade out",
                               radio_button_value_1="fade in",
                               radio_button_value_2="fade out",
                               default_radio_button_value="fade in",
                               scale_default_value=5,
                               scale_from_value=1,
                               scale_to_value=100,
                               scale_instructions="Fade speed (1 to 100):")

        page_object_fade_until =\
            CharacterFadeUntil(parent_frame=self.frame_contents_outer,
                               header_label=self.lbl_header,
                               purpose_label=self.lbl_purpose,
                               treeview_commands=self.treeview_commands,
                               parent_display_text="Object",
                               sub_display_text="object_fade_until",
                               command_name="object_fade_until",
                               purpose_line="Indicate at what fade level a fade animation should stop.\n"
                               "Note: the object sprite must already be visible.",
                               scale_instructions="Stop fading when the opacity reaches... (0 to 255)\n"
                               "0 = fully transparent  255 = fully opaque",
                               scale_from_value=0,
                               scale_to_value=255,
                               scale_default_value=128)

        page_object_start_fading =\
            CharacterStartFading(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Object",
                                 sub_display_text="object_start_fading",
                                 command_name="object_start_fading",
                                 purpose_line="Starts an object sprite fading animation.\n"
                                 "Note: the object sprite must already be visible.")

        page_object_stop_fading =\
            CharacterStopFading(parent_frame=self.frame_contents_outer,
                                header_label=self.lbl_header,
                                purpose_label=self.lbl_purpose,
                                treeview_commands=self.treeview_commands,
                                parent_display_text="Object",
                                sub_display_text="object_stop_fading",
                                command_name="object_stop_fading",
                                purpose_line="Stops an object sprite fading animation.\n"
                                "Note: the object sprite must already be visible.")

        page_object_after_rotating_stop =\
            CharacterAfterRotatingStop(parent_frame=self.frame_contents_outer,
                                       header_label=self.lbl_header,
                                       purpose_label=self.lbl_purpose,
                                       treeview_commands=self.treeview_commands,
                                       parent_display_text="Object",
                                       sub_display_text="object_after_rotating_stop",
                                       command_name="object_after_rotating_stop",
                                       purpose_line="When a specific sprite image stops rotating, run a reusable script.\n"
                                       "Note: the object sprite must already be visible.")

        page_object_rotate_current_value =\
            CharacterRotateCurrentValue(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Object",
                                        sub_display_text="object_rotate_current_value",
                                        command_name="object_rotate_current_value",
                                        purpose_line="Immediately set a sprite's rotation value (no gradual animation).\n"
                                        "Note: the object sprite must already be visible.")

        page_object_rotate_delay =\
            CharacterRotateDelay(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Object",
                                 sub_display_text="object_rotate_delay",
                                 command_name="object_rotate_delay",
                                 purpose_line="Specify the number of frames to skip for this sprite's rotate animation.\n"
                                 "This is used to create an extra-slow rotating effect.\n\n"
                                 "Example: a value of 2 means to delay the rotation animation\n"
                                 "by 2 frames each time.\n\n"
                                 "Note: the object sprite must already be visible.",
                                 from_value=1,
                                 to_value=120,
                                 amount_usage_info="Number of frames to skip:",
                                 amount_name="number of frames to skip")

        page_object_rotate_speed =\
            CharacterRotateSpeed(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Object",
                                 sub_display_text="object_rotate_speed",
                                 command_name="object_rotate_speed",
                                 purpose_line="Set the rotation speed percentage of an object sprite.\n"
                                 "The speed range is 1 (slowest) to 100 (fastest).\n\n"
                                 "Note: the object sprite must already be visible.",
                                 radio_button_instructions="Rotate direction:",
                                 radio_button_text_1="Clockwise",
                                 radio_button_text_2="Counterclockwise",
                                 radio_button_value_1="clockwise",
                                 radio_button_value_2="counterclockwise",
                                 default_radio_button_value="clockwise",
                                 scale_default_value=5,
                                 scale_from_value=1,
                                 scale_to_value=100,
                                 scale_instructions="Rotation speed (1 to 100):")

        page_object_rotate_until =\
            CharacterRotateUntil(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Object",
                                 sub_display_text="object_rotate_until",
                                 command_name="object_rotate_until",
                                 purpose_line="Indicate at what degree a rotation animation should stop.\n"
                                 "Note: the object sprite must already be visible.",
                                 scale_instructions="Stop rotating when the angle reaches... (0 to 359)",
                                 scale_from_value=0,
                                 scale_to_value=359,
                                 scale_default_value=180)

        page_object_start_rotating =\
            CharacterStartRotating(parent_frame=self.frame_contents_outer,
                                   header_label=self.lbl_header,
                                   purpose_label=self.lbl_purpose,
                                   treeview_commands=self.treeview_commands,
                                   parent_display_text="Object",
                                   sub_display_text="object_start_rotating",
                                   command_name="object_start_rotating",
                                   purpose_line="Starts an object sprite rotation animation.\n"
                                   "Note: the object sprite must already be visible.")

        page_object_stop_rotating =\
            CharacterStopRotating(parent_frame=self.frame_contents_outer,
                                  header_label=self.lbl_header,
                                  purpose_label=self.lbl_purpose,
                                  treeview_commands=self.treeview_commands,
                                  parent_display_text="Object",
                                  sub_display_text="object_stop_rotating",
                                  command_name="object_stop_rotating",
                                  purpose_line="Stops an object sprite rotation animation.\n"
                                  "Note: the object sprite must already be visible.")

        page_object_after_scaling_stop =\
            CharacterAfterScalingStop(parent_frame=self.frame_contents_outer,
                                      header_label=self.lbl_header,
                                      purpose_label=self.lbl_purpose,
                                      treeview_commands=self.treeview_commands,
                                      parent_display_text="Object",
                                      sub_display_text="object_after_scaling_stop",
                                      command_name="object_after_scaling_stop",
                                      purpose_line="When a specific sprite image stops scaling using <object_scale_until>,\n"
                                      "run a specific reusable script.\n\n"
                                      "Note: the object sprite must already be visible.")

        page_object_scale_by =\
            CharacterScaleBy(parent_frame=self.frame_contents_outer,
                             header_label=self.lbl_header,
                             purpose_label=self.lbl_purpose,
                             treeview_commands=self.treeview_commands,
                             parent_display_text="Object",
                             sub_display_text="object_scale_by",
                             command_name="object_scale_by",
                             purpose_line="Sets the scale speed of an object sprite.\n"
                             "Note: the object sprite must already be visible.",
                             radio_button_instructions="Scale direction:",
                             radio_button_text_1="Scale up",
                             radio_button_text_2="Scale down",
                             radio_button_value_1="scale up",
                             radio_button_value_2="scale down",
                             default_radio_button_value="scale up",
                             scale_default_value=5,
                             scale_from_value=1,
                             scale_to_value=100,
                             scale_instructions="Scale speed (1 to 100):")

        page_object_scale_current_value =\
            CharacterScaleCurrentValue(parent_frame=self.frame_contents_outer,
                                       header_label=self.lbl_header,
                                       purpose_label=self.lbl_purpose,
                                       treeview_commands=self.treeview_commands,
                                       parent_display_text="Object",
                                       sub_display_text="object_scale_current_value",
                                       command_name="object_scale_current_value",
                                       purpose_line="Immediately set a sprite's scale value (no gradual animation).\n"
                                       "Note: the object sprite must already be visible.",
                                       from_value=0,
                                       to_value=100,
                                       amount_usage_info="Scale value:\n"
                                       "(example: 2 means twice as big as the original size)",
                                       amount_name="scale")

        page_object_scale_delay =\
            CharacterScaleDelay(parent_frame=self.frame_contents_outer,
                                header_label=self.lbl_header,
                                purpose_label=self.lbl_purpose,
                                treeview_commands=self.treeview_commands,
                                parent_display_text="Object",
                                sub_display_text="object_scale_delay",
                                command_name="object_scale_delay",
                                purpose_line="Specify the number of frames to skip for this sprite's scale animation.\n"
                                "This is used to create an extra-slow scaling effect.\n\n"
                                "Example: a value of 2 means to delay the scaling animation\n"
                                "by 2 frames each time.\n\n"
                                "Note: the object sprite must already be visible.",
                                from_value=1,
                                to_value=120,
                                amount_usage_info="Number of frames to skip:",
                                amount_name="number of frames to skip")

        page_object_scale_until =\
            CharacterScaleUntil(parent_frame=self.frame_contents_outer,
                                header_label=self.lbl_header,
                                purpose_label=self.lbl_purpose,
                                treeview_commands=self.treeview_commands,
                                parent_display_text="Object",
                                sub_display_text="object_scale_until",
                                command_name="object_scale_until",
                                purpose_line="Indicate at what scale a scaling animation should stop.\n"
                                "Note: the object sprite must already be visible.",
                                scale_instructions="Stop scaling when the scale reaches... (0 to 100)",
                                scale_from_value=0,
                                scale_to_value=100,
                                scale_default_value=2)

        page_object_start_scaling =\
            CharacterStartScaling(parent_frame=self.frame_contents_outer,
                                  header_label=self.lbl_header,
                                  purpose_label=self.lbl_purpose,
                                  treeview_commands=self.treeview_commands,
                                  parent_display_text="Object",
                                  sub_display_text="object_start_scaling",
                                  command_name="object_start_scaling",
                                  purpose_line="Starts an object sprite scaling animation.\n\n"
                                  "Note: the object sprite must already be visible.\n"
                                  "Also, <object_scale_until> should be used prior.")

        page_object_stop_scaling =\
            CharacterStopScaling(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Object",
                                 sub_display_text="object_stop_scaling",
                                 command_name="object_stop_scaling",
                                 purpose_line="Stops an object sprite scaling animation.\n\n"
                                 "The scale value is not lost. If the scaling is started again,\n"
                                 "it will resume from where it stopped last.\n\n"
                                 "Note: the object sprite must already be visible.")

        page_object_after_movement_stop =\
            CharacterAfterMovementStop(parent_frame=self.frame_contents_outer,
                                       header_label=self.lbl_header,
                                       purpose_label=self.lbl_purpose,
                                       treeview_commands=self.treeview_commands,
                                       parent_display_text="Object",
                                       sub_display_text="object_after_movement_stop",
                                       command_name="object_after_movement_stop",
                                       purpose_line="Run a reusable script after a specific object sprite stops moving.")
   
        page_object_stop_movement_condition =\
            CharacterStopMovementCondition(parent_frame=self.frame_contents_outer,
                                      header_label=self.lbl_header,
                                      purpose_label=self.lbl_purpose,
                                      treeview_commands=self.treeview_commands,
                                      parent_display_text="Object",
                                      sub_display_text="object_stop_movement_condition",
                                      command_name="object_stop_movement_condition",
                                      purpose_line="Add a condition that defines when to stop a moving sprite.\n\n"
                                      "Multiple stop conditions can be added for a single sprite by calling\n"
                                      "this command multiple times with different parameters.\n\n"
                                      "Once all the stop conditions have been satisfied, then the specified sprite\n"
                                      "will stop moving.")

        page_object_move =\
            CharacterMove(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Object",
                          sub_display_text="object_move",
                          command_name="object_move",
                          purpose_line="Sets the movement amount and direction of an object sprite.")

        page_object_move_delay =\
            CharacterMoveDelay(parent_frame=self.frame_contents_outer,
                               header_label=self.lbl_header,
                               purpose_label=self.lbl_purpose,
                               treeview_commands=self.treeview_commands,
                               parent_display_text="Object",
                               sub_display_text="object_move_delay",
                               command_name="object_move_delay",
                               purpose_line="Specify the number of frames to skip for a sprite's movement animation.\n"
                               "This is used to create an extra-slow movement.\n\n"
                               "The higher the values, the slower the animation.",
                               spinbox_1_instructions="Number of frames to skip\n"
                               "(horizontal movement):",
                               spinbox_2_instructions="Number of frames to skip\n"
                               "(vertical movement):",
                               spinbox_1_subject="horizontal",
                               spinbox_2_subject="vertical",
                               subject_sentence_1="the number of frames to skip for horizontal movements",
                               subject_sentence_2="the number of frames to skip for vertical movements",
                               spinbox_from_value=1,
                               spinbox_to_value=120)

        page_object_start_moving =\
            CharacterStartMoving(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Object",
                                 sub_display_text="object_start_moving",
                                 command_name="object_start_moving",
                                 purpose_line="Starts a movement animation on specific object sprite.")


        page_object_set_position_x =\
            CharacterSetPositionX(parent_frame=self.frame_contents_outer,
                                  header_label=self.lbl_header,
                                  purpose_label=self.lbl_purpose,
                                  treeview_commands=self.treeview_commands,
                                  parent_display_text="Object",
                                  sub_display_text="object_set_position_x",
                                  command_name="object_set_position_x",
                                  purpose_line="Sets the horizontal position of a specific object relative to the top-left\n"
                                  "corner of the sprite.\n\n"
                                  "Note: the object sprite must already be visible.",
                                  direction="horizontal")

        page_object_set_position_y =\
            CharacterSetPositionY(parent_frame=self.frame_contents_outer,
                                  header_label=self.lbl_header,
                                  purpose_label=self.lbl_purpose,
                                  treeview_commands=self.treeview_commands,
                                  parent_display_text="Object",
                                  sub_display_text="object_set_position_y",
                                  command_name="object_set_position_y",
                                  purpose_line="Sets the vertical position of a specific object relative to the top-left\n"
                                  "corner of the sprite.\n\n"
                                  "Note: the object sprite must already be visible.",
                                  direction="vertical")

        page_object_set_center =\
            CharacterSetCenter(parent_frame=self.frame_contents_outer,
                               header_label=self.lbl_header,
                               purpose_label=self.lbl_purpose,
                               treeview_commands=self.treeview_commands,
                               parent_display_text="Object",
                               sub_display_text="object_set_center",
                               command_name="object_set_center",
                               purpose_line="Set the center point of the sprite.\n"
                               "corner of the sprite.\n\n"
                               "Note: the object sprite must already be visible.",
                               spinbox_1_instructions="Center of X (horizontal position):",
                               spinbox_2_instructions="Center of Y (vertical position):",
                               spinbox_1_subject="horizontal",
                               spinbox_2_subject="vertical",
                               subject_sentence_1="the horizontal center position",
                               subject_sentence_2="the vertical center position",
                               spinbox_from_value=-5000,
                               spinbox_to_value=9000)

        

        """
        Dialog
        """
    
    
        page_dialog_define =\
            TextDialogDefine(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Dialog",
                                 sub_display_text="text_dialog_define",
                                 command_name="text_dialog_define",
                                 purpose_line="Create a dialog rectangle for character text to appear in.")

        page_dialog_show =\
            TextDialogShow(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Dialog",
                                 sub_display_text="text_dialog_show",
                                 command_name="text_dialog_show",
                                 purpose_line="Show a dialog rectangle that has already been defined using <text_dialog_define>.",
                                 when_to_use="When a character wants to speak or for narration text.")
    
        page_dialog_close =\
            TextDialogClose(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Dialog",
                                 sub_display_text="text_dialog_close",
                                 command_name="text_dialog_close",
                                 purpose_line="Close the dialog by initiating its outro animation.",
                                 when_to_use="When all the characters finish speaking.")

        page_dialog_halt =\
            DialogHalt(parent_frame=self.frame_contents_outer,
                       header_label=self.lbl_header,
                       purpose_label=self.lbl_purpose,
                       treeview_commands=self.treeview_commands,
                       parent_display_text="Dialog",
                       sub_display_text="halt",
                       command_name="halt",
                       purpose_line="Pause the dialog text until the viewer clicks the mouse or presses a key.",
                       when_to_use="When you want to give the viewer a chance to pause and read.")

        page_dialog_halt_auto =\
            DialogHaltAuto(parent_frame=self.frame_contents_outer,
                       header_label=self.lbl_header,
                       purpose_label=self.lbl_purpose,
                       treeview_commands=self.treeview_commands,
                       parent_display_text="Dialog",
                       sub_display_text="halt_auto",
                       command_name="halt_auto",
                       purpose_line="Pause the dialog text for a specific number of frames.",
                       scale_instructions="Choose the number of frames to halt the dialog.\nNote: 60 frames is 1 second.",
                       scale_from_value=1,
                       scale_to_value=600,
                       scale_default_value=120)
        
        page_dialog_continue =\
            DialogContinue(parent_frame=self.frame_contents_outer,
                       header_label=self.lbl_header,
                       purpose_label=self.lbl_purpose,
                       treeview_commands=self.treeview_commands,
                       parent_display_text="Dialog",
                       sub_display_text="continue",
                       command_name="continue",
                       purpose_line="Stay on the same line as the previous text.")

        page_load_dialog =\
            Character_LoadCharacter(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Dialog",
                                        sub_display_text="load_dialog_sprite",
                                        command_name="load_dialog_sprite",
                                        purpose_line="Load an dialog sprite into memory.")
    
        page_show_dialog =\
                CharacterShow(parent_frame=self.frame_contents_outer,
                              header_label=self.lbl_header,
                              purpose_label=self.lbl_purpose,
                              treeview_commands=self.treeview_commands,
                              parent_display_text="Dialog",
                              sub_display_text="dialog_sprite_show",
                              command_name="dialog_sprite_show",
                              purpose_line="Shows the given sprite and it hides the currently visible\n"
                              "sprite with the same general alias as the one we’re about to show.")
    
        page_hide_dialog =\
                CharacterHide(parent_frame=self.frame_contents_outer,
                              header_label=self.lbl_header,
                              purpose_label=self.lbl_purpose,
                              treeview_commands=self.treeview_commands,
                              parent_display_text="Dialog",
                              sub_display_text="dialog_sprite_hide",
                              command_name="dialog_sprite_hide",
                              purpose_line="Hides the given sprite.")

        page_dialog_flip_both =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Dialog",
                          sub_display_text="dialog_sprite_flip_both",
                          command_name="dialog_sprite_flip_both",
                          purpose_line="Flips the given sprite both horizontally and vertically.")


        page_dialog_flip_horizontal =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Dialog",
                          sub_display_text="dialog_sprite_flip_horizontal",
                          command_name="dialog_sprite_flip_horizontal",
                          purpose_line="Flips the given sprite horizontally.")


        page_dialog_flip_vertical =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Dialog",
                          sub_display_text="dialog_sprite_flip_vertical",
                          command_name="dialog_sprite_flip_vertical",
                          purpose_line="Flips the given sprite vertically.")

    
        page_dialog_after_fading_stop =\
                CharacterAfterFadingStop(parent_frame=self.frame_contents_outer,
                                         header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Dialog",
                                        sub_display_text="dialog_sprite_after_fading_stop",
                                        command_name="dialog_sprite_after_fading_stop",
                                        purpose_line="Run a reusable script after a specific dialog sprite stops fading.")
    
        page_dialog_fade_current_value =\
                CharacterFadeCurrentValue(parent_frame=self.frame_contents_outer,
                                          header_label=self.lbl_header,
                                          purpose_label=self.lbl_purpose,
                                          treeview_commands=self.treeview_commands,
                                          parent_display_text="Dialog",
                                          sub_display_text="dialog_sprite_fade_current_value",
                                          command_name="dialog_sprite_fade_current_value",
                                          purpose_line="Set the opacity level of a specific dialog.\n"
                                          "Note: the dialog sprite must already be visible.",
                                          from_value=0,
                                          to_value=255,
                                          amount_usage_info="Opacity level:\n"
                                          "0=fully transparent  255=fully opaque",
                                          amount_name="opacity level")
    
        page_dialog_fade_delay =\
                CharacterFadeDelay(parent_frame=self.frame_contents_outer,
                                   header_label=self.lbl_header,
                                   purpose_label=self.lbl_purpose,
                                   treeview_commands=self.treeview_commands,
                                   parent_display_text="Dialog",
                                   sub_display_text="dialog_sprite_fade_delay",
                                   command_name="dialog_sprite_fade_delay",
                                   purpose_line="Specify the number of frames to skip for a sprite's fade animation.\n"
                                   "This is used to create an extra-slow fade effect.\n\n"
                                   "Example: a value of 30 (frames) will delay the fade every 1 second.\n"
                                   "Note: the dialog sprite must already be visible.",
                                   from_value=1,
                                   to_value=120,
                                   amount_usage_info="Number of frames to skip:",
                                   amount_name="number of frames to skip")
    
        page_dialog_fade_speed =\
                CharacterFadeSpeed(parent_frame=self.frame_contents_outer,
                                   header_label=self.lbl_header,
                                   purpose_label=self.lbl_purpose,
                                   treeview_commands=self.treeview_commands,
                                   parent_display_text="Dialog",
                                   sub_display_text="dialog_sprite_fade_speed",
                                   command_name="dialog_sprite_fade_speed",
                                   purpose_line="Set the fade-speed of an dialog sprite.\n"
                                   "Note: the dialog sprite must already be visible.",
                                   radio_button_instructions="Fade direction:",
                                   radio_button_text_1="Fade in",
                                   radio_button_text_2="Fade out",
                                   radio_button_value_1="fade in",
                                   radio_button_value_2="fade out",
                                   default_radio_button_value="fade in",
                                   scale_default_value=5,
                                   scale_from_value=1,
                                   scale_to_value=100,
                                   scale_instructions="Fade speed (1 to 100):")
    
        page_dialog_fade_until =\
                CharacterFadeUntil(parent_frame=self.frame_contents_outer,
                                   header_label=self.lbl_header,
                                   purpose_label=self.lbl_purpose,
                                   treeview_commands=self.treeview_commands,
                                   parent_display_text="Dialog",
                                   sub_display_text="dialog_sprite_fade_until",
                                   command_name="dialog_sprite_fade_until",
                                   purpose_line="Indicate at what fade level a fade animation should stop.\n"
                                   "Note: the dialog sprite must already be visible.",
                                   scale_instructions="Stop fading when the opacity reaches... (0 to 255)\n"
                                   "0 = fully transparent  255 = fully opaque",
                                   scale_from_value=0,
                                   scale_to_value=255,
                                   scale_default_value=128)
    
        page_dialog_start_fading =\
                CharacterStartFading(parent_frame=self.frame_contents_outer,
                                     header_label=self.lbl_header,
                                     purpose_label=self.lbl_purpose,
                                     treeview_commands=self.treeview_commands,
                                     parent_display_text="Dialog",
                                     sub_display_text="dialog_sprite_start_fading",
                                     command_name="dialog_sprite_start_fading",
                                     purpose_line="Starts an dialog sprite fading animation.\n"
                                     "Note: the dialog sprite must already be visible.")
    
        page_dialog_stop_fading =\
                CharacterStopFading(parent_frame=self.frame_contents_outer,
                                    header_label=self.lbl_header,
                                    purpose_label=self.lbl_purpose,
                                    treeview_commands=self.treeview_commands,
                                    parent_display_text="Dialog",
                                    sub_display_text="dialog_sprite_stop_fading",
                                    command_name="dialog_sprite_stop_fading",
                                    purpose_line="Stops an dialog sprite fading animation.\n"
                                    "Note: the dialog sprite must already be visible.")
    
        page_dialog_after_rotating_stop =\
                CharacterAfterRotatingStop(parent_frame=self.frame_contents_outer,
                                           header_label=self.lbl_header,
                                           purpose_label=self.lbl_purpose,
                                           treeview_commands=self.treeview_commands,
                                           parent_display_text="Dialog",
                                           sub_display_text="dialog_sprite_after_rotating_stop",
                                           command_name="dialog_sprite_after_rotating_stop",
                                           purpose_line="When a specific sprite image stops rotating, run a reusable script.\n"
                                           "Note: the dialog sprite must already be visible.")
    
        page_dialog_rotate_current_value =\
                CharacterRotateCurrentValue(parent_frame=self.frame_contents_outer,
                                            header_label=self.lbl_header,
                                            purpose_label=self.lbl_purpose,
                                            treeview_commands=self.treeview_commands,
                                            parent_display_text="Dialog",
                                            sub_display_text="dialog_sprite_rotate_current_value",
                                            command_name="dialog_sprite_rotate_current_value",
                                            purpose_line="Immediately set a sprite's rotation value (no gradual animation).\n"
                                            "Note: the dialog sprite must already be visible.")
    
        page_dialog_rotate_delay =\
                CharacterRotateDelay(parent_frame=self.frame_contents_outer,
                                     header_label=self.lbl_header,
                                     purpose_label=self.lbl_purpose,
                                     treeview_commands=self.treeview_commands,
                                     parent_display_text="Dialog",
                                     sub_display_text="dialog_sprite_rotate_delay",
                                     command_name="dialog_sprite_rotate_delay",
                                     purpose_line="Specify the number of frames to skip for this sprite's rotate animation.\n"
                                     "This is used to create an extra-slow rotating effect.\n\n"
                                     "Example: a value of 2 means to delay the rotation animation\n"
                                     "by 2 frames each time.\n\n"
                                     "Note: the dialog sprite must already be visible.",
                                     from_value=1,
                                     to_value=120,
                                     amount_usage_info="Number of frames to skip:",
                                     amount_name="number of frames to skip")
    
        page_dialog_rotate_speed =\
                CharacterRotateSpeed(parent_frame=self.frame_contents_outer,
                                     header_label=self.lbl_header,
                                     purpose_label=self.lbl_purpose,
                                     treeview_commands=self.treeview_commands,
                                     parent_display_text="Dialog",
                                     sub_display_text="dialog_sprite_rotate_speed",
                                     command_name="dialog_sprite_rotate_speed",
                                     purpose_line="Set the rotation speed percentage of an dialog sprite.\n"
                                     "The speed range is 1 (slowest) to 100 (fastest).\n\n"
                                     "Note: the dialog sprite must already be visible.",
                                     radio_button_instructions="Rotate direction:",
                                     radio_button_text_1="Clockwise",
                                     radio_button_text_2="Counterclockwise",
                                     radio_button_value_1="clockwise",
                                     radio_button_value_2="counterclockwise",
                                     default_radio_button_value="clockwise",
                                     scale_default_value=5,
                                     scale_from_value=1,
                                     scale_to_value=100,
                                     scale_instructions="Rotation speed (1 to 100):")
    
        page_dialog_rotate_until =\
                CharacterRotateUntil(parent_frame=self.frame_contents_outer,
                                     header_label=self.lbl_header,
                                     purpose_label=self.lbl_purpose,
                                     treeview_commands=self.treeview_commands,
                                     parent_display_text="Dialog",
                                     sub_display_text="dialog_sprite_rotate_until",
                                     command_name="dialog_sprite_rotate_until",
                                     purpose_line="Indicate at what degree a rotation animation should stop.\n"
                                     "Note: the dialog sprite must already be visible.",
                                     scale_instructions="Stop rotating when the angle reaches... (0 to 359)",
                                     scale_from_value=0,
                                     scale_to_value=359,
                                     scale_default_value=180)
    
        page_dialog_start_rotating =\
                CharacterStartRotating(parent_frame=self.frame_contents_outer,
                                       header_label=self.lbl_header,
                                       purpose_label=self.lbl_purpose,
                                       treeview_commands=self.treeview_commands,
                                       parent_display_text="Dialog",
                                       sub_display_text="dialog_sprite_start_rotating",
                                       command_name="dialog_sprite_start_rotating",
                                       purpose_line="Starts an dialog sprite rotation animation.\n"
                                       "Note: the dialog sprite must already be visible.")
    
        page_dialog_stop_rotating =\
                CharacterStopRotating(parent_frame=self.frame_contents_outer,
                                      header_label=self.lbl_header,
                                      purpose_label=self.lbl_purpose,
                                      treeview_commands=self.treeview_commands,
                                      parent_display_text="Dialog",
                                      sub_display_text="dialog_sprite_stop_rotating",
                                      command_name="dialog_sprite_stop_rotating",
                                      purpose_line="Stops an dialog sprite rotation animation.\n"
                                      "Note: the dialog sprite must already be visible.")
    
        page_dialog_after_scaling_stop =\
                CharacterAfterScalingStop(parent_frame=self.frame_contents_outer,
                                          header_label=self.lbl_header,
                                          purpose_label=self.lbl_purpose,
                                          treeview_commands=self.treeview_commands,
                                          parent_display_text="Dialog",
                                          sub_display_text="dialog_sprite_after_scaling_stop",
                                          command_name="dialog_sprite_after_scaling_stop",
                                          purpose_line="When a specific sprite image stops scaling using <dialog_scale_until>,\n"
                                          "run a specific reusable script.\n\n"
                                          "Note: the dialog sprite must already be visible.")
    
        page_dialog_scale_by =\
                CharacterScaleBy(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Dialog",
                                 sub_display_text="dialog_sprite_scale_by",
                                 command_name="dialog_sprite_scale_by",
                                 purpose_line="Sets the scale speed of an dialog sprite.\n"
                                 "Note: the dialog sprite must already be visible.",
                                 radio_button_instructions="Scale direction:",
                                 radio_button_text_1="Scale up",
                                 radio_button_text_2="Scale down",
                                 radio_button_value_1="scale up",
                                 radio_button_value_2="scale down",
                                 default_radio_button_value="scale up",
                                 scale_default_value=5,
                                 scale_from_value=1,
                                 scale_to_value=100,
                                 scale_instructions="Scale speed (1 to 100):")
    
        page_dialog_scale_current_value =\
                CharacterScaleCurrentValue(parent_frame=self.frame_contents_outer,
                                           header_label=self.lbl_header,
                                           purpose_label=self.lbl_purpose,
                                           treeview_commands=self.treeview_commands,
                                           parent_display_text="Dialog",
                                           sub_display_text="dialog_sprite_scale_current_value",
                                           command_name="dialog_sprite_scale_current_value",
                                           purpose_line="Immediately set a sprite's scale value (no gradual animation).\n"
                                           "Note: the dialog sprite must already be visible.",
                                           from_value=0,
                                           to_value=100,
                                           amount_usage_info="Scale value:\n"
                                           "(example: 2 means twice as big as the original size)",
                                           amount_name="scale")
    
        page_dialog_scale_delay =\
                CharacterScaleDelay(parent_frame=self.frame_contents_outer,
                                    header_label=self.lbl_header,
                                    purpose_label=self.lbl_purpose,
                                    treeview_commands=self.treeview_commands,
                                    parent_display_text="Dialog",
                                    sub_display_text="dialog_sprite_scale_delay",
                                    command_name="dialog_sprite_scale_delay",
                                    purpose_line="Specify the number of frames to skip for this sprite's scale animation.\n"
                                    "This is used to create an extra-slow scaling effect.\n\n"
                                    "Example: a value of 2 means to delay the scaling animation\n"
                                    "by 2 frames each time.\n\n"
                                    "Note: the dialog sprite must already be visible.",
                                    from_value=1,
                                    to_value=120,
                                    amount_usage_info="Number of frames to skip:",
                                    amount_name="number of frames to skip")
    
        page_dialog_scale_until =\
                CharacterScaleUntil(parent_frame=self.frame_contents_outer,
                                    header_label=self.lbl_header,
                                    purpose_label=self.lbl_purpose,
                                    treeview_commands=self.treeview_commands,
                                    parent_display_text="Dialog",
                                    sub_display_text="dialog_sprite_scale_until",
                                    command_name="dialog_sprite_scale_until",
                                    purpose_line="Indicate at what scale a scaling animation should stop.\n"
                                    "Note: the dialog sprite must already be visible.",
                                    scale_instructions="Stop scaling when the scale reaches... (0 to 100)",
                                    scale_from_value=0,
                                    scale_to_value=100,
                                    scale_default_value=2)
    
        page_dialog_start_scaling =\
                CharacterStartScaling(parent_frame=self.frame_contents_outer,
                                      header_label=self.lbl_header,
                                      purpose_label=self.lbl_purpose,
                                      treeview_commands=self.treeview_commands,
                                      parent_display_text="Dialog",
                                      sub_display_text="dialog_sprite_start_scaling",
                                      command_name="dialog_sprite_start_scaling",
                                      purpose_line="Starts an dialog sprite scaling animation.\n\n"
                                      "Note: the dialog sprite must already be visible."
                                      "Also, <dialog_sprite_scale_until> should be used prior.")
    
        page_dialog_stop_scaling =\
                CharacterStopScaling(parent_frame=self.frame_contents_outer,
                                     header_label=self.lbl_header,
                                     purpose_label=self.lbl_purpose,
                                     treeview_commands=self.treeview_commands,
                                     parent_display_text="Dialog",
                                     sub_display_text="dialog_sprite_stop_scaling",
                                     command_name="dialog_sprite_stop_scaling",
                                     purpose_line="Stops an dialog sprite scaling animation.\n\n"
                                     "The scale value is not lost. If the scaling is started again,\n"
                                     "it will resume from where it stopped last.\n\n"
                                     "Note: the dialog sprite must already be visible.")
    
        page_dialog_after_movement_stop =\
                CharacterAfterMovementStop(parent_frame=self.frame_contents_outer,
                                           header_label=self.lbl_header,
                                           purpose_label=self.lbl_purpose,
                                           treeview_commands=self.treeview_commands,
                                           parent_display_text="Dialog",
                                           sub_display_text="dialog_sprite_after_movement_stop",
                                           command_name="dialog_sprite_after_movement_stop",
                                           purpose_line="Run a reusable script after a specific dialog sprite stops moving.")
    
        page_dialog_stop_movement_condition =\
                CharacterStopMovementCondition(parent_frame=self.frame_contents_outer,
                                               header_label=self.lbl_header,
                                          purpose_label=self.lbl_purpose,
                                          treeview_commands=self.treeview_commands,
                                          parent_display_text="Dialog",
                                          sub_display_text="dialog_sprite_stop_movement_condition",
                                          command_name="dialog_sprite_stop_movement_condition",
                                          purpose_line="Add a condition that defines when to stop a moving sprite.\n\n"
                                          "Multiple stop conditions can be added for a single sprite by calling\n"
                                          "this command multiple times with different parameters.\n\n"
                                          "Once all the stop conditions have been satisfied, then the specified sprite\n"
                                          "will stop moving.")
    
        page_dialog_move =\
                CharacterMove(parent_frame=self.frame_contents_outer,
                              header_label=self.lbl_header,
                              purpose_label=self.lbl_purpose,
                              treeview_commands=self.treeview_commands,
                              parent_display_text="Dialog",
                              sub_display_text="dialog_sprite_move",
                              command_name="dialog_sprite_move",
                              purpose_line="Sets the movement amount and direction of an dialog sprite.")
    
        page_dialog_move_delay =\
                CharacterMoveDelay(parent_frame=self.frame_contents_outer,
                                   header_label=self.lbl_header,
                                   purpose_label=self.lbl_purpose,
                                   treeview_commands=self.treeview_commands,
                                   parent_display_text="Dialog",
                                   sub_display_text="dialog_sprite_move_delay",
                                   command_name="dialog_sprite_move_delay",
                                   purpose_line="Specify the number of frames to skip for a sprite's movement animation.\n"
                                   "This is used to create an extra-slow movement.\n\n"
                                   "The higher the values, the slower the animation.",
                                   spinbox_1_instructions="Number of frames to skip\n"
                                   "(horizontal movement):",
                                   spinbox_2_instructions="Number of frames to skip\n"
                                   "(vertical movement):",
                                   spinbox_1_subject="horizontal",
                                   spinbox_2_subject="vertical",
                                   subject_sentence_1="the number of frames to skip for horizontal movements",
                                   subject_sentence_2="the number of frames to skip for vertical movements",
                                   spinbox_from_value=1,
                                   spinbox_to_value=120)
    
        page_dialog_start_moving =\
                CharacterStartMoving(parent_frame=self.frame_contents_outer,
                                     header_label=self.lbl_header,
                                     purpose_label=self.lbl_purpose,
                                     treeview_commands=self.treeview_commands,
                                     parent_display_text="Dialog",
                                     sub_display_text="dialog_sprite_start_moving",
                                     command_name="dialog_sprite_start_moving",
                                     purpose_line="Starts a movement animation on specific dialog sprite.")
    
    
        page_dialog_set_position_x =\
                CharacterSetPositionX(parent_frame=self.frame_contents_outer,
                                      header_label=self.lbl_header,
                                      purpose_label=self.lbl_purpose,
                                      treeview_commands=self.treeview_commands,
                                      parent_display_text="Dialog",
                                      sub_display_text="dialog_sprite_set_position_x",
                                      command_name="dialog_sprite_set_position_x",
                                      purpose_line="Sets the horizontal position of a specific dialog relative to the top-left\n"
                                      "corner of the sprite.\n\n"
                                      "Note: the dialog sprite must already be visible.",
                                      direction="horizontal")
    
        page_dialog_set_position_y =\
                CharacterSetPositionY(parent_frame=self.frame_contents_outer,
                                      header_label=self.lbl_header,
                                      purpose_label=self.lbl_purpose,
                                      treeview_commands=self.treeview_commands,
                                      parent_display_text="Dialog",
                                      sub_display_text="dialog_sprite_set_position_y",
                                      command_name="dialog_sprite_set_position_y",
                                      purpose_line="Sets the vertical position of a specific dialog relative to the top-left\n"
                                      "corner of the sprite.\n\n"
                                      "Note: the dialog sprite must already be visible.",
                                      direction="vertical")
    
        page_dialog_set_center =\
                CharacterSetCenter(parent_frame=self.frame_contents_outer,
                                   header_label=self.lbl_header,
                                   purpose_label=self.lbl_purpose,
                                   treeview_commands=self.treeview_commands,
                                   parent_display_text="Dialog",
                                   sub_display_text="dialog_sprite_set_center",
                                   command_name="dialog_sprite_set_center",
                                   purpose_line="Set the center point of the sprite.\n"
                                   "corner of the sprite.\n\n"
                                   "Note: the dialog sprite must already be visible.",
                                   spinbox_1_instructions="Center of X (horizontal position):",
                                   spinbox_2_instructions="Center of Y (vertical position):",
                                   spinbox_1_subject="horizontal",
                                   spinbox_2_subject="vertical",
                                   subject_sentence_1="the horizontal center position",
                                   subject_sentence_2="the vertical center position",
                                   spinbox_from_value=-5000,
                                   spinbox_to_value=9000)


        """
        Font
        """
        page_load_font =\
            Font_LoadFont(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Font",
                          sub_display_text="load_font_sprite",
                          command_name="load_font_sprite",
                          purpose_line="Load a font sprite into memory.")

        page_font =\
            Font_Font(parent_frame=self.frame_contents_outer,
                      header_label=self.lbl_header,
                      purpose_label=self.lbl_purpose,
                      treeview_commands=self.treeview_commands,
                      parent_display_text="Font",
                      sub_display_text="font",
                      command_name="font",
                      purpose_line="Sets the font to use for the next letter.")
        
        page_font_x =\
            Font_Position(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Font",
                          sub_display_text="font_x",
                          command_name="font_x",
                          purpose_line="Sets the horizontal position of where the dialog text should start,\n"
                          "relative to the text dialog.\nThe left-most edge of the dialog rectangle is 0 (zero).",
                          from_value=-50,
                          to_value=5000,
                          amount_usage_info="Set the horizontal position (x):",
                          amount_name="horizontal position")

        
        page_font_y =\
            Font_Position(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Font",
                          sub_display_text="font_y",
                          command_name="font_y",
                          purpose_line="Sets the vertical position of where the dialog text should start,\n"
                          "relative to the text dialog. The top of the dialog rectangle is 0 (zero).",
                          from_value=-50,
                          to_value=5000,
                          amount_usage_info="Set the vertical position (y):",
                          amount_name="vertical position")

        page_font_text_delay =\
            Font_TextDelay(parent_frame=self.frame_contents_outer,
                           header_label=self.lbl_header,
                           purpose_label=self.lbl_purpose,
                           treeview_commands=self.treeview_commands,
                           parent_display_text="Font",
                           sub_display_text="font_text_delay",
                           command_name="font_text_delay",
                           purpose_line="Sets the number of frames to skip when applying\n"
                           "gradual dialog text animation (letter-by-letter).\n"
                           "Does not apply to letter fade-ins",
                           scale_from_value=0,
                           scale_to_value=600,
                           scale_instructions="Delay (frames) (0-600):\n\n"
                           "For example: a value of 2 means: apply the letter by letter animation\n"
                           "every 2 frames. A value of 0 means apply the animation at every frame.",
                           scale_default_value=2)
        
        page_font_text_delay_punc =\
            Font_TextDelayPunc(parent_frame=self.frame_contents_outer,
                           header_label=self.lbl_header,
                           purpose_label=self.lbl_purpose,
                           treeview_commands=self.treeview_commands,
                           parent_display_text="Font",
                           sub_display_text="font_text_delay_punc",
                           command_name="font_text_delay_punc",
                           purpose_line="Sets the number of frames to skip *after* a specific letter is shown.\n"
                           "Only applies to gradual letter-by-letter text (not fade-ins).\n\n"
                           "This command can be used to cause a short delay\n"
                           "after punctuation marks, such as periods.\n\n"
                           "Note: this command only works with letters on the same line.",
                           scale_from_value=0,
                           scale_to_value=120,
                           scale_instructions="The number of frames to skip (0 to 120):",
                           scale_default_value=2)

        page_font_text_fade_speed =\
            Font_TextFadeSpeed(parent_frame=self.frame_contents_outer,
                               header_label=self.lbl_header,
                               purpose_label=self.lbl_purpose,
                               treeview_commands=self.treeview_commands,
                               parent_display_text="Font",
                               sub_display_text="font_text_fade_speed",
                               command_name="font_text_fade_speed",
                               purpose_line="Sets the fade speed of gradually-shown dialog text\n" +
                               "(letter-by-letter fade speed) and also the overall fade-in speed\n" +
                               "(non letter-by-letter)",
                               scale_from_value=1,
                               scale_to_value=10,
                               scale_instructions="Set the fade speed (1-10):\n"
                               "1 = slowest  10 = fastest",
                               scale_default_value=5)

        page_font_intro_animation =\
            Font_IntroAnimation(parent_frame=self.frame_contents_outer,
                                header_label=self.lbl_header,
                                purpose_label=self.lbl_purpose,
                                treeview_commands=self.treeview_commands,
                                parent_display_text="Font",
                                sub_display_text="font_intro_animation",
                                command_name="font_intro_animation",
                                purpose_line="Set the animation type when the character text is being displayed.",
                                instructions="Dialog text starting animation:",
                                values_to_choose=("sudden", "fade in", "gradual letter", "gradual letter fade in"))



        page_general_rest =\
            DialogHaltAuto(parent_frame=self.frame_contents_outer,
                       header_label=self.lbl_header,
                       purpose_label=self.lbl_purpose,
                       treeview_commands=self.treeview_commands,
                       parent_display_text="General",
                       sub_display_text="rest",
                       command_name="rest",
                       purpose_line="Pauses all chapter and scene scripts for a specific number of frames.\n"
                       "It does not pause reusable scripts, but can be used from a reusable script.\n\n"
                       "Purpose: to give the viewer a break from reading.\n\n"
                       "Example usage: use <rest> to pause the chapter/scenes scripts\n"
                       "and allow the viewer to watch an animation while music is playing.",
                       scale_instructions="Choose the number of frames to halt chapter/scenes.\nNote: 60 frames is 1 second.",
                       scale_from_value=1,
                       scale_to_value=600,
                       scale_default_value=120)        

        page_after =\
            ReusableScriptSelect(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="General",
                                 sub_display_text="after",
                                 command_name="after",
                                 purpose_line="Runs a reusable script after a number of frames have elapsed.\n\n"
                                 "Note: 60 frames is 1 second, 120 frames is 2 seconds, etc.\n"
                                 "Only one after-timer can be used at a time per reusable script name.", 
                                 spinbox_instructions="Choose the number of frames to elapse:",
                                 from_value=1,
                                 to_value=30000,
                                 amount_name="number of frames to elapse", 
                                 spinbox_default_value=120,
                                 show_delay_widgets=True)
        
        page_after_cancel =\
            ReusableScriptSelect(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="General",
                                 sub_display_text="after_cancel",
                                 command_name="after_cancel",
                                 purpose_line="Cancels an existing 'after' timer.")   

        page_after_cancel_all =\
            AfterCancelAll(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="General",
                                 sub_display_text="after_cancel_all",
                                 command_name="after_cancel_all",
                                 purpose_line="Cancels all after-timers.")
        
        page_call =\
            ReusableScriptSelect(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="General",
                                 sub_display_text="call",
                                 command_name="call",
                                 purpose_line="Run a reusable script.")           

        page_scene =\
            SceneScriptSelect(parent_frame=self.frame_contents_outer,
                              header_label=self.lbl_header,
                              purpose_label=self.lbl_purpose,
                              treeview_commands=self.treeview_commands,
                              parent_display_text="General",
                              sub_display_text="scene",
                              command_name="scene",
                              purpose_line="Run a scene in a specific chapter.")  

        self.pages["Home"] = default_page

        self.pages["load_audio"] = page_audio_load
        self.pages["load_music"] = page_music_load

        self.pages["play_music"] = page_audio_play_music
        self.pages["play_sound"] = page_audio_play_sound
        self.pages["play_voice"] = page_audio_play_voice
        
        self.pages["stop_all_audio"] = page_audio_stop_all_audio
        self.pages["stop_fx"] = page_audio_stop_fx
        self.pages["stop_music"] = page_audio_stop_music
        self.pages["stop_voice"] = page_audio_stop_voice
        
        self.pages["volume_fx"] = page_audio_volume_fx
        self.pages["volume_music"] = page_audio_volume_music
        self.pages["volume_text"] = page_audio_volume_text
        self.pages["volume_voice"] = page_audio_volume_voice

        self.pages["dialog_text_sound"] = page_audio_dialog_text_sound
        self.pages["dialog_text_sound_clear"] = page_audio_dialog_text_sound_clear

        self.pages["load_background"] = page_load_background
        self.pages["background_show"] = page_show_background
        self.pages["background_hide"] = page_hide_background

        self.pages["load_character"] = page_load_character
        self.pages["character_show"] = page_show_character
        self.pages["character_hide"] = page_hide_character
        
        self.pages["character_flip_both"] = page_character_flip_both
        self.pages["character_flip_horizontal"] = page_character_flip_horizontal
        self.pages["character_flip_vertical"] = page_character_flip_vertical
        
        self.pages["character_after_fading_stop"] = page_character_after_fading_stop
        self.pages["character_fade_current_value"] = page_character_fade_current_value
        self.pages["character_fade_delay"] = page_character_fade_delay
        self.pages["character_fade_speed"] = page_character_fade_speed
        self.pages["character_fade_until"] = page_character_fade_until
        self.pages["character_start_fading"] = page_character_start_fading
        self.pages["character_stop_fading"] = page_character_stop_fading
        
        self.pages["character_after_rotating_stop"] = page_character_after_rotating_stop
        self.pages["character_rotate_current_value"] = page_character_rotate_current_value
        self.pages["character_rotate_delay"] = page_character_rotate_delay
        self.pages["character_rotate_speed"] = page_character_rotate_speed
        self.pages["character_rotate_until"] = page_character_rotate_until
        self.pages["character_start_rotating"] = page_character_start_rotating
        self.pages["character_stop_rotating"] = page_character_stop_rotating

        self.pages["character_after_scaling_stop"] = page_character_after_scaling_stop
        self.pages["character_scale_by"] = page_character_scale_by
        self.pages["character_scale_current_value"] = page_character_scale_current_value
        self.pages["character_scale_delay"] = page_character_scale_delay
        self.pages["character_scale_until"] = page_character_scale_until
        self.pages["character_scale_delay"] = page_character_scale_delay
        self.pages["character_start_scaling"] = page_character_start_scaling
        self.pages["character_stop_scaling"] = page_character_stop_scaling

        self.pages["character_after_movement_stop"] = page_character_after_movement_stop
        self.pages["character_stop_movement_condition"] = page_character_stop_movement_condition
        self.pages["character_move"] = page_character_move
        self.pages["character_move_delay"] = page_character_move_delay
        self.pages["character_start_moving"] = page_character_start_moving
        self.pages["character_set_position_x"] = page_character_set_position_x
        self.pages["character_set_position_y"] = page_character_set_position_y
        self.pages["character_set_center"] = page_character_set_center
        
        """
        General
        """
        self.pages["after"] = page_after
        self.pages["after_cancel"] = page_after_cancel
        self.pages["after_cancel_all"] = page_after_cancel_all
        
        self.pages["rest"] = page_general_rest
        
        self.pages["call"] = page_call
        
        self.pages["scene"] = page_scene
        
        """
        Object
        """
        self.pages["load_object"] = page_load_object
        self.pages["object_show"] = page_show_object
        self.pages["object_hide"] = page_hide_object
        
        self.pages["object_flip_both"] = page_object_flip_both
        self.pages["object_flip_horizontal"] = page_object_flip_horizontal
        self.pages["object_flip_vertical"] = page_object_flip_vertical
        
        self.pages["object_after_fading_stop"] = page_object_after_fading_stop
        self.pages["object_fade_current_value"] = page_object_fade_current_value
        self.pages["object_fade_delay"] = page_object_fade_delay
        self.pages["object_fade_speed"] = page_object_fade_speed
        self.pages["object_fade_until"] = page_object_fade_until
        self.pages["object_start_fading"] = page_object_start_fading
        self.pages["object_stop_fading"] = page_object_stop_fading
        
        self.pages["object_after_rotating_stop"] = page_object_after_rotating_stop
        self.pages["object_rotate_current_value"] = page_object_rotate_current_value
        self.pages["object_rotate_delay"] = page_object_rotate_delay
        self.pages["object_rotate_speed"] = page_object_rotate_speed
        self.pages["object_rotate_until"] = page_object_rotate_until
        self.pages["object_start_rotating"] = page_object_start_rotating
        self.pages["object_stop_rotating"] = page_object_stop_rotating

        self.pages["object_after_scaling_stop"] = page_object_after_scaling_stop
        self.pages["object_scale_by"] = page_object_scale_by
        self.pages["object_scale_current_value"] = page_object_scale_current_value
        self.pages["object_scale_delay"] = page_object_scale_delay
        self.pages["object_scale_until"] = page_object_scale_until
        self.pages["object_scale_delay"] = page_object_scale_delay
        self.pages["object_start_scaling"] = page_object_start_scaling
        self.pages["object_stop_scaling"] = page_object_stop_scaling

        self.pages["object_after_movement_stop"] = page_object_after_movement_stop
        self.pages["object_stop_movement_condition"] = page_object_stop_movement_condition
        self.pages["object_move"] = page_object_move
        self.pages["object_move_delay"] = page_object_move_delay
        self.pages["object_start_moving"] = page_object_start_moving
        self.pages["object_set_position_x"] = page_object_set_position_x
        self.pages["object_set_position_y"] = page_object_set_position_y
        self.pages["object_set_center"] = page_object_set_center


        """
        Dialog
        """
        self.pages["text_dialog_define"] = page_dialog_define
        self.pages["text_dialog_show"] = page_dialog_show
        self.pages["text_dialog_close"] = page_dialog_close
        self.pages["halt"] = page_dialog_halt
        self.pages["halt_auto"] = page_dialog_halt_auto
        self.pages["continue"] = page_dialog_continue

        self.pages["load_dialog_sprite"] = page_load_dialog
        self.pages["dialog_sprite_show"] = page_show_dialog
        self.pages["dialog_sprite_hide"] = page_hide_dialog
        
        self.pages["dialog_sprite_flip_both"] = page_dialog_flip_both
        self.pages["dialog_sprite_flip_horizontal"] = page_dialog_flip_horizontal
        self.pages["dialog_sprite_flip_vertical"] = page_dialog_flip_vertical
        
        self.pages["dialog_sprite_after_fading_stop"] = page_dialog_after_fading_stop
        self.pages["dialog_sprite_fade_current_value"] = page_dialog_fade_current_value
        self.pages["dialog_sprite_fade_delay"] = page_dialog_fade_delay
        self.pages["dialog_sprite_fade_speed"] = page_dialog_fade_speed
        self.pages["dialog_sprite_fade_until"] = page_dialog_fade_until
        self.pages["dialog_sprite_start_fading"] = page_dialog_start_fading
        self.pages["dialog_sprite_stop_fading"] = page_dialog_stop_fading
        
        self.pages["dialog_sprite_after_rotating_stop"] = page_dialog_after_rotating_stop
        self.pages["dialog_sprite_rotate_current_value"] = page_dialog_rotate_current_value
        self.pages["dialog_sprite_rotate_delay"] = page_dialog_rotate_delay
        self.pages["dialog_sprite_rotate_speed"] = page_dialog_rotate_speed
        self.pages["dialog_sprite_rotate_until"] = page_dialog_rotate_until
        self.pages["dialog_sprite_start_rotating"] = page_dialog_start_rotating
        self.pages["dialog_sprite_stop_rotating"] = page_dialog_stop_rotating

        self.pages["dialog_sprite_after_scaling_stop"] = page_dialog_after_scaling_stop
        self.pages["dialog_sprite_scale_by"] = page_dialog_scale_by
        self.pages["dialog_sprite_scale_current_value"] = page_dialog_scale_current_value
        self.pages["dialog_sprite_scale_delay"] = page_dialog_scale_delay
        self.pages["dialog_sprite_scale_until"] = page_dialog_scale_until
        self.pages["dialog_sprite_scale_delay"] = page_dialog_scale_delay
        self.pages["dialog_sprite_start_scaling"] = page_dialog_start_scaling
        self.pages["dialog_sprite_stop_scaling"] = page_dialog_stop_scaling

        self.pages["dialog_sprite_after_movement_stop"] = page_dialog_after_movement_stop
        self.pages["dialog_sprite_stop_movement_condition"] = page_dialog_stop_movement_condition
        self.pages["dialog_sprite_move"] = page_dialog_move
        self.pages["dialog_sprite_move_delay"] = page_dialog_move_delay
        self.pages["dialog_sprite_start_moving"] = page_dialog_start_moving
        self.pages["dialog_sprite_set_position_x"] = page_dialog_set_position_x
        self.pages["dialog_sprite_set_position_y"] = page_dialog_set_position_y
        self.pages["dialog_sprite_set_center"] = page_dialog_set_center


        
        """
        Font
        """
        self.pages["load_font_sprite"] = page_load_font
        self.pages["font"] = page_font
        self.pages["font_x"] = page_font_x
        self.pages["font_y"] = page_font_y
        self.pages["font_text_fade_speed"] = page_font_text_fade_speed
        self.pages["font_text_delay"] = page_font_text_delay
        self.pages["font_text_delay_punc"] = page_font_text_delay_punc
        self.pages["font_intro_animation"] = page_font_intro_animation
        


        self.active_page = default_page
        default_page.show()

    def on_ok_btn_clicked(self):
        generated_command = self.active_page.generate_command()
        if not generated_command:
            return
        else:
            self.generated_command = generated_command
            
        self.mainwindow.destroy()
        
    def on_cancel_button_clicked(self):
        self.mainwindow.destroy()
        
    def on_treeview_item_selected(self, event):
        """
        An item was selected. Make sure a sub-item is selected
        because we're only interested in command rows, not category rows.
        """
        selected_item_iid = self.treeview_commands.selection()
        if not selected_item_iid:
            return
        selected_item_iid = selected_item_iid[0]
        
        if not self.treeview_commands.parent(selected_item_iid):
            return
        
        item_details = self.treeview_commands.item(selected_item_iid)
        
        command_name = item_details.get("values")[0]
        
        page = self.pages.get(command_name)
        if not page:
            return
        
        if self.active_page:
            self.active_page.frame_content.grid_forget()

        self.active_page = page
        page.show()

    def run(self):
        self.mainwindow.mainloop()


class WizardListing:
    def __init__(self,
                 parent_frame: ttk.Frame,
                 header_label: ttk.Label,
                 purpose_label: ttk.Label,
                 treeview_commands: ttk.Treeview,
                 parent_display_text: str,
                 sub_display_text: str,
                 command_name: str,
                 purpose_line: str,
                 **kwargs):

        """
        This object will get put into a list.
        The list will be iterated and the WizardListing objects will be
        used for populating the treeview widget.
        
        Arguments:
        
        - parent_frame: the frame that this wizard page/frame will be put onto.
        
        - header_label: this ttk label will show the command name
        
        - purpose_label: this ttk label will show a brief explanation
        of the command.
        
        - treeview_commands: the treeview that needs to be populated
        with the commands.
        
        - parent_display_text: the root item text to appear as
        in the treeview widget.
        
        - sub_display_text: the sub item text to appear as in the
        treeview widget (a child of the parent item text above)
        
        - command_name: the command name will get shown near the header
        
        - purpose_line: a brief explanation of what the command does.
        This will show up in the header label at the top.
        """
        
        self.parent_frame = parent_frame
        self.header_label = header_label
        self.purpose_label = purpose_label
        self.treeview_commands = treeview_commands
        self.parent_display_text = parent_display_text
        self.sub_display_text = sub_display_text
        self.command_name = command_name
        self.purpose_line = purpose_line
        self.kwargs = kwargs
        
        # Record the type of listing this is, so we can display
        # the appropriate texts in the widgets.
        if "character" in command_name:
            self.purpose_type = Purpose.CHARACTER

        elif "background" in command_name:
            self.purpose_type = Purpose.BACKGROUND

        elif "object" in command_name:
            self.purpose_type = Purpose.OBJECT

        elif "font" in command_name:
            self.purpose_type = Purpose.FONT_SPRITE
            
        elif [item for item in ("sound", "fx", "audio", "voice")
              if item in command_name]:
            self.purpose_type = Purpose.AUDIO

        elif "music" in command_name:
            self.purpose_type = Purpose.MUSIC            

        elif "dialog" in command_name:
            self.purpose_type = Purpose.DIALOG
            
        elif command_name in ("after", "after_cancel", "call"):
            self.purpose_type = Purpose.REUSABLE_SCRIPT
            
        elif command_name in ("scene", ):
            self.purpose_type = Purpose.SCENE_SCRIPT

        else:
            self.purpose_type = Purpose.ACTION

        # If it's the 'default page' (beginning page), then a treeview
        # widget won't be supplied, because we won't be populating
        # the treeview with the default page.
        if not self.treeview_commands:
            return

        # Populate the treeview widget with the category and/or name
        # of the command.

        # Root item
        parent_iid = ""
        
        # Does a root item with the specific name already exist?
        # If so, use the existing root item.
        for root_item_iid in self.treeview_commands.get_children():

            item_details = self.treeview_commands.item(root_item_iid)
            item_text = item_details.get("text")
            if item_text == parent_display_text:
                # The root item (category) for this command already exists.
                # in the treeview widget.
                parent_iid = root_item_iid
                break
        else:
            # The root/category for this command doesn't exist in
            # the treeview widget, so add it now.
            parent_iid = self.treeview_commands.insert(parent=parent_iid,
                                                       index="end",
                                                       text=parent_display_text)

        # Insert command name to the treeview.
        self.treeview_commands.insert(parent=parent_iid,
                                      index="end",
                                      values=(sub_display_text, ))

        # This frame will contain the contents of the page.
        # It will be shown when the show() method is called.
        self.frame_content: ttk.Frame        
        self.frame_content = None

    def get_purpose_name(self,
                         title_casing: bool = False,
                         plural: bool = False,
                         capitalize_first_word: bool = False) -> str:
        """
        Return the name of the purpose based on the purpose type.
        For example, if the purpose type is Character, then return "character".
        
        Purpose: to display the purpose/subject in widgets.
        
        Arguments:
        
        - title_casing: (bool) set to True to return with title casing.
        Example: if True, 'Character' will be returned instead of 'character'.
        
        - plural: (bool) will return the plural name instead of the singular name.
        Example: 'characters' instead of 'character'.
        
        - capitalize_first_word: (bool) For example: 'Reusable script' instead of 'reusable script'.
        """

        name_mapping = {Purpose.BACKGROUND: ("background", "backgrounds"),
                        Purpose.CHARACTER: ("character", "characters"),
                        Purpose.OBJECT: ("object", "objects"),
                        Purpose.DIALOG: ("dialog sprite", "dialog sprites"),
                        Purpose.FONT_SPRITE: ("font sprite", "font sprites"),
                        Purpose.AUDIO: ("sound", "sounds"),
                        Purpose.MUSIC: ("music file", "music"),
                        Purpose.REUSABLE_SCRIPT: ("reusable script name", "reusable script names"),
                        Purpose.SCENE_SCRIPT: ("scene name", "scene names")}

        name: str
        name = name_mapping.get(self.purpose_type)

        if name:
            
            if not plural:
                # Get the singular name.
                name = name[0]
            else:
                # Get the plural name.
                name = name[1]

            if title_casing:
                name = name.title()
            elif capitalize_first_word:
                name = name.capitalize()

        return name
    
    def get_population_dictionary(self) -> Dict | None:
        """
        Return the dictionary that holds the references
        to the images, based on the purpose type.
        For example, for backgrounds, the reference dictionary
        would be ProjectSnapshot.background_images.
        
        Purpose: gets used for populating comboboxes.
        
        Note: not all purpose types have a dictionary.
        For example, Purpose.DIALOG has no dictionary reference.
        
        Return: a dictionary or None if there is no reference dictionary.
        """

        dict_mapping = {Purpose.BACKGROUND: ProjectSnapshot.background_images,
                        Purpose.CHARACTER: ProjectSnapshot.character_images,
                        Purpose.OBJECT: ProjectSnapshot.object_images,
                        Purpose.DIALOG: ProjectSnapshot.dialog_images,
                        Purpose.FONT_SPRITE: ProjectSnapshot.font_sprites,
                        Purpose.AUDIO: ProjectSnapshot.sounds,
                        Purpose.MUSIC: ProjectSnapshot.music}

        dict_ref = dict_mapping.get(self.purpose_type)
        
        return dict_ref
    
    def show(self):
        """
        Set the text of the purpose labels to indicate to the user
        what this command does.
        
        Also, grid the frame so the user can see its contents.
        """

        self.header_label.configure(text=self.command_name)
        self.purpose_label.configure(text=self.purpose_line)

        self.frame_content.grid()    


class SharedPages:

    class DropDownReadOnly(WizardListing):
        """
        <font_intro_animation: animation type>
        <font_outro_animation: animation type>
        
        1 Label
        1 Combobox (read-only) with custom values
        
        Used for selecting a font intro/outro animation.
        """
    
        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name,
                             purpose_line, **kwargs)
    
            self.frame_content = self.create_content_frame()
    
        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """
    
            frame_content = ttk.Frame(self.parent_frame)
            
            self.instructions = self.kwargs.get("instructions")
            self.values_to_choose = self.kwargs.get("values_to_choose")

            self.lbl_instructions = ttk.Label(frame_content,
                                              text=self.instructions)
    

            self.cb_selection =\
                ttk.Combobox(frame_content,
                             values=self.values_to_choose,
                             state="readonly")

            # Default to the first index
            self.cb_selection.current(newindex=0)
    
            self.lbl_instructions.grid(row=0, column=0, sticky="w")
            self.cb_selection.grid(row=1, column=0, sticky="w")

            return frame_content

        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict with the character general alias.
            Example:
            {"Selection": "Rave"}
            or None if insufficient information was provided by the user.
            """
            user_input = {}

            selection = self.cb_selection.get()
            if not selection:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="Selection",
                                       message=f"Choose a selection from the drop-down menu.")
                return

            user_input = {"Selection": selection}
    
            return user_input
        
        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """
    
            # The user input will be a dictionary like this:
            # {"Selection": "Rave"}
            user_inputs = self.check_inputs()
            
            if not user_inputs:
                return
    
            selection = user_inputs.get("Selection")

            return f"<{self.command_name}: {selection}>"


    class Position(WizardListing):
        """
        <character_set_position_x: general alias, position name>
        """

        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):

            # "horizontal" or "vertical"
            self.direction = None

            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name,
                             purpose_line, **kwargs)

            self.frame_content = self.create_content_frame()

        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """

            # For display purposes
            # "horizontal" or "vertical"
            self.direction: str
            self.direction = self.kwargs.get("direction")

            frame_content = ttk.Frame(self.parent_frame)

            self.lbl_general_alias =\
                ttk.Label(frame_content,
                text=f"{self.get_purpose_name(title_casing=True)} alias:")

            self.entry_general_alias = ttk.Entry(frame_content, width=25)

            self.lbl_position = ttk.Label(frame_content, text=f"{self.direction.title()} position:")

            selection = ["Specific pixel coordinate",
                         "start of display",
                         "end of display",
                         "before start of display",
                         "after end of display",
                         "top of display",
                         "above top of display",
                         "bottom of display",
                         "below bottom of display"]

            if self.direction == "horizontal":
                selection = selection[:5]
            elif self.direction == "vertical":
                selection = [selection[0]] + selection[5:]

            self.cb_position =\
                ttk.Combobox(frame_content,
                             values=selection,
                             state="readonly")
            self.cb_position.bind("<<ComboboxSelected>>", self.on_position_selection_changed)

            # Default to 'Specific pixel coordinate'
            self.cb_position.current(newindex=0)

            self.frame_pixel_location = ttk.Frame(frame_content)
            self.spinbox_pixel_location = ttk.Spinbox(self.frame_pixel_location,
                                                      width=5,
                                                      from_=-2000,
                                                      to=9000)
            self.spinbox_pixel_location.set(0)

            self.lbl_pixel_location = ttk.Label(self.frame_pixel_location, text="(pixel coordinate)")

            self.lbl_general_alias.grid(row=0, column=0, sticky="w", columnspan=2)
            self.entry_general_alias.grid(row=1, column=0, sticky="w", columnspan=2)

            self.lbl_position.grid(row=2, column=0, sticky="w", pady=(10, 0))
            self.cb_position.grid(row=3, column=0, sticky="w")

            self.frame_pixel_location.grid(row=3, column=1, sticky="w", padx=(3, 1))
            self.spinbox_pixel_location.grid(row=0, column=0, sticky="w")
            self.lbl_pixel_location.grid(row=0, column=1, sticky="w")

            return frame_content
        
        def on_position_selection_changed(self, event):
            """
            The combobox selection for 'Horizontal position' has changed.
            
            If 'specific pixel location' has been selected, grid the frame
            which allows the user to type in a pixel coordinate.
            Otherwise, grid_forget the frame.
            """
            selection_index = event.widget.current()
    
            # Specific pixel coordinate is at index zero.
            if selection_index == 0:
                self.frame_pixel_location.grid(row=3, column=1, sticky="w", padx=(3, 1))
                self.spinbox_pixel_location.focus()
            else:
                self.frame_pixel_location.grid_forget()
    
        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict with the character general alias.
            Example:
            {"Alias": "Rave",
             "Position": "start of display" or "123"}
            or None if insufficient information was provided by the user.
            """
            user_input = {}
    
            alias = self.entry_general_alias.get().strip()
            if not alias:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No alias provided",
                                       message=f"Enter an alias for the {self.get_purpose_name()}.")
                return
    
            position = self.cb_position.get()
            if not position:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="Position",
                                       message=f"Choose a {self.direction} position.")
                return
    
            # Is 'Specific pixel coordinate' selected?
            index_stop_location = self.cb_position.current()
            if index_stop_location == 0:
                pixel_perfect_stop = True
            else:
                pixel_perfect_stop = False
    
    
            # If a specific pixel coordinate is selected,
            # set the position to that pixel coordinate.
            if pixel_perfect_stop:
                position = self.spinbox_pixel_location.get()
    
                # Make sure the pixel location is an int
                try:
                    int(position)
                except ValueError:
                    messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                           title="Pixel coordinate",
                                           message="The pixel coordinate must be a number.")
                    return
    
            user_input = {"Alias": alias,
                          "Position": position}
    
            return user_input
        
        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """
    
            # The user input will be a dictionary like this:
            # {"Alias": "Rave",
            # "Position": "start of display" or "30"}
            user_inputs = self.check_inputs()
            
            if not user_inputs:
                return
    
            position = user_inputs.get("Position")
            alias = user_inputs.get("Alias")

            return f"<{self.command_name}: {alias}, {position}>"    
    
    class MoveDelay(WizardListing):
        """
        <character_move_delay: general alias, x delay, y delay>
        """
    
        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name,
                             purpose_line, **kwargs)
            
            self.frame_content = self.create_content_frame()
    
        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """
            
            # For example: "Number of frames to skip:"
            spinbox_1_instructions = self.kwargs.get("spinbox_1_instructions")
            spinbox_2_instructions = self.kwargs.get("spinbox_2_instructions")

            # For example: "horizontal", "vertical"
            # Used for display purposes.
            self.spinbox_1_subject = self.kwargs.get("spinbox_1_subject")
            self.spinbox_2_subject = self.kwargs.get("spinbox_2_subject")

            self.spinbox_from_value = self.kwargs.get("spinbox_from_value")
            self.spinbox_to_value = self.kwargs.get("spinbox_to_value")

            # For example: "number of frames to skip"
            # Used in a messagebox missing-field sentence.
            self.subject_sentence_1 = self.kwargs.get("subject_sentence_1")
            self.subject_sentence_2 = self.kwargs.get("subject_sentence_2")
    
            frame_content = ttk.Frame(self.parent_frame)
    
            lbl_general_alias =\
                ttk.Label(frame_content,
                          text=f"{self.get_purpose_name(title_casing=True)} alias:")

            self.entry_general_alias = ttk.Entry(frame_content, width=25)
    
            lbl_frames_to_skip_horizontal = ttk.Label(frame_content,
                                           text=spinbox_1_instructions)
            
            self.sb_horizontal =\
                ttk.Spinbox(frame_content,
                            from_=self.spinbox_from_value,
                            to=self.spinbox_to_value)
    
            lbl_frames_to_skip_vertical = ttk.Label(frame_content,
                                           text=spinbox_2_instructions)
            
            self.sb_vertical =\
                ttk.Spinbox(frame_content,
                            from_=self.spinbox_from_value,
                            to=self.spinbox_to_value)
    
            lbl_general_alias.grid(row=0, column=0, sticky="w")
            self.entry_general_alias.grid(row=1, column=0, sticky="w")
    
            lbl_frames_to_skip_horizontal.grid(row=2, column=0, sticky="w", pady=(15, 0))
            self.sb_horizontal.grid(row=3, column=0, sticky="w")
            
            lbl_frames_to_skip_vertical.grid(row=4, column=0, sticky="w", pady=(15, 0))
            self.sb_vertical.grid(row=5, column=0, sticky="w")
    
            return frame_content
        
        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict with the general alias and the number
            of frames to skip to create a delay effect.
            Example:
            {"Alias": "Rave",
             "Spinbox1Value": "120",
             "Spinbox2Value": "120"}
            or None if insufficient information was provided by the user.
            """
    
            user_input = {}
            
            # Get the number from the spinbox.
            skip_frames_count_horizontal = self.sb_horizontal.get()
            if not skip_frames_count_horizontal:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title=f"No {self.spinbox_1_subject} value",
                                       message=f"Please specify {self.subject_sentence_1}.")
                return
            
            skip_frames_count_vertical = self.sb_vertical.get()
            if not skip_frames_count_vertical:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title=f"No {self.spinbox_2_subject} value",
                                       message=f"Please specify {self.subject_sentence_2}.")
                return        
    
            alias = self.entry_general_alias.get().strip()
            if not alias:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No alias provided",
                                       message=f"Enter an alias for the {self.get_purpose_name()}.")
                return
            
            user_input = {"Alias": alias,
                          "Spinbox1Value": skip_frames_count_horizontal,
                          "Spinbox2Value": skip_frames_count_vertical}
    
            return user_input
        
        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """
    
            # The user input will be a dictionary like this:
            # {"Alias": "Rave",
            # "Spinbox1Value": "120",
            # "Spinbox2Value": "120"}
            user_inputs = self.check_inputs()
            
            if not user_inputs:
                return
    
            alias = user_inputs.get("Alias")
            skip_frames_count_horizontal = user_inputs.get("Spinbox1Value")
            skip_frames_count_vertical = user_inputs.get("Spinbox2Value")
    
            return f"<{self.command_name}: {alias}, {skip_frames_count_horizontal}, {skip_frames_count_vertical}>"
            
    class SetCenter(MoveDelay):

        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name,
                             purpose_line, **kwargs)
        
    class Move(WizardListing):
        """
        <character_move: general alias, x value, y value>
        
        For example: <character_move: rave, 50, 100> which means move the
        sprite horizontally by 50 pixels each time and 100 pixels vertically
        each time. The ‘time’ portion depends on <character_move_delay>
        """
    
        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line)

            self.frame_content = self.create_content_frame()
    
        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """
    
            frame_content = ttk.Frame(self.parent_frame)
    
            lbl_general_alias =\
                ttk.Label(frame_content,
                          text=f"{self.get_purpose_name(title_casing=True)} alias:")

            self.entry_general_alias = ttk.Entry(frame_content, width=25)
    
            """
            Horizontal frame
            """
            
            self.v_horizontal_direction = tk.StringVar()
            self.v_horizontal_direction.set("left")
            
            self.v_horizontal_amount = tk.IntVar()
            self.v_horizontal_amount.set(0)
            
            self.v_move_horizontally = tk.BooleanVar()            
            self.v_move_vertically = tk.BooleanVar()
            
            
            self.frame_horizontal = ttk.Frame(frame_content)
            self.frame_horizontal.grid_rowconfigure(1, weight=1)
            self.frame_horizontal.grid_columnconfigure(1, weight=1)
            self.frame_horizontal.grid_columnconfigure(2, weight=1)
            
            self.lbl_horizontal_amount =\
                ttk.Label(self.frame_horizontal,
                          text="Horizontal movement (x):")
            
            self.chk_move_horizontally =\
                ttk.Checkbutton(self.frame_horizontal,
                                text="Move horizontally",
                                variable=self.v_move_horizontally)
                        
            
            self.sb_horizontal_amount = ttk.Spinbox(self.frame_horizontal,
                                                    from_=0, to=8000,
                                                    width=7,
                                                    textvariable=self.v_horizontal_amount)
          
            self.radio_left = ttk.Radiobutton(self.frame_horizontal,
                                              text="Move left",
                                              value="left",
                                              variable=self.v_horizontal_direction)
            self.radio_right = ttk.Radiobutton(self.frame_horizontal,
                                               text="Move right",
                                               value="right",
                                               variable=self.v_horizontal_direction)
    
            self.lbl_horizontal_amount.grid(row=0, column=0, sticky="w", columnspan=2)
            self.chk_move_horizontally.grid(row=1, column=0, sticky="w", columnspan=2)
            self.sb_horizontal_amount.grid(row=2, column=0, sticky="w")
            
            self.radio_left.grid(row=2, column=1, sticky="w")
            self.radio_right.grid(row=2, column=2, sticky="w", padx=(5, 0))
    
            """
            Vertical frame
            """
            self.v_vertical_direction = tk.StringVar()
            self.v_vertical_direction.set("up")
    
            self.v_vertical_amount = tk.IntVar()
            self.v_vertical_amount.set(0)        
    
            self.frame_vertical = ttk.Frame(frame_content)
            self.frame_vertical.grid_rowconfigure(1, weight=1)
            self.frame_vertical.grid_columnconfigure(1, weight=1)
            self.frame_vertical.grid_columnconfigure(2, weight=1)
            self.lbl_vertical_amount = ttk.Label(self.frame_vertical, text="Vertical movement (y):")
            
            
            self.chk_move_vertically =\
                ttk.Checkbutton(self.frame_vertical,
                                text="Move vertically",
                                variable=self.v_move_vertically)
            
            self.sb_vertical_amount = ttk.Spinbox(self.frame_vertical,
                                                  from_=0, to=8000,
                                                  width=7,
                                                  textvariable=self.v_vertical_amount)
            
            self.radio_up = ttk.Radiobutton(self.frame_vertical,
                                              text="Move up",
                                              value="up",
                                              variable=self.v_vertical_direction)
            self.radio_down = ttk.Radiobutton(self.frame_vertical,
                                               text="Move down",
                                               value="down",
                                               variable=self.v_vertical_direction)
    
            self.lbl_vertical_amount.grid(row=0, column=0, sticky="w", columnspan=2)
            self.chk_move_vertically.grid(row=1, column=0, sticky="w", columnspan=2)
            self.sb_vertical_amount.grid(row=2, column=0, sticky="w")
            
            
            self.radio_up.grid(row=2, column=1, sticky="w")
            self.radio_down.grid(row=2, column=2, sticky="w", padx=(5, 0))
    
            """
            Other widgets
            """
            lbl_general_alias.grid(row=0, column=0, sticky="w")
            self.entry_general_alias.grid(row=1, column=0, sticky="w")
    
            self.frame_horizontal.grid(row=2, column=0, sticky="w", pady=(15, 0))
            self.frame_vertical.grid(row=3, column=0, sticky="w", pady=(15, 0))
            
            """
            Checkbutton traces
            """
            self.v_move_horizontally.trace_add("write",
                                                   self.horizontal_checkbox_changed)
            
            self.v_move_vertically.trace_add("write",
                                                 self.vertical_checkbox_changed)
            
            # Enable move horizontally by default
            self.v_move_horizontally.set(True)
            self.v_move_vertically.set(False)            
            
            return frame_content

        def vertical_checkbox_changed(self, *args):
            """
            The checkbox, 'Move vertically', has changed its check value.
            """
            
            enable_vertical_movement = self.v_move_vertically.get()
            if enable_vertical_movement:
                state = "!disabled"
            else:
                state = "disabled"
            
            # Hint
            self.frame_vertical: ttk.Frame
            
            # Enable/disable all widgets in the frame, except for labels
            # and checkbuttons.
            for widget in self.frame_vertical.winfo_children():
                if widget.winfo_class() in ("TLabel", "TCheckbutton"):
                    continue
                
                widget.state([state])
        
        def horizontal_checkbox_changed(self, *args):
            """
            The checkbox, 'Move horizontally', has changed its check value.
            """
            
            enable_horizontal_movement = self.v_move_horizontally.get()
            if enable_horizontal_movement:
                state = "!disabled"
            else:
                state = "disabled"
            
            # Hint
            self.frame_horizontal: ttk.Frame
            
            # Enable/disable all widgets in the frame, except for labels
            # and checkbuttons.
            for widget in self.frame_horizontal.winfo_children():
                if widget.winfo_class() in ("TLabel", "TCheckbutton"):
                    continue
                
                widget.state([state])
    
        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict with the general alias and the movement details.
            Example:
            {"Alias": "Rave",
             "MoveX": 50,
             "MoveY": 0,
             "XDirection": "right",
             "YDirection": "up"}
            or None if insufficient information was provided by the user.
            """
    
            user_input = {}
            x_movement_amount = 0
            y_movement_amount = 0
    
            alias = self.entry_general_alias.get().strip()
            if not alias:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No alias provided",
                                       message="Enter an alias.")
                return
            
            
            # Horizontal and vertical movements disabled?
            horizontal_movement_enabled = self.v_move_horizontally.get()
            vertical_movement_enabled = self.v_move_vertically.get()

            if not any([horizontal_movement_enabled, vertical_movement_enabled]):
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No direction specified",
                                       message="Please specify a direction for the movement.")
                return                

            # Get the horizontal (x) movement amount from the spinbox.
            if horizontal_movement_enabled:
                
                x_movement_amount = self.sb_horizontal_amount.get()
                if x_movement_amount is None:
                    messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                           title="No horizontal movement",
                                           message="Please specify a horizontal movement amount.")
                    return
                
                
                # Convert and make sure the given X and Y amounts are integers.
                try:
                    x_movement_amount = int(x_movement_amount)
                except ValueError:
                    messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                           title="Vertical value",
                                           message="Please specify a numeric vertical movement amount.")
                    return
                        
            
            # Get the horizontal movement direction (left or right)
            horizontal_direction = self.v_horizontal_direction.get()
    
    
            # Get the vertical (y) movement amount from the spinbox.
            if vertical_movement_enabled:
                y_movement_amount = self.sb_vertical_amount.get()
                if y_movement_amount is None:
                    messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                           title="No vertical movement",
                                           message="Please specify a vertical movement amount.")
                    return
        
                try:
                    y_movement_amount = int(y_movement_amount)
                except ValueError:
                    messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                           title="Horizontal value",
                                           message="Please specify a numeric horizontal movement amount.")
                    return
                

            # If the X and Y amounts are both zero, there is no point in using
            # this command.
            if not any((x_movement_amount, y_movement_amount)):
                
                # Suggest a stop command depending on whether
                # this is being called for a character sprite or object sprite.
                if "character" in self.command_name:
                    intention_command = "<character_stop_moving>"
                elif "dialog" in self.command_name:
                    intention_command = "<dialog_sprite_stop_moving>"
                else:
                    intention_command = "<object_stop_moving>"

                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No Movement",
                                       message="Please enter at least one movement amount.\n\n"
                                       f"If the intention is to stop a movement, use {intention_command}")
                return            
    
            # Get the vertical movement direction (up or down)
            vertical_direction = self.v_vertical_direction.get()
            
            user_input = {"Alias": alias,
                          "MoveX": x_movement_amount,
                          "MoveY": y_movement_amount,
                          "XDirection": horizontal_direction,
                          "YDirection": vertical_direction}
    
            return user_input
        
        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """
    
            # The user input will be a dictionary like this:
            # {"Alias": "Rave",
            # "MoveX": 50,
            # "MoveY": 0,
            # "XDirection": "right",
            # "YDirection": "up"}
            user_inputs = self.check_inputs()
            
            if not user_inputs:
                return
    
            alias = user_inputs.get("Alias")
            x_amount = user_inputs.get("MoveX")
            y_amount = user_inputs.get("MoveY")
            x_direction = user_inputs.get("XDirection")
            y_direction = user_inputs.get("YDirection")
  
            return f"<{self.command_name}: {alias}, {x_amount}, {x_direction}, {y_amount}, {y_direction}>"

    
    class StopMovementCondition(WizardListing):
        """
        <character_stop_movement_condition: general alias, (optional)sprite side to check, stop location>
        Add a condition that defines when to stop a moving sprite.
        """

        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line)
    
            self.frame_content = self.create_content_frame()
    
        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """
    
            frame_content = ttk.Frame(self.parent_frame)
    
            self.lbl_general_alias =\
                ttk.Label(frame_content,
                          text=f"{self.get_purpose_name(title_casing=True)} alias:")
            
            self.entry_general_alias = ttk.Entry(frame_content, width=25)
            
            self.lbl_side_to_check =\
                ttk.Label(frame_content, text="Side of sprite to check:")

            self.cb_side_to_check =\
                ttk.Combobox(frame_content,
                             values=("Determine automatically",
                                     "left", "right", "top", "bottom"),
                             state="readonly")
            
            # Default to 'Determine automatically'
            self.cb_side_to_check.current(newindex=0)
    
            self.lbl_stop_location = ttk.Label(frame_content,
                                               text="Stop location:")
            
            self.cb_stop_location =\
                ttk.Combobox(frame_content,
                             values=("Specific pixel coordinate",
                                     "start of display",
                                     "end of display",
                                     "before start of display",
                                     "after end of display",
                                     "top of display",
                                     "above top of display",
                                     "bottom of display",
                                     "below bottom of display"),
                             state="readonly")
            self.cb_stop_location.bind("<<ComboboxSelected>>", self.on_stop_location_changed)
    
            # Default to 'Specific pixel coordinate'
            self.cb_stop_location.current(newindex=0)
            
            self.frame_pixel_location = ttk.Frame(frame_content)
            self.spinbox_pixel_location = ttk.Spinbox(self.frame_pixel_location,
                                                      width=5,
                                                      from_=-2000,
                                                      to=9000)
            self.spinbox_pixel_location.set(0)
    
            self.lbl_pixel_location = ttk.Label(self.frame_pixel_location, text="(pixel coordinate)")
    
            self.lbl_general_alias.grid(row=0, column=0, sticky="w", columnspan=2)
            self.entry_general_alias.grid(row=1, column=0, sticky="w", columnspan=2)
            
            self.lbl_side_to_check.grid(row=2, column=0, sticky="w", pady=(10, 0))
            self.cb_side_to_check.grid(row=3, column=0, sticky="w")
    
            self.lbl_stop_location.grid(row=4, column=0, sticky="w", pady=(10, 0))
            self.cb_stop_location.grid(row=5, column=0, sticky="w")
    
            self.frame_pixel_location.grid(row=5, column=1, sticky="w", padx=(3, 1))
            self.spinbox_pixel_location.grid(row=0, column=0, sticky="w")
            self.lbl_pixel_location.grid(row=0, column=1, sticky="w")
    
            return frame_content
        
        def on_stop_location_changed(self, event):
            """
            The combobox selection for 'Stop location' has changed.
            
            If 'specific pixel location' has been selected, grid the frame
            which allows the user to type in a pixel coordinate.
            Otherwise, grid_forget the frame.
            """
            selection_index = event.widget.current()
    
            # Specific pixel coordinate is at index zero.
            if selection_index == 0:
                self.frame_pixel_location.grid(row=5, column=1, sticky="w", padx=(3, 1))
                self.spinbox_pixel_location.focus()
            else:
                self.frame_pixel_location.grid_forget()
    
        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict with the character general alias.
            Example:
            {"Alias": "Rave",
             "SpriteSideCheck": "start of display" or None,
             "StopLocation": "123"}
            or None if insufficient information was provided by the user.
            """
            user_input = {}
    
            alias = self.entry_general_alias.get().strip()
            if not alias:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No alias provided",
                                       message=f"Enter an alias for the {self.get_purpose_name()}.")
                return
    
    
            side_to_check = self.cb_side_to_check.get()
            if not side_to_check:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No side specified",
                                       message="Choose which side of the sprite to check.")
                return
            
            stop_location = self.cb_stop_location.get()
            if not stop_location:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="Stop Location",
                                       message="Choose a stop location.")
                return
    
            # Is 'automatically determine side' selected?
            index_auto_side = self.cb_side_to_check.current()
            if index_auto_side == 0:
                auto_side_check = True
                side_to_check = None
            else:
                auto_side_check = False
    
            # Is 'Specific pixel coordinate' selected?
            index_stop_location = self.cb_stop_location.current()
            if index_stop_location == 0:
                pixel_perfect_stop = True
            else:
                pixel_perfect_stop = False
    
            """
            Note: if a pixel-perfect stop location is entered,
            then the side of the sprite must be specified.
            """
            if pixel_perfect_stop and auto_side_check:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="Side must be specified",
                                       message="A pixel coordinate is being used for the stop location, so "
                                       "the side of the sprite must be specified.")
                self.cb_side_to_check.focus()
                return
            
            # If a specific pixel coordinate is selected,
            # set the stop location to that pixel coordinate.
            if pixel_perfect_stop:
                stop_location = self.spinbox_pixel_location.get()
    
                # Make sure the pixel location is an int
                try:
                    int(stop_location)
                except ValueError:
                    messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                           title="Pixel coordinate",
                                           message="The pixel coordinate must be a number.")
                    return
    
            user_input = {"Alias": alias,
                          "SpriteSideCheck": side_to_check,
                          "StopLocation": stop_location}
    
            return user_input
        
        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """
    
            # The user input will be a dictionary like this:
            # {"Alias": "Rave",
            # "SpriteSideCheck": "start of display" or None,
            # "StopLocation": "123"}
            user_inputs = self.check_inputs()
            
            if not user_inputs:
                return
    
            alias = user_inputs.get("Alias")
            side_to_check = user_inputs.get("SpriteSideCheck")
            stop_location = user_inputs.get("StopLocation")
    
            # No sprite side given
            # Example: <character_stop_movement_condition: rave, end of display>
            if not side_to_check:
                command_line = f"<{self.command_name}: {alias}, {stop_location}>"
            else:
                command_line = f"<{self.command_name}: {alias}, {side_to_check}, {stop_location}>"
    
            return command_line
  
        
    class StartStop(WizardListing):
        """
        <character_start_fading: general alias>
        
        1 Label (ie: Character alias)
        1 Entry widget (to type the alias)
        """
    
        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line)
    
            self.frame_content = self.create_content_frame()
    
        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """
    
            frame_content = ttk.Frame(self.parent_frame)
    
            self.lbl_general_alias =\
                ttk.Label(frame_content,
                          text=f"{self.get_purpose_name(title_casing=True)} alias:")

            self.entry_general_alias = ttk.Entry(frame_content, width=25)
    
            self.lbl_general_alias.grid(row=0, column=0, sticky="w", columnspan=2)
            self.entry_general_alias.grid(row=1, column=0, sticky="w", columnspan=2)
    
            return frame_content
        
        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict with the general alias.
            Example:
            {"Alias": "Rave"}
            or None if insufficient information was provided by the user.
            """
            user_input = {}
    
            alias = self.entry_general_alias.get().strip()
            if not alias:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No alias provided",
                                       message=f"Enter an alias for the {self.get_purpose_name()}.")
                return
    
            user_input = {"Alias": alias}
    
            return user_input
        
        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """
    
            # The user input will be a dictionary like this:
            # {"Alias": "Rave"}
            user_inputs = self.check_inputs()
            
            if not user_inputs:
                return
    
            alias = user_inputs.get("Alias")
    
            return f"<{self.command_name}: {alias}>"
      

    class Until(WizardListing):
        """
        <character_fade_until: general alias, fade value>
        The fade value should be between 0 and 255.
        
        1 Label
        1 Entry
        1 Label
        1 LabelScale
        *1 Checkbutton (*Rotate until only)
        """
    
        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name,
                             purpose_line, **kwargs)
            
            self.frame_content = self.create_content_frame()
    
        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """
    
            frame_content = ttk.Frame(self.parent_frame)

            # The text to show the user
            # ie: "Stop rotating when the angle reaches... (degrees): (0 to 359):"
            scale_instructions = self.kwargs.get("scale_instructions")
            
            # Get the scale range
            scale_from_value = self.kwargs.get("scale_from_value")
            scale_to_value = self.kwargs.get("scale_to_value")

            # The default value for the scale widget.
            scale_default_value = self.kwargs.get("scale_default_value")
    
            lbl_general_alias =\
                ttk.Label(frame_content,
                text=f"{self.get_purpose_name(title_casing=True)} alias:")
            
            self.entry_general_alias = ttk.Entry(frame_content, width=25)
    
            self.v_until = tk.IntVar()
            self.v_until.set(0)

            # Is this page for 'rotate until'?

            # We need this to know whether to show the 'Rotate forever'
            # checkbutton or not.
            self.is_rotate_until = "rotate" in self.command_name
    
            if self.is_rotate_until:
                self.v_rotate_forever = tk.BooleanVar()
                self.v_rotate_forever.set(False)
                
                self.chk_rotate_forever = ttk.Checkbutton(frame_content,
                                                          text="Rotate forever",
                                                          variable=self.v_rotate_forever)
                
                self.v_rotate_forever.trace("w", self.on_checkbutton_rotate_forever_changed)
    

            self.lbl_until = ttk.Label(frame_content,
                                       text=scale_instructions)
            
            self.scale = ttk.LabeledScale(frame_content,
                                          from_=scale_from_value,
                                          to=scale_to_value,
                                          variable=self.v_until)
    
            # Set the default value for the scale.
            self.v_until.set(scale_default_value)
    
            lbl_general_alias.grid(row=0, column=0, sticky="w", columnspan=2)
            self.entry_general_alias.grid(row=1, column=0, sticky="w", columnspan=2)
    
            self.lbl_until.grid(row=2, column=0, sticky="w", pady=(10, 0), columnspan=2)
            self.scale.grid(row=3, column=0, sticky="w", columnspan=2)

            if self.is_rotate_until:
                self.chk_rotate_forever.grid(row=4, column=0, sticky="w", pady=(10, 0))

            return frame_content
        
        def on_checkbutton_rotate_forever_changed(self, *args):
            """
            The checkbox, 'Rotate forever', has been checked or unchecked.
            
            When unchecked, disable the scale widget which allows the degrees
            to be chosen.
            """
    
            if self.v_rotate_forever.get():
                # Rotate forever is checked
                state_change = "disabled"
            else:
                state_change = "!disabled"
                
            self.lbl_until.state([state_change])
            
            # Using the state method doesn't work on a labeled scale.
            # We need to disable/enable individual widgets in the labeledscale.
            for name in self.scale.children.values():
                widget = self.scale.nametowidget(name)
                widget.state([state_change])
    
        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict with the character general alias, and the scale
            value (ie: the angle between 0 and 359).
            Example:
            {"Alias": "Rave",
            "UntilValue": 90}
            or None if insufficient information was provided by the user.
            """
            user_input = {}
    
            alias = self.entry_general_alias.get().strip()
            if not alias:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No alias provided",
                                       message=f"Enter an alias for the {self.get_purpose_name()}.")
                return
    
    
            # Get the value from the scale widget.
            scale_value = self.v_until.get()
    
            user_input = {"Alias": alias,
                          "UntilValue": scale_value}
    
            return user_input
        
        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """
    
            # The user input will be a dictionary like this:
            # {"Alias": "Rave",
            # "UntilValue": 90}
            user_inputs = self.check_inputs()
            
            if not user_inputs:
                return
    
            alias = user_inputs.get("Alias")
            rotate_until_value = user_inputs.get("UntilValue")

            # Is this a page for 'Rotate until'? Check the 'Rotate forever'
            # checkbutton value.
            if self.is_rotate_until:
                rotate_forever = self.v_rotate_forever.get()
    
                if rotate_forever:
                    rotate_until_value = "forever"
                
            return f"<{self.command_name}: {alias}, {rotate_until_value}>"

    class Speed(WizardListing):
        """
        <character_fade_speed: general alias, speed percentage, 'fade in' or 'fade out'>
        
        Examples:
        <character_rotate_speed: rave, 31, clockwise>
        <character_fade_speed: rave, 33, fade in>
        <character_scale_by: rave, 43, scale up>
        
        Layout:
          1 Entry
          2 Radiobuttons
          1 Labelscale
        """

        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):

            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name,
                             purpose_line, **kwargs)

            self.frame_content = self.create_content_frame()

        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """

            frame_content = ttk.Frame(self.parent_frame)

            lbl_general_alias =\
                ttk.Label(frame_content,
                text=f"{self.get_purpose_name(title_casing=True)} alias:")
            
            self.entry_general_alias = ttk.Entry(frame_content, width=25)
            
            # The text before the radio button widgets.
            self.radio_button_instructions =\
                self.kwargs.get("radio_button_instructions")

            # The text before the LabelScale widget, for the user to see.
            # Example: "Fade speed (1 to 100):"
            self.scale_instructions = self.kwargs.get("scale_instructions")

            # The texts of the radio buttons, for the user to see.
            self.radio_button_text1 = self.kwargs.get("radio_button_text_1")
            self.radio_button_text2 = self.kwargs.get("radio_button_text_2")

            # Radio button values (example: "fade in" and "fade out")
            self.radio_button_value_1 = self.kwargs.get("radio_button_value_1")
            self.radio_button_value_2 = self.kwargs.get("radio_button_value_2")

            # The default int value of the LabelScale to set.
            self.scale_default_value = self.kwargs.get("scale_default_value")
            self.v_scale_value = tk.IntVar()

            # Scale range
            self.scale_from_value = self.kwargs.get("scale_from_value")
            self.scale_to_value = self.kwargs.get("scale_to_value")
            
            # Tk variable for the radio buttons.
            self.v_radio_button_selection = tk.StringVar()
            
            # Get the default radio button selection
            self.default_radio_button_value = self.kwargs.get("default_radio_button_value")
            self.v_radio_button_selection.set(self.default_radio_button_value)

            # The text to show before the radio buttons, for the user to see.
            # Example: "Fade type:"
            self.lbl_radio_selection = ttk.Label(frame_content,
                                                 text=self.radio_button_instructions)
            
            self.radio_1 = ttk.Radiobutton(frame_content,
                                           text=self.radio_button_text1,
                                           value=self.radio_button_value_1,
                                           variable=self.v_radio_button_selection)

            self.radio_2 = ttk.Radiobutton(frame_content,
                                           text=self.radio_button_text2,
                                           value=self.radio_button_value_2,
                                           variable=self.v_radio_button_selection)

            self.lbl_scale = ttk.Label(frame_content,
                                  text=self.scale_instructions)

            self.scale = ttk.LabeledScale(frame_content,
                                          from_=self.scale_from_value,
                                          to=self.scale_to_value,
                                          variable=self.v_scale_value)

            # Set the default value of the scale.
            self.v_scale_value.set(self.scale_default_value)

            lbl_general_alias.grid(row=0, column=0, sticky="w", columnspan=2)
            self.entry_general_alias.grid(row=1, column=0, sticky="w", columnspan=2)

            self.lbl_radio_selection.grid(row=2, column=0, sticky="w", pady=(10, 0), columnspan=2)
            self.radio_1.grid(row=3, column=0, sticky="w")
            self.radio_2.grid(row=3, column=1, sticky="w", padx=(10, 0))

            self.lbl_scale.grid(row=4, column=0, sticky="w", pady=(10, 0), columnspan=2)
            self.scale.grid(row=5, column=0, sticky="w", columnspan=2)

            return frame_content

        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict with the general alias, the scale value,
            and the selection type (ie: fade in or fade out).
            Example:
            {"Alias": "Rave",
            "Type": "fade in",
            "ScaleValue": 25,}
            or None if insufficient information was provided by the user.
            """
            user_input = {}

            alias = self.entry_general_alias.get().strip()
            if not alias:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No alias provided",
                                       message=f"Enter an alias for the {self.get_purpose_name()}.")
                return

            radio_button_selection = self.v_radio_button_selection.get()
            scale_value = self.v_scale_value.get()

            user_input = {"Alias": alias,
                          "Type": radio_button_selection,
                          "ScaleValue": scale_value}

            return user_input

        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """

            # The user input will be a dictionary like this:
            # {"Alias": "Rave",
            # "ScaleValue": 30,
            # "Type": "fade in"}
            user_inputs = self.check_inputs()

            if not user_inputs:
                return

            alias = user_inputs.get("Alias")
            scale_value = user_inputs.get("ScaleValue")
            radio_button_selection = user_inputs.get("Type")

            return f"<{self.command_name}: {alias}, {scale_value}, {radio_button_selection}>"


    class SpeedOnly(WizardListing):
        """
        <font_text_speed: speed amount>
        
        Shows a LabelScale, with no alias entry widget.
        Used for font speed.
        
        1 Label
        1 LabelScale
        """

        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):

            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name,
                             purpose_line, **kwargs)

            self.frame_content = self.create_content_frame()

        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """

            frame_content = ttk.Frame(self.parent_frame)

            # The text before the LabelScale widget, for the user to see.
            # Example: "Font speed (1 to 10):"
            self.scale_instructions = self.kwargs.get("scale_instructions")

            # The default int value of the LabelScale to set.
            self.scale_default_value = self.kwargs.get("scale_default_value")
            self.v_scale_value = tk.IntVar()

            # Scale range
            self.scale_from_value = self.kwargs.get("scale_from_value")
            self.scale_to_value = self.kwargs.get("scale_to_value")
            

            self.lbl_scale = ttk.Label(frame_content,
                                  text=self.scale_instructions)

            self.scale = ttk.LabeledScale(frame_content,
                                          from_=self.scale_from_value,
                                          to=self.scale_to_value,
                                          variable=self.v_scale_value)

            # Set the default value of the scale.
            self.v_scale_value.set(self.scale_default_value)

            self.lbl_scale.grid(row=0, column=0, sticky="w", columnspan=2)
            self.scale.grid(row=1, column=0, sticky="w", pady=(5, 0), columnspan=2)

            return frame_content

        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict with the scale value.
            Example:
            {"ScaleValue": 25}
            """
            user_input = {}

            scale_value = self.v_scale_value.get()

            user_input = {"ScaleValue": scale_value}

            return user_input

        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """

            # The user input will be a dictionary like this:
            # {"ScaleValue": 30}
            user_inputs = self.check_inputs()

            if not user_inputs:
                return

            scale_value = user_inputs.get("ScaleValue")

            return f"<{self.command_name}: {scale_value}>"

    class CurrentValue(WizardListing):
        """
        <character_fade_current_value: general alias, fade value>
        <character_fade_delay: general alias, number of frames to skip>
        
        1 Entry widget
        1 Spinbox widget.
        """

        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):

            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line, **kwargs)

            self.frame_content = self.create_content_frame()

        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """

            frame_content = ttk.Frame(self.parent_frame)
            
            # Used for limiting the spinbox widget.
            from_value = self.kwargs.get("from_value")
            to_value = self.kwargs.get("to_value")
            
            # For example: "Set the opacity level:"
            amount_usage_info = self.kwargs.get("amount_usage_info")

            # Such as 'opacity level'; used for the message box
            # when the amount is missing
            self.amount_name = self.kwargs.get("amount_name")

            self.lbl_general_alias = ttk.Label(frame_content, text=f"{self.get_purpose_name(title_casing=True)} alias:")
            self.entry_general_alias = ttk.Entry(frame_content, width=25)

            self.lbl_amount = ttk.Label(frame_content, text=amount_usage_info)
            self.sb_amount = ttk.Spinbox(frame_content, from_=from_value, to=to_value)

            self.lbl_general_alias.grid(row=0, column=0, sticky="w")
            self.entry_general_alias.grid(row=1, column=0, sticky="w")

            self.lbl_amount.grid(row=2, column=0, sticky="w", pady=(15, 0))
            self.sb_amount.grid(row=3, column=0, sticky="w")

            return frame_content

        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict with the character general alias and an opacity level.
            Example:
            {"Alias": "Rave",
             "Amount": "255"}
            or None if insufficient information was provided by the user.
            """

            user_input = {}

            # Get the amount from the spinbox widget.
            amount = self.sb_amount.get()
            if not amount:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title=f"No {self.amount_name} specified",
                                       message=f"Please specify the {self.amount_name}.")
                return

            alias = self.entry_general_alias.get().strip()
            if not alias:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No alias provided",
                                       message=f"Enter an alias for the {self.get_purpose_name()}.")
                return

            user_input = {"Alias": alias,
                          "Amount": amount}

            return user_input

        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """

            # The user input will be a dictionary like this:
            # {"Alias": "Rave",
            # "Amount": "255"}
            user_inputs = self.check_inputs()

            if not user_inputs:
                return

            amount = user_inputs.get("Amount")
            alias = user_inputs.get("Alias")

            return f"<{self.command_name}: {alias}, {amount}>"


    class ReusableScriptSelect(WizardListing):
        """
        <call: reusable script name>
        <after: 60, reusable script name>
        <after_cancel: reusable script name>
        
        1 Label
        1 Combobox
        
        (below only if frames_delay flag is set)
        1 Label
        1 Spinbox widget.
        """

        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):

            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line, **kwargs)


            # Used for showing a spinbox and its label.
            # For <after: elapse frames, script name>
            self.show_delay_widgets = False

            self.frame_content = self.create_content_frame()
            
            # Populate reusable script names combobox
            self.populate()
            

        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """

            frame_content = ttk.Frame(self.parent_frame)
            
            # Used for limiting the spinbox widget.
            from_value = self.kwargs.get("from_value")
            to_value = self.kwargs.get("to_value")
            
            # Meant for showing spinbox for delay frames selection.
            # (<after> uses this, but not <after_cancel>)
            self.show_delay_widgets = self.kwargs.get("show_delay_widgets")

            self.lbl_reusable_script = ttk.Label(frame_content, text=f"{self.get_purpose_name(capitalize_first_word=True)}:")
            self.cb_reusable_script = ttk.Combobox(frame_content, width=25)

            
            if self.show_delay_widgets:
                
                # So the user knows what the spinbox is for.
                # Example: "The number of frames to elapse:"
                spinbox_instructions = self.kwargs.get("spinbox_instructions")
                
                spinbox_default_value = self.kwargs.get("spinbox_default_value")
    
                # Such as 'number of frames to delay level'; used for the message box
                # when the amount is missing
                self.amount_name = self.kwargs.get("amount_name")
            
                self.lbl_amount = ttk.Label(frame_content, text=spinbox_instructions)
                self.sb_amount = ttk.Spinbox(frame_content, from_=from_value, to=to_value)
                self.sb_amount.delete(0, "end")
                self.sb_amount.insert(0, spinbox_default_value)
    

            self.lbl_reusable_script.grid(row=0, column=0, sticky="w")
            self.cb_reusable_script.grid(row=1, column=0, sticky="w")

            if self.show_delay_widgets:
                self.lbl_amount.grid(row=2, column=0, sticky="w", pady=(15, 0))
                self.sb_amount.grid(row=3, column=0, sticky="w")

            return frame_content

        def populate(self):
            """
            Populate the reusables combobox with a list of
            reusable script names.
            """

            # Clear the existing combobox, just in case there are values in it.
            self.cb_reusable_script.configure(values=())

            reusable_script_names = [item for item in ProjectSnapshot.reusables]

            self.cb_reusable_script.configure(values=reusable_script_names)

            self.cb_reusable_script.delete(0, "end")

        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict with the character general alias and an opacity level.
            Example:
            {"ReusableScriptName": "some script name",
             "DelayFramesAmount": "60"}
            or None if insufficient information was provided by the user.
            """

            user_input = {}
            
            # There may not be an amount, so we initialize to None.
            # (the amount is only used for <after>, not <after_cancel> and not <after_cancel_all>
            delay_frames_amount = None

            # Get the amount from the spinbox widget, if it's being shown.
            if self.show_delay_widgets:
                amount = self.sb_amount.get()
                if not amount:
                    messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                           title=f"No {self.amount_name} specified",
                                           message=f"Please specify the {self.amount_name}.")
                    return
                
                # Attempt to convert frames delay value to an int
                try:
                    delay_frames_amount = int(amount)
                except ValueError:
                    messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                           title=f"Numeric Value Expected",
                                           message=f"A number is expected for the elapse-frames value.")
                    return                    

            # The reusable script name
            reusable_script_name = self.cb_reusable_script.get().strip()
            if not reusable_script_name:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title=f"No {self.get_purpose_name()} provided",
                                       message=f"Enter a {self.get_purpose_name()}.")
                return

            user_input = {"ReusableScriptName": reusable_script_name,
                          "DelayFramesAmount": delay_frames_amount}

            return user_input

        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """

            # The user input will be a dictionary like this:
            # {"DelayFramesAmount": "120",
            # "ReusableScriptName": "some script name"}
            user_inputs = self.check_inputs()

            if not user_inputs:
                return

            delay_frames_amount = user_inputs.get("DelayFramesAmount")
            reusable_script_name = user_inputs.get("ReusableScriptName")
            
            if self.show_delay_widgets:
                # <after: 60, reusable script name>
                return f"<{self.command_name}: {delay_frames_amount}, {reusable_script_name}>"
            else:
                # <after_cancel: reusable script name>
                return f"<{self.command_name}: {reusable_script_name}>"


    class SceneScriptSelect(WizardListing):
        """
        <scene: chapter name, scene name>

        1 Label (Chapters)
        1 Combobox
        
        1 Label (Scenes)
        1 Combobox
        """

        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):

            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line, **kwargs)


            self.frame_content = self.create_content_frame()
            
            # Populate chapter and scene names comboboxes
            self.populate()

        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """

            frame_content = ttk.Frame(self.parent_frame)
            
            self.lbl_chapters_title = ttk.Label(frame_content, text="Chapters:")
            self.cb_chapters = ttk.Combobox(frame_content, width=25)

            self.lbl_scenes_title = ttk.Label(frame_content, text="Scenes:")
            self.cb_scenes = ttk.Combobox(frame_content, width=25)
            
            self.lbl_chapters_title.grid(row=0, column=0, sticky="w")
            self.cb_chapters.grid(row=1, column=0, sticky="w")
            
            self.lbl_scenes_title.grid(row=2, column=0, sticky="w", pady=(15, 0))
            self.cb_scenes.grid(row=3, column=0, sticky="w")            

            return frame_content

        def populate(self):
            """
            Populate the comboboxes with a list of
            chapter and scene names.
            """

            # Clear the existing comboboxs, just in case there are values in them.
            self.cb_chapters.configure(values=())
            self.cb_scenes.configure(values=())

            # Key (str): chapter name, Value: [ chapter script,  another dict {Key: scene name (str): Value script (str)} ]
            chapter_names = [item for item in ProjectSnapshot.chapters_and_scenes]         
            scene_names = [item[1] for item in ProjectSnapshot.chapters_and_scenes.values()]
            scene_names = [scene_name for scene_name in scene_names[0]]

            self.cb_chapters.configure(values=chapter_names)
            self.cb_chapters.delete(0, "end")
            
            self.cb_scenes.configure(values=scene_names)
            self.cb_scenes.delete(0, "end")            

        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict with the character general alias and an opacity level.
            Example:
            {"ReusableScriptName": "some script name",
             "DelayFramesAmount": "60"}
            or None if insufficient information was provided by the user.
            """

            user_input = {}

            # Chapter name
            chapter_name = self.cb_chapters.get().strip()
            if not chapter_name:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title=f"No chapter selected.",
                                       message=f"Type or select a chapter name.")
                return
            
            # Scene name
            scene_name = self.cb_scenes.get().strip()
            if not scene_name:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title=f"No scene selected.",
                                       message=f"Type or select a scene name.")
                return            

            user_input = {"ChapterName": chapter_name,
                          "SceneName": scene_name}
            
            return user_input

        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """

            # The user input will be a dictionary like this:
            # {"ChapterName": "some chapter name",
            # "SceneName": "some scene name"}
            user_inputs = self.check_inputs()

            if not user_inputs:
                return

            chapter_name = user_inputs.get("ChapterName")
            scene_name = user_inputs.get("SceneName")

            # <scene: chapter name, scene name>
            return f"<{self.command_name}: {chapter_name}, {scene_name}>"


    class PositionOnly(CurrentValue):
        """
        <font_x: 5>
        <font_y: 120>
        
        Used for just the position, no sprite name.
        """
        
        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):

            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line, **kwargs)

            self.frame_content = self.create_content_frame()

        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """

            frame_content = ttk.Frame(self.parent_frame)
            
            # Used for limiting the spinbox widget.
            from_value = self.kwargs.get("from_value")
            to_value = self.kwargs.get("to_value")
            
            # For example: "Set the opacity level:"
            amount_usage_info = self.kwargs.get("amount_usage_info")

            # Such as 'opacity level'; used for the message box
            # when the amount is missing
            self.amount_name = self.kwargs.get("amount_name")

            self.lbl_amount = ttk.Label(frame_content, text=amount_usage_info)
            self.sb_amount = ttk.Spinbox(frame_content, from_=from_value, to=to_value)

            self.lbl_amount.grid(row=0, column=0, sticky="w")
            self.sb_amount.grid(row=1, column=0, sticky="w")

            return frame_content

        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict with the character general alias and an opacity level.
            Example:
            {"Amount": "255"}
            or None if insufficient information was provided by the user.
            """

            user_input = {}

            # Get the amount from the spinbox widget.
            amount = self.sb_amount.get()
            if not amount:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title=f"No {self.amount_name} specified",
                                       message=f"Please specify the {self.amount_name}.")
                return

            user_input = {"Amount": amount}

            return user_input

        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """

            # The user input will be a dictionary like this:
            # {Amount": "255"}
            user_inputs = self.check_inputs()

            if not user_inputs:
                return

            amount = user_inputs.get("Amount")

            return f"<{self.command_name}: {amount}>"



    class Delay(CurrentValue):
        def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name,
                             purpose_line, **kwargs)


    class AfterStop(WizardListing):
        """
        <character_after_fading_stop: general alias, reusable script name to run>
        <character_after_scaling_stop: general alias, reusable script name to run>
        <object_after_fading_stop: general alias, reusable script name to run>
        <object_after_scaling_stop: general alias, reusable script name to run>
        """

        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line):

            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line)

            self.frame_content = self.create_content_frame()

        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """

            frame_content = ttk.Frame(self.parent_frame)

            self.lbl_general_alias = ttk.Label(frame_content,
                                               text=f"{self.get_purpose_name(title_casing=True)} alias:")
            self.entry_general_alias = ttk.Entry(frame_content, width=25)

            lbl_reusable_script_name = ttk.Label(frame_content, text="Reusable script:")
            self.cb_reusable_script = ttk.Combobox(frame_content)

            self.lbl_general_alias.grid(row=0, column=0, sticky="w")
            self.entry_general_alias.grid(row=1, column=0, sticky="w")

            lbl_reusable_script_name.grid(row=2, column=0, sticky="w", pady=(15, 0))
            self.cb_reusable_script.grid(row=3, column=0, sticky="w")

            return frame_content

        def populate(self):
            """
            Populate the reusables combobox with a list of
            reusable script names.
            """

            # Clear the existing combobox, just in case there are values in it.
            self.cb_reusable_script.configure(values=())

            # Clear the general alias entry, just in case there is a value in it.
            self.entry_general_alias.delete(0, "end")

            reusable_script_names = [item for item in ProjectSnapshot.reusables]

            self.cb_reusable_script.configure(values=reusable_script_names)

            self.cb_reusable_script.delete(0, "end")

        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict with the character general alias and reusable script name.
            Example:
            {"Alias": "Rave",
             "ReusableScript": "rotate_script"}
            or None if insufficient information was provided by the user.
            """

            user_input = {}

            # Get the selected value in the combobox.
            selection = self.cb_reusable_script.get()
            if not selection:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No reusable script specified",
                                       message="Choose a reusable script from the drop-down menu.")
                return

            alias = self.entry_general_alias.get().strip()
            if not alias:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No alias provided",
                                       message=f"Enter an alias for the {self.get_purpose_name()}.")
                return

            user_input = {"Alias": alias,
                          "ReusableScript": selection}

            return user_input

        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """

            # The user input will be a dictionary like this:
            # {"Alias": "Rave",
            # "ReusableScript": "rave_normal"}
            user_inputs = self.check_inputs()

            if not user_inputs:
                return

            reusable_script_name = user_inputs.get("ReusableScript")
            alias = user_inputs.get("Alias")

            return f"<{self.command_name}: {alias}, {reusable_script_name}>"

        def show(self):
            """
            Set the text of the purpose labels to indicate to the user
            what this command does.
            
            Also, grid the frame so the user can see its contents.
            """

            self.header_label.configure(text=self.command_name)
            self.purpose_label.configure(text=self.purpose_line)

            self.populate()

            self.frame_content.grid()
            

    class LoadSpriteNoAlias(WizardListing):
        """
        <load_background>
        """
    
        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line)
    
            self.frame_content = self.create_content_frame()
            
            self.populate()
    
        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """
    
            frame_content = ttk.Frame(self.parent_frame)
    
            self.lbl_prompt = ttk.Label(frame_content, text=f"Which {self.get_purpose_name()} would you like to load into memory?")
            self.cb_selections = ttk.Combobox(frame_content)
    
            self.lbl_prompt.grid(row=0, column=0, sticky="w")
            self.cb_selections.grid(row=1, column=0, sticky="w")
    
            return frame_content
        
        def populate(self):
            """
            Populate the selections combobox with a list of names.
            """
    
            # Get the appropriate dictionary for this purpose type,
            # used for populating the combobox.
            ref_dict = self.get_population_dictionary()
    
            # Clear the existing combobox, just in case there are values in it.
            self.cb_selections.configure(values=())
    
            names = [item for item in ref_dict]
            self.cb_selections.configure(values=names)
            
            self.cb_selections.delete(0, "end")
            
        def check_inputs(self) -> str | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: the selection (str) if there is sufficient information;
            otherwise, None.
            """
            
            # Get the selected value in the combobox.
            selection = self.cb_selections.get()
            if not selection:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title=f"No {self.get_purpose_name()} selected",
                                       message=f"Choose a {self.get_purpose_name()} from the drop-down menu.")
                return
            
            return selection
        
        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """
            selection = self.check_inputs()
            if not selection:
                return
    
            return f"<{self.command_name}: {selection}>"
    
        def show(self):
            """
            Set the text of the purpose labels to indicate to the user
            what this command does.
            
            Also, grid the frame so the user can see its contents.
            """
    
            self.header_label.configure(text=self.command_name)
            self.purpose_label.configure(text=self.purpose_line)
    
            self.populate()
    
            self.frame_content.grid()
            
            
    class LoadSpriteWithAlias(LoadSpriteNoAlias):
        """
        <load_character>
        <load_object>
        
        Loading backgrounds doesn't support aliases, which is why
        we have a separate generic class here for commands that support aliases.
        """
    
        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line)

        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """

            frame_content = ttk.Frame(self.parent_frame)


            purpose = self.get_purpose_name()
            
            if "dialog" in purpose:
                message = f"Which {purpose} would you like to load into memory?"
            else:
                message = f"Which {purpose} sprite would you like to load into memory?"
            

            lbl_prompt = ttk.Label(frame_content, text=message)
            self.cb_selections = ttk.Combobox(frame_content)
            
            purpose = self.get_purpose_name()
            if "dialog" in purpose:
                message = f"Enter an alias for this dialog sprite below:\n" + \
                f"(This alias can later be used to reference this dialog sprite\n" + \
                "regardless of the image that's being shown for this sprite.)"
            else:
                message = f"Enter an alias for this {self.get_purpose_name()} below:\n" + \
                f"(This alias can later be used to reference this {self.get_purpose_name()}'s sprite\n" + \
                "regardless of the image that's being shown for this sprite.)"
                
            self.lbl_general_alias = ttk.Label(frame_content, text=message)

            self.entry_general_alias = ttk.Entry(frame_content, width=25)

            lbl_prompt.grid(row=0, column=0, sticky="w")
            self.cb_selections.grid(row=1, column=0, sticky="w")
            
            self.lbl_general_alias.grid(row=2, column=0, sticky="w", pady=(15, 0))
            self.entry_general_alias.grid(row=3, column=0, sticky="w")
            
            return frame_content

        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict with the image name (str) and general alias.
            Example:
            {"Selection": "rave_normal",
             "Alias": "Rave"}
            or None if insufficient information was provided by the user.
            """
    
            user_input = {}
            
            # Get the selected value in the combobox.
            selection = self.cb_selections.get()
            if not selection:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title=f"No {self.get_purpose_name()} selected",
                                       message=f"Choose a {self.get_purpose_name()} from the drop-down menu.")
                return
    
            alias = self.entry_general_alias.get().strip()
            if not alias:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No alias provided",
                                       message=f"Enter an alias for the {self.get_purpose_name()}.")
                return
            
            user_input = {"Selection": selection,
                          "Alias": alias}
    
            return user_input
        
        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """
    
            # The user input will be a dictionary like this:
            # {"Selection": "rave_normal",
            # "Alias": "Rave"}
            user_inputs = self.check_inputs()
            
            if not user_inputs:
                return
    
            sprite_name = user_inputs.get("Selection")
            alias = user_inputs.get("Alias")
            
            return f"<{self.command_name}: {sprite_name}, {alias}>"


    class PlayAudioGeneric(LoadSpriteNoAlias):
        """
        <play_sound: name>
        <play_voice: name>
        <play_music: name, loop (optional)>
        """
        
        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line,
                             **kwargs)

            self.lbl_prompt.configure(text=f"Which {self.get_purpose_name()} would you like to play?")
            
            # Add 'Loop' checkbutton for the <play_music> command-only.
            if self.command_name == "play_music":
                self.v_loop_audio = tk.BooleanVar()
                self.create_frame_loop_audio().grid(row=2, column=0, sticky="w")
            
        def create_frame_loop_audio(self) -> ttk.Frame:
            """
            Create a frame that contains a checkbutton with the text 'Loop'.
            This is used by <play_music>
            """
            frame_loop = ttk.Frame(self.frame_content)
            
            chk_loop = ttk.Checkbutton(master=frame_loop,
                                       text="Loop",
                                       variable=self.v_loop_audio)
            
            chk_loop.pack()
            
            return frame_loop
        
        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """
            selection = self.check_inputs()
            if not selection:
                return
    
            # For <play_music: name, loop>
            # (if loop is checked)
            if self.command_name == "play_music":
                if self.v_loop_audio.get():
                    return f"<{self.command_name}: {selection}, loop>"
                    
            return f"<{self.command_name}: {selection}>"
    
    

    class CommandNoParameters(WizardListing):
        """
        <text_dialog_show>
        <text_dialog_hide>
        <halt>
        .....
        """

        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line,
                             **kwargs)

            self.frame_content = self.create_frame_content()

        def create_frame_content(self) -> ttk.Frame:

            frame_content = ttk.Frame(self.parent_frame)

            lbl_no_parameters = ttk.Label(frame_content,
                                          text="This command has no parameters. It's used as-is.")
            
            lbl_no_parameters.pack(anchor=tk.W)            

            # 'when-to-use' is optional
            when_to_use = self.kwargs.get("when_to_use")
           
            if when_to_use:
                lbl_when_to_use_title = ttk.Label(frame_content,
                                                  text="When to use this command:",
                                                  font="TkHeadingFont")
    
                lbl_when_to_use = ttk.Label(frame_content,
                                                  text=when_to_use)                
                
                lbl_when_to_use_title.pack(pady=(10, 0), anchor=tk.W)
                lbl_when_to_use.pack(anchor=tk.W)
            
            return frame_content
        
        def generate_command(self):
            """
            Generate the command.
            
            There are no parameters for the command.
            """
    
            return f"<{self.command_name}>"


    class ShowSprite(LoadSpriteNoAlias):
        """
        <background_show>
        <character_show>
        <object_show>
        """

        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line)

            self.show_relative_text()

        def show_relative_text(self):
            """
            Change the text of the widget(s) to reflect the purpose
            of this class.
            """

            prompt_text = f"Show which {self.get_purpose_name()}?"

            # For sprites that have aliases (characters, objects),
            # let the user know that it's possible to use an alias here.
            prompt_text_additional_info = ("\n(sprite name only, not an alias)")
            
            if self.purpose_type in (Purpose.CHARACTER, Purpose.OBJECT, Purpose.DIALOG):
                prompt_text += prompt_text_additional_info
                
            self.lbl_prompt.configure(text=prompt_text)


    class HideSpriteWithAlias(StartStop):
        """
        <character_hide >
        <object_hide>
        """
        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line)          

            self.show_relative_text()

        def show_relative_text(self):
            """
            Change the text of the widget(s) to reflect the purpose
            of this class.
            """
            self.lbl_general_alias.configure(text=f"Hide which {self.get_purpose_name()}?\n"
                                             f"{self.get_purpose_name(title_casing=True)} alias:")



    class HideSpriteNoAlias(LoadSpriteNoAlias):
        """
        <background_hide>
        """
        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line)          

            self.show_relative_text()

        def show_relative_text(self):
            """
            Change the text of the widget(s) to reflect the purpose
            of this class.
            """
            self.lbl_prompt.configure(text=f"Hide which {self.get_purpose_name()}?")
            
            


class CharacterStartFading(SharedPages.StartStop):
    """
    <character_start_fading: general alias>
    Starts a character sprite fading animation.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)

        
class CharacterStopFading(SharedPages.StartStop):
    """
    <character_stop_fading: general alias>
    Stops a character sprite fading animation.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)


class CharacterFadeUntil(SharedPages.Until):
    """
    <character_fade_until: general alias, fade value>
    The fade value should be between 0 and 255.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)


class CharacterFadeSpeed(SharedPages.Speed):
    """
    <character_fade_speed: general alias, speed percentage, 'fade in' or 'fade out'>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)

class CharacterFadeDelay(SharedPages.Delay):
    """
    <character_fade_delay: general alias, number of frames to skip>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)


class CharacterFadeCurrentValue(SharedPages.CurrentValue):
    """
    <character_fade_current_value: general alias, fade value>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)


class CharacterAfterFadingStop(SharedPages.AfterStop):
    """
    <character_after_fading_stop: general alias, reusable script name to run>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)



class Character_LoadCharacter(SharedPages.LoadSpriteWithAlias):
    """
    <load_character>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)


class Background_LoadBackground(SharedPages.LoadSpriteNoAlias):
    """
    <load_background>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)


class Audio_Volume(SharedPages.SpeedOnly):
    """
    <volume_fx: 0 to 100>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)


class AudioLoad(SharedPages.LoadSpriteNoAlias):
    
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)    



class AudioPlay(SharedPages.PlayAudioGeneric):
    """
    <play_sound: name>
    <play_voice: name>
    <play_music: name, loop (optional)>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)


class AudioStop(SharedPages.CommandNoParameters):
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs)



class AfterCancelAll(SharedPages.CommandNoParameters):
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs)




class Font_LoadFont(SharedPages.LoadSpriteNoAlias):
    """
    <load_font_sprite>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)


class Font_Position(SharedPages.PositionOnly):
    """
    <font_x>
    <font_y>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)


class Font_TextDelay(SharedPages.SpeedOnly):
    """
    <font_text_speed_delay: frames to skip>>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)
        
        
class Font_TextDelayPunc(WizardListing):
    """
    <font_text_delay_punc: previous letter, frames to skip>>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)
        
        self.frame_content = self.create_content_frame()

    def create_content_frame(self) -> ttk.Frame:
        """
        label = 'Previous letter:' entry (max 1 character)
        
        label = 'The number of frames to skip' (1 to 120)'
        labelscale
        """
        
        frame_content = ttk.Frame(self.parent_frame)
        
        frame_content.grid_rowconfigure(1, weight=1)
        frame_content.grid_columnconfigure(1, weight=1)
        
        scale_instructions = self.kwargs.get("scale_instructions")
        scale_from_value = self.kwargs.get("scale_from_value")
        scale_to_value = self.kwargs.get("scale_to_value")
        scale_default_value = self.kwargs.get("scale_default_value")
        

        lbl_previous_letter = ttk.Label(frame_content,
                                        text="Previous letter:")

        self.entry_letter = EntryWithLimit(frame_content,
                                           max_length=1,
                                           width=5)

        lbl_scale_instructions = ttk.Label(frame_content,
                                     text=scale_instructions)
        
        self.v_scale_value = tk.IntVar()

        self.scale = ttk.LabeledScale(frame_content,
                                 from_=scale_from_value,
                                 to=scale_to_value,
                                 variable=self.v_scale_value)

        self.v_scale_value.set(scale_default_value)
        
        lbl_previous_letter.grid(row=0, column=0, sticky="w")
        self.entry_letter.grid(row=0, column=1, sticky="w", padx=(5, 0))

        lbl_scale_instructions.grid(row=1,
                                    column=0,
                                    columnspan=2,
                                    sticky="w",
                                    pady=(15, 0))
        
        self.scale.grid(row=2, column=0, sticky="nw")

        return frame_content
    
    def check_inputs(self) -> Dict:
        """
        Make sure a letter has been provided.
        """
        
        letter = self.entry_letter.get()
        if not letter:
            messagebox.showerror(self.parent_frame.winfo_toplevel(), 
                                 title="Missing Letter",
                                 message="Please type a letter.")
            return
        
        user_input = {"Letter": letter,
              "DelayFrames": self.v_scale_value.get()}

        return user_input
    
    def generate_command(self) -> str:
        """
        Generate the <font_text_delay_punc> command.
        """
        
        user_inputs = self.check_inputs()

        if not user_inputs:
            return

        letter = user_inputs.get("Letter")
        delay_frames = user_inputs.get("DelayFrames")
        
        return f"<{self.command_name}: {letter}, {delay_frames}>"
        

class Font_TextFadeSpeed(SharedPages.SpeedOnly):
    """
    <font_text_speed: speed amount>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)


class Font_IntroAnimation(SharedPages.DropDownReadOnly):
    """
    <font_intro_animation: animation type>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)


class Font_Font(SharedPages.LoadSpriteNoAlias):
    """
    <font>
    Sets the font to use for the next letter.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)

        self.set_font_text()

    def set_font_text(self):
        """
        Show font specific instructions.
        """
        self.lbl_prompt.configure(text="Font:")


        
class BackgroundShow(SharedPages.ShowSprite):
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line)


class BackgroundHide(SharedPages.HideSpriteNoAlias):
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line)
        

class DefaultPage(WizardListing):
    """
    Default wizard page which has basic instructions for the user.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)


        # Create the command's frame contents so that
        # it's ready when the show() method is called.
        self.frame_content = self.create_content_frame()
        

    def create_content_frame(self) -> ttk.Frame:
        """
        Create the widgets needed for the default page
        and return a frame that contains the widgets.
        """

        frame_content = ttk.Frame(self.parent_frame)
        
        text = """Choose a command from the list.
        
Tips:
   - Blank lines can be used in scripts; they are simply ignored.
   - Blank lines in a character's dialog text can be shown with <line>.
   
Comments:
   - You can write comments in your scripts using the # symbol.
   - Comments are ignored by the visual novel.
"""

        lbl_prompt = ttk.Label(frame_content, text=text)
        lbl_prompt.grid(row=0, column=0, sticky="w")

        return frame_content

    def show(self):
        """
        Set the text of the purpose labels to indicate to the user
        what this command does.
        
        Also, grid the frame so the user can see its contents.
        """

        self.header_label.configure(text=self.command_name)
        self.purpose_label.configure(text=self.purpose_line)
        
        self.frame_content.grid()


class TextDialogShow(SharedPages.CommandNoParameters):
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs)


class TextDialogClose(SharedPages.CommandNoParameters):
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs)


class DialogHalt(SharedPages.CommandNoParameters):
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs)


class Flip(SharedPages.StartStop):
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs)


class DialogTextSound(SharedPages.LoadSpriteNoAlias):
    """
    <dialog_text_sound: audio name>
    Sets the audio to play for letter-by-letter text displays (non fading).
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)
        
        self.set_audio_text()
        
    def set_audio_text(self):
        """
        Show audio specific instructions.
        """
        self.lbl_prompt.configure(text="Audio:")



class DialogTextSoundClear(SharedPages.CommandNoParameters):
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs)



class DialogHaltAuto(SharedPages.SpeedOnly):
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs)


class DialogContinue(WizardListing):
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs)

        self.frame_content = self.create_content_frame()
        
    def create_content_frame(self) -> ttk.Frame:
        """
        Create and return a frame that will hold the configuration contents
        for this command.
        """
        
        frame_contents = ttk.Frame(self.parent_frame)
        
        instructions = "This command will cause the dialog text to continue on the last line\n" + \
        "instead of the next line."
        
        when_to_use_title = "When to use this command:"
        when_to_use = "When you want to change the font of the next letter on the same line."

        lbl_instructions = ttk.Label(frame_contents,
                                     text=instructions)

        lbl_when_to_use_title = ttk.Label(frame_contents,
                                          text=when_to_use_title,
                                          font="TkHeadingFont")
        
        lbl_when_to_use = ttk.Label(frame_contents,
                                    text=when_to_use)
        
        lbl_instructions.pack(anchor=tk.W, pady=(0, 10))
        lbl_when_to_use_title.pack(anchor=tk.W)
        lbl_when_to_use.pack(anchor=tk.W)
        
        lframe = ttk.LabelFrame(frame_contents,
                                text="Change Y coordinate of text (optional)")

        inner_frame = ttk.Frame(lframe)

        self.v_use_manual_y = tk.BooleanVar()
        self.v_use_manual_y.trace_add("write", self.on_use_manual_y_checkbutton_clicked)
        
        self.v_scale_value = tk.IntVar()

        chk_manual_y = ttk.Checkbutton(inner_frame,
                                       text="Use manual Y position",
                                       variable=self.v_use_manual_y)
        
        y_position_instructions = "The purpose of wanting to continue at a different Y position is if\n" + \
            "the font has changed and the new font's height is different than\n" + \
            "the text before it. For example: you can use <continue: -5>\n" + \
            "to position the new text slightly higher than the previous text."
        
        self.lbl_y_position_instructions = ttk.Label(inner_frame,
                                                text=y_position_instructions)
        
        self.scale = ttk.LabeledScale(inner_frame,
                                 from_=-50,
                                 to=50,
                                 variable=self.v_scale_value)
        
        self.v_scale_value.set(-5)

        chk_manual_y.pack(anchor=tk.W)
        self.scale.pack(anchor=tk.W)
        self.lbl_y_position_instructions.pack(anchor=tk.W, pady=10)
        
        inner_frame.pack(padx=10, pady=10)

        lframe.pack(pady=(10, 0),
                    anchor=tk.W,
                    expand=True,
                    fill=tk.X)
        
        # Simulate that the checkbutton was clicked so that
        # we can disable the appropriate widgets on startup.
        self.on_use_manual_y_checkbutton_clicked()
        
        return frame_contents
    
    def generate_command(self) -> str:
        """
        Return the command with its optional parameter (if needed).
        """

        if self.v_use_manual_y.get():
            y_value = self.v_scale_value.get()

            command_return = f"<{self.command_name}: {y_value}>"
        else:
            command_return = f"<{self.command_name}>"
            
        return command_return

    def on_use_manual_y_checkbutton_clicked(self, *args):
        """
        The checkbutton, 'Use manual Y position', was clicked.
        Read the new checkbutton state and enable/disable widgets as needed.
        """
        is_checked = self.v_use_manual_y.get()

        if is_checked:
            state_change = "!disabled"
        else:
            state_change = "disabled"
        
        # Using the state method doesn't work on a labeled scale.
        # We need to disable/enable individual widgets in the labeledscale.
        for name in self.scale.children.values():
            widget = self.scale.nametowidget(name)
            widget.state([state_change])        

        self.lbl_y_position_instructions.state([state_change])
        

class TextDialogDefine(WizardListing):
    """
    <text_dialog_define: width, height, animation_speed, intro_animation,
         outro_animation, anchor, bg_red, bg_green, bg_blue, padding_x, padding_y, opacity,
         rounded_corners, reusable_intro_starting, reusable_intro_finished,
         reusable_outro_starting, reusable_outro_finished, border_red,
         border_green, border_blue, border_opacity, border width>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)
        
        self.text_define: TextCreateDialogFrame
        self.frame_content = self.create_content_frame()


    def create_content_frame(self) -> ttk.Frame:
        """
        Create the widgets needed for this command
        and return a frame that contains the widgets.
        """

        frame_content = ttk.Frame(self.parent_frame)

        self.text_define = TextCreateDialogFrame(frame_content)
        self.text_define.mainframe.pack()
        
        return frame_content
    
    def check_inputs(self) -> Dict | None:
        """
        Check whether the user has inputted sufficient information
        to use this command.
        
        Return: a dict with the chosen parameters
        or None if insufficient information was provided by the user.
        """

        user_input = {}
        
        # Get the number from the spinbox.
        try:
            
            dialog_width = self.text_define.v_width.get()
            dialog_height = self.text_define.v_height.get()
        except tk.TclError:
            messagebox.showerror(parent=self.parent_frame.winfo_toplevel(), 
                                 title="Dialog Dimensions",
                                 message="Numbers are expected for the width and height of the dialog rectangle.")
            return
        
        # Get the label's background color in hex format.
        bg_color_hex = self.text_define.lbl_backcolor.cget("background")
        
        # Get the label's background colour for the border, in hex format
        border_color_hex =\
            self.text_define.lbl_backcolor_border.cget("background")
        
        border_opacity = self.text_define.v_opacity_border.get()
        border_width = self.text_define.v_border_width.get()

        # Set Rounded Corners bool to "yes" or "no" because that's what
        # LVNAuth player expects.
        rounded_corners = self.text_define.v_rounded_corners.get()
        if rounded_corners:
            rounded_corners = "yes"
        else:
            rounded_corners = "no"


        """
        Reusable scripts to run when an intro/outro dialog animation
        starts or finishes.
        """
        
        reusable_intro_starting =\
            self.text_define.cb_reusable_on_intro_starting.get()
        
        reusable_intro_finished =\
            self.text_define.cb_reusable_on_intro_finished.get()

        reusable_outro_starting =\
            self.text_define.cb_reusable_on_outro_starting.get()
        
        reusable_outro_finished =\
            self.text_define.cb_reusable_on_outro_finished.get()

        """
        Run reusable scripts on <halt> and <unhalt>
        """
        reusable_on_halt = self.text_define.cb_resuable_on_halt.get()
        reusable_on_unhalt = self.text_define.cb_resuable_on_unhalt.get()
        
        if not reusable_on_halt:
            reusable_on_halt = "none"

        if not reusable_on_unhalt:
            reusable_on_unhalt = "none"
        


        # Get the animation type of the dialog intro and outro
        intro_animation = self.text_define.cb_intro_animation.get()
        outro_animation = self.text_define.cb_outro_animation.get()


        # Don't allow a reusable script to run when the dialog is starting
        # to show, if there is no animation, because it will suddenly show.
        if not intro_animation or intro_animation == "no animation":
            reusable_intro_starting = "none"

        # Don't allow a reusable script to run when the dialog is starting
        # to close, if there is no animation, because it will suddenly hide.
        if not outro_animation or outro_animation == "no animation":
            reusable_outro_starting == "none"

        # Don't allow empty reusable script names
        if not reusable_intro_starting:
            reusable_intro_starting = "none"
        
        if not reusable_intro_finished:
            reusable_intro_finished = "none"

        if not reusable_outro_starting:
            reusable_outro_starting = "none"

        if not reusable_outro_finished:
            reusable_outro_finished = "none"


        user_input = {"Width": dialog_width,
                      "Height": dialog_height,
                      "AnimationSpeed": self.text_define.v_animation_speed.get(),
                      "IntroAnimation": intro_animation,
                      "OutroAnimation": outro_animation,
                      "Anchor": self.text_define.cb_dialog_position.get(),
                      "PaddingX": self.text_define.v_padding_x.get(),
                      "PaddingY": self.text_define.v_padding_y.get(),
                      "RoundedCorners": rounded_corners,
                      "Alpha": self.text_define.v_opacity.get(),
                      "BackgroundColor": bg_color_hex,
                      "IntroAnimationStartRunReusable": reusable_intro_starting,
                      "IntroAnimationFinishedRunReusable": reusable_intro_finished,
                      "OutroAnimationStartRunReusable": reusable_outro_starting,
                      "OutroAnimationFinishedRunReusable": reusable_outro_finished,
                      "OnHaltRunReusable": reusable_on_halt,
                      "OnUnhaltRunReusable": reusable_on_unhalt,
                      "BorderColor": border_color_hex,
                      "BorderOpacity": border_opacity,
                      "BorderWidth": border_width}

        return user_input

    def generate_command(self) -> str | None:
        """
        Return the command based on the user's configuration/selection.
        """
        
        # <text_dialog_define>

        user_inputs = self.check_inputs()
        
        if not user_inputs:
            return

        width = user_inputs.get("Width")
        height = user_inputs.get("Height")
        animation_speed = user_inputs.get("AnimationSpeed")
        intro_animation = user_inputs.get("IntroAnimation")
        outro_animation = user_inputs.get("OutroAnimation")
        anchor = user_inputs.get("Anchor")
        padding_x = user_inputs.get("PaddingX")
        padding_y = user_inputs.get("PaddingY")
        rounded_corners = user_inputs.get("RoundedCorners")
        opacity = user_inputs.get("Alpha")
        bg_color_hex = user_inputs.get("BackgroundColor")
        reusable_intro_starting = user_inputs.get("IntroAnimationStartRunReusable")
        reusable_intro_finished = user_inputs.get("IntroAnimationFinishedRunReusable")
        reusable_outro_starting = user_inputs.get("OutroAnimationStartRunReusable")
        reusable_outro_finished = user_inputs.get("OutroAnimationFinishedRunReusable")
        reusable_on_halt = user_inputs.get("OnHaltRunReusable")
        reusable_on_unhalt = user_inputs.get("OnUnhaltRunReusable")
        border_color_hex = user_inputs.get("BorderColor")
        border_opacity = user_inputs.get("BorderOpacity")
        border_width = user_inputs.get("BorderWidth")
        

        command_line = f"<{self.command_name}: {width}, {height}, {animation_speed}, " \
            f"{intro_animation}, {outro_animation}, {anchor}, " \
            f"{bg_color_hex}, {padding_x}, {padding_y}, " \
            f"{opacity}, {rounded_corners}, {reusable_intro_starting}, " \
            f"{reusable_intro_finished}, {reusable_outro_starting}, {reusable_outro_finished}, " \
            f"{reusable_on_halt}, {reusable_on_unhalt}, {border_color_hex}, " \
            f"{border_opacity}, {border_width}>"

        return command_line

class ReusableScriptSelect(SharedPages.ReusableScriptSelect):
    """
    <call: reusable script name>
    <after: frames elapse, reusable script name>
    <after_cancel: reusable script name>
    
    Layout:
      1 Label
      1 Combobox
      
      (below is optional, meant for <after>, but not <after_cancel>)
      1 Label
      1 Spinbox
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)


class SceneScriptSelect(SharedPages.SceneScriptSelect):
    """
    <scene: chapter name, scene name>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)


class CharacterAfterRotatingStop(SharedPages.AfterStop):
    """
    <character_after_rotating_stop: general alias, reusable script name to run>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)


class CharacterRotateCurrentValue(WizardListing):
    """
    <character_rotate_current_value: general alias, angle value>
    Immediately set a sprite's rotation value (no gradual animation).
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)

        self.frame_content = self.create_content_frame()

    def create_content_frame(self) -> ttk.Frame:
        """
        Create the widgets needed for this command
        and return a frame that contains the widgets.
        """

        frame_content = ttk.Frame(self.parent_frame)

        lbl_general_alias = ttk.Label(frame_content,
                                      text=f"{self.get_purpose_name(title_casing=True)} alias:")
        self.entry_general_alias = ttk.Entry(frame_content, width=25)
        
        self.v_angle = tk.IntVar()
        self.v_angle.set(90)
        
        lbl_angle = ttk.Label(frame_content, text="Angle (degrees):")
        scale = ttk.LabeledScale(frame_content,
                                 from_=0,
                                 to=359,
                                 variable=self.v_angle)

        lbl_general_alias.grid(row=0, column=0, sticky="w")
        self.entry_general_alias.grid(row=1, column=0, sticky="w")

        lbl_angle.grid(row=2, column=0, sticky="w", pady=(15, 0))
        scale.grid(row=3, column=0, sticky="w")
        
        return frame_content
    

    def check_inputs(self) -> Dict | None:
        """
        Check whether the user has inputted sufficient information
        to use this command.
        
        Return: a dict with the character general alias and an angle.
        Example:
        {"Alias": "Rave", "Angle": 90}
        or None if insufficient information was provided by the user.
        """

        user_input = {}
        
        # Get the angle from the scale widget.
        angle = self.v_angle.get()
        if angle is None:
            messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                   title="No angle specified",
                                   message="Please specify an angle.")
            return

        alias = self.entry_general_alias.get().strip()
        if not alias:
            messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                   title="No alias provided",
                                   message="Enter an alias for the character.")
            return
        
        user_input = {"Alias": alias,
                      "Angle": angle}

        return user_input
    
    def generate_command(self) -> str | None:
        """
        Return the command based on the user's configuration/selection.
        """

        # The user input will be a dictionary like this:
        # {"Alias": "Rave",
        # "Angle": 90}
        user_inputs = self.check_inputs()
        
        if not user_inputs:
            return

        angle = user_inputs.get("Angle")
        alias = user_inputs.get("Alias")
        
        return f"<character_rotate_current_value: {alias}, {angle}>"

    def show(self):
        """
        Set the text of the purpose labels to indicate to the user
        what this command does.
        
        Also, grid the frame so the user can see its contents.
        """

        self.header_label.configure(text=self.command_name)
        self.purpose_label.configure(text=self.purpose_line)


        self.frame_content.grid()


class CharacterRotateDelay(SharedPages.Delay):
    """
    <character_rotate_delay: general alias, number of frames to skip>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)


class CharacterRotateSpeed(SharedPages.Speed):
    """
    <character_rotate_speed: general alias, rotate speed value, "clockwise" or "counterclockwise">
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)


class CharacterRotateUntil(SharedPages.Until):
    """
    <character_fade_until: general alias, fade value>
    The fade value should be between 0 and 255.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)
        
        self.frame_content = self.create_content_frame()


class CharacterStartRotating(SharedPages.StartStop):
    """
    <character_start_rotating: general alias>
    Starts a character sprite rotation animation.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)


class CharacterStopRotating(SharedPages.StartStop):
    """
    <character_stop_rotating: general alias>
    Stops a character sprite rotation animation.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)


class CharacterAfterScalingStop(SharedPages.AfterStop):
    """
    <character_after_scaling_stop: general alias, reusable script name to run>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)


class CharacterScaleBy(SharedPages.Speed):
    """
    <character_scale_by: general alias, scale value, "scale up" or "scale down">
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)



class CharacterScaleCurrentValue(SharedPages.CurrentValue):
    """
    <character_scale_current_value: general alias, scale value>
    Immediately set a sprite's scale value (no gradual animation).
    
    Example of value: 2  (2 means twice as big as the original sprite)
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)


class CharacterScaleDelay(SharedPages.Delay):
    """
    <character_scale_delay: general alias, number of frames to skip>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)


class CharacterScaleUntil(SharedPages.Until):
    """
    <character_scale_until: general alias, scale amount>
    Set when to stop scaling a sprite.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)


class CharacterStartScaling(SharedPages.StartStop):
    """
    <character_start_scaling: general alias>
    Starts a character sprite scaling animation.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)


class CharacterStopScaling(SharedPages.StartStop):
    """
    <character_stop_scaling: general alias>
    Stops a character sprite scaling animation.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)


class CharacterAfterMovementStop(SharedPages.AfterStop):
    """
    <character_after_movement_stop: general alias, reusable script to run>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)


class CharacterStopMovementCondition(SharedPages.StopMovementCondition):
    """
    <character_stop_movement_condition: general alias, (optional)sprite side to check, stop location>
    Add a condition that defines when to stop a moving sprite.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)

class CharacterMove(SharedPages.Move):
    """
    <character_move: general alias, x value, y value>
    
    For example: <character_move: rave, 50, 100> which means move the
    sprite horizontally by 50 pixels each time and 100 pixels vertically
    each time. The ‘time’ portion depends on <character_move_delay>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)


class CharacterStartMoving(SharedPages.StartStop):
    """
    <character_move_start: general alias>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line)


class CharacterMoveDelay(SharedPages.MoveDelay):
    """
    <character_move_delay: general alias, x delay, y delay>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)


class CharacterSetPositionX(SharedPages.Position):
    """
    <character_set_position_x: general alias, position name>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)



class CharacterSetPositionY(SharedPages.Position):
    """
    <character_set_position_y: general alias, position name>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)


class CharacterSetCenter(SharedPages.SetCenter):
    """
    <character_set_center: general alias, x position, y position>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)


class CharacterShow(SharedPages.ShowSprite):
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line)



class CharacterHide(SharedPages.HideSpriteWithAlias):
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line)

        

if __name__ == "__main__":
    app = WizardWindow()
    app.run()
