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

"""
Changes:

Nov 13, 2023 (Jobin Rezai) - The scenes combo box now only show scenes
in the selected chapter.

Nov 16, 2023 (Jobin Rezai) - Add these commands to the wizard:
<dialog_sprite_center_x_with>, <object_center_x_with>, <character_center_x_with>

Nov 23, 2023 (Jobin Rezai) - Added <Escape> binding to close window.
"""

import re
import pathlib
import tkinter as tk
import pygubu
import command_class as cc
from player.condition_handler import ConditionOperator
from tkinter import messagebox
from tkinter import ttk
from tkinter import colorchooser
from typing import Dict
from enum import Enum, auto
from project_snapshot import ProjectSnapshot
from entry_limit import EntryWithLimit
from functools import partial
from re import search, IGNORECASE
from command_helper import CommandHelper, ContextEditRun


PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "wizard.ui"
TEXT_CREATE_DIALOG_UI = PROJECT_PATH / "ui" / "text_create_dialog.ui"
WAIT_FOR_ANIMATION_UI = PROJECT_PATH / "ui" / "wait_for_animation_dialog.ui"
SCENE_WITH_FADE_UI = PROJECT_PATH / "ui" / "scene_with_fade_dialog.ui"


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
    VARIABLE_SET = auto() # such as <variable_set>
    REMOTE_WEB = auto() # such as <remote: get into myvar, somekey>


