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

import command_class as cc
from re import search, IGNORECASE
from typing import Dict


class ContextEditRun:
    """
    Used for recording the command name and an object which holds
    the arguments. This gets used when a script line has its arguments
    successfully parsed and we record the data that's needed in this class
    object for when the 'Edit' menu is clicked by the user.
    """
    def __init__(self, command_name: str, command_object):
        
        self.command_name = command_name
        self.command_object = command_object
        

class CommandHelper:

    context_edit_run = None
    class_lookup = {
        "load_audio": cc.PlayAudio,
        "load_music": cc.PlayAudio,
        "play_music": cc.PlayAudio,
        "play_sound": cc.PlayAudio,
        "play_voice": cc.PlayAudio,
        "volume_fx": cc.Volume,
        "volume_music": cc.Volume,
        "volume_text": cc.Volume,
        "volume_voice": cc.Volume,
        "dialog_text_sound": cc.DialogTextSound,
        "load_background": cc.SpriteLoad,
        "background_show": cc.SpriteShowHide,
        "background_hide": cc.SpriteShowHide,
        "load_character": cc.SpriteLoad,
    }
    
    @staticmethod
    def extract_arguments(command_line: str) -> Dict | None:
        """
        Given a line, such as <load_character: rave_normal, second argument, third argument>,
        return {'Command': 'load_character', 'Arguments': ' rave_normal, second argument, third argument'}
        
        Arguments:
        - command_line: the story script line
        
        Return: Dict
        """
        pattern_with_arguments =\
            r"^<(?P<Command>[a-z]+[_]*[\w]+):{1}(?P<Arguments>.*)>$"
        
        pattern_no_arguments =\
            r"^<(?P<Command>[a-z]+[_]*[\w]+)>$"
    
        # Try searching for a command with arguments.
        # Example: <call: some script>
        result = search(pattern=pattern_with_arguments,
                        string=command_line)
    
        # No results? Try searching for a command with no arguments.
        # Example: <halt>
        if not result:
            result = search(pattern=pattern_no_arguments,
                            string=command_line)
    
        if result:
            return result.groupdict()    
    
    @staticmethod
    def get_arguments(class_namedtuple, given_arguments: str):
        """
        Take the given string arguments (comma separated) and turn them
        into a namedtuple class.
    
        For example: if 'given_arguments' contains '5, 4'
        then this method will return an object in the given class in
        'class_namedtuple'.
        
        That object may be something like: MovementSpeed and its fields,
        X and Y will be set to int (based on the arguments example '5, 4').
    
        For example; MovementSpeed.x = 5 (int)  , MovementSpeed.y = 4 (int)
    
        This method will convert numeric types to int and will keep string
        types as strings.
        
        For example, if the given argument is: 'Bob, 100' (str argument),
        then 'Bob' will end up becoming a field in the class object as a string, 
        and 100 will be another field as an integer.
        
        This method will handle int types and str types automatically by
        making the class object fields match the expected type of variable.
    
        Arguments:
        
        - the class to use when returning an object in this method.
        One example of a class is: MovementSpeed
          
        - given_arguments: string-based argument separated by commas.
        For example: '5, 4' or 'Bob, 100'.
        
        Return: an object based on the class provided in 'class_namedtuple'.
        """
        
        # Get a tuple of types that the type-hint has for the given fields 
        # of the class.
        # We'll use this to find out what type of variables each argument 
        # field needs to be.
        expected_argument_types =\
            tuple(class_namedtuple.__annotations__.values())
    
        # Create a regex pattern to extract the correct number of arguments.
        # The expected number of arguments will be dictated by the number of 
        # fields in the given class: len(class._fields).
        field_count = len(class_namedtuple._fields)
        pattern = ""
        adder = r",([^,]*)"
        pattern += adder * field_count
        pattern = pattern.removeprefix(",")
        pattern += "$"
        pattern = "^" + pattern
    
        results = search(pattern=pattern,
                         string=given_arguments)
    
        if not results:
            return
    
        # Get the individual arguments as a tuple.
        # Example: ('5', '4')
        individual_arguments = results.groups()
    
        # This list will contain the individual arguments in their 
        # appropriate type
        # If it's a numeric argument, it will be added to this list as an int.
        # If it's a str argument, it will be added to this list as a str.
        converted_arguments = []
    
        # Combine the expected type (ie: class 'int') with each individual 
        # argument value (ie: '5')
        for expected_type, argument_value in \
            zip(expected_argument_types, individual_arguments):
            
            argument_value = argument_value.strip()
    
            if expected_type is str:
                converted_arguments.append(argument_value)
    
            # elif expected_type is int or expected_type is float:
            elif any(expected_type is item for item in [int, float]):
                try:
                    converted_arguments.append(expected_type(argument_value))
                except ValueError:
                    return
    
        # Convert the list of arguments to a namedtuple for easier access 
        # by the caller.
        generate_class = class_namedtuple(*converted_arguments)
    
        return generate_class
    
    @staticmethod
    def get_class_by_command_name(command_name: str) -> object | None:
        """
        Given a command name, such as 'character_show', return
        the appropriate class name for the command, such as SpriteShowHide.
        
        Return: the class for the provided command or None if not found.
        """
        return CommandHelper.class_lookup.get(command_name)
    
    @staticmethod
    def can_edit(script_line: str) -> bool:
        """
        Determine whether the given line is eligible to be edited or not.
        It does this by extracting the arguments and passing it to the
        appropriate class for the command and if the class gets instantiated
        successfully, that means the arguments are likely valid.
        
        During the validation, record the command name and the instantiated
        class for the command so if the user clicks on the Edit menu, we will
        be able to find the wizard's page using the command name and pass in
        the instantiated class to the wizard's page to populate the widgets.
        
        Return: True if the supplied script line can be edited in the Wizard
        and is ready to be edited in the Wizard. Return False if the supplied
        script line cannot be parsed.
        """
        if not script_line:
            return False
        
        extracted = CommandHelper.extract_arguments(script_line)
        if not extracted:
            return False
        
        command_name = extracted.get("Command")
        
        # There may not be any arguments, because some commands
        # don't have arguments.
        arguments = extracted.get("Arguments")
        
        # Get the class for the given command.
        command_cls = CommandHelper.get_class_by_command_name(command_name)
        if not command_cls:
            return
        
        # Remove excess spacing
        if arguments:
            arguments = arguments.strip()
            
            # If there is more than 1 argument, put the arguments in a list
            # because multi-parameter command classes need to be instantiated
            # using a list, not a single string.
            if "," in arguments:
                arguments = [item.strip() for item in arguments.split(",")]
        
        # Attempt to instantiate the command's class using the supplied
        # arguments. If successful, that means the arguments are likely
        # valid and can be edited in the Wizard.
        command_object = None
        if arguments:
            
            # <load_background> has a special fixed alias, so we need
            # to deal with this command a bit differently.
            if command_name == "load_background":
                if "," not in arguments:
                    fixed_alias = "fixedalias"
                    command_object = command_cls(arguments, fixed_alias)
            
            # If we haven't instantiated the command class from 
            # <load_background> above, then continue instantiating here.
            if not command_object:
                # If we're passing in a list, unpack it into separate arguments.
                # This is used for commands that accept multiple arguments.
                
                if isinstance(arguments, list):
                    # Multi-argument command
                    command_object = command_cls(*arguments)
                else:
                    # Single argument command
                    command_object = command_cls(arguments)
            
        # So if the 'Edit' menu is clicked, we know which command
        # to show the wizard's page for.
        CommandHelper.context_edit_run =\
            ContextEditRun(command_name=command_name,
                           command_object=command_object)
            
        # So the caller knows that this script line can be edited.
        return True

    @staticmethod
    def get_preferred_sprite_name(sprite_name_argument: str) -> Dict | None:
        """
        Return the preferred name and the original name of a sprite
        when using 'Load As' in the name section.
        If 'Load As' is not used, then None is returned.
        
        For example:
        'Theo Load As Th' will return {"LoadAsName": "Th", "OriginalName": "Theo"}
        The 'Load As' keyword part is not case-sensitive
        
        If there is no 'Load As', None is returned.
        For example:
        'Theo' will return None.
        """
    
        result = search(pattern=r"^(?P<OriginalName>.*)[\s](load as)[\s](?P<LoadAsName>.*)",
                           string=sprite_name_argument,
                           flags=IGNORECASE)
        
        # Was there a search match?
        if not result:
            # No match was found, which means 'Load As' is not being used.
            
            return
        
        else:
        
            result = result.groupdict()
            load_as_name = result.get("LoadAsName")
            original_name = result.get("OriginalName")
            
            # Remove leading and trailing spaces.
            if load_as_name and original_name:
                load_as_name = load_as_name.strip()
                original_name = original_name.strip()
                
                return {"LoadAsName": load_as_name,
                        "OriginalName": original_name}