class GroupName(Enum):
    LOAD = auto()
    PLAY = auto()
    STOP = auto()
    VOLUME = auto()
    TEXT_SOUND = auto()
    SHOW = auto()
    HIDE = auto()
    FLIP = auto()
    FADE = auto()
    ROTATE = auto()
    SCALE = auto()
    MOVE = auto()
    POSITION = auto()
    MOUSE = auto()

    # Font
    SPEED = auto()
    TEXT = auto()
    USE_FONT = auto()
    FONT_ANIMATION = auto()
    
    CREATE_DIALOGUE_AREA = auto()
    PAUSE = auto()
    TIMER = auto()
    
    RUN_SCRIPT = auto()
    


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
        self.default_width = 400
        self.default_height = 200
        self.v_width.set(self.default_width)
        self.v_height.set(self.default_height)
        
        self.default_anchor = "mid bottom"
        self.cb_dialog_position.configure(state="normal")
        self.cb_dialog_position.insert(0, self.default_anchor)
        self.cb_dialog_position.configure(state="readonly")

        
        """
        Animation tab
        """
        self.cb_intro_animation = self.builder.get_object("cb_intro_animation")
        self.cb_outro_animation = self.builder.get_object("cb_outro_animation")
        self.v_animation_speed = self.builder.get_variable("v_animation_speed")

        # Default values
        self.default_intro_animation = "scale up width and height"
        self.cb_intro_animation.configure(state="normal")
        self.cb_intro_animation.insert(0, self.default_intro_animation)
        self.cb_intro_animation.configure(state="readonly")

        self.default_outro_animation = "fade out"
        self.cb_outro_animation.configure(state="normal")
        self.cb_outro_animation.insert(0, self.default_outro_animation)
        self.cb_outro_animation.configure(state="readonly")

        self.default_animation_speed = 5
        self.v_animation_speed.set(self.default_animation_speed)


        """
        Colours tab
        """
        self.lbl_backcolor: ttk.Label
        self.lbl_backcolor = self.builder.get_object("lbl_backcolor")
        self.v_opacity = self.builder.get_variable("v_opacity")
        
        self.default_opacity = 200
        self.v_opacity.set(self.default_opacity)
        
        self.lbl_backcolor_border: ttk.Label
        self.lbl_backcolor_border =\
            self.builder.get_object("lbl_backcolor_border")
        
        self.default_opacity_border = 200
        self.v_opacity_border = self.builder.get_variable("v_opacity_border")
        self.v_opacity_border.set(self.default_opacity_border)
        
        self.default_border_width = 0
        self.v_border_width = self.builder.get_variable("v_border_width")
        self.v_border_width.set(self.default_border_width)
        
        
        
        """
        Padding tab
        """
        self.v_padding_x = self.builder.get_variable("v_padding_x")
        self.v_padding_y = self.builder.get_variable("v_padding_y")
        
        # Default values
        self.default_padding_x = 0
        self.default_padding_y = 0
        self.v_padding_x.set(self.default_padding_x)
        self.v_padding_y.set(self.default_padding_y)

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
    
    # This dictionary is used for selecting a specific command
    # in the treeview widget when editing an existing command from a script.
    # Purpose: so we can select any command via the treeview widget when
    # editing a script command.
    # Key: command name (lowercase)
    # Value: iid in the treeview widget
    command_item_iids = {}
    
    def __init__(self, master=None):
        
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow = builder.get_object("toplevel1", master)
        self.mainwindow.bind("<Escape>", self.on_cancel_button_clicked)
        
        builder.connect_callbacks(self)
        
        # Clear dictionary used for keeping track of command name item iids
        # in the treeview widget.
        WizardWindow.command_item_iids.clear()
        
        self.sb_vertical = builder.get_object("sb_vertical")

        # The sub-frame will be put into the frame below.
        self.frame_contents_outer = builder.get_object("frame_contents_outer")
        
        self.lbl_header = builder.get_object("lbl_header")
        self.lbl_purpose = builder.get_object("lbl_purpose")

        self.treeview_commands: ttk.Treeview
        self.treeview_commands = builder.get_object("treeview_commands")
        
        # The row background color to change to when a new group of command
        # rows are being populated in the wizard treeview widget.
        self.treeview_commands.tag_configure("row_color_1",
                                             background="#e4e4e4")        
        self.treeview_commands.tag_configure("row_color_2",
                                             background="lightgray")
        
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
                         purpose_line="Prepare an audio file to be played.",
                         group_name=GroupName.LOAD)

        page_music_load =\
            AudioLoad(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="load_music",
                         command_name="load_music",
                         purpose_line="Prepare a music file to be played.",
                         group_name=GroupName.LOAD)

        page_audio_play_music =\
            AudioPlay(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="play_music",
                         command_name="play_music",
                         purpose_line="Play audio in the music channel.",
                         group_name=GroupName.PLAY)
        
        page_audio_play_sound =\
            AudioPlay(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="play_sound",
                         command_name="play_sound",
                         purpose_line="Play a sound effect in the sound channel.",
                         group_name=GroupName.PLAY)

        page_audio_play_voice =\
            AudioPlay(parent_frame=self.frame_contents_outer,
                         header_label=self.lbl_header,
                         purpose_label=self.lbl_purpose,
                         treeview_commands=self.treeview_commands,
                         parent_display_text="Audio",
                         sub_display_text="play_voice",
                         command_name="play_voice",
                         purpose_line="Play audio in the voice channel.",
                         group_name=GroupName.PLAY)

        page_audio_stop_fx = \
            CommandOnly(parent_frame=self.frame_contents_outer,
                        header_label=self.lbl_header,
                        purpose_label=self.lbl_purpose,
                        treeview_commands=self.treeview_commands,
                        parent_display_text="Audio",
                        sub_display_text="stop_fx",
                        command_name="stop_fx",
                        purpose_line="Stops the audio in the FX channel.",
                        when_to_use="When you want to stop playing an audio effect.",
                        group_name=GroupName.STOP)

        page_audio_stop_all_audio = \
            CommandOnly(parent_frame=self.frame_contents_outer,
                        header_label=self.lbl_header,
                        purpose_label=self.lbl_purpose,
                        treeview_commands=self.treeview_commands,
                        parent_display_text="Audio",
                        sub_display_text="stop_all_audio",
                        command_name="stop_all_audio",
                        purpose_line="Stops playing the audio for: effects, voices, music.",
                        when_to_use="When you want to stop playing audio effects, voices, and music.\n"
                                    "No error will occur if no audio is playing.",
                        group_name=GroupName.STOP)

        page_audio_stop_music = \
            CommandOnly(parent_frame=self.frame_contents_outer,
                        header_label=self.lbl_header,
                        purpose_label=self.lbl_purpose,
                        treeview_commands=self.treeview_commands,
                        parent_display_text="Audio",
                        sub_display_text="stop_music",
                        command_name="stop_music",
                        purpose_line="Stops the audio in the music channel.",
                        when_to_use="When you want to stop playing music.",
                        group_name=GroupName.STOP)

        page_audio_stop_voice = \
            CommandOnly(parent_frame=self.frame_contents_outer,
                        header_label=self.lbl_header,
                        purpose_label=self.lbl_purpose,
                        treeview_commands=self.treeview_commands,
                        parent_display_text="Audio",
                        sub_display_text="stop_voice",
                        command_name="stop_voice",
                        purpose_line="Stops the audio in the voice channel.",
                        when_to_use="When you want to stop playing audio in the voice channel.",
                        group_name=GroupName.STOP)


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
                         scale_default_value=100,
                         group_name=GroupName.VOLUME)

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
                         scale_default_value=100,
                         group_name=GroupName.VOLUME)

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
                         scale_default_value=100,
                         group_name=GroupName.VOLUME)

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
                         scale_default_value=100,
                         group_name=GroupName.VOLUME)

        page_audio_dialog_text_sound =\
            DialogTextSound(parent_frame=self.frame_contents_outer,
                            header_label=self.lbl_header,
                            purpose_label=self.lbl_purpose,
                            treeview_commands=self.treeview_commands,
                            parent_display_text="Audio",
                            sub_display_text="dialog_text_sound",
                            command_name="dialog_text_sound",
                            purpose_line="Set audio to play for each gradually shown letter.\n"
                            "Only works for gradually-shown text (non-fading).",
                            group_name=GroupName.TEXT_SOUND)

        page_audio_dialog_text_sound_clear = \
            CommandOnly(parent_frame=self.frame_contents_outer,
                        header_label=self.lbl_header,
                        purpose_label=self.lbl_purpose,
                        treeview_commands=self.treeview_commands,
                        parent_display_text="Audio",
                        sub_display_text="dialog_text_sound_clear",
                        command_name="dialog_text_sound_clear",
                        purpose_line="Set no audio to play for each gradually shown letter.",
                        when_to_use="When you no longer want to have any audio play\nfor each letter that is shown one by one.",
                        group_name=GroupName.TEXT_SOUND)


        page_load_background =\
            Background_LoadBackground(parent_frame=self.frame_contents_outer,
                                      header_label=self.lbl_header,
                                      purpose_label=self.lbl_purpose,
                                      treeview_commands=self.treeview_commands,
                                      parent_display_text="Background",
                                      sub_display_text="load_background",
                                      command_name="load_background",
                                      purpose_line="Load a background sprite into memory.",
                                      group_name=GroupName.LOAD)

        page_show_background =\
            BackgroundShow(parent_frame=self.frame_contents_outer,
                           header_label=self.lbl_header,
                           purpose_label=self.lbl_purpose,
                           treeview_commands=self.treeview_commands,
                           parent_display_text="Background",
                           sub_display_text="background_show",
                           command_name="background_show",
                           purpose_line="Show a specific a background sprite in the story.",
                           group_name=GroupName.SHOW)

        page_hide_background =\
            BackgroundHide(parent_frame=self.frame_contents_outer,
                           header_label=self.lbl_header,
                           purpose_label=self.lbl_purpose,
                           treeview_commands=self.treeview_commands,
                           parent_display_text="Background",
                           sub_display_text="background_hide",
                           command_name="background_hide",
                           purpose_line="Hide a specific a background sprite in the story.",
                           group_name=GroupName.HIDE)

        page_load_character =\
            Character_LoadCharacter(parent_frame=self.frame_contents_outer,
                                    header_label=self.lbl_header,
                                    purpose_label=self.lbl_purpose,
                                    treeview_commands=self.treeview_commands,
                                    parent_display_text="Character",
                                    sub_display_text="load_character",
                                    command_name="load_character",
                                    purpose_line="Load a character sprite into memory.",
                                    group_name=GroupName.LOAD)

        page_show_character =\
            CharacterShow(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Character",
                          sub_display_text="character_show",
                          command_name="character_show",
                          purpose_line="Shows the given sprite and it hides the currently visible\n"
                          "sprite with the same general alias as the one we’re about to show.",
                          group_name=GroupName.SHOW)


        page_hide_character =\
            CharacterHide(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Character",
                          sub_display_text="character_hide",
                          command_name="character_hide",
                          purpose_line="Hides the given sprite.",
                          group_name=GroupName.HIDE)

        page_hide_all_character = \
            CommandOnly(parent_frame=self.frame_contents_outer,
                        header_label=self.lbl_header,
                        purpose_label=self.lbl_purpose,
                        treeview_commands=self.treeview_commands,
                        parent_display_text="Character",
                        sub_display_text="character_hide_all",
                        command_name="character_hide_all",
                        purpose_line="Hides all character sprites.",
                        group_name=GroupName.HIDE)

        page_character_flip_both =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Character",
                          sub_display_text="character_flip_both",
                          command_name="character_flip_both",
                          purpose_line="Flips the given sprite both horizontally and vertically.",
                          group_name=GroupName.FLIP)


        page_character_flip_horizontal =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Character",
                          sub_display_text="character_flip_horizontal",
                          command_name="character_flip_horizontal",
                          purpose_line="Flips the given sprite horizontally.",
                          group_name=GroupName.FLIP)


        page_character_flip_vertical =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Character",
                          sub_display_text="character_flip_vertical",
                          command_name="character_flip_vertical",
                          purpose_line="Flips the given sprite vertically.",
                          group_name=GroupName.FLIP)
        

        page_character_after_fading_stop =\
            CharacterAfterFadingStop(parent_frame=self.frame_contents_outer,
                                    header_label=self.lbl_header,
                                    purpose_label=self.lbl_purpose,
                                    treeview_commands=self.treeview_commands,
                                    parent_display_text="Character",
                                    sub_display_text="character_after_fading_stop",
                                    command_name="character_after_fading_stop",
                                    purpose_line="Run a reusable script after a specific character sprite stops fading.",
                                    group_name=GroupName.FADE)

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
                                      amount_name="opacity level",
                                      group_name=GroupName.FADE)

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
                               amount_name="number of frames to skip",
                               group_name=GroupName.FADE)

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
                               scale_instructions="Fade speed (1 to 100):",
                               group_name=GroupName.FADE)

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
                               scale_default_value=128,
                               group_name=GroupName.FADE)

        page_character_start_fading =\
            CharacterStartFading(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Character",
                                 sub_display_text="character_start_fading",
                                 command_name="character_start_fading",
                                 purpose_line="Starts a character sprite fading animation.\n"
                                 "Note: the character sprite must already be visible.",
                                 group_name=GroupName.FADE)

        page_character_stop_fading =\
            CharacterStopFading(parent_frame=self.frame_contents_outer,
                                header_label=self.lbl_header,
                                purpose_label=self.lbl_purpose,
                                treeview_commands=self.treeview_commands,
                                parent_display_text="Character",
                                sub_display_text="character_stop_fading",
                                command_name="character_stop_fading",
                                purpose_line="Stops a character sprite fading animation.\n"
                                "Note: the character sprite must already be visible.",
                                group_name=GroupName.FADE)

        page_character_after_rotating_stop =\
            CharacterAfterRotatingStop(parent_frame=self.frame_contents_outer,
                                       header_label=self.lbl_header,
                                       purpose_label=self.lbl_purpose,
                                       treeview_commands=self.treeview_commands,
                                       parent_display_text="Character",
                                       sub_display_text="character_after_rotating_stop",
                                       command_name="character_after_rotating_stop",
                                       purpose_line="When a specific sprite image stops rotating, run a reusable script.\n"
                                       "Note: the character sprite must already be visible.",
                                       group_name=GroupName.ROTATE)

        page_character_rotate_current_value =\
            CharacterRotateCurrentValue(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Character",
                                        sub_display_text="character_rotate_current_value",
                                        command_name="character_rotate_current_value",
                                        purpose_line="Immediately set a sprite's rotation value (no gradual animation).\n"
                                        "Note: the character sprite must already be visible.",
                                        group_name=GroupName.ROTATE)

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
                                 amount_name="number of frames to skip",
                                 group_name=GroupName.ROTATE)

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
                                 scale_instructions="Rotation speed (1 to 100):",
                                 group_name=GroupName.ROTATE)

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
                                 scale_default_value=180,
                                 group_name=GroupName.ROTATE)

        page_character_start_rotating =\
            CharacterStartRotating(parent_frame=self.frame_contents_outer,
                                   header_label=self.lbl_header,
                                   purpose_label=self.lbl_purpose,
                                   treeview_commands=self.treeview_commands,
                                   parent_display_text="Character",
                                   sub_display_text="character_start_rotating",
                                   command_name="character_start_rotating",
                                   purpose_line="Starts a character sprite rotation animation.\n"
                                   "Note: the character sprite must already be visible.",
                                   group_name=GroupName.ROTATE)

        page_character_stop_rotating =\
            CharacterStopRotating(parent_frame=self.frame_contents_outer,
                                  header_label=self.lbl_header,
                                  purpose_label=self.lbl_purpose,
                                  treeview_commands=self.treeview_commands,
                                  parent_display_text="Character",
                                  sub_display_text="character_stop_rotating",
                                  command_name="character_stop_rotating",
                                  purpose_line="Stops a character sprite rotation animation.\n"
                                  "Note: the character sprite must already be visible.",
                                  group_name=GroupName.ROTATE)

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
                                      "Note: the character sprite must already be visible.",
                                      group_name=GroupName.SCALE)

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
                             scale_instructions="Scale speed (1 to 100):",
                             group_name=GroupName.SCALE)

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
                                       "(example: 2 means twice as big as the original size)\nDecimal numbers such as 1.1 can be used as well.",
                                       amount_name="scale",
                                       group_name=GroupName.SCALE)

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
                                amount_name="number of frames to skip",
                                group_name=GroupName.SCALE)

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
                                scale_instructions="Stop scaling when the scale reaches... (0 to 100)\nDecimal values like 1.1 can be used as well.",
                                scale_from_value=0,
                                scale_to_value=100,
                                scale_default_value=2,
                                group_name=GroupName.SCALE)

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
                                  "Also, <character_scale_until> should be used prior.",
                                  group_name=GroupName.SCALE)

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
                                 "Note: the character sprite must already be visible.",
                                 group_name=GroupName.SCALE)

        page_character_after_movement_stop =\
            CharacterAfterMovementStop(parent_frame=self.frame_contents_outer,
                                       header_label=self.lbl_header,
                                       purpose_label=self.lbl_purpose,
                                       treeview_commands=self.treeview_commands,
                                       parent_display_text="Character",
                                       sub_display_text="character_after_movement_stop",
                                       command_name="character_after_movement_stop",
                                       purpose_line="Run a reusable script after a specific character sprite stops moving.",
                                       group_name=GroupName.MOVE)
   
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
                                      "will stop moving.",
                                      group_name=GroupName.MOVE)

        page_character_move =\
            CharacterMove(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Character",
                          sub_display_text="character_move",
                          command_name="character_move",
                          purpose_line="Sets the movement amount and direction of a character sprite.",
                          group_name=GroupName.MOVE)

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
                               spinbox_to_value=120,
                               group_name=GroupName.MOVE)

        page_character_start_moving =\
            CharacterStartMoving(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Character",
                                 sub_display_text="character_start_moving",
                                 command_name="character_start_moving",
                                 purpose_line="Starts a movement animation on a specific character sprite.",
                                 group_name=GroupName.MOVE)

        page_character_stop_moving = \
            CharacterStartMoving(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Character",
                                 sub_display_text="character_stop_moving",
                                 command_name="character_stop_moving",
                                 purpose_line="Stops a movement animation on a specific character sprite.",
                                 group_name=GroupName.MOVE)

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
                                  direction="horizontal",
                                  group_name=GroupName.POSITION)

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
                                  direction="vertical",
                                  group_name=GroupName.POSITION)                                  

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
                               spinbox_to_value=9000,
                               group_name=GroupName.POSITION)
        
        page_character_center_x_with =\
            SharedPages.CenterWithAlias(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Character",
                                        sub_display_text="character_center_x_with",
                                        command_name="character_center_x_with",
                                        purpose_line="Center the X of a character sprite with the center X of another sprite.\n"
                                        "Note: both sprites must already be visible.",
                                        group_name=GroupName.POSITION)
        
        page_character_on_mouse_click =\
            SharedPages.SpriteMouseEvent(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Character",
                                        sub_display_text="character_on_mouse_click",
                                        command_name="character_on_mouse_click",
                                        purpose_line="Run a reusable script when a specific sprite is left-clicked with the mouse.",
                                        group_name=GroupName.MOUSE)             

        page_character_on_mouse_enter =\
            SharedPages.SpriteMouseEvent(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Character",
                                        sub_display_text="character_on_mouse_enter",
                                        command_name="character_on_mouse_enter",
                                        purpose_line="Run a reusable script when the mouse pointer hovers over a specific sprite.",
                                        group_name=GroupName.MOUSE)             

        page_character_on_mouse_leave =\
            SharedPages.SpriteMouseEvent(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Character",
                                        sub_display_text="character_on_mouse_leave",
                                        command_name="character_on_mouse_leave",
                                        purpose_line="Run a reusable script when the mouse pointer is no longer hovering\nover a specific sprite.",
                                        group_name=GroupName.MOUSE)             


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
                                 purpose_line="Create a dialog rectangle for character text to appear in.",
                                 group_name=GroupName.CREATE_DIALOGUE_AREA)

        page_dialog_show = \
            CommandOnly(parent_frame=self.frame_contents_outer,
                        header_label=self.lbl_header,
                        purpose_label=self.lbl_purpose,
                        treeview_commands=self.treeview_commands,
                        parent_display_text="Dialog",
                        sub_display_text="text_dialog_show",
                        command_name="text_dialog_show",
                        purpose_line="Show a dialog rectangle that has already been defined using <text_dialog_define>.",
                        when_to_use="When a character wants to speak or for narration text.",
                        group_name=GroupName.SHOW)

        page_dialog_close = \
            CommandOnly(parent_frame=self.frame_contents_outer,
                        header_label=self.lbl_header,
                        purpose_label=self.lbl_purpose,
                        treeview_commands=self.treeview_commands,
                        parent_display_text="Dialog",
                        sub_display_text="text_dialog_close",
                        command_name="text_dialog_close",
                        purpose_line="Close the dialog by initiating its outro animation.",
                        when_to_use="When all the characters finish speaking.",
                        group_name=GroupName.HIDE)

        page_dialog_halt = \
            CommandOnly(parent_frame=self.frame_contents_outer,
                        header_label=self.lbl_header,
                        purpose_label=self.lbl_purpose,
                        treeview_commands=self.treeview_commands,
                        parent_display_text="Dialog",
                        sub_display_text="halt",
                        command_name="halt",
                        purpose_line="Pause the dialog text until the viewer clicks the mouse or presses a key.",
                        when_to_use="When you want to give the viewer a chance to pause and read.",
                        group_name=GroupName.PAUSE)

        page_dialog_halt_auto = \
            DialogHaltAuto(parent_frame=self.frame_contents_outer,
                           header_label=self.lbl_header,
                           purpose_label=self.lbl_purpose,
                           treeview_commands=self.treeview_commands,
                           parent_display_text="Dialog",
                           sub_display_text="halt_auto",
                           command_name="halt_auto",
                           purpose_line="Pause the dialog text for a specific number of frames.\n\n",
                           scale_instructions="Choose the number of frames to halt the dialog.\nNote: 60 frames is 1 second.",
                           scale_from_value=1,
                           scale_to_value=600,
                           scale_default_value=120,
                           group_name=GroupName.PAUSE)

        page_dialog_no_clear = \
            CommandOnly(parent_frame=self.frame_contents_outer,
                        header_label=self.lbl_header,
                        purpose_label=self.lbl_purpose,
                        treeview_commands=self.treeview_commands,
                        parent_display_text="Dialog",
                        sub_display_text="no_clear",
                        command_name="no_clear",
                        purpose_line="Prevent the dialog text from clearing on the next <halt> or <halt_auto>.",
                        group_name=GroupName.PAUSE)

        page_dialog_continue = \
            DialogContinue(parent_frame=self.frame_contents_outer,
                           header_label=self.lbl_header,
                           purpose_label=self.lbl_purpose,
                           treeview_commands=self.treeview_commands,
                           parent_display_text="Dialog",
                           sub_display_text="continue",
                           command_name="continue",
                           purpose_line="Stay on the same line as the previous text.",
                           group_name=GroupName.TEXT)

        page_load_dialog =\
            Character_LoadCharacter(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Dialog",
                                        sub_display_text="load_dialog_sprite",
                                        command_name="load_dialog_sprite",
                                        purpose_line="Load an dialog sprite into memory.",
                                        group_name=GroupName.LOAD)
    
        page_show_dialog =\
                CharacterShow(parent_frame=self.frame_contents_outer,
                              header_label=self.lbl_header,
                              purpose_label=self.lbl_purpose,
                              treeview_commands=self.treeview_commands,
                              parent_display_text="Dialog",
                              sub_display_text="dialog_sprite_show",
                              command_name="dialog_sprite_show",
                              purpose_line="Shows the given sprite and it hides the currently visible\n"
                                           "sprite with the same general alias as the one we’re about to show.",
                              group_name=GroupName.SHOW)
    
        page_hide_dialog =\
                CharacterHide(parent_frame=self.frame_contents_outer,
                              header_label=self.lbl_header,
                              purpose_label=self.lbl_purpose,
                              treeview_commands=self.treeview_commands,
                              parent_display_text="Dialog",
                              sub_display_text="dialog_sprite_hide",
                              command_name="dialog_sprite_hide",
                              purpose_line="Hides the given sprite.",
                              group_name=GroupName.HIDE)

        page_hide_all_dialog = \
            CommandOnly(parent_frame=self.frame_contents_outer,
                        header_label=self.lbl_header,
                        purpose_label=self.lbl_purpose,
                        treeview_commands=self.treeview_commands,
                        parent_display_text="Dialog",
                        sub_display_text="dialog_sprite_hide_all",
                        command_name="dialog_sprite_hide_all",
                        purpose_line="Hides all dialog sprites.",
                        group_name=GroupName.HIDE)

        page_dialog_flip_both =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Dialog",
                          sub_display_text="dialog_sprite_flip_both",
                          command_name="dialog_sprite_flip_both",
                          purpose_line="Flips the given sprite both horizontally and vertically.",
                          group_name=GroupName.FLIP)


        page_dialog_flip_horizontal =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Dialog",
                          sub_display_text="dialog_sprite_flip_horizontal",
                          command_name="dialog_sprite_flip_horizontal",
                          purpose_line="Flips the given sprite horizontally.",
                          group_name=GroupName.FLIP)


        page_dialog_flip_vertical =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Dialog",
                          sub_display_text="dialog_sprite_flip_vertical",
                          command_name="dialog_sprite_flip_vertical",
                          purpose_line="Flips the given sprite vertically.",
                          group_name=GroupName.FLIP)

    
        page_dialog_after_fading_stop =\
                CharacterAfterFadingStop(parent_frame=self.frame_contents_outer,
                                         header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Dialog",
                                        sub_display_text="dialog_sprite_after_fading_stop",
                                        command_name="dialog_sprite_after_fading_stop",
                                        purpose_line="Run a reusable script after a specific dialog sprite stops fading.",
                                        group_name=GroupName.FADE)
    
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
                                          amount_name="opacity level",
                                          group_name=GroupName.FADE)
    
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
                                   amount_name="number of frames to skip",
                                   group_name=GroupName.FADE)
    
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
                                   scale_instructions="Fade speed (1 to 100):",
                                   group_name=GroupName.FADE)
    
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
                                   scale_default_value=128,
                                   group_name=GroupName.FADE)
    
        page_dialog_start_fading =\
                CharacterStartFading(parent_frame=self.frame_contents_outer,
                                     header_label=self.lbl_header,
                                     purpose_label=self.lbl_purpose,
                                     treeview_commands=self.treeview_commands,
                                     parent_display_text="Dialog",
                                     sub_display_text="dialog_sprite_start_fading",
                                     command_name="dialog_sprite_start_fading",
                                     purpose_line="Starts an dialog sprite fading animation.\n"
                                     "Note: the dialog sprite must already be visible.",
                                     group_name=GroupName.FADE)
    
        page_dialog_stop_fading =\
                CharacterStopFading(parent_frame=self.frame_contents_outer,
                                    header_label=self.lbl_header,
                                    purpose_label=self.lbl_purpose,
                                    treeview_commands=self.treeview_commands,
                                    parent_display_text="Dialog",
                                    sub_display_text="dialog_sprite_stop_fading",
                                    command_name="dialog_sprite_stop_fading",
                                    purpose_line="Stops a dialog sprite fading animation.\n"
                                    "Note: the dialog sprite must already be visible.",
                                    group_name=GroupName.FADE)
    
        page_dialog_after_rotating_stop =\
                CharacterAfterRotatingStop(parent_frame=self.frame_contents_outer,
                                           header_label=self.lbl_header,
                                           purpose_label=self.lbl_purpose,
                                           treeview_commands=self.treeview_commands,
                                           parent_display_text="Dialog",
                                           sub_display_text="dialog_sprite_after_rotating_stop",
                                           command_name="dialog_sprite_after_rotating_stop",
                                           purpose_line="When a specific sprite image stops rotating, run a reusable script.\n"
                                           "Note: the dialog sprite must already be visible.",
                                           group_name=GroupName.ROTATE)
    
        page_dialog_rotate_current_value =\
                CharacterRotateCurrentValue(parent_frame=self.frame_contents_outer,
                                            header_label=self.lbl_header,
                                            purpose_label=self.lbl_purpose,
                                            treeview_commands=self.treeview_commands,
                                            parent_display_text="Dialog",
                                            sub_display_text="dialog_sprite_rotate_current_value",
                                            command_name="dialog_sprite_rotate_current_value",
                                            purpose_line="Immediately set a sprite's rotation value (no gradual animation).\n"
                                            "Note: the dialog sprite must already be visible.",
                                            group_name=GroupName.ROTATE)
    
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
                                     amount_name="number of frames to skip",
                                     group_name=GroupName.ROTATE)
    
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
                                     scale_instructions="Rotation speed (1 to 100):",
                                     group_name=GroupName.ROTATE)
    
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
                                     scale_default_value=180,
                                     group_name=GroupName.ROTATE)
    
        page_dialog_start_rotating =\
                CharacterStartRotating(parent_frame=self.frame_contents_outer,
                                       header_label=self.lbl_header,
                                       purpose_label=self.lbl_purpose,
                                       treeview_commands=self.treeview_commands,
                                       parent_display_text="Dialog",
                                       sub_display_text="dialog_sprite_start_rotating",
                                       command_name="dialog_sprite_start_rotating",
                                       purpose_line="Starts an dialog sprite rotation animation.\n"
                                       "Note: the dialog sprite must already be visible.",
                                       group_name=GroupName.ROTATE)
    
        page_dialog_stop_rotating =\
                CharacterStopRotating(parent_frame=self.frame_contents_outer,
                                      header_label=self.lbl_header,
                                      purpose_label=self.lbl_purpose,
                                      treeview_commands=self.treeview_commands,
                                      parent_display_text="Dialog",
                                      sub_display_text="dialog_sprite_stop_rotating",
                                      command_name="dialog_sprite_stop_rotating",
                                      purpose_line="Stops a dialog sprite rotation animation.\n"
                                      "Note: the dialog sprite must already be visible.",
                                      group_name=GroupName.ROTATE)
    
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
                                          "Note: the dialog sprite must already be visible.", 
                                          group_name=GroupName.SCALE)
    
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
                                 scale_instructions="Scale speed (1 to 100):",
                                 group_name=GroupName.SCALE)
    
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
                                           "(example: 2 means twice as big as the original size)\nDecimal values like 1.1 can be used as well.",
                                           amount_name="scale",
                                           group_name=GroupName.SCALE)
    
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
                                    amount_name="number of frames to skip",
                                    group_name=GroupName.SCALE)
    
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
                                    scale_instructions="Stop scaling when the scale reaches... (0 to 100)\nDecimal values like 1.1 can be used as well.",
                                    scale_from_value=0,
                                    scale_to_value=100,
                                    scale_default_value=2,
                                    group_name=GroupName.SCALE)
    
        page_dialog_start_scaling =\
                CharacterStartScaling(parent_frame=self.frame_contents_outer,
                                      header_label=self.lbl_header,
                                      purpose_label=self.lbl_purpose,
                                      treeview_commands=self.treeview_commands,
                                      parent_display_text="Dialog",
                                      sub_display_text="dialog_sprite_start_scaling",
                                      command_name="dialog_sprite_start_scaling",
                                      purpose_line="Starts an dialog sprite scaling animation.\n\n"
                                      "Note: the dialog sprite must already be visible.\n"
                                      "Also, <dialog_sprite_scale_until> should be used prior.",
                                      group_name=GroupName.SCALE)
    
        page_dialog_stop_scaling =\
                CharacterStopScaling(parent_frame=self.frame_contents_outer,
                                     header_label=self.lbl_header,
                                     purpose_label=self.lbl_purpose,
                                     treeview_commands=self.treeview_commands,
                                     parent_display_text="Dialog",
                                     sub_display_text="dialog_sprite_stop_scaling",
                                     command_name="dialog_sprite_stop_scaling",
                                     purpose_line="Stops a dialog sprite scaling animation.\n\n"
                                     "The scale value is not lost. If the scaling is started again,\n"
                                     "it will resume from where it stopped last.\n\n"
                                     "Note: the dialog sprite must already be visible.",
                                     group_name=GroupName.SCALE)
    
        page_dialog_after_movement_stop =\
                CharacterAfterMovementStop(parent_frame=self.frame_contents_outer,
                                           header_label=self.lbl_header,
                                           purpose_label=self.lbl_purpose,
                                           treeview_commands=self.treeview_commands,
                                           parent_display_text="Dialog",
                                           sub_display_text="dialog_sprite_after_movement_stop",
                                           command_name="dialog_sprite_after_movement_stop",
                                           purpose_line="Run a reusable script after a specific dialog sprite stops moving.",
                                           group_name=GroupName.MOVE)
    
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
                                          "will stop moving.",
                                          group_name=GroupName.MOVE)
    
        page_dialog_move =\
                CharacterMove(parent_frame=self.frame_contents_outer,
                              header_label=self.lbl_header,
                              purpose_label=self.lbl_purpose,
                              treeview_commands=self.treeview_commands,
                              parent_display_text="Dialog",
                              sub_display_text="dialog_sprite_move",
                              command_name="dialog_sprite_move",
                              purpose_line="Sets the movement amount and direction of an dialog sprite.",
                              group_name=GroupName.MOVE)
    
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
                                   spinbox_to_value=120,
                                   group_name=GroupName.MOVE)
    
        page_dialog_start_moving =\
                CharacterStartMoving(parent_frame=self.frame_contents_outer,
                                     header_label=self.lbl_header,
                                     purpose_label=self.lbl_purpose,
                                     treeview_commands=self.treeview_commands,
                                     parent_display_text="Dialog",
                                     sub_display_text="dialog_sprite_start_moving",
                                     command_name="dialog_sprite_start_moving",
                                     purpose_line="Starts a movement animation on a specific dialog sprite.",
                                     group_name=GroupName.MOVE)

        page_dialog_stop_moving = \
            CharacterStartMoving(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Dialog",
                                 sub_display_text="dialog_sprite_stop_moving",
                                 command_name="dialog_sprite_stop_moving",
                                 purpose_line="Stops a movement animation on a specific dialog sprite.",
                                 group_name=GroupName.MOVE)

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
                                      direction="horizontal",
                                      group_name=GroupName.POSITION)
    
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
                                      direction="vertical",
                                      group_name=GroupName.POSITION)
    
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
                                   spinbox_to_value=9000,
                                   group_name=GroupName.POSITION)

        page_dialog_sprite_center_x_with =\
            SharedPages.CenterWithAlias(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Dialog",
                                        sub_display_text="dialog_sprite_center_x_with",
                                        command_name="dialog_sprite_center_x_with",
                                        purpose_line="Center the X of a dialog sprite with the center X of another sprite.\n"
                                        "Note: both sprites must already be visible.",
                                        group_name=GroupName.POSITION)     

        page_dialog_sprite_on_mouse_click =\
            SharedPages.SpriteMouseEvent(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Dialog",
                                        sub_display_text="dialog_sprite_on_mouse_click",
                                        command_name="dialog_sprite_on_mouse_click",
                                        purpose_line="Run a reusable script when a specific sprite is left-clicked with the mouse.",
                                        group_name=GroupName.MOUSE)             

        page_dialog_sprite_on_mouse_enter =\
            SharedPages.SpriteMouseEvent(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Dialog",
                                        sub_display_text="dialog_sprite_on_mouse_enter",
                                        command_name="dialog_sprite_on_mouse_enter",
                                        purpose_line="Run a reusable script when the mouse pointer hovers over a specific sprite.",
                                        group_name=GroupName.MOUSE)             

        page_dialog_sprite_on_mouse_leave =\
            SharedPages.SpriteMouseEvent(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Dialog",
                                        sub_display_text="dialog_sprite_on_mouse_leave",
                                        command_name="dialog_sprite_on_mouse_leave",
                                        purpose_line="Run a reusable script when the mouse pointer is no longer hovering\nover a specific sprite.",
                                        group_name=GroupName.MOUSE)             


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
                                    purpose_line="Load an object sprite into memory.",
                                    group_name=GroupName.LOAD)

        page_show_object =\
            CharacterShow(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Object",
                          sub_display_text="object_show",
                          command_name="object_show",
                          purpose_line="Shows the given sprite and it hides the currently visible\n"
                          "sprite with the same general alias as the one we’re about to show.",
                          group_name=GroupName.SHOW)

        page_hide_object =\
            CharacterHide(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Object",
                          sub_display_text="object_hide",
                          command_name="object_hide",
                          purpose_line="Hides the given sprite.",
                          group_name=GroupName.HIDE)

        page_hide_all_object = \
            CommandOnly(parent_frame=self.frame_contents_outer,
                        header_label=self.lbl_header,
                        purpose_label=self.lbl_purpose,
                        treeview_commands=self.treeview_commands,
                        parent_display_text="Object",
                        sub_display_text="object_hide_all",
                        command_name="object_hide_all",
                        purpose_line="Hides all object sprites.",
                        group_name=GroupName.HIDE)
        
        page_object_flip_both =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Object",
                          sub_display_text="object_flip_both",
                          command_name="object_flip_both",
                          purpose_line="Flips the given sprite both horizontally and vertically.",
                          group_name=GroupName.FLIP)


        page_object_flip_horizontal =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Object",
                          sub_display_text="object_flip_horizontal",
                          command_name="object_flip_horizontal",
                          purpose_line="Flips the given sprite horizontally.",
                          group_name=GroupName.FLIP)


        page_object_flip_vertical =\
            Flip(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Object",
                          sub_display_text="object_flip_vertical",
                          command_name="object_flip_vertical",
                          purpose_line="Flips the given sprite vertically.",
                          group_name=GroupName.FLIP)
        

        page_object_after_fading_stop =\
            CharacterAfterFadingStop(parent_frame=self.frame_contents_outer,
                                    header_label=self.lbl_header,
                                    purpose_label=self.lbl_purpose,
                                    treeview_commands=self.treeview_commands,
                                    parent_display_text="Object",
                                    sub_display_text="object_after_fading_stop",
                                    command_name="object_after_fading_stop",
                                    purpose_line="Run a reusable script after a specific object sprite stops fading.",
                                    group_name=GroupName.FLIP)

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
                                      amount_name="opacity level",
                                      group_name=GroupName.FADE)

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
                               amount_name="number of frames to skip",
                               group_name=GroupName.FADE)

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
                               scale_instructions="Fade speed (1 to 100):",
                               group_name=GroupName.FADE)

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
                               scale_default_value=128,
                               group_name=GroupName.FADE)

        page_object_start_fading =\
            CharacterStartFading(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Object",
                                 sub_display_text="object_start_fading",
                                 command_name="object_start_fading",
                                 purpose_line="Starts an object sprite fading animation.\n"
                                 "Note: the object sprite must already be visible.",
                                 group_name=GroupName.FADE)

        page_object_stop_fading =\
            CharacterStopFading(parent_frame=self.frame_contents_outer,
                                header_label=self.lbl_header,
                                purpose_label=self.lbl_purpose,
                                treeview_commands=self.treeview_commands,
                                parent_display_text="Object",
                                sub_display_text="object_stop_fading",
                                command_name="object_stop_fading",
                                purpose_line="Stops an object sprite fading animation.\n"
                                "Note: the object sprite must already be visible.",
                                group_name=GroupName.FADE)

        page_object_after_rotating_stop =\
            CharacterAfterRotatingStop(parent_frame=self.frame_contents_outer,
                                       header_label=self.lbl_header,
                                       purpose_label=self.lbl_purpose,
                                       treeview_commands=self.treeview_commands,
                                       parent_display_text="Object",
                                       sub_display_text="object_after_rotating_stop",
                                       command_name="object_after_rotating_stop",
                                       purpose_line="When a specific sprite image stops rotating, run a reusable script.\n"
                                       "Note: the object sprite must already be visible.",
                                       group_name=GroupName.ROTATE)

        page_object_rotate_current_value =\
            CharacterRotateCurrentValue(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Object",
                                        sub_display_text="object_rotate_current_value",
                                        command_name="object_rotate_current_value",
                                        purpose_line="Immediately set a sprite's rotation value (no gradual animation).\n"
                                        "Note: the object sprite must already be visible.",
                                        group_name=GroupName.ROTATE)

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
                                 amount_name="number of frames to skip",
                                 group_name=GroupName.ROTATE)

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
                                 scale_instructions="Rotation speed (1 to 100):",
                                 group_name=GroupName.ROTATE)

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
                                 scale_default_value=180,
                                 group_name=GroupName.ROTATE)

        page_object_start_rotating =\
            CharacterStartRotating(parent_frame=self.frame_contents_outer,
                                   header_label=self.lbl_header,
                                   purpose_label=self.lbl_purpose,
                                   treeview_commands=self.treeview_commands,
                                   parent_display_text="Object",
                                   sub_display_text="object_start_rotating",
                                   command_name="object_start_rotating",
                                   purpose_line="Starts an object sprite rotation animation.\n"
                                   "Note: the object sprite must already be visible.",
                                   group_name=GroupName.ROTATE)

        page_object_stop_rotating =\
            CharacterStopRotating(parent_frame=self.frame_contents_outer,
                                  header_label=self.lbl_header,
                                  purpose_label=self.lbl_purpose,
                                  treeview_commands=self.treeview_commands,
                                  parent_display_text="Object",
                                  sub_display_text="object_stop_rotating",
                                  command_name="object_stop_rotating",
                                  purpose_line="Stops an object sprite rotation animation.\n"
                                  "Note: the object sprite must already be visible.",
                                  group_name=GroupName.ROTATE)

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
                                      "Note: the object sprite must already be visible.",
                                      group_name=GroupName.SCALE)

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
                             scale_instructions="Scale speed (1 to 100):",
                             group_name=GroupName.SCALE)

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
                                       "(example: 2 means twice as big as the original size)\nDecimal values like 1.1 can be used as well.",
                                       amount_name="scale",
                                       group_name=GroupName.SCALE)

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
                                amount_name="number of frames to skip",
                                group_name=GroupName.SCALE)

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
                                scale_instructions="Stop scaling when the scale reaches... (0 to 100)\nDecimal values like 1.1 can be used as well.",
                                scale_from_value=0,
                                scale_to_value=100,
                                scale_default_value=2,
                                group_name=GroupName.SCALE)

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
                                  "Also, <object_scale_until> should be used prior.",
                                  group_name=GroupName.SCALE)

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
                                 "Note: the object sprite must already be visible.",
                                 group_name=GroupName.SCALE)

        page_object_after_movement_stop =\
            CharacterAfterMovementStop(parent_frame=self.frame_contents_outer,
                                       header_label=self.lbl_header,
                                       purpose_label=self.lbl_purpose,
                                       treeview_commands=self.treeview_commands,
                                       parent_display_text="Object",
                                       sub_display_text="object_after_movement_stop",
                                       command_name="object_after_movement_stop",
                                       purpose_line="Run a reusable script after a specific object sprite stops moving.",
                                       group_name=GroupName.MOVE)
   
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
                                      "will stop moving.",
                                      group_name=GroupName.MOVE)

        page_object_move =\
            CharacterMove(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Object",
                          sub_display_text="object_move",
                          command_name="object_move",
                          purpose_line="Sets the movement amount and direction of an object sprite.",
                          group_name=GroupName.MOVE)

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
                               spinbox_to_value=120,
                               group_name=GroupName.MOVE)

        page_object_start_moving =\
            CharacterStartMoving(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Object",
                                 sub_display_text="object_start_moving",
                                 command_name="object_start_moving",
                                 purpose_line="Starts a movement animation on a specific object sprite.",
                                 group_name=GroupName.MOVE)

        page_object_stop_moving = \
            CharacterStartMoving(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Object",
                                 sub_display_text="object_stop_moving",
                                 command_name="object_stop_moving",
                                 purpose_line="Stops a movement animation on a specific object sprite.",
                                 group_name=GroupName.MOVE)

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
                                  direction="horizontal",
                                  group_name=GroupName.POSITION)

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
                                  direction="vertical",
                                  group_name=GroupName.POSITION)

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
                               spinbox_to_value=9000,
                               group_name=GroupName.POSITION)

        page_object_center_x_with =\
            SharedPages.CenterWithAlias(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Object",
                                        sub_display_text="object_center_x_with",
                                        command_name="object_center_x_with",
                                        purpose_line="Center the X of an object sprite with the center X of another sprite.\n"
                                        "Note: both sprites must already be visible.",
                                        group_name=GroupName.POSITION)  

        page_object_on_mouse_click =\
            SharedPages.SpriteMouseEvent(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Object",
                                        sub_display_text="object_on_mouse_click",
                                        command_name="object_on_mouse_click",
                                        purpose_line="Run a reusable script when a specific sprite is left-clicked with the mouse.",
                                        group_name=GroupName.MOUSE)             

        page_object_on_mouse_enter =\
            SharedPages.SpriteMouseEvent(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Object",
                                        sub_display_text="object_on_mouse_enter",
                                        command_name="object_on_mouse_enter",
                                        purpose_line="Run a reusable script when the mouse pointer hovers over a specific sprite.",
                                        group_name=GroupName.MOUSE)

        page_object_on_mouse_leave =\
            SharedPages.SpriteMouseEvent(parent_frame=self.frame_contents_outer,
                                        header_label=self.lbl_header,
                                        purpose_label=self.lbl_purpose,
                                        treeview_commands=self.treeview_commands,
                                        parent_display_text="Object",
                                        sub_display_text="object_on_mouse_leave",
                                        command_name="object_on_mouse_leave",
                                        purpose_line="Run a reusable script when the mouse pointer is no longer hovering\nover a specific sprite.",
                                        group_name=GroupName.MOUSE)             


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
                          purpose_line="Load a font sprite into memory.",
                          group_name=GroupName.LOAD)

        page_font =\
            Font_Font(parent_frame=self.frame_contents_outer,
                      header_label=self.lbl_header,
                      purpose_label=self.lbl_purpose,
                      treeview_commands=self.treeview_commands,
                      parent_display_text="Font",
                      sub_display_text="font",
                      command_name="font",
                      purpose_line="Sets the font to use for the next letter.",
                      group_name=GroupName.USE_FONT)      
        
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
                          amount_name="horizontal position",
                          group_name=GroupName.POSITION)

        
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
                          amount_name="vertical position",
                          group_name=GroupName.POSITION)
        
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
                           scale_default_value=2,
                           group_name=GroupName.SPEED)
        
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
                           scale_default_value=2,
                           group_name=GroupName.SPEED)
    

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
                               scale_default_value=5,
                               group_name=GroupName.SPEED)

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
                                values_to_choose=("sudden", "fade in", "gradual letter", "gradual letter fade in"),
                                group_name=GroupName.FONT_ANIMATION)
        

        page_sprite_font =\
            Font_SpriteFont(parent_frame=self.frame_contents_outer,
                            header_label=self.lbl_header,
                            purpose_label=self.lbl_purpose,
                            treeview_commands=self.treeview_commands,
                            parent_display_text="Font",
                            sub_display_text="sprite_font",
                            command_name="sprite_font",
                            purpose_line="Sets the font to use for a sprite's text.\n"
                            "Note: the sprite must already be visible.",
                            group_name=GroupName.USE_FONT)  

        page_sprite_font_x =\
            Font_SpriteFontPosition(parent_frame=self.frame_contents_outer,
                                    header_label=self.lbl_header,
                                    purpose_label=self.lbl_purpose,
                                    treeview_commands=self.treeview_commands,
                                    parent_display_text="Font",
                                    sub_display_text="sprite_font_x",
                                    command_name="sprite_font_x",
                                    purpose_line="Sets the horizontal position of where the sprite text should start,\n"
                                    "relative to the sprite.\nThe left-most edge of the sprite is 0 (zero).\n\n"
                                    "Note: the sprite must already be visible.",
                                    from_value=-50,
                                    to_value=5000,
                                    amount_usage_info="Set the horizontal position (x):",
                                    amount_name="horizontal position",
                                    group_name=GroupName.POSITION)
        
        page_sprite_font_y =\
            Font_SpriteFontPosition(parent_frame=self.frame_contents_outer,
                                    header_label=self.lbl_header,
                                    purpose_label=self.lbl_purpose,
                                    treeview_commands=self.treeview_commands,
                                    parent_display_text="Font",
                                    sub_display_text="sprite_font_y",
                                    command_name="sprite_font_y",
                                    purpose_line="Sets the vertical position of where the sprite text should start,\n"
                                    "relative to the sprite. The top of the sprite is 0 (zero).\n\n"
                                    "Note: the sprite must already be visible.",
                                    from_value=-50,
                                    to_value=5000,
                                    amount_usage_info="Set the vertical position (y):",
                                    amount_name="vertical position",
                                    group_name=GroupName.POSITION)

        page_sprite_font_delay =\
            Font_SpriteTextDelay(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Font",
                                 sub_display_text="sprite_font_delay",
                                 command_name="sprite_font_delay",
                                 purpose_line="Sets the number of frames to skip when applying\n"
                                 "gradual sprite text animation (letter-by-letter).\n"
                                 "Does not apply to letter fade-ins\n\n"
                                 "Note: the sprite must already be visible.",
                                 scale_from_value=0,
                                 scale_to_value=600,
                                 scale_instructions="Delay (frames) (0-600):\n\n"
                                 "For example: a value of 2 means: apply the letter by letter animation\n"
                                 "every 2 frames. A value of 0 means apply the animation at every frame.",
                                 scale_default_value=2,
                                 group_name=GroupName.SPEED)
        
        page_sprite_font_delay_punc =\
            Font_SpriteTextDelayPunc(parent_frame=self.frame_contents_outer,
                                     header_label=self.lbl_header,
                                     purpose_label=self.lbl_purpose,
                                     treeview_commands=self.treeview_commands,
                                     parent_display_text="Font",
                                     sub_display_text="sprite_font_delay_punc",
                                     command_name="sprite_font_delay_punc",
                                     purpose_line="Sets the number of frames to skip *after* a specific letter is shown.\n"
                                     "Only applies to gradual letter-by-letter text (not fade-ins).\n\n"
                                     "This command can be used to cause a short delay\n"
                                     "after punctuation marks, such as periods.\n\n"
                                     "Note: this command only works with letters on the same line.\n\n"
                                     "Note: the sprite must already be visible.",
                                     scale_from_value=0,
                                     scale_to_value=120,
                                     scale_instructions="The number of frames to skip (0 to 120):",
                                     scale_default_value=2,
                                     group_name=GroupName.SPEED)

        page_sprite_font_fade_speed =\
            Font_SpriteTextFadeSpeed(parent_frame=self.frame_contents_outer,
                                     header_label=self.lbl_header,
                                     purpose_label=self.lbl_purpose,
                                     treeview_commands=self.treeview_commands,
                                     parent_display_text="Font",
                                     sub_display_text="sprite_font_fade_speed",
                                     command_name="sprite_font_fade_speed",
                                     purpose_line="Sets the fade speed of gradually-shown sprite text\n" +
                                     "(letter-by-letter fade speed) and also the overall fade-in speed\n" +
                                     "(non letter-by-letter)\n\n"
                                     "Note: the sprite must already be visible.",
                                     scale_from_value=1,
                                     scale_to_value=10,
                                     scale_instructions="Set the fade speed (1-10):\n"
                                     "1 = slowest  10 = fastest",
                                     scale_default_value=5,
                                     group_name=GroupName.SPEED)
        
        page_sprite_font_intro_animation =\
            Font_SpriteIntroAnimation(parent_frame=self.frame_contents_outer,
                                header_label=self.lbl_header,
                                purpose_label=self.lbl_purpose,
                                treeview_commands=self.treeview_commands,
                                parent_display_text="Font",
                                sub_display_text="sprite_font_intro_animation",
                                command_name="sprite_font_intro_animation",
                                purpose_line="Set the animation type when sprite text is being displayed.\n"
                                "Note: the sprite must already be visible.",
                                instructions="Sprite text starting animation:",
                                values_to_choose=("sudden", "fade in", "gradual letter", "gradual letter fade in"),
                                group_name=GroupName.FONT_ANIMATION)
        
        page_sprite_text =\
            Font_SpriteText(parent_frame=self.frame_contents_outer,
                            header_label=self.lbl_header,
                            purpose_label=self.lbl_purpose,
                            treeview_commands=self.treeview_commands,
                            parent_display_text="Font",
                            sub_display_text="sprite_text",
                            command_name="sprite_text",
                            purpose_line="Set the text to show on a sprite.\n\n"
                            "You can run this command multiple times to append text.\n"
                            "To clear the text, use <sprite_text_clear>\n\n"
                            "Note: the sprite must already be visible.",
                            group_name=GroupName.TEXT)
        
        page_sprite_text_clear =\
            Font_SpriteTextClear(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="Font",
                                 sub_display_text="sprite_text_clear",
                                 command_name="sprite_text_clear",
                                 purpose_line="Clear text on a sprite where <sprite_text> was used.\n"
                                 "Note: the sprite must already be visible.",
                                 group_name=GroupName.TEXT)

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
                       scale_default_value=120,
                       group_name=GroupName.PAUSE)        

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
                                 show_delay_widgets=True,
                                 show_additional_argument_widgets=True, 
                                 group_name=GroupName.TIMER)
        
        page_after_cancel =\
            ReusableScriptSelect(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="General",
                                 sub_display_text="after_cancel",
                                 command_name="after_cancel",
                                 purpose_line="Cancels an existing 'after' timer.",
                                 group_name=GroupName.TIMER)

        page_after_cancel_all = \
            CommandOnly(parent_frame=self.frame_contents_outer,
                        header_label=self.lbl_header,
                        purpose_label=self.lbl_purpose,
                        treeview_commands=self.treeview_commands,
                        parent_display_text="General",
                        sub_display_text="after_cancel_all",
                        command_name="after_cancel_all",
                        purpose_line="Cancels all after-timers.",
                        group_name=GroupName.TIMER)
        
        page_call =\
            ReusableScriptSelect(parent_frame=self.frame_contents_outer,
                                 header_label=self.lbl_header,
                                 purpose_label=self.lbl_purpose,
                                 treeview_commands=self.treeview_commands,
                                 parent_display_text="General",
                                 sub_display_text="call",
                                 command_name="call",
                                 purpose_line="Run a reusable script.",
                                 group_name=GroupName.RUN_SCRIPT,
                                 show_additional_argument_widgets=True)           

        page_scene =\
            SceneScriptSelect(parent_frame=self.frame_contents_outer,
                              header_label=self.lbl_header,
                              purpose_label=self.lbl_purpose,
                              treeview_commands=self.treeview_commands,
                              parent_display_text="General",
                              sub_display_text="scene",
                              command_name="scene",
                              purpose_line="Run a scene in a specific chapter.",
                              group_name=GroupName.RUN_SCRIPT)
        
        page_general_scene_with_fade = \
            SceneWithFade(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="General",
                          sub_display_text="scene_with_fade",
                          command_name="scene_with_fade",
                          purpose_line="Gradually fade into another scene.\n"
                                       "Provides a fade effect when transitioning between scenes.",
                          group_name=GroupName.RUN_SCRIPT)

        page_wait_for_animation = \
            WaitForAnimation(parent_frame=self.frame_contents_outer,
                             header_label=self.lbl_header,
                             purpose_label=self.lbl_purpose,
                             treeview_commands=self.treeview_commands,
                             parent_display_text="General",
                             sub_display_text="wait_for_animation",
                             command_name="wait_for_animation",
                             purpose_line="Pauses the main script until one or more types of animations\n"
                                          "have finished animating.\n\n"
                                          "This command will only pause the main script, but can\n"
                                          "be called from anywhere (chapters/scenes/reusable scripts).",
                             group_name=GroupName.PAUSE)
        
        page_exit = \
            CommandOnly(parent_frame=self.frame_contents_outer,
                        header_label=self.lbl_header,
                        purpose_label=self.lbl_purpose,
                        treeview_commands=self.treeview_commands,
                        parent_display_text="General",
                        sub_display_text="exit",
                        command_name="exit",
                        purpose_line="Stops a script from running.",
                        when_to_use="When you want to prevent the rest of a script from running.\n\n"
                        "It can be used in any script, such as: chapters, scenes, reusable scripts.\n"
                        "The script that uses <exit> will be the script that will be stopped.",
                        group_name=GroupName.STOP)
        
        """
        Variable
        """
        page_variable_set =\
            VariableSet(parent_frame=self.frame_contents_outer,
                                    header_label=self.lbl_header,
                                    purpose_label=self.lbl_purpose,
                                    treeview_commands=self.treeview_commands,
                                    parent_display_text="Variable",
                                    sub_display_text="variable_set",
                                    command_name="variable_set",
                                    purpose_line="Create a new variable or update an existing one.\n\n"
                                    "Variable names are case-sensitive",
                                    hide_load_as_widgets=True)
        
        page_case_condition =\
            CaseCondition(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Condition",
                          sub_display_text="case",
                          command_name="case",
                          purpose_line="Create a new condition.")
        
        page_or_case_condition =\
            CaseCondition(parent_frame=self.frame_contents_outer,
                          header_label=self.lbl_header,
                          purpose_label=self.lbl_purpose,
                          treeview_commands=self.treeview_commands,
                          parent_display_text="Condition",
                          sub_display_text="or_case",
                          command_name="or_case",
                          purpose_line="Create a new 'or' condition.")
        
        page_case_else = \
            CommandOnly(parent_frame=self.frame_contents_outer,
                        header_label=self.lbl_header,
                        purpose_label=self.lbl_purpose,
                        treeview_commands=self.treeview_commands,
                        parent_display_text="Condition",
                        sub_display_text="case_else",
                        command_name="case_else",
                        purpose_line="Fall through if <case>, <or_case> are not satisfied.",
                        when_to_use="When the commands <case> <or_case> do not go through.")
        
        page_case_end = \
            CommandOnly(parent_frame=self.frame_contents_outer,
                        header_label=self.lbl_header,
                        purpose_label=self.lbl_purpose,
                        treeview_commands=self.treeview_commands,
                        parent_display_text="Condition",
                        sub_display_text="case_end",
                        command_name="case_end",
                        purpose_line="Ends a case command block.")


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
        self.pages["character_hide_all"] = page_hide_all_character
        
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
        self.pages["character_stop_moving"] = page_character_stop_moving
        self.pages["character_set_position_x"] = page_character_set_position_x
        self.pages["character_set_position_y"] = page_character_set_position_y
        self.pages["character_set_center"] = page_character_set_center
        self.pages["character_center_x_with"] = page_character_center_x_with
        
        self.pages["character_on_mouse_click"] =  page_character_on_mouse_click
        self.pages["character_on_mouse_enter"] =  page_character_on_mouse_enter
        self.pages["character_on_mouse_leave"] =  page_character_on_mouse_leave
        
        """
        General
        """
        self.pages["after"] = page_after
        self.pages["after_cancel"] = page_after_cancel
        self.pages["after_cancel_all"] = page_after_cancel_all
        
        self.pages["rest"] = page_general_rest
        
        self.pages["call"] = page_call
        
        self.pages["scene"] = page_scene

        self.pages["wait_for_animation"] = page_wait_for_animation
        
        self.pages["exit"] = page_exit

        self.pages["scene_with_fade"] = page_general_scene_with_fade
        
        """
        Object
        """
        self.pages["load_object"] = page_load_object
        self.pages["object_show"] = page_show_object
        self.pages["object_hide"] = page_hide_object
        self.pages["object_hide_all"] = page_hide_all_object
        
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
        self.pages["object_stop_moving"] = page_object_stop_moving
        self.pages["object_set_position_x"] = page_object_set_position_x
        self.pages["object_set_position_y"] = page_object_set_position_y
        self.pages["object_set_center"] = page_object_set_center
        self.pages["object_center_x_with"] = page_object_center_x_with

        self.pages["object_on_mouse_click"] =  page_object_on_mouse_click
        self.pages["object_on_mouse_enter"] =  page_object_on_mouse_enter
        self.pages["object_on_mouse_leave"] =  page_object_on_mouse_leave

        """
        Dialog
        """
        self.pages["text_dialog_define"] = page_dialog_define
        self.pages["text_dialog_show"] = page_dialog_show
        self.pages["text_dialog_close"] = page_dialog_close
        self.pages["halt"] = page_dialog_halt
        self.pages["halt_auto"] = page_dialog_halt_auto
        self.pages["no_clear"] = page_dialog_no_clear
        self.pages["continue"] = page_dialog_continue

        self.pages["load_dialog_sprite"] = page_load_dialog
        self.pages["dialog_sprite_show"] = page_show_dialog
        self.pages["dialog_sprite_hide"] = page_hide_dialog
        self.pages["dialog_sprite_hide_all"] = page_hide_all_dialog
        
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
        self.pages["dialog_sprite_stop_moving"] = page_dialog_stop_moving
        self.pages["dialog_sprite_set_position_x"] = page_dialog_set_position_x
        self.pages["dialog_sprite_set_position_y"] = page_dialog_set_position_y
        self.pages["dialog_sprite_set_center"] = page_dialog_set_center
        self.pages["dialog_sprite_center_x_with"] = page_dialog_sprite_center_x_with

        self.pages["dialog_sprite_on_mouse_click"] =  page_dialog_sprite_on_mouse_click
        self.pages["dialog_sprite_on_mouse_enter"] =  page_dialog_sprite_on_mouse_enter
        self.pages["dialog_sprite_on_mouse_leave"] =  page_dialog_sprite_on_mouse_leave
        
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
        
        self.pages["sprite_font"] = page_sprite_font
        self.pages["sprite_font_x"] = page_sprite_font_x        
        self.pages["sprite_font_y"] = page_sprite_font_y       
        self.pages["sprite_font_delay"] = page_sprite_font_delay
        self.pages["sprite_font_delay_punc"] = page_sprite_font_delay_punc
        self.pages["sprite_font_fade_speed"] = page_sprite_font_fade_speed
        self.pages["sprite_font_intro_animation"] = page_sprite_font_intro_animation
        self.pages["sprite_text"] = page_sprite_text
        self.pages["sprite_text_clear"] = page_sprite_text_clear
        
        
        """
        Variable
        """
        self.pages["variable_set"] = page_variable_set
        self.pages["case"] = page_case_condition
        self.pages["or_case"] = page_or_case_condition
        self.pages["case_else"] = page_case_else
        self.pages["case_end"] = page_case_end
        

        self.active_page = default_page
        default_page.show()

    def on_ok_btn_clicked(self):
        # The 'Default' page doesn't have a generate_command method,
        # so check for it, in case the user clicked OK on the default page.
        if hasattr(self.active_page, "generate_command"):
            
            generated_command = self.active_page.generate_command()
            if not generated_command:
                return
            else:
                self.generated_command = generated_command
            
        self.mainwindow.destroy()
        
    def on_cancel_button_clicked(self, *args):
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
        
    def show_edit_page(self, command_object: ContextEditRun):
        """
        Edit a command based on the given command object variable.
        
        First, find the page in the wizard from the command name.
        Then once the page is found, pass the command object to the page,
        which is basically the arguments from the script line.
        """
        wizard_page: WizardListing
        wizard_page = self.pages.get(command_object.command_name)
        
        if not wizard_page:
            return
        
        # Populate the widgets on the page with the provided argument(s) data.
        wizard_page.edit(command_object.command_object)

    def run(self):
        self.mainwindow.mainloop()


class GroupRowColorSwitch:
    """
    Used for switching row background colors in the wizard window's
    treeview widget, whenever a new/different group is being listed
    in the treeview widget.
    
    For example:
    Group A
    Group A
    Group B <-switch row color here, because we're no longer on group A
    Group B
    Group C <-switch row color here, because we're no longer on group B
    """
    def __init__(self):
        
        # The last group name that was populated in the treeview widget.
        self.last_group_name = None

        # Start off with this row color tag value.
        self.tag_color = "row_color_1"
        
    def switch_color(self):
        """
        Toggle the next row's background color.
        """
        if self.tag_color == "row_color_1":
            self.tag_color = "row_color_2"
        else:
            self.tag_color = "row_color_1"
            
    def set_current_group_name(self, group_name: GroupName):
        """
        Record the group that was last added to the treeview.
        
        Arguments:
        
        - group_name: the enum group name that was last added.
        """
        self.last_group_name = group_name
        
    def is_group_different(self, group_name: GroupName) -> bool:
        """
        Return whether the given group name is different from the
        last recorded group name.
        
        Purpose: this method is used to determine whether it's time
        to switch the next row's background color or not.
        
        Return: True if the given group name is not the same as the
        last recorded group name, which would mean it's time to switch
        the row's background color (dealt with in a different method).
        
        Return False if the given group name matches the last inserted
        treeview group name, which would mean it's not time to switch the
        row's background color.
        """
        return group_name and group_name != self.last_group_name
            
    def get_row_color_tag(self) -> str:
        """
        Return the current background row color tag name.
        This gets used when inserting rows in the wizard's treeview widget.
        """
        return self.tag_color


class WizardListing:
    
    # Used for determining when to switch the wizard's treeview widget
    # row background color.
    row_switcher = GroupRowColorSwitch()
    
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
        
        # sprite_text commands such as <sprite_text_font>
        # are subclasses of existing frames, such as <font>, so we use
        # this flag to know whether we need to check additional widgets
        # when using check_inputs() and generate_command().
        self.has_sprite_text_extension = False
        
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
            
        elif "variable" in command_name or "case" in command_name:
            self.purpose_type = Purpose.VARIABLE_SET
            
        elif command_name in ("after", "after_cancel", "call"):
            self.purpose_type = Purpose.REUSABLE_SCRIPT
            
        elif command_name in ("scene", ):
            self.purpose_type = Purpose.SCENE_SCRIPT
            
        elif command_name in ("remote", ):
            self.purpose_type = Purpose.REMOTE_WEB
            
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
            
        """
        If available, use the group name for this listing to determine
        whether we should change the background row of the treeview item
        or not (so that similarly grouped names will have the same
        background row color).
        
        How it works: if we're on a different group name compared to the
        last-recorded group name for a wizard listing, then toggle its row
        color to a different color.
        """       

        group_name: GroupName
        group_name = kwargs.get("group_name", "")
        
        # Different group name than last time?
        if WizardListing.row_switcher.is_group_different(group_name):
            # Yes, different group name than last time.
            
            # Record the new group name that we're now on, so we can
            # check it again for the next wizard listing.
            WizardListing.row_switcher.set_current_group_name(group_name)
            
            # Toggle the row color to the other row color
            # because we're about to show a new group name.
            WizardListing.row_switcher.switch_color()
            
        # The group name to display in the treeview widget.
        if group_name:
            display_group_name = f"{group_name.name.title()}"
        else:
            display_group_name = ""

        # Insert command name to the treeview.
        command_iid = \
            self.treeview_commands.insert(
                parent=parent_iid,
                index="end",
                text=display_group_name, 
                values=(sub_display_text, ),
                tag=WizardListing.row_switcher.get_row_color_tag())
        
        # So we can find the item iid in the treeview widget for a particular
        # command when editing a command from a script. That way, we can select
        # the command item iid in the treeview widget later on if needed.
        WizardWindow.command_item_iids[sub_display_text.lower()] = command_iid

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
                        Purpose.SCENE_SCRIPT: ("scene name", "scene names"),
                        Purpose.VARIABLE_SET: ("variable", "variables"),
                        Purpose.REMOTE_WEB: ("variable", "variables")}

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
                        Purpose.MUSIC: ProjectSnapshot.music,
                        Purpose.VARIABLE_SET: ProjectSnapshot.variables,
                        Purpose.REMOTE_WEB: ProjectSnapshot.variables,
                        Purpose.REUSABLE_SCRIPT: ProjectSnapshot.reusables}

        dict_ref = dict_mapping.get(self.purpose_type)
        
        return dict_ref    

    def populate(self, combobox_widget: ttk.Combobox, clear_entry: bool = False):
        """
        Populate the given combobox with a list of names.
        
        Arguments:
        
        - combobox_widget: the combobox widget that we want to populate
        data with.
        
        - clear_entry: whether to clear the current text in the combobox or not.
        """

        # Get the appropriate dictionary for this purpose type,
        # used for populating the combobox.
        ref_dict = self.get_population_dictionary()

        # Clear the existing combobox, just in case there are values in it.
        combobox_widget.configure(values=())

        names = [item for item in ref_dict]
        combobox_widget.configure(values=names)  
        
        if clear_entry:
            combobox_widget.delete(0, "end")
    
    def show(self):
        """
        Set the text of the purpose labels to indicate to the user
        what this command does.
        
        Also, grid the frame so the user can see its contents.
        """

        self.header_label.configure(text=self.command_name)
        self.purpose_label.configure(text=self.purpose_line)

        self.frame_content.grid()
    
    @staticmethod
    def set_combobox_readonly_text(combobox, text: str):
        """
        Set the displayed text in a combobox.
        
        Purpose: when editing a command, we dynamically set the combobox text
        combobox using this method. It's a convenience method.
        """
        combobox.state(["!readonly"])
        combobox.delete(0, tk.END)
        combobox.insert(0, text)
        combobox.state(["readonly"])     
    
    def edit(self, command_class_object):
        """
        Show the current wizard listing (frame) and populate
        the widgets with the given command arguments.
        
        This method is used when editing an existing command in the editor,
        not when adding a new command.
        
        Arguments:
        
        - command_class_object: the arguments for the applicable class
        of the command. For example, for <character_show>, the command
        object class would be: SpriteShowHide.
        
        Each command will have its own class object, although some commands
        will be share the same class object due to similarities.
        """
        
        # Find the treeview iid for the command
        command_iid =\
            WizardWindow.command_item_iids.get(self.command_name.lower())
        
        if not command_iid:
            return
        
        self.treeview_commands.see(command_iid)
        self.treeview_commands.selection_add(command_iid)
        
        self._edit_populate(command_class_object=command_class_object)
        
    def _edit_populate(self, command_class_object):
        """
        Populate the widgets for this listing from the given command
        class arguments (namedtuple).
        
        This method should be overridden by each page as each
        wizard listing page will have its own unique widgets and parameters.
        """
        pass
        

class SharedPages:
    
    class SpriteTextExtension:
        """
        Label: sprite type
        Combobox: sprite type
        
        Label: sprite alias
        Entry: sprite alias
        """
        def __init__(self,
                     parent_frame: ttk.Frame,
                     add_sprite_text_widgets: bool = False):
            """
            Arguments:
            
            - parent_frame: the frame that will contain this extension
            
            - add_sprite_text_widgets: when set to True, it will add
            a label widget and entry widget for typing the sprite text.
            This is used with the <sprite_text> command.
            """
            
            self.parent_frame = parent_frame
            
            # Include a 'Sprite text' label and entry?
            # (used with the <sprite_text> command)
            self.frame_sprite_text: ttk.Frame
            self.frame_sprite_text = None
            if add_sprite_text_widgets:
                self.frame_sprite_text = self.get_frame_sprite_text()
                self.frame_sprite_text.grid(sticky="w")
            
            # Combobox: sprite type
            # Entry: sprite alias
            self.sprite_frame = self.get_sprite_template()
            self.sprite_frame.grid(pady=(15, 0), sticky=tk.W, columnspan=2)   
            
        def set_sprite_type(self, sprite_type: str):
            """
            Set the sprite type in the combobox.
            
            Purpose: when editing a command, we dynamically set the sprite type
            combobox using this method. It's a convenience method.
            """
            
            if sprite_type:
                sprite_type = sprite_type.lower()
                
            # Make sure a valid sprite type value is selected.
            if sprite_type in self.cb_sprite_type.cget("values"):
                WizardListing.set_combobox_readonly_text(self.cb_sprite_type,
                                                         sprite_type)       
            
        def get_frame_sprite_text(self) -> ttk.Frame:
            """
            Create a frame that includes a sprite text label and entry widget
            and then return the frame.
            
            1 Sprite text (label)
            1 Entry (to type sprite text)
            """
            frame_text = ttk.Frame(self.parent_frame)
            
            lbl_sprite_text = ttk.Label(frame_text, text="Sprite text:")
            self.entry_sprite_text = ttk.Entry(frame_text, width=25)
            
            lbl_sprite_text.pack(anchor=tk.W)
            self.entry_sprite_text.pack()
            
            return frame_text
            
        def get_sprite_template(self) -> ttk.Frame:
            """
            Sprite type combobox
            sprite alias (entry)
            """
            self.frame_sprite = ttk.Frame(self.parent_frame)
            
            self.lbl_sprite_type = ttk.Label(self.frame_sprite,
                                             text="Sprite type:",
                                             anchor=tk.W)
            self.cb_sprite_type = ttk.Combobox(self.frame_sprite,
                                               values=("character", "object", "dialog_sprite"),
                                               state="readonly")
            
            
            self.lbl_sprite_alias = ttk.Label(self.frame_sprite,
                                              text="Sprite alias:",
                                              anchor=tk.W)
            self.entry_sprite_alias = ttk.Entry(self.frame_sprite, width=25)
            
            self.lbl_sprite_type.grid(column=0, row=0, sticky=tk.W)
            self.cb_sprite_type.grid(column=0, row=1, sticky=tk.W)
            
            self.lbl_sprite_alias.grid(column=0, row=2, sticky=tk.W, pady=(15, 0))
            self.entry_sprite_alias.grid(column=0, row=3, sticky=tk.W)
            
            self.frame_sprite.grid()
            
            return self.frame_sprite

        def check_inputs_sprite_text(self) -> Dict:
            """
            Check sprite_text specific widgets: 'sprite type' and 'sprite alias'.
            """
            
            sprite_text_inputs = {}
            
            
            # Do we have sprite text widgets?
            # (used with the <sprite_text> command)
            if self.frame_sprite_text:
                sprite_text = self.entry_sprite_text.get().strip()
                if not sprite_text:
                    messagebox.showinfo(parent=self.parent_frame.winfo_toplevel(), 
                                        title="Sprite text",
                                        message="The sprite text is blank.")
                    return
                else:
                    sprite_text_inputs["SpriteText"] = sprite_text            
            
            sprite_type = self.cb_sprite_type.get()
            if not sprite_type:
                messagebox.showinfo(parent=self.parent_frame.winfo_toplevel(), 
                                    title="Sprite type",
                                    message="Select a sprite type from the drop-down menu.")
                return
                
            sprite_alias = self.entry_sprite_alias.get().strip()
            if not sprite_alias:
                messagebox.showinfo(parent=self.parent_frame.winfo_toplevel(), 
                                    title="Sprite alias",
                                    message="Enter a sprite alias.")
                return

            
            sprite_text_inputs["SpriteType"] = sprite_type
            sprite_text_inputs["SpriteAlias"] = sprite_alias
            
            return sprite_text_inputs
        
        def custom_generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            Specific to a couple of sprite_text commands:
            <sprite_text> and <sprite_text_clear>
            """
    
            # The user input will be a dictionary like this:
            # {SpriteType": "character",
            # "SpriteAlias": "theo",
            # "SpriteText", "some text"}
            user_inputs = self.check_inputs_sprite_text()
    
            if not user_inputs:
                return
    
            sprite_type = user_inputs.get("SpriteType")
            sprite_alias = user_inputs.get("SpriteAlias")
            sprite_text = user_inputs.get("SpriteText")
            
            # Sprite text won't be available for <sprite_text_clear>
            if sprite_text:
                # <sprite_text: character, rave, some text>
                return f"<{self.command_name}: {sprite_type}, {sprite_alias}, {sprite_text}>"
            else:
                # <sprite_text_clear: character, rave>
                return f"<{self.command_name}: {sprite_type}, {sprite_alias}>"
    

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

        def _edit_populate(self, command_class_object: cc.FontIntroAnimation):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            # This part is specific to SpriteFontIntroAnimation
            # Used with <sprite_font_intro_animation>
            match command_class_object:
                case cc.SpriteFontIntroAnimation(sprite_type,
                                                 alias, animation_type):
                    
               
                    # Sprite type (ie: character, object, dialog_sprite)
                    self.set_sprite_type(sprite_type)
                    
                    # General alias
                    self.entry_sprite_alias.insert(0, alias)              
            
                    # Set to lowercase so we can compare it in lowercase.
                    if animation_type:
                        animation_type = animation_type.lower()
                            
                        # Default to the first selection if an invalid
                        # value was provided.
                        if animation_type not in self.values_to_choose:
                            # Default to the first index
                            self.cb_selection.current(newindex=0)
                        else:
                            WizardListing.set_combobox_readonly_text(
                                self.cb_selection,
                                animation_type)

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
            
            # If it's being used in a sprite_text related page,
            # such as <sprite_font>, then check for the two common
            # fields: sprite type and sprite alias.
            if self.has_sprite_text_extension:
                sprite_type_and_alias = self.check_inputs_sprite_text()
                if not sprite_type_and_alias:
                    return
                
                sprite_type = sprite_type_and_alias.get("SpriteType")
                sprite_alias = sprite_type_and_alias.get("SpriteAlias")
        
                return f"<{self.command_name}: {sprite_type}, {sprite_alias}, {selection}>"  
    
            else:
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

            self.selection_choices = ["Specific pixel coordinate",
                                      "start of display",
                                      "end of display",
                                      "before start of display",
                                      "after end of display",
                                      "top of display",
                                      "above top of display",
                                      "bottom of display",
                                      "below bottom of display"]

            if self.direction == "horizontal":
                self.selection_choices = self.selection_choices[:5]
            elif self.direction == "vertical":
                self.selection_choices = [self.selection_choices[0]] + self.selection_choices[5:]

            self.cb_position =\
                ttk.Combobox(frame_content,
                             values=self.selection_choices,
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
                self.show_pixel_widgets()
            else:
                self.hide_pixel_widgets()
                
        def show_pixel_widgets(self):
            """
            Show the pixel location related widgets.
            """
            
            self.frame_pixel_location.grid(row=3, column=1,
                                           sticky="w", padx=(3, 1))
            self.spinbox_pixel_location.focus()
            
        def hide_pixel_widgets(self):
            """
            Ungrid / hide the pixel location related widgets.
            """
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
        
        def _edit_populate(self, command_class_object: cc.SpritePosition):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            sprite_name = command_class_object.sprite_name
            position = command_class_object.position
            
            self.entry_general_alias.insert(0, sprite_name)
            
            # Initialize
            show_pixel_coordinate_widgets = False            

            try:
                # Specific pixel location?
                position = int(position)
                
                self.spinbox_pixel_location.delete(0, tk.END)
                self.spinbox_pixel_location.insert(0, position)
                
                # Show the widgets related to a specific pixel location.
                show_pixel_coordinate_widgets = True
                
            except ValueError:
                # We don't have a numeric value, so check if it's
                # a valid string value.
                
                if position:
                    position = position.lower()
                    
                    # Make sure it's a valid string value, such as 
                    # 'end of display' and not just any random string value.
                    if position in self.selection_choices:
                        WizardListing.set_combobox_readonly_text(
                            self.cb_position, position)
                    else:
                        # There's an unsupported string value
                        # So default to showing the pixel coordinate widgets.
                        show_pixel_coordinate_widgets = True
                else:
                    # We have no position value (it's blank)
                    # so default to showing the pixel coordinate widgets.
                    show_pixel_coordinate_widgets = True
                    
            if show_pixel_coordinate_widgets:
                self.show_pixel_widgets()
            else:                
                # If we got here, it means we have a proper valid
                # string value (such as 'end of display')
                self.hide_pixel_widgets()
                
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

        def _edit_populate(self, command_class_object: cc.MovementDelay):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            sprite_name = command_class_object.sprite_name
            x_skip_frames_amount = command_class_object.x
            y_skip_frames_amount = command_class_object.y
            
            self.entry_general_alias.insert(0, sprite_name)
            
            # Set skip frame x/y amounts
            self.sb_horizontal.set(x_skip_frames_amount)
            self.sb_vertical.set(y_skip_frames_amount)

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
                    command_name, purpose_line, **kwargs):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line,
                             **kwargs)

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
        
        def _edit_populate(self, command_class_object: cc.MovementSpeed):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            sprite_name = command_class_object.sprite_name
            x_amount = command_class_object.x
            x_direction = command_class_object.x_direction
            y_amount = command_class_object.y
            y_direction = command_class_object.y_direction
            
            try:
                x_amount = int(x_amount)
            except ValueError:
                x_amount = 0
                
            try:
                y_amount = int(y_amount)
            except ValueError:
                y_amount = 0
                
            # Default to 'right' if x_direction contains an invalid value.
            if not x_direction:
                x_direction = "right"
    
            x_direction = x_direction.lower()
            
            if x_direction not in ("left", "right"):
                x_direction = "right"
                
            # Default to 'up' if y_direction contains an invalid value.
            if not y_direction:
                y_direction = "up"
            
            y_direction = y_direction.lower()
            
            if y_direction not in ("up", "down"):
                y_direction = "up"            
            
            # Sprite alias    
            self.entry_general_alias.insert(0, sprite_name)
            
            # X movement amount and direction
            self.v_horizontal_amount.set(x_amount)
            self.v_horizontal_direction.set(x_direction)
            
            # Y movement amount and direction
            self.v_vertical_amount.set(y_amount)
            self.v_vertical_direction.set(y_direction)
            
            # Check the 'Move' checkbuttons if the values are greater than zero.
            self.v_move_horizontally.set(x_amount>0)
            self.v_move_vertically.set(y_amount>0)
            
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
                    command_name, purpose_line, **kwargs):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line,
                             **kwargs)
    
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
                self.show_pixel_widgets()
            else:
                self.hide_pixel_widgets()

        def show_pixel_widgets(self):
            """
            Show widgets related to pixel coordinates.
            """
            self.frame_pixel_location.grid(row=5, column=1, sticky="w", padx=(3, 1))
            self.spinbox_pixel_location.focus()
            
        def hide_pixel_widgets(self):
            """
            Hide widgets related to pixel coordinates.
            """
            self.frame_pixel_location.grid_forget()

        def _edit_populate(self, command_class_object: cc.MovementStopCondition):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            sprite_name = command_class_object.sprite_name
            
            self.entry_general_alias.insert(0, sprite_name)
            
            match command_class_object:
                
                # Do we have a specific side to check?
                case cc.MovementStopCondition(_, side_to_check, stop_location):
                
                    # Yes, we have a specific side to check.
                
                    # if 'side of sprite' is an empty string, 
                    # set self.cb_side_to_check to index 0, which is 
                    # "Determine automatically"
                    if not side_to_check:
                        self.cb_side_to_check.current(0)
                    else:
                        side_to_check = side_to_check.lower()
                        
                        # Show the 'side to check' in the combobox
                        if side_to_check in ("left", "right", "top", "bottom"):
                            WizardListing.\
                                set_combobox_readonly_text(self.cb_side_to_check,
                                                           side_to_check)
                    
                    if stop_location:
                        stop_location = stop_location.lower()
                    
                    # Is the stop location a specific pixel location?
                    if not self.supported_stop_location(stop_location):
                        # Not a valid 'text' based stop location.
                        
                        # The stop location is a specific pixel location.
                        # Show the spinbox widget.
                        self.cb_stop_location.current(0)
                        self.spinbox_pixel_location.set(stop_location)
                    
                case cc.MovementStopConditionShorter(_, stop_location):
                    # The stop location is a fixed section, such as 'left', 
                    # 'right', etc.
                    
                    if not self.supported_stop_location(stop_location):
                        # Not a valid 'text' based stop location.
                        
                        # Default to 'Specific pixel coordinate'.
                        self.cb_stop_location.current(0)
                    else:
                        # Show the stop location in the combobox.
                        WizardListing.\
                            set_combobox_readonly_text(self.cb_stop_location,
                                                       stop_location)
                        
                        # Causes the pixel coordinate spinbox to ungrid.
                        self.hide_pixel_widgets()
                    
        def supported_stop_location(self, stop_location: str):
            """
            Check whether the given stop location is a valid stop location.
            
            Return: True if the stop location is valid or False if not.
            """
            
            # Is the stop location a specific pixel location?
            return stop_location in ("start of display", "end of display",
                                     "before start of display",
                                     "after end of display",
                                     "top of display",
                                     "above top of display",
                                     "bottom of display",
                                     "below bottom of display")
                
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
                    command_name, purpose_line, **kwargs):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line,
                             **kwargs)
    
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
        
        def _edit_populate(self, command_class_object: cc.SpriteShowHide|cc.Flip):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            match command_class_object:
                case cc.SpriteShowHide(name) | cc.Flip(name):
                    
                    # Show the alias in the entry widget
                    self.entry_general_alias.insert(0, name)
        
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
      
    class CenterWithAlias(WizardListing):
        """
        <character_center_x_with: alias_to_move, sprite_type_to_center_with (character, dialog, object), center_with_alias>
        <object_center_x_with: alias_to_move, sprite_type_to_center_with (character, dialog, object), center_with_alias>
        <dialog_sprite_center_x_with: alias_to_move, sprite_type_to_center_with (character, dialog, object), center_with_alias>
        """
        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name,
                             purpose_line, **kwargs)
            
            # Used for label display purposes on the wizard's page.
            self.sprite_type = self.get_sprite_type()
            
            self.v_alias_to_move = tk.StringVar()
            self.v_sprite_type_center_with = tk.StringVar()
            self.v_center_with_alias = tk.StringVar()
            
            # We're going to change the label's text depending
            # on the sprite type selected in the combo box.
            self.lbl_center_with_alias: ttk.Label = None
            
            # The page's contents.
            self.frame_content = self.create_content_frame()
            
        def on_combo_box_selection_changed(self, event: tk.Event):
            """
            Change the 'Center with alias:' label to mention
            the type of sprite in the combo box.
            
            For example: 'Center with character alias:'
            """
            
            # Get the combo box widget
            cb_widget: ttk.Combobox
            cb_widget = self.frame_content.nametowidget(event.widget)
            
            # Get the chosen combo box item text.
            selection: str
            selection = cb_widget.get()
            
            # Update the label's text.
            self.lbl_center_with_alias.\
                configure(text=f"Center with {selection.lower()} alias:")
            
        def get_sprite_type(self) -> str:
            """
            Return the source sprite type depending on the
            command name.
            
            For example: 'character' will be returned (lowercase)
            if the command is <character_center_x_with>.
            
            Purpose: used for label display purposes on the wizard's page.
            """
            
            command_name = self.command_name.lower()
            
            if "character" in command_name:
                return "character"
            elif "dialog" in command_name:
                return "dialog_sprite"
            elif "object" in command_name:
                return "object"
                
        def create_content_frame(self) -> ttk.Frame:
            """
            Label: '<subject> alias to move:'
            Entry: 25 width
            
            Label: 'Sprite type to center with:'
            Combobox: (character, dialog, object)
            
            Label: 'Center with alias:'
            Entry: 25 width
            """
            frame_content = ttk.Frame(self.parent_frame)

            # Alias to move
            frame_sprite_to_move = ttk.Frame(frame_content)
            lbl_alias_to_move =\
                ttk.Label(frame_sprite_to_move,
                          text=f"{self.sprite_type.replace('_', ' ').capitalize()} alias to move:",
                          anchor=tk.W)
            
            entry_alias_to_move = ttk.Entry(frame_sprite_to_move,
                                            width=25,
                                            textvariable=self.v_alias_to_move)

            lbl_alias_to_move.pack(anchor=tk.W)
            entry_alias_to_move.pack(anchor=tk.W)
            
            # Sprite type to center with
            frame_sprite_type = ttk.Frame(frame_content)
            lbl_sprite_type_center_with =\
                ttk.Label(frame_sprite_type,
                text="Sprite type to center with:",
                anchor=tk.W)
            
            cb_sprite_type =\
                ttk.Combobox(frame_sprite_type,
                             state="readonly",
                             values=("Character", "Dialog sprite", "Object"),
                             width=20,
                             textvariable=self.v_sprite_type_center_with)
            
            # So we can change the 'Center with alias:' label to mention
            # the type of sprite alias.
            cb_sprite_type.bind("<<ComboboxSelected>>",
                                self.on_combo_box_selection_changed)
            
            lbl_sprite_type_center_with.pack(anchor=tk.W)
            cb_sprite_type.pack(anchor=tk.W)
            
            # Center with alias:
            frame_center_with_alias = ttk.Frame(frame_content)
            self.lbl_center_with_alias = ttk.Label(frame_center_with_alias,
                                                   text="Center with sprite alias:",
                                                   anchor=tk.W)
            entry_center_with_alias =\
                ttk.Entry(frame_center_with_alias,
                          width=25,
                          textvariable=self.v_center_with_alias)
            
            self.lbl_center_with_alias.pack(anchor=tk.W)
            entry_center_with_alias.pack(anchor=tk.W)
            
            frame_sprite_to_move.pack(anchor=tk.W)
            frame_sprite_type.pack(anchor=tk.W, pady=8)
            frame_center_with_alias.pack(anchor=tk.W)
            
            return frame_content
        
        def _edit_populate(self, command_class_object: cc.SpriteCenterWith):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            alias_to_move = command_class_object.alias_to_move
            
            sprite_type_to_center_with =\
                command_class_object.sprite_type_to_center_with
            
            # Capitalize the sprite type, because that's how the sprite types
            # are listed in the combobox.
            if sprite_type_to_center_with:
                sprite_type_to_center_with =\
                    sprite_type_to_center_with.capitalize()
                
                # A sprite type can only be these 3 values, nothing else.
                if sprite_type_to_center_with not in ("Character",
                                                      "Dialog sprite",
                                                      "Object"):
                    sprite_type_to_center_with = ""
            
            center_with_alias = command_class_object.center_with_alias
            
            self.v_alias_to_move.set(alias_to_move)
            self.v_sprite_type_center_with.set(sprite_type_to_center_with)
            self.v_center_with_alias.set(center_with_alias)
        
        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: the selection (str) if there is sufficient information;
            otherwise, None.
            """
            
            user_input = {}
            
            # Get the alias to move
            alias_to_move = self.v_alias_to_move.get().strip()
            
            if not alias_to_move:
                messagebox.showwarning(\
                    parent=self.treeview_commands.winfo_toplevel(),
                    title="Alias to move",
                    message="Missing: alias to move")
                return
            
            # Get the selected value in the combobox.
            sprite_type_center_with = self.v_sprite_type_center_with.get().lower()
            if not sprite_type_center_with:
                messagebox.showwarning(\
                    parent=self.treeview_commands.winfo_toplevel(),
                    title=f"No sprite type selected",
                    message=f"Choose a sprite type to center with from the drop-down menu.")
                return
            
            # Get the alias to center with
            center_with_alias = self.v_center_with_alias.get().strip()
            
            if not center_with_alias:
                messagebox.showwarning(\
                    parent=self.treeview_commands.winfo_toplevel(),
                    title="Alias to center with",
                    message="Missing: alias to center with")
                return            
            
            user_input = {"AliasToMove": alias_to_move,
                          "CenterWithAlias": center_with_alias,
                          "SpriteTypeCenterWith": sprite_type_center_with}
            
            return user_input
        
        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """
            selection = self.check_inputs()
            if not selection:
                return
            
            alias_to_move = selection.get("AliasToMove")
            center_with_alias = selection.get("CenterWithAlias")
            sprite_type_center_with = selection.get("SpriteTypeCenterWith")
            
            return f"<{self.command_name}: {alias_to_move}, {sprite_type_center_with}, {center_with_alias}>"
            
    
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
    
        def _edit_populate(self,
                           command_class_object: cc.FadeUntilValue | cc.RotateUntil):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            match command_class_object:
                case cc.FadeUntilValue(alias, numeric_value) | cc.ScaleUntil(alias, numeric_value):
                    # We've extracted the values.
                    pass
                    
                case cc.RotateUntil(alias, rotate_until_value):
                    
                    # str because the word 'forever' can be used to rotate
                    # continuously.
                    if rotate_until_value == "forever":
                        self.v_rotate_forever.set(True)
                        numeric_value = 0
                    else:
                        try:
                            numeric_value = float(rotate_until_value)
                        except ValueError:
                            numeric_value = 0                    
                        
                        self.v_until.set(numeric_value)
                    
            # To ensure it's not a non-numeric value.
            try:
                numeric_value = float(numeric_value)
            except ValueError:
                numeric_value = 0
            
            self.v_until.set(numeric_value)                
            
            self.entry_general_alias.insert(0, alias)
    
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

            self.lbl_general_alias = \
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

            self.lbl_general_alias.grid(row=0, column=0, sticky="w", columnspan=2)
            self.entry_general_alias.grid(row=1, column=0, sticky="w", columnspan=2)

            self.lbl_radio_selection.grid(row=2, column=0, sticky="w", pady=(10, 0), columnspan=2)
            self.radio_1.grid(row=3, column=0, sticky="w")
            self.radio_2.grid(row=3, column=1, sticky="w", padx=(10, 0))

            self.lbl_scale.grid(row=4, column=0, sticky="w", pady=(10, 0), columnspan=2)
            self.scale.grid(row=5, column=0, sticky="w", columnspan=2)

            return frame_content

        def _edit_populate(self,
                           command_class_object: cc.FadeSpeed | cc.RotateSpeed | cc.ScaleBy):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            

            # Get the alias
            sprite_name = command_class_object.sprite_name            
            
            match command_class_object:
                case cc.FadeSpeed(sprite_name, speed, direction) | \
                    cc.RotateSpeed(sprite_name, speed, direction) | \
                    cc.ScaleBy(sprite_name, speed, direction):
        
                    # Show the alias in the entry widget
                    self.entry_general_alias.insert(0, sprite_name)
        
                    # Set the direction in the appropriate optionbutton widget
                    self.v_radio_button_selection.set(direction)
                    
                    try:
                        speed = int(speed)
                    except ValueError:
                        speed = 0
        
                    # Show the speed value in the spinbox widget
                    self.v_scale_value.set(speed)

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

        def _edit_populate(self, command_class_object: cc.Volume|cc.HaltAuto):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            match command_class_object:
                # Get the audio volume, which may look like this:
                # '35'                
                case cc.Volume(scale_value) | cc.HaltAuto(scale_value) | \
                    cc.FontTextDelay(scale_value) | \
                    cc.FontTextFadeSpeed(scale_value) | \
                    cc.Rest(scale_value):
                    
                    # We've extracted the scale value.
                    pass
                
                case cc.SpriteFontFadeSpeed(sprite_type, general_alias, scale_value) | \
                    cc.SpriteTextDelay(sprite_type, general_alias, scale_value):

                    # Set the sprite type in the combobox
                    self.set_sprite_type(sprite_type)
                    
                    self.entry_sprite_alias.insert(0, general_alias)                

            try:
                scale_value = int(scale_value)
            except ValueError:
                scale_value = 1

            self.v_scale_value.set(scale_value)

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
            
            # If it's being used in a sprite_text related page,
            # such as <sprite_font>, then check for the two common
            # fields: sprite type and sprite alias.
            if self.has_sprite_text_extension:
                sprite_type_and_alias = self.check_inputs_sprite_text()
                if not sprite_type_and_alias:
                    return
                
                sprite_type = sprite_type_and_alias.get("SpriteType")
                sprite_alias = sprite_type_and_alias.get("SpriteAlias")
        
                return f"<{self.command_name}: {sprite_type}, {sprite_alias}, {scale_value}>"  
    
            else:
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

        def _edit_populate(self, command_class_object: cc.FadeCurrentValue | cc.FadeDelay):
            """
            Populate the widgets with the arguments for editing.
            
            This specific method gets used by various different commands
            so we have a lot of if-statements to check each one.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            # Initialize
            numeric_value = 0
            
            # The type of numeric class to try to convert the value to,
            # to ensure it's a proper number. Most of the time it will be an int
            # but sometimes it will be a float, depending on the command.
            numeric_class_type = int
            
            if hasattr(command_class_object, "sprite_name"):
                sprite_name = command_class_object.sprite_name
                entry_widget = self.entry_general_alias
                
            elif hasattr(command_class_object, "general_alias"):
                sprite_name = command_class_object.general_alias
                entry_widget = self.entry_sprite_alias                
            else:
                sprite_name = None
                entry_widget = None
            
            match command_class_object:
                
                # SpriteText class, used by commands such as <sprite_font_x>
                case cc.SpriteText(sprite_type, sprite_name, numeric_value):

                    # Set the sprite type in the combobox
                    self.set_sprite_type(sprite_type)
                    
                case cc.FadeDelay(sprite_name, numeric_value) | \
                    cc.FadeCurrentValue(sprite_name, numeric_value) | \
                    cc.RotateDelay(sprite_name, numeric_value) | \
                    cc.ScaleDelay(sprite_name, numeric_value):
                    pass
                
                case cc.ScaleCurrentValue(sprite_name, numeric_value):
                    
                    # ScaleCurrentValue uses float instead of the usual int
                    # for use in commands such as: <character_scale_current_value>
                    numeric_class_type = float                       
        
                case cc.FontStartPosition(numeric_value):
                    
                    # We have the numeric_value now.
                    pass

            if entry_widget:
                entry_widget.insert(0, sprite_name)

            try:
                numeric_value = numeric_class_type(numeric_value)
            except:
                numeric_value = 0
            
            # Show the fade value in the spinbox widget
            self.sb_amount.insert(0, numeric_value)

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
            
            # Default frames_elapse value
            self.spinbox_default_value =\
                self.kwargs.get("spinbox_default_value")            

            self.frame_content = self.create_content_frame()

            # Populate reusable script names combobox
            self.populate(combobox_widget=self.cb_reusable_script, clear_entry=True)

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
            
            # Used for showing 'optional additional arguments'
            # for use with <call> and <after> when passing additional
            # arguments to a reusable script.
            self.show_additional_argument_widgets =\
                self.kwargs.get("show_additional_argument_widgets")

            self.lbl_reusable_script =\
                ttk.Label(frame_content,
                          text=f"{self.get_purpose_name(capitalize_first_word=True)}:")
            self.cb_reusable_script = ttk.Combobox(frame_content, width=25)

            
            if self.show_delay_widgets:
                
                # So the user knows what the spinbox is for.
                # Example: "The number of frames to elapse:"
                spinbox_instructions = self.kwargs.get("spinbox_instructions")
                
                # Such as 'number of frames to delay level'; used for the message box
                # when the amount is missing
                self.amount_name = self.kwargs.get("amount_name")
            
                self.lbl_amount = ttk.Label(frame_content, text=spinbox_instructions)
                self.sb_amount = ttk.Spinbox(frame_content, from_=from_value, to=to_value)
                self.sb_amount.delete(0, "end")
                self.sb_amount.insert(0, self.spinbox_default_value)
                
            if self.show_additional_argument_widgets:
                # For optional additional arguments (used by <call> and <after>)
                frame_additional_args = ttk.Frame(frame_content)
                lbl_argument_instructions = ttk.Label(frame_additional_args,
                                                      text="(optional) Arguments to pass to the reusable script")
                
                self.entry_arguments = ttk.Entry(frame_additional_args,
                                                 width=30)
                
                lbl_argument_instructions.grid(row=0, column=0, sticky=tk.W)
                self.entry_arguments.grid(row=1, column=0, sticky=tk.W)


            self.lbl_reusable_script.grid(row=0, column=0, sticky="w")
            self.cb_reusable_script.grid(row=1, column=0, sticky="w")

            if self.show_delay_widgets:
                self.lbl_amount.grid(row=2, column=0, sticky="w", pady=(15, 0))
                self.sb_amount.grid(row=3, column=0, sticky="w")

            if self.show_additional_argument_widgets:
                frame_additional_args.grid(row=4, column=0, sticky="w", pady=(15, 0))

            return frame_content

        def _edit_populate(self,
                           command_class_object: cc.AfterWithArguments|cc.AfterWithoutArguments|cc.AfterCancel):
            """
            Populate the widgets with the arguments for editing.
            Used by <after>, <after_cancel>, <call>
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            # Only <after> (with or without arguments) uses frames_elapse, 
            # not <after_cancel> or <call>
            match command_class_object:
                case cc.AfterWithArguments(frames_elapse, _, _) | \
                    cc.AfterWithoutArguments(frames_elapse):
                    
                    # Verify that it's a valid numeric value.
                    try:
                        frames_elapse = int(frames_elapse)
                    except ValueError:
                        frames_elapse = self.spinbox_default_value
                        
                    self.sb_amount.set(frames_elapse)
                
            reusable_script_name = command_class_object.reusable_script_name
            self.cb_reusable_script.insert(0, reusable_script_name)
            
            # <call> without additional arguments won't have an 'arguments'
            # attribute, so check for it here.
            if hasattr(command_class_object, "arguments"):
                additional_arguments = command_class_object.arguments
            else:
                additional_arguments = ""
            
            if self.show_additional_argument_widgets:
                self.entry_arguments.insert(0, additional_arguments)

        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict with the character general alias and an opacity level.
            Example:
            {"ReusableScriptName": "some script name",
             "DelayFramesAmount": "60"}
            or None if insufficient information was provided by the user.
            
            In the case of <after> and <call>, there will be an optional
            arguments entry widget too, with the user_input key: "Arguments"
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
            
            # In the case of <after> and <call>, there will be an arguments
            # entry widget too.
            if hasattr(self, "entry_arguments"):
                arguments = self.entry_arguments.get().strip()
            else:
                arguments = None

            user_input = {"ReusableScriptName": reusable_script_name,
                          "DelayFramesAmount": delay_frames_amount,
                          "Arguments": arguments,}

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
            arguments = user_inputs.get("Arguments")
            
            if self.show_delay_widgets:
                # <after: 60, reusable script name, optional arguments>
                if arguments:
                    return f"<{self.command_name}: {delay_frames_amount}, {reusable_script_name}, {arguments}>"
                else:
                    return f"<{self.command_name}: {delay_frames_amount}, {reusable_script_name}>"
            else:
                # <after_cancel: reusable script name> or <call: reusable script name, optional arguments>
                if arguments:
                    return f"<{self.command_name}: {reusable_script_name}, {arguments}>"
                else:
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

            # Populate chapter and scene names combo boxes
            self.populate(self.cb_chapters,
                          self.cb_scenes)

        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """

            frame_content = ttk.Frame(self.parent_frame)
            
            self.lbl_chapters_title = ttk.Label(frame_content, text="Chapters:")
            self.cb_chapters = ttk.Combobox(frame_content, width=25, state="readonly")

            self.lbl_scenes_title = ttk.Label(frame_content, text="Scenes:")
            self.cb_scenes = ttk.Combobox(frame_content, width=25, state="readonly")
            
            self.lbl_chapters_title.grid(row=0, column=0, sticky="w")
            self.cb_chapters.grid(row=1, column=0, sticky="w")
            
            self.lbl_scenes_title.grid(row=2, column=0, sticky="w", pady=(15, 0))
            self.cb_scenes.grid(row=3, column=0, sticky="w")            

            return frame_content

        @staticmethod
        def populate(combo_box_chapters: ttk.Combobox,
                     combo_box_scenes: ttk.Combobox):
            """
            Populate the combo boxes with a list of
            chapter and scene names.
            """

            # Clear the existing combo boxes, just in case there are values in them.
            combo_box_chapters.configure(values=())
            combo_box_scenes.configure(values=())

            # Key (str): chapter name, Value: [ chapter script,  another dict {Key: scene name (str): Value script (str)} ]
            chapter_names = [item for item in ProjectSnapshot.chapters_and_scenes]         

            combo_box_chapters.configure(values=chapter_names)
            combo_box_chapters.delete(0, "end")
            combo_box_scenes.delete(0, "end")
            
            # A partial method for on_chapter_selection_changed(), which
            # attaches the scenes combo box.
            partial_on_chapter_changed =\
                partial(SharedPages.SceneScriptSelect.on_chapter_selection_changed,
                        combo_box_scenes)
            
            # When the chapters combo box changes selection, populate
            # the scenes combo box with scenes in the selected chapter.
            combo_box_chapters.bind("<<ComboboxSelected>>",
                                    partial_on_chapter_changed)
            
        
        @staticmethod
        def on_chapter_selection_changed(cb_scenes: ttk.Combobox,
                                         event: tk.Event):
            """
            Populate the scenes combo box with a list of scenes
            in the selected chapter.
            """
            
            # A reference to the chapters combobox
            cb_chapters: ttk.Combobox = event.widget
            
            # Get the selected chapter
            chapter_name = cb_chapters.get()
            
            if not chapter_name:
                return
            
            # Clear the combobox entry portion
            cb_scenes.configure(state="normal")
            cb_scenes.configure(values="")
            cb_scenes.delete(0, tk.END)
            cb_scenes.configure(state="readonly")
            
            # Get all the scenes in the given chapter.
            scenes = ProjectSnapshot.chapters_and_scenes.get(chapter_name)
            if not scenes:
                return
            
            # Example of what we have so far:
            # ['<load_background: some image>', {'Some scene name': '<background_show: ..>'}]
            # Get just the scene names and scene scripts.
            scenes = scenes[1]
            
            # Get just the scene names, excluding the scene scripts.
            scene_names = [scene_name for scene_name in scenes.keys()]
            
            # Populate the scenes combo box with a list of scenes
            # in the selected chapter.
            cb_scenes.configure(values=scene_names)

        def _edit_populate(self, command_class_object: cc.SceneLoad):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            chapter_name = command_class_object.chapter_name
            scene_name = command_class_object.scene_name
            
            WizardListing.set_combobox_readonly_text(self.cb_chapters,
                                                     chapter_name)
            
            # Populate the scene combobox values based on the chapter name above.
            # See the method: SharedPages.SceneScriptSelect.populate
            # for more info.
            self.cb_chapters.event_generate("<<ComboboxSelected>>")            
            
            WizardListing.set_combobox_readonly_text(self.cb_scenes,
                                                     scene_name)

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
                
                # If the chapter checkbox is read-only, don't ask the user 
                # to 'type' a chapter name.
                if "readonly" in self.cb_chapters.state():
                    msg = "Select a chapter name."
                else:
                    msg = "Type or select a chapter name."                
                
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No chapter selected.",
                                       message=msg)
                return
            
            # Scene name
            scene_name = self.cb_scenes.get().strip()
            if not scene_name:
                
                # If the scene checkbox is read-only, don't ask the user 
                # to 'type' a scene name.
                if "readonly" in self.cb_scenes.state():
                    msg = "Select a scene name."
                else:
                    msg = "Type or select a scene name."
                
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No scene selected.",
                                       message=msg)
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
            
            # If it's being used in a sprite_text related page,
            # such as <sprite_font>, then check for the two common
            # fields: sprite type and sprite alias.
            if self.has_sprite_text_extension:
                sprite_type_and_alias = self.check_inputs_sprite_text()
                if not sprite_type_and_alias:
                    return
                
                sprite_type = sprite_type_and_alias.get("SpriteType")
                sprite_alias = sprite_type_and_alias.get("SpriteAlias")
        
                return f"<{self.command_name}: {sprite_type}, {sprite_alias}, {amount}>"  
    
            else:
                return f"<{self.command_name}: {amount}>"



    class Delay(CurrentValue):
        def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name,
                             purpose_line, **kwargs)


    class Case(WizardListing):
        """
        <case: variable name, operator, value, case name>
        <or_case: case name to check against, variable name, operator, value>
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
        
            # Variable names
            dict_variables = self.get_population_dictionary()
        
            # Vertical pad spacing
            pady_spacing = 15
        
            variable_names = []
            if dict_variables:
                variable_names = tuple(dict_variables.keys())

            lbl_variable_name = ttk.Label(frame_content,
                                          text=f"Value 1 or variable name:")
            self.cb_variable_names = ttk.Combobox(frame_content,
                                                 width=25, 
                                                 values=variable_names)
            
            # We have this binding so that when a variable is selected,
            # we surround it with ($) (ie: ($selection_here))
            self.cb_variable_names.bind("<<ComboboxSelected>>",
                                        self.on_combobox_selection_changed)
            
            lbl_operator = ttk.Label(frame_content,
                                     text="Comparison operator:")
            
            # Get a tuple of condition operators (is, is not, etc.)
            operators = ConditionOperator.get_values()
            self.cb_operators = ttk.Combobox(frame_content,
                                             width=25, 
                                             values=operators)
            
            lbl_value_compare_with =\
                ttk.Label(frame_content,
                          text="Value 2 or variable name:")
            
            # Variable names (or manually typed value) to check against.
            self.cb_variable_names_check_against =\
                ttk.Combobox(frame_content,
                             width=25, 
                             values=variable_names)
            
            # We have this binding so that when a variable is selected,
            # we surround it with ($) (ie: ($selection_here))
            self.cb_variable_names_check_against.\
                bind("<<ComboboxSelected>>",
                     self.on_combobox_selection_changed)            
            
            # Set the instructions for the condition name
            # depending on whether it's a <case> command or <or_case> command.
            if self.command_name == "case":
                    
                condition_name_text = "Condition name:\n" \
                    "(mandatory if you want to use <or_case> later, otherwise it's optional.)"
                
            elif self.command_name == "or_case":
                condition_name_text = "Condition name to compare with:"
            
            lbl_case_name = ttk.Label(frame_content,
                                      text=condition_name_text)
            self.entry_condition_name = ttk.Entry(frame_content,
                                                  width=25)
            
            lbl_variable_name.grid(row=0, column=0, sticky=tk.W)
            self.cb_variable_names.grid(row=1, column=0, sticky=tk.W)
            
            lbl_operator.grid(row=2, column=0, sticky=tk.W, pady=(pady_spacing, 0))
            self.cb_operators.grid(row=3, column=0, sticky=tk.W)
            
            lbl_value_compare_with.grid(row=4, column=0, sticky=tk.W, pady=(pady_spacing, 0))
            self.cb_variable_names_check_against.grid(row=5, column=0, sticky=tk.W)
            
            lbl_case_name.grid(row=6, column=0, sticky=tk.W, pady=(pady_spacing, 0))
            self.entry_condition_name.grid(row=7, column=0, sticky=tk.W)
            
            return frame_content

        def on_combobox_selection_changed(self, event):
            """
            A variable has been selected, so encapsulate the variable name
            with ($). For example, if the combobox has 'my_var' as the selection,
            change it to ($my_var), because a variable has been selected.
            """
            text = event.widget.get()
            if text:
                text = f"(${text})"
                event.widget.delete(0, tk.END)
                event.widget.insert(0, text)

        def _edit_populate(self, command_class_object: cc.ConditionDefinition):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            variable_name = command_class_object.value1
            comparison_operator = command_class_object.operator
            check_against = command_class_object.value2
            
            # Variable name
            self.cb_variable_names.insert(0, variable_name)
            
            # Comparison operator
            if comparison_operator in self.cb_operators.cget("values"):
                self.cb_operators.insert(0, comparison_operator)
                
            # Variable or value to check against
            self.cb_variable_names_check_against.insert(0, check_against)
                
            # <case> can have an optional 'condition_name' argument.
            # If the class is ConditionDefinition, it has the condition name.
            # If it's ConditionDefinitionNoConditionName, then it will have
            # no condition name. Check for it here.
            match command_class_object:
                case cc.ConditionDefinition(_, _, _, condition_name):
                    # There is a condition name.
    
                    self.entry_condition_name.insert(0, condition_name)
                    
        def contains_variable_syntax(self, text: str) -> bool:
            """
            Determine whether the given text contains a variable format
            such as ($some_variable_name).
            
            Purpose: to know whether it's ok to not have ' and ' in value 2
            when using the BETWEEN or NOT BETWEN operators without actually
            having the word ' and ' in Value 2. If it's a variable in Value 2,
            then the requirement for having ' and ' for a BETWEEN/NOT BETWEEN
            operator doesn't apply and that's why we have this method.
            
            Return: True if the given text contains a variable format or
            False if not.
            """
            
            # Used for searching for ($variable_format) syntax in a string.
            pattern = r"(?P<variable_name>[(][ ]*[\$][\w ]+[)])"
            
            # If a variable syntax was found in the string, then re.search()
            # will return a value, or None if otherwise.
            results = re.search(pattern, text)
            if results:
                return True
            else:
                return False
            
        def check_inputs(self) -> Dict | None:
            """
            Check whether the user has inputted sufficient information
            to use this command.
            
            Return: a dict
            Example:
            {"FirstValue": "some name",
             "Operator": ConditionOperator.EQUALS,
             "SecondValue": "some variable name here",
             "ConditionName": "some name here" or None}
            or None if insufficient information was provided by the user.
            """

            user_input = {}

            # Get the entered variable name value in the combobox.
            value_1 = self.cb_variable_names.get()
            if not value_1:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No variable name specified",
                                       message="Choose a variable from the drop-down menu or type a variable's name")
                return

            # Get the operator value
            operator = self.cb_operators.get()
            
            # Try to get the operator enum value.
            # This is done to ensure the operator is one that really exists.
            try:
                operator = ConditionOperator(value=operator)
            except ValueError:            
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No operator selected",
                                       message=f"Select an operator from the drop-down menu.")
                return
            
            # Get the variable that is going to be checked against.
            value_2 = self.cb_variable_names_check_against.get()
            if not value_2:
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title="No variable name specified",
                                       message="Choose a variable or enter a value to check against.")
                return
            
            """
            When using the BETWEEN / NOT BETWEEN operators, it's important
            that Value 1 be the source and Value 2 be like '1 and 10'.
            It's not valid to have, for example, '1 and 10', in value 1.
            '1 and 10' is only valid in value 2. Also, when using these two
            operators, value 2 *must* have a syntax like '1 and 10', it can't
            just be '10' (single value).
            """
            if operator in (ConditionOperator.BETWEEN,
                            ConditionOperator.NOT_BETWEEN) :
                
                value_1_check = re.sub(r"\s+", " ", value_1).lower().strip()
                value_2_check = re.sub(r"\s+", " ", value_2).lower().strip()
                
                msg = None
                msg_title = None
                
                # Don't allow ' and ' in value 1
                if " and " in value_1_check:
                    
                    msg_title = "Value 1"
                    msg = "A range value using 'and' cannot be used in value 1.\n\nThat should be in value 2."
                
                # ' and ' must exist in value 2, if a variable hasn't been specified.
                elif " and " not in (value_2_check) \
                     and not self.contains_variable_syntax(value_2_check):
                    
                    msg_title = "Value 2"
                    msg = "A range using 'and' has to be specified in value 2.\n\nFor example: 1 and 10"
                
                if msg:
                    messagebox.showwarning(
                        parent=self.treeview_commands.winfo_toplevel(), 
                        title=msg_title,
                        message=msg)
                    return
            
            # Condition name (optional field for <case> but mandatory
            # for <or_case>)
            condition_name = self.entry_condition_name.get()
            
            if self.command_name == "or_case":
                if not condition_name:
                    messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                           title="No condition name specified",
                                           message="Enter a name for the condition.")
                    return                    

            user_input = {"FirstValue": value_1,
                          "Operator": operator,
                          "SecondValue": value_2,
                          "ConditionName": condition_name}

            return user_input

        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """

            # The user input will be a dictionary like this:
            # {"FirstValue": "some name",
            # "Operator": ConditionOperator.EQUALS,
            # "SecondValue": "some variable name here",
            # "ConditionName": "some name here" or None}
            user_inputs = self.check_inputs()

            if not user_inputs:
                return
            
            first_value = user_inputs.get("FirstValue")
            operator = user_inputs.get("Operator").value
            second_value = user_inputs.get("SecondValue")
            condition_name = user_inputs.get("ConditionName")
                
            if condition_name:
                return f"<{self.command_name}: {first_value}, {operator}, {second_value}, {condition_name}>"
            else:
                # No condition name
                return f"<{self.command_name}: {first_value}, {operator}, {second_value}>"
        

    class AfterStop(WizardListing):
        """
        <character_after_fading_stop: general alias, reusable script name to run>
        <character_after_scaling_stop: general alias, reusable script name to run>
        <object_after_fading_stop: general alias, reusable script name to run>
        <object_after_scaling_stop: general alias, reusable script name to run>
        """

        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):

            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line,
                             **kwargs)

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

        def _edit_populate(self, command_class_object: cc.FadeStopRunScript):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            sprite_name = command_class_object.sprite_name
            reusable_script_name = command_class_object.reusable_script_name
            
            self.entry_general_alias.insert(0, sprite_name)
            self.cb_reusable_script.insert(0, reusable_script_name)

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

            self.populate(combobox_widget=self.cb_reusable_script)

            self.frame_content.grid(pady=5)
            
            
    class SpriteMouseEvent(AfterStop):
        """
        <dialog_sprite_on_mouse_enter: alias, reusable script name, (optional values to send to the reusable script)>
        <object_on_mouse_enter: alias, reusable script name, (optional values to send to the reusable script)>
        <character_on_mouse_enter: alias, reusable script name, (optional values to send to the reusable script)>
        
        Also, same arguments for:
        <dialog_sprite_on_mouse_leave>
        <dialog_sprite_on_mouse_click>
        
        <object_on_mouse_leave>
        <object_on_mouse_click>
        
        <character_on_mouse_leave>
        <character_on_mouse_click>
        """
    
        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line,
                             **kwargs)
            
            self.create_frame_arguments().grid(pady=15)
    
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
            
            # We don't get the optional arguments from a dictionary, we just
            # get it directly from the entry widget.            
            optional_arguments = self.entry_arguments.get().strip()
    
            if optional_arguments:
                return f"<{self.command_name}: {alias}, {reusable_script_name}, {optional_arguments}>"
            else:
                return f"<{self.command_name}: {alias}, {reusable_script_name}>"
            
        def create_frame_arguments(self) -> ttk.Frame:
            """
            Create and return a frame, used for specifying arguments
            when running a specific script.
            
            Example:
            For a command like this:
            <character_on_mouse_enter: alias, reusable script name, (optional values to send to the reusable script)>
            This method is used for the optional values part.
            """
            
            self.frame_arguments = ttk.Frame(self.frame_content)
            
            self.lbl_arguments_instructions = ttk.Label(self.frame_arguments,
                                                        text="(optional) Argument(s) to pass to the reusable script:\nExample: color=blue,character=Theo")
            self.entry_arguments = ttk.Entry(self.frame_arguments)
            
            self.lbl_arguments_instructions.grid(row=0, column=0, sticky=tk.W)
            self.entry_arguments.grid(row=1, column=0, sticky=tk.W)
            
            return self.frame_arguments    

        def _edit_populate(self, command_class_object: cc.MouseEventRunScriptWithArguments):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            sprite_name = command_class_object.sprite_name
            reusable_script_name = command_class_object.reusable_script_name
            
            self.entry_general_alias.insert(0, sprite_name)
            self.cb_reusable_script.insert(0, reusable_script_name)
            
            match command_class_object:
                case cc.MouseEventRunScriptWithArguments(_, _, arguments):
                    self.entry_arguments.insert(0, arguments)

    class LoadSpriteNoAlias(WizardListing):
        """
        <load_background>
        """
    
        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line,
                             **kwargs)
    
            self.frame_content = self.create_content_frame()
            
            self.populate(combobox_widget=self.cb_selections)
    
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
            
            # If it's being used in a sprite_text related page,
            # such as <sprite_font>, then check for the two common
            # fields: sprite type and sprite alias.
            if self.has_sprite_text_extension:
                sprite_type_and_alias = self.check_inputs_sprite_text()
                if not sprite_type_and_alias:
                    return
                
                sprite_type = sprite_type_and_alias.get("SpriteType")
                sprite_alias = sprite_type_and_alias.get("SpriteAlias")
        
                return f"<{self.command_name}: {sprite_type}, {sprite_alias}, {selection}>"  
    
            else:
                return f"<{self.command_name}: {selection}>"
    
        def show(self):
            """
            Set the text of the purpose labels to indicate to the user
            what this command does.
            
            Also, grid the frame so the user can see its contents.
            """
    
            self.header_label.configure(text=self.command_name)
            self.purpose_label.configure(text=self.purpose_line)
    
            self.populate(combobox_widget=self.cb_selections)
    
            self.frame_content.grid()
            
        def _edit_populate(self, command_class_object: cc.PlayAudio | cc.SpriteLoad):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            match command_class_object:
                
                # Get the audio name, which may look like this: 'normal_music'
                case cc.PlayAudio(name) | \
                    cc.DialogTextSound(name) | \
                    cc.SpriteLoad(name, _) | \
                    cc.SpriteShowHide(name):

                    name = name.strip()
                    self.cb_selections.insert(0, name)
                    
                case cc.SpriteText(sprite_type, alias, font_name):
                    # Used with <sprite_font>

                    # Font name
                    WizardListing.set_combobox_readonly_text(self.cb_selections,
                                                             font_name)                     
                
                    # Set the sprite type in the combobox
                    self.set_sprite_type(sprite_type)                
                    
                    # General alias of the sprite
                    self.entry_sprite_alias.insert(0, alias)
                

    class LoadSpriteWithAlias(LoadSpriteNoAlias):
        """
        <load_character>
        <load_object>
        <variable_set>
        
        Loading backgrounds doesn't support aliases, which is why
        we have a separate generic class here for commands that support aliases.
        """
    
        def __init__(self, parent_frame, header_label, purpose_label,
                    treeview_commands, parent_display_text, sub_display_text,
                    command_name, purpose_line, **kwargs):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line,
                             **kwargs)

        def create_content_frame(self) -> ttk.Frame:
            """
            Create the widgets needed for this command
            and return a frame that contains the widgets.
            """

            frame_content = ttk.Frame(self.parent_frame)


            purpose = self.get_purpose_name()
            
            if "variable" in purpose:
                message = "Variable name to create or update:"
            elif "dialog" in purpose:
                message = f"Which {purpose} would you like to load into memory?"
            else:
                message = f"Which {purpose} sprite would you like to load into memory?"
            

            lbl_prompt = ttk.Label(frame_content, text=message)
            self.cb_selections = ttk.Combobox(frame_content)
            
            if "variable" in purpose:
                message = "Variable value:"
            elif "dialog" in purpose:
                message = "Enter an alias for this dialog sprite below:\n" + \
                "(This alias can later be used to reference this dialog sprite\n" + \
                "regardless of the image that's being shown for this sprite.)"
            else:
                message = f"Enter an alias for this {self.get_purpose_name()} below:\n" + \
                f"(This alias can later be used to reference this {self.get_purpose_name()}'s sprite\n" + \
                "regardless of the image that's being shown for this sprite.)"
                
            self.lbl_general_alias = ttk.Label(frame_content, text=message)

            self.entry_general_alias = ttk.Entry(frame_content, width=25)

            # Without this, it will show widgets for 'Load as name...'
            # which doesn't apply to <variable_set>, which is why we
            # have 'hide_load_as_widgets' here.
            hide_load_as_widgets = self.kwargs.get("hide_load_as_widgets")

            if not hide_load_as_widgets:
                message = "(optional) - Load as a different name? Used for spawning copies.\n" \
                          "Enter a new copy name below:"
                lbl_load_as_prompt = ttk.Label(frame_content, text=message)
                self.entry_load_as = ttk.Entry(frame_content, width=25)

            lbl_prompt.grid(row=0, column=0, sticky="w")
            self.cb_selections.grid(row=1, column=0, sticky="w")

            self.lbl_general_alias.grid(row=2, column=0, sticky="w",
                                        pady=(15, 0))
            self.entry_general_alias.grid(row=3, column=0, sticky="w")


            # We shouldn't show 'load as' widgets for
            # the <variable_set>.
            if not hide_load_as_widgets:
                lbl_load_as_prompt.grid(row=4, column=0, sticky="w",
                                        pady=(15, 0))
                self.entry_load_as.grid(row=5, column=0, sticky="w")
            
            return frame_content

        def _edit_populate(self, command_class_object: cc.SpriteLoad):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
                
            match command_class_object:
                
                case cc.VariableSet(sprite_name, alias):
                    # For use with <variable_set>
          
                    # variable name and variable value, but we use
                    # sprite name and general alias here for consistency.
                    pass
                
                case _:
                    # For use with ie: <load_character>, etc.
        
                    sprite_name = command_class_object.sprite_name
                    alias = command_class_object.sprite_general_alias
                    
                    # Should we sprite be loaded as a different name instead of
                    # the original name? Find out with the method below.            
                    preferred_name =\
                        CommandHelper.get_preferred_sprite_name(sprite_name)
                    
                    if preferred_name:
                        # The argument for this command has a 'load as' keyword
                        # meaning that the sprite needs to be loaded using 
                        # a different name.
                        # Example:
                        # <load_character: akari_happy load as other_akari, akari>
                        
                        # Distinguish the two names so we can show them in
                        # separate widgets.
                        sprite_name = preferred_name.get("OriginalName")
                        load_as_name = preferred_name.get("LoadAsName")
                        
                        # Include a custom 'load as' name.
                        self.entry_load_as.insert(0, load_as_name)

            self.cb_selections.insert(0, sprite_name)
            self.entry_general_alias.insert(0, alias)

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
                
                # The entry widget is used for variable values and sprite aliases.
                
                # Show the appropriate error message to the user depending on the
                # purpose of the entry widget.
                if self.purpose_type == Purpose.VARIABLE_SET:
                    entry_type = "value"
                    entry_type_preposition = "a"
                else:
                    entry_type = "alias"
                    entry_type_preposition = "an"
                
                messagebox.showwarning(parent=self.treeview_commands.winfo_toplevel(),
                                       title=f"No {entry_type} provided",
                                       message=f"Enter {entry_type_preposition} {entry_type} for the {self.get_purpose_name()}.")
                return

            # Load the sprite using a different name? (load as).
            load_as_name = self.entry_load_as.get().strip()

            # Make sure the copy/load as name is different
            # from the original name.
            if load_as_name and load_as_name.lower() == selection.lower():
                messagebox.showwarning(
                    parent=self.treeview_commands.winfo_toplevel(),
                    title="Load As Name",
                    message=f"The name of the copy must be different from the original name: '{selection}'")
                return

            elif not load_as_name:
                # So we don't end up with an empty string.
                load_as_name = None
            
            user_input = {"Selection": selection,
                          "LoadAsName": load_as_name,
                          "Alias": alias}
    
            return user_input
        
        def generate_command(self) -> str | None:
            """
            Return the command based on the user's configuration/selection.
            """
    
            # The user input will be a dictionary like this:
            # {"Selection": "rave_normal",
            # "LoadAsName": None,
            # "Alias": "Rave"}
            user_inputs = self.check_inputs()
            
            if not user_inputs:
                return
    
            sprite_name = user_inputs.get("Selection")
            load_as_name = user_inputs.get("LoadAsName")
            alias = user_inputs.get("Alias")

            if load_as_name:
                # Using 'load as'
                return_value = f"<{self.command_name}: {sprite_name} load as {load_as_name}, {alias}>"
            else:
                # Not using 'load as'
                return_value = f"<{self.command_name}: {sprite_name}, {alias}>"

            return return_value


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
        
        def _edit_populate(self, command_class_object: cc.PlayAudio):
            """
            Populate the widgets with the arguments for editing.
            """
            
            # No arguments? return.
            if not command_class_object:
                return
            
            match command_class_object:
                
                case cc.PlayAudio(audio_name):
                
                    # We now have the audio name.
                    pass
                
                case cc.PlayAudioLoop(audio_name, loop):
                    
                    # We now have the audio name
                    
                    # The loop option is specific to <play_music> 
                    # and is optional.
                    if loop == "loop":
                        loop = True
                    else:
                        loop = False
                    
                    self.v_loop_audio.set(loop)
                
            self.cb_selections.insert(0, audio_name)
            

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
                    command_name, purpose_line, **kwargs):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line,
                             **kwargs)

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
                    command_name, purpose_line, **kwargs):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line,
                             **kwargs)          

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
                    command_name, purpose_line, **kwargs):
    
            super().__init__(parent_frame, header_label, purpose_label,
                             treeview_commands, parent_display_text,
                             sub_display_text, command_name, purpose_line,
                             **kwargs)          

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
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)

        
class CharacterStopFading(SharedPages.StartStop):
    """
    <character_stop_fading: general alias>
    Stops a character sprite fading animation.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)


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
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)
        


class VariableSet(SharedPages.LoadSpriteWithAlias):
    """
    <variable_set>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line,
                         **kwargs)


class CaseCondition(SharedPages.Case):
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
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line,
                         **kwargs)


class Background_LoadBackground(SharedPages.LoadSpriteNoAlias):
    """
    <load_background>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line,
                         **kwargs)


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
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)    



class AudioPlay(SharedPages.PlayAudioGeneric):
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


class Font_LoadFont(SharedPages.LoadSpriteNoAlias):
    """
    <load_font_sprite>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)


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
        
        
class Font_SpriteTextDelay(SharedPages.SpeedOnly, SharedPages.SpriteTextExtension):
    """
    <sprite_font_text_speed_delay: sprite type, sprite alias, frames to skip>>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)
        
        SharedPages.SpriteTextExtension.__init__(self, parent_frame=self.frame_content)
        
        # So check_inputs() and generate_command() will check for
        # additional sprite_text related widgets.
        self.has_sprite_text_extension = True
        
        
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
    
    def _edit_populate(self, command_class_object: cc.FontTextDelayPunc):
        """
        Populate the widgets with the arguments for editing.
        """
        
        # No arguments? return.
        if not command_class_object:
            return
        
        previous_letter = command_class_object.previous_letter
        number_of_frames = command_class_object.number_of_frames
        
        try:
            number_of_frames = int(number_of_frames)
        except ValueError:
            number_of_frames = 1

        self.entry_letter.insert(0, previous_letter)
        self.v_scale_value.set(number_of_frames)
        
        # SpriteTextDelayPunc has 2 additional widgets:
        # an entry widget and a combobox.
        # Used with <sprite_font_delay_punc>
        match command_class_object:
            
            case cc.SpriteTextDelayPunc(sprite_type, alias, _, _):
                self.entry_sprite_alias.insert(0, alias)
                self.set_sprite_type(sprite_type)

    def check_inputs(self) -> Dict:
        """
        Make sure a letter has been provided.
        """
        
        letter = self.entry_letter.get()
        if not letter:
            messagebox.showerror(parent=self.parent_frame.winfo_toplevel(), 
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
        
        # If it's being used in a sprite_text related page,
        # such as <sprite_font>, then check for the two common
        # fields: sprite type and sprite alias.
        if self.has_sprite_text_extension:
            sprite_type_and_alias = self.check_inputs_sprite_text()
            if not sprite_type_and_alias:
                return
            
            sprite_type = sprite_type_and_alias.get("SpriteType")
            sprite_alias = sprite_type_and_alias.get("SpriteAlias")
    
            return f"<{self.command_name}: {sprite_type}, {sprite_alias}, {letter}, {delay_frames}>"  

        else:
            return f"<{self.command_name}: {letter}, {delay_frames}>"
        
        
        
class Font_SpriteTextDelayPunc(Font_TextDelayPunc, SharedPages.SpriteTextExtension):
    """
    <sprite_font_text_delay_punc: sprite type, sprite alias, previous letter, frames to skip>>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)
        
        SharedPages.SpriteTextExtension.__init__(self, parent_frame=self.frame_content)
        
        # So check_inputs() and generate_command() will check for
        # additional sprite_text related widgets.
        self.has_sprite_text_extension = True


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
        
        
class Font_SpriteTextFadeSpeed(SharedPages.SpeedOnly, SharedPages.SpriteTextExtension):
    """
    <sprite_font_text_speed: sprite type, sprite alias, speed amount>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)

        SharedPages.SpriteTextExtension.__init__(self, parent_frame=self.frame_content)
        
        # So check_inputs() and generate_command() will check for
        # additional sprite_text related widgets.
        self.has_sprite_text_extension = True

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
        
        
class Font_SpriteIntroAnimation(SharedPages.DropDownReadOnly, SharedPages.SpriteTextExtension):
    """
    <sprite_font_intro_animation: sprite type, sprite alias, animation type>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name,
                         purpose_line, **kwargs)

        SharedPages.SpriteTextExtension.__init__(self, parent_frame=self.frame_content)
        
        # So check_inputs() and generate_command() will check for
        # additional sprite_text related widgets.
        self.has_sprite_text_extension = True
        

class Font_Font(SharedPages.LoadSpriteNoAlias):
    """
    <font>
    Sets the font to use for the next letter.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)

        self.set_font_text()

    def set_font_text(self):
        """
        Show font specific instructions.
        """
        self.lbl_prompt.configure(text="Font:")


class Font_SpriteFont(Font_Font, SharedPages.SpriteTextExtension):
    """
    <sprite_font: sprite type, sprite alias, font name>
    Sets the font to use for the next letter.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                           treeview_commands, parent_display_text,
                           sub_display_text, command_name, purpose_line,
                           **kwargs)
        
        SharedPages.SpriteTextExtension.__init__(self, parent_frame=self.frame_content)
        
        # So check_inputs() and generate_command() will check for
        # additional sprite_text related widgets.
        self.has_sprite_text_extension = True


class Font_SpriteText(WizardListing, SharedPages.SpriteTextExtension):
    """
    <sprite_text: sprite type, sprite alias, text>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        WizardListing.__init__(self, parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)
        
        self.frame_content = ttk.Frame(self.parent_frame)
        #self.scene_frame = SceneWithFadeFrame(self.frame_content)
        #self.scene_frame.mainframe.pack()        
        
        SharedPages.SpriteTextExtension.__init__(self,
                                                 parent_frame=self.frame_content,
                                                 add_sprite_text_widgets=True)
        
        
        # So check_inputs() and generate_command() will check for
        # additional sprite_text related widgets.
        self.has_sprite_text_extension = True
        
        # Use a sprite_text specific generate_command method.
        self.generate_command = self.custom_generate_command
        
    def _edit_populate(self, command_class_object: cc.SpriteText):
        """
        Populate the widgets with the arguments for editing.
        """
        
        # No arguments? return.
        if not command_class_object:
            return
        
        sprite_name = command_class_object.general_alias
        text = command_class_object.value
        sprite_type = command_class_object.sprite_type
        
        self.set_sprite_type(sprite_type)
        
        self.entry_sprite_alias.insert(0, sprite_name)
        self.entry_sprite_text.insert(0, text)    
        
class Font_SpriteTextClear(WizardListing, SharedPages.SpriteTextExtension):
    """
    <sprite_text_clear: sprite type, sprite alias>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        WizardListing.__init__(self, parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)
        
        self.frame_content = ttk.Frame(self.parent_frame)       
        
        SharedPages.SpriteTextExtension.__init__(self,
                                                 parent_frame=self.frame_content,
                                                 add_sprite_text_widgets=False)
        
        
        # So check_inputs() and generate_command() will check for
        # additional sprite_text related widgets.
        self.has_sprite_text_extension = True
        
        # Use a sprite_text specific generate_command method.
        self.generate_command = self.custom_generate_command
        
    def _edit_populate(self, command_class_object: cc.SpriteTextClear):
        """
        Populate the widgets with the arguments for editing.
        """
        
        # No arguments? return.
        if not command_class_object:
            return
        
        sprite_name = command_class_object.general_alias
        sprite_type = command_class_object.sprite_type
        
        self.set_sprite_type(sprite_type)
        self.entry_sprite_alias.insert(0, sprite_name)   
        

class Font_SpriteFontPosition(Font_Position, SharedPages.SpriteTextExtension):
    """
    <sprite_font_x>
    <sprite_font_y>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                           treeview_commands, parent_display_text,
                           sub_display_text, command_name, purpose_line,
                           **kwargs)
        
        SharedPages.SpriteTextExtension.__init__(self, parent_frame=self.frame_content)
        
        # So check_inputs() and generate_command() will check for
        # additional sprite_text related widgets.
        self.has_sprite_text_extension = True


        
class BackgroundShow(SharedPages.ShowSprite):
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs)


class BackgroundHide(SharedPages.HideSpriteNoAlias):
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line,
                **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line,
                **kwargs)
        

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


class CommandOnly(SharedPages.CommandNoParameters):
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


class SceneWithFadeFrame:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(SCENE_WITH_FADE_UI)
        # Main widget
        self.mainframe = builder.get_object("frame_scene_with_fade", master)
        self.master = master
        builder.connect_callbacks(self)

        self.lbl_color = builder.get_object("lbl_color")
        self.btn_change_color = builder.get_object("btn_change_color")

        self.cb_chapters = builder.get_object("cb_chapters")
        self.cb_scenes = builder.get_object("cb_scenes")
        
        # Default values
        self.default_fade_in = 10
        self.default_fade_out = 10
        self.default_hold_frames = 80
        self.default_background_color = "#000000"

        self.v_scale_fade_in = builder.get_variable("v_scale_fade_in")
        self.v_scale_fade_in.set(self.default_fade_in)

        self.v_scale_fade_out = builder.get_variable("v_scale_fade_out")
        self.v_scale_fade_out.set(self.default_fade_out)

        self.v_scale_hold_frames = builder.get_variable("v_scale_hold_frames")
        self.v_scale_hold_frames.set(self.default_hold_frames)

    def on_change_color_button_clicked(self):
        """
        Show the colour chooser dialog for the background.

        The 'Change Colour' button has been clicked.
        """

        current_color_hex = self.lbl_color.cget("background")
        current_color_rgb = self.lbl_color.winfo_rgb(current_color_hex)

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

        color = colorchooser.askcolor(parent=self.lbl_color.winfo_toplevel(),
                                      title="Background Colour",
                                      initialcolor=current_color_rgb)

        # The return value will be like this if a colour is chosen:
        # ((0, 153, 0), '#009900')

        # Or like this if no color is chosen
        # (None, None)
        hex_new_color = color[1]

        if not hex_new_color:
            return

        self.lbl_color.configure(background=hex_new_color)


class SceneWithFade(WizardListing):
    """
    <scene_with_fade: hex color, fade in speed (1-100), fade out speed (1-100),
    fade hold frame count (number of frames to stay at full opacity,
    chapter name, scene name>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                 treeview_commands, parent_display_text, sub_display_text,
                 command_name, purpose_line, **kwargs):
        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)

        self.frame_content = ttk.Frame(self.parent_frame)
        self.scene_frame = SceneWithFadeFrame(self.frame_content)
        self.scene_frame.mainframe.pack()

        # Populate chapter and scene names combo boxes
        SharedPages.SceneScriptSelect.populate(self.scene_frame.cb_chapters,
                                               self.scene_frame.cb_scenes)           
                               
    def _edit_populate(self, command_class_object: cc.SceneWithFade):
        """
        Populate the widgets with the arguments for editing.
        """
        
        # No arguments? return.
        if not command_class_object:
            return
        
        hex_color = command_class_object.hex_color
        fade_in_speed = command_class_object.fade_in_speed
        fade_out_speed = command_class_object.fade_out_speed
        fade_hold_for_frame_count =\
            command_class_object.fade_hold_for_frame_count
        chapter_name = command_class_object.chapter_name
        scene_name = command_class_object.scene_name
        
        # Background color
        try:
            self.scene_frame.lbl_color.configure(background=hex_color)
        except tk.TclError:
            # Default background color
            self.scene_frame.lbl_color.\
                configure(background=self.scene_frame.default_background_color)
            
        # Fade in speed
        try:
            fade_in_speed = int(fade_in_speed)
        except ValueError:
            fade_in_speed = self.scene_frame.default_fade_in
        self.scene_frame.v_scale_fade_in.set(fade_in_speed)
        
        # Fade out speed
        try:
            fade_out_speed = int(fade_out_speed)
        except ValueError:
            fade_out_speed = self.scene_frame.default_fade_out
        self.scene_frame.v_scale_fade_out.set(fade_out_speed)
        
        # Hold frames value
        try:
            fade_hold_for_frame_count = int(fade_hold_for_frame_count)
        except ValueError:
            fade_hold_for_frame_count = self.scene_frame.default_hold_frames
        self.scene_frame.v_scale_hold_frames.set(fade_hold_for_frame_count)
        
        # Chapter name
        WizardListing.set_combobox_readonly_text(self.scene_frame.cb_chapters,
                                                 chapter_name)
        
        # Populate the scene combobox values based on the chapter name above.
        # See the method: SharedPages.SceneScriptSelect.populate
        # for more info.
        self.scene_frame.cb_chapters.event_generate("<<ComboboxSelected>>")
        
        # Scene name
        WizardListing.set_combobox_readonly_text(self.scene_frame.cb_scenes,
                                                 scene_name)

    def check_inputs(self) -> Dict | None:
        """
        Check whether the user has inputted sufficient information
        to use this command.

        Return: the selection (str) if there is sufficient information;
        otherwise, None.
        """

        # Get the label's background color in hex format.
        chapter_name = self.scene_frame.cb_chapters.get().strip()
        scene_name = self.scene_frame.cb_scenes.get().strip()
        bg_color_hex = self.scene_frame.lbl_color.cget("background")
        fade_in_speed = self.scene_frame.v_scale_fade_in.get()
        fade_out_speed = self.scene_frame.v_scale_fade_out.get()
        hold_frames = self.scene_frame.v_scale_hold_frames.get()

        if not chapter_name:
            messagebox.showerror(parent=self.scene_frame.lbl_color.winfo_toplevel(),
                                 title="No chapter",
                                 message="The chapter name is missing")
            self.scene_frame.cb_chapters.focus()
            return
        elif not scene_name:
            messagebox.showerror(parent=self.scene_frame.lbl_color.winfo_toplevel(),
                                 title="No scene",
                                 message="The scene name is missing")
            self.scene_frame.cb_scenes.focus()
            return

        user_input = {"ChapterName": chapter_name,
                      "SceneName": scene_name,
                      "FadeColor": bg_color_hex,
                      "FadeInSpeed": fade_in_speed,
                      "FadeOutSpeed": fade_out_speed,
                      "HoldFrames": hold_frames}

        return user_input

    def generate_command(self) -> str | None:
        """
        Return the command based on the user's configuration/selection.
        """

        # The user input will be a dictionary like this:
        # {"ChapterName": chapter_name,
        #  "SceneName": scene_name,
        #  "FadeColor": bg_color_hex,
        #  "FadeInSpeed": fade_in_speed,
        #  "FadeOutSpeed": fade_out_speed,
        #  "HoldFrames": hold_frames}
        user_inputs = self.check_inputs()

        if not user_inputs:
            return

        chapter_name = user_inputs.get("ChapterName")
        scene_name = user_inputs.get("SceneName")
        fade_color = user_inputs.get("FadeColor")
        fade_in_speed = user_inputs.get("FadeInSpeed")
        fade_out_speed = user_inputs.get("FadeOutSpeed")
        hold_frames = user_inputs.get("HoldFrames")

        return f"<{self.command_name}: {fade_color}, {fade_in_speed}, {fade_out_speed}, {hold_frames}, {chapter_name}, {scene_name}>"


class WaitForAnimationFrame:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(WAIT_FOR_ANIMATION_UI)
        # Main widget
        self.mainframe = builder.get_object("frame_wait_for_animation", master)
        self.master = master
        builder.connect_callbacks(self)

        self.v_sprite_type: tk.StringVar = self.builder.get_variable("v_sprite_type")

        # Valid values for the radiobuttons.
        # Purpose: when editing the <wait_for_animation> command, it will
        # select the appropriate radio button only if the argument has
        # a valid sprite-type value that's defined here.
        self.valid_sprite_types =\
            ("character", "object", "dialog_sprite", "cover")

        # Default to the radio button, 'Character'
        self.v_sprite_type.set("character")

        # So we can disable the sprite alias and animation type widgets
        # when 'Screen fade' is selected.
        self.v_sprite_type.trace_add("write", self.on_sprite_type_changed)
        self.frame_sprite_alias = self.builder.get_object("frame_sprite_alias")
        self.frame_animation_type = self.builder.get_object("frame_animation_type")

        self.entry_sprite_alias: ttk.Entry = self.builder.get_object("entry_sprite_alias")
        self.cb_animation_type: ttk.Combobox = self.builder.get_object("cb_animation_type")

    def on_sprite_type_changed(self, *args):
        """
        Disable the sprite alias and animation type widgets
        if the wait is for 'Screen fade'. Otherwise, enable all the widgets.

        Purpose: when 'Screen fade' is selected, there is no general alias
        or animation type - it's just one type of wait.
        """
        sprite_type = self.v_sprite_type.get()

        if sprite_type == "cover":
            set_state = "disabled"
        else:
            set_state = "!disabled"

        # Enable or widgets in the following two frames.
        for widget in self.frame_sprite_alias.winfo_children():
            widget.state([set_state])

        for widget in self.frame_animation_type.winfo_children():
            widget.state([set_state])


class WaitForAnimation(WizardListing):
    def __init__(self, parent_frame, header_label, purpose_label,
                 treeview_commands, parent_display_text,
                 sub_display_text, command_name, purpose_line, **kwargs):
        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)

        self.frame_content = ttk.Frame(self.parent_frame)
        self.wait_frame = WaitForAnimationFrame(self.frame_content)
        self.wait_frame.mainframe.pack()
        
    def _edit_populate(self, command_class_object: cc.WaitForAnimation):
        """
        Populate the widgets with the arguments for editing.
        """
        
        # No arguments? return.
        if not command_class_object:
            return
        
        # Waiting for a fade screen animation?
        if hasattr(command_class_object, "fade_screen"):
            fade_screen = command_class_object.fade_screen
            
            if fade_screen == "fade screen":
                self.wait_frame.v_sprite_type.set("cover")
            
        else:
            # Waiting for a specific type of animation on a specific
            # type of sprite.
        
            sprite_type = command_class_object.sprite_type
            general_alias = command_class_object.general_alias
            animation_type = command_class_object.animation_type
            
            if animation_type:
                animation_type = animation_type.lower()
                
            if sprite_type:
                sprite_type = sprite_type.lower()
                
            wait_for = \
                ("fade", "move", "rotate", "scale", "all", "any")
            
            try:
                wait_for_animation_index = wait_for.index(animation_type)
            except ValueError:
                wait_for_animation_index = None
            
            self.wait_frame.cb_animation_type.current(wait_for_animation_index)         
            
            # Select a sprite type radio button, only if a valid sprite type
            # has been specified. Sprite type examples are: 'character', 
            # 'object', etc.
            if sprite_type in self.wait_frame.valid_sprite_types:      
                self.wait_frame.v_sprite_type.set(sprite_type)
            else:
                # Select no sprite type, because the provided sprite type
                # is invalid.
                self.wait_frame.v_sprite_type.set("")
                
            self.wait_frame.entry_sprite_alias.insert(0, general_alias)
        
    def check_inputs(self) -> Dict | None:
        """
        Check whether the user has inputted sufficient information
        to use this command.

        Return: a dict with the chosen parameters
        or None if insufficient information was provided by the user.
        """

        user_input = {}

        sprite_type = self.wait_frame.v_sprite_type.get()
        sprite_alias = self.wait_frame.entry_sprite_alias.get()
        animation_type = self.wait_frame.cb_animation_type.get()

        if not sprite_type:
            messagebox.showerror(parent=self.frame_content.winfo_toplevel(), 
                                 title="Sprite type",
                                 message="Choose a sprite type.")
            return            

        if sprite_alias:
            sprite_alias = sprite_alias.strip()

        if not sprite_alias:
            messagebox.showerror(parent=self.frame_content.winfo_toplevel(), 
                                 title="Sprite alias",
                                 message="The sprite alias is missing.")
            self.wait_frame.entry_sprite_alias.focus()
            return

        if not animation_type:
            messagebox.showerror(parent=self.frame_content.winfo_toplevel(), 
                                 title="Animation type",
                                 message="Choose the animation type to wait for.")
            self.wait_frame.cb_animation_type.focus()
            return

        # Shorten all/any from the combobox, so it works with the final command
        if animation_type == "all (wait when *all* types of animations are occurring)":
            animation_type = "all"
        elif animation_type == "any (wait when at least one type of animation is occurring)":
            animation_type = "any"

        user_input = {"SpriteType": sprite_type,
                      "SpriteAlias": sprite_alias,
                      "AnimationType": animation_type}

        return user_input

    def generate_command(self) -> str | None:
        """
        Return the command based on the user's configuration/selection.
        """

        # <wait_for_animation: sprite type, sprite alias, animation type>
        # or
        # <wait_for_animation: screen fade>

        # For <wait_for_animation: screen fade>
        if self.wait_frame.v_sprite_type.get() == "cover":
            command_line = f"<{self.command_name}: fade screen>"
            return command_line

        # For # <wait_for_animation: sprite type, sprite alias, animation type>
        user_inputs = self.check_inputs()

        if not user_inputs:
            return

        sprite_type = user_inputs.get("SpriteType")
        sprite_alias = user_inputs.get("SpriteAlias")
        animation_type = user_inputs.get("AnimationType")

        command_line = f"<{self.command_name}: {sprite_type}, {sprite_alias}, {animation_type}>"

        return command_line


class DialogTextSound(SharedPages.LoadSpriteNoAlias):
    """
    <dialog_text_sound: audio name>
    Sets the audio to play for letter-by-letter text displays (non fading).
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line,
                         **kwargs)
        
        self.set_audio_text()
        
    def set_audio_text(self):
        """
        Show audio specific instructions.
        """
        self.lbl_prompt.configure(text="Audio:")


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
        
    def _edit_populate(self, command_class_object: cc.Continue):
        """
        Populate the widgets with the arguments for editing.
        """
        
        # No arguments? return.
        if not command_class_object:
            return
        
        adjust_y = command_class_object.adjust_y
        
        try:
            # Do we have a proper int value as an argument?
            
            adjust_y = int(adjust_y)
            
            self.v_use_manual_y.set(True)
            self.v_scale_value.set(adjust_y)
            
        except ValueError:
            # The argument value does not evaluate to an int,
            # so uncheck the 'adjust y' checkbutton.
            adjust_y = 0
            self.v_use_manual_y.set(False)
        
        
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
    
    def set_combobox_text(self, combobox_widget, text: str):
        """
        Set the combobox to normal-mode (not read-only) and set its text
        then change it back to read-only.
        
        Since there are many combobox widgets on the dialog define window,
        it's easier to have one method handle this.
        """
        
        # Interpret the text 'none' as a blank string.
        # 'none' gets used for on_reusuable_on_halt, etc.
        if text == "none":
            text = ""
        
        combobox_widget.state(["!readonly"])
        combobox_widget.delete(0, tk.END)
        combobox_widget.insert(0, text)
        combobox_widget.state(["readonly"])

    def _edit_populate(self, command_class_object: cc.DialogRectangleDefinition):
        """
        Populate the widgets with the arguments for editing.
        """
        
        # No arguments? return.
        if not command_class_object:
            return
        
        width = command_class_object.width
        height = command_class_object.height
        animation_speed = command_class_object.animation_speed
        padding_x = command_class_object.padding_x
        padding_y = command_class_object.padding_y
        opacity = command_class_object.opacity
        
        try:
            width = int(width)
        except ValueError:
            width = self.text_define.default_width
            
        self.text_define.v_width.set(command_class_object.width)
        
            
        try:
            height = int(height)
        except ValueError:
            height = self.text_define.default_height        
        
        self.text_define.v_height.set(command_class_object.height)
        
        try:
            animation_speed = float(animation_speed)
        except ValueError:
            animation_speed = self.text_define.default_animation_speed
            
        self.text_define.v_animation_speed.set(animation_speed)
            
            
        # Intro animation
        
        # Valid values for intro animation.
        intro_animation_possible_values =\
            self.text_define.cb_intro_animation.cget("values")
        
        intro_animation = command_class_object.intro_animation
        if not intro_animation:
            intro_animation = self.text_define.default_intro_animation
        else:
            intro_animation = intro_animation.lower()
        
        # No valid value provided? Set it to the default intro animation.
        if intro_animation not in (intro_animation_possible_values):
            intro_animation = self.text_define.default_intro_animation
        else:
            WizardListing.set_combobox_readonly_text(
                self.text_define.cb_intro_animation,
                intro_animation)
            
        # Outro animation
        
        # Valid values for outro animation.
        outro_animation_possible_values =\
            self.text_define.cb_outro_animation.cget("values")
        
        outro_animation = command_class_object.outro_animation
        if not outro_animation:
            outro_animation = self.text_define.default_outro_animation
        else:
            outro_animation = outro_animation.lower()
        
        # No valid value provided? Set it to the default outro animation.
        if outro_animation not in (outro_animation_possible_values):
            outro_animation = self.text_define.default_outro_animation
        else:
            self.set_combobox_text(self.text_define.cb_outro_animation,
                                   outro_animation)
            
        # Anchor (dialog rectangle position)
        
        # Valid values for anchor.
        anchor_possible_values =\
            self.text_define.cb_dialog_position.cget("values")
        
        anchor = command_class_object.anchor
        if not anchor:
            anchor = self.text_define.default_anchor
        else:
            anchor = anchor.lower()
        
        # No valid value provided? Set it to the default anchor position.
        if anchor not in (anchor_possible_values):
            anchor = self.text_define.default_anchor
        else:
            self.set_combobox_text(self.text_define.cb_dialog_position,
                                   anchor)

        # Background color hex
        bg_color_hex = command_class_object.bg_color_hex
        try:
            self.text_define.lbl_backcolor.configure(background=bg_color_hex)
        except tk.TclError:
            # Default to black
            self.text_define.lbl_backcolor.configure(background="#000000")

            
        try:
            padding_x = int(padding_x)
        except ValueError:
            padding_x = self.text_define.default_padding_x
            
        self.text_define.v_padding_x.set(padding_x)
            
        try:
            padding_y = int(padding_y)
        except ValueError:
            padding_y = self.text_define.default_padding_y
            
        self.text_define.v_padding_y.set(padding_y)
            
        try:
            opacity = int(opacity)
        except ValueError:
            opacity = self.text_define.default_opacity
            
        self.text_define.v_opacity.set(opacity)
            
            
        # Rounded corners?
        rounded_corners = command_class_object.rounded_corners
        if rounded_corners:
            rounded_corners = rounded_corners.lower()
            
        if rounded_corners not in ("yes", "no"):
            # Default to no rounded corners.
            rounded_corners = False
            
        elif rounded_corners == "yes":
            rounded_corners = True
        else:
            rounded_corners = False
            
        self.text_define.v_rounded_corners.set(rounded_corners)
        
        # Run a reusable script when the intro animation starts
        self.set_combobox_text(self.text_define.cb_reusable_on_intro_starting,
                               command_class_object.reusable_on_intro_starting)         
        
        # Run a reusable script when the intro animation finishes
        self.set_combobox_text(self.text_define.cb_reusable_on_intro_finished,
                               command_class_object.reusable_on_intro_finished)           
        
        # Run a reusable script when the outro animation starts      
        self.set_combobox_text(self.text_define.cb_reusable_on_outro_starting,
                               command_class_object.reusable_on_outro_starting)        
        
        # Run a reusable script when the outro animation finishes
        self.set_combobox_text(self.text_define.cb_reusable_on_outro_finished,
                               command_class_object.reusable_on_outro_finished)             
        
        # Run a reusable script when the the visual novel is halted
        self.set_combobox_text(self.text_define.cb_resuable_on_halt,
                               command_class_object.reusable_on_halt)           
        
        # Run a reusable script when the the visual novel is unhalted
        self.set_combobox_text(self.text_define.cb_resuable_on_unhalt,
                               command_class_object.reusable_on_unhalt)               
        
        
        # Border color hex
        border_color_hex = command_class_object.border_color_hex
        try:
            
            self.text_define.\
                lbl_backcolor_border.configure(background=border_color_hex)
        except tk.TclError:
            
            # Default to black
            self.text_define.\
                lbl_backcolor_border.configure(background="#000000")        
        
            
        try:
            border_opacity = int(command_class_object.border_opacity)
        except ValueError:
            border_opacity = self.text_define.default_opacity_border
            
        self.text_define.v_opacity_border.set(border_opacity)
        
            
        try:
            border_width = int(command_class_object.border_width)
        except ValueError:
            border_width = self.text_define.default_border_width
            
        self.text_define.v_border_width.set(border_width)
        
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
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)


class CharacterRotateCurrentValue(WizardListing):
    """
    <character_rotate_current_value: general alias, angle value>
    Immediately set a sprite's rotation value (no gradual animation).
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
        
        return f"<{self.command_name}: {alias}, {angle}>"

    def _edit_populate(self, command_class_object: cc.RotateCurrentValue):
        """
        Populate the widgets with the arguments for editing.
        """
        
        # No arguments? return.
        if not command_class_object:
            return

        # Get the alias
        sprite_name = command_class_object.sprite_name
        
        # Show the alias in the entry widget
        self.entry_general_alias.insert(0, sprite_name)
        
        # Rotation angle
        angle = command_class_object.rotate_current_value
        
        # The angle may not be numeric, so be prepared for an invalid value.
        try:
            angle = float(angle)
        except ValueError:
            angle = 0
        
        if angle > 359:
            angle = 359
        elif angle < 0:
            angle = 0
                
        # Rotation angle
        self.v_angle.set(angle)
    
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
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)


class CharacterStopRotating(SharedPages.StartStop):
    """
    <character_stop_rotating: general alias>
    Stops a character sprite rotation animation.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)


class CharacterAfterScalingStop(SharedPages.AfterStop):
    """
    <character_after_scaling_stop: general alias, reusable script name to run>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)


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
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)


class CharacterStopScaling(SharedPages.StartStop):
    """
    <character_stop_scaling: general alias>
    Stops a character sprite scaling animation.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)


class CharacterAfterMovementStop(SharedPages.AfterStop):
    """
    <character_after_movement_stop: general alias, reusable script to run>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)


class CharacterStopMovementCondition(SharedPages.StopMovementCondition):
    """
    <character_stop_movement_condition: general alias, (optional)sprite side to check, stop location>
    Add a condition that defines when to stop a moving sprite.
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)

class CharacterMove(SharedPages.Move):
    """
    <character_move: general alias, x value, y value>
    
    For example: <character_move: rave, 50, 100> which means move the
    sprite horizontally by 50 pixels each time and 100 pixels vertically
    each time. The ‘time’ portion depends on <character_move_delay>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)


class CharacterStartMoving(SharedPages.StartStop):
    """
    <character_move_start: general alias>
    """

    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text, sub_display_text,
                command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                         treeview_commands, parent_display_text,
                         sub_display_text, command_name, purpose_line, **kwargs)


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
                sub_display_text, command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs)



class CharacterHide(SharedPages.HideSpriteWithAlias):
    def __init__(self, parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs):

        super().__init__(parent_frame, header_label, purpose_label,
                treeview_commands, parent_display_text,
                sub_display_text, command_name, purpose_line, **kwargs)

        

if __name__ == "__main__":
    app = WizardWindow()
    app.run()
