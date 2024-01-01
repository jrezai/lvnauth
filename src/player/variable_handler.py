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

import re
from typing import Tuple, List


class VariableValidate:
    
    @staticmethod
    def validate_variable_name(variable_name: str) -> str | None:
        """
        Check whether the given variable name is valid or not
        (no invalid letters).
        
        Return value: if not valid, the invalid letter is returned.
        If valid, the return value is None.
        
        Purpose: used with the <variable_set> command.
        """
        
        invalid_letters = r"\/,()$:<> "
        
        if not variable_name:
            # Variable names cannot be blank.
            return 'Blank name'
        
        for letter in invalid_letters:
            if letter in variable_name:
                # Invalid latter in variable name.
                return letter
            
        # Valid name
        return


class VariableHandler:
    """
    Handles replacing variable names with values in strings.
    
    For use with LVNAuth Player, not the editor.
    """
    
    # Class dict that holds all variables in the visual novel.
    variables = {}
    
    def __init__(self):
        pass
    
    def set_variable(self, variable_name: str, variable_value: str):
        """
        
        """
        pass
    
    def find_and_replace_variables(self, line: str) -> str:
        """
        Given a string with variable names ($like_this), try to find the
        variables in the variables dictionary and replace the names with
        their values.
        
        Arguments:
        
        - line: a string containing references to variables.
        For example: "<character_show: ($some_variable)>
        
        Return: a string with variable names replaced with values.
        Example: "<character_show: some_character_name>"
        
        If the variable names were not replacable because the variables
        don't exist, then the variable names will show up as-is (unaltered).
        """
        counter = 0
        result = True
        
        # We have a loop so we can get values for
        # nested variable names, if there are any.
        # For example: if a variable value is another variable name.
        while (result := self._get_variables(line=line)):
            
            line = self._fill_in_variables(values_and_spans=result,
                                           line=line)
            
            # Limit nested variable fills to 4 checks
            # because if the variable value is another variable,
            # we'll get stuck in a loop.
            counter += 1
            
            if counter > 3:
                break
        
        return line

    def _get_variables(self, line: str) -> List:
        """
        Find variables in the given line and attempt
        to replace them with values.
        
        If the variable(s) does not exist in the variables dictionary,
        leave the variable line as-is.
        
        Return a list of variable values and a tuple of span ranges.
        Example: (variable_value, span)
        """
        
        # pattern = r"(?P<variable_name>[(][\$][\w ]+[)])"
        pattern = r"(?P<variable_name>[(][ ]*[\$][\w ]+[)])"
        search = line
        
        results = []
        
        for match in re.finditer(pattern=pattern, string=search):
            if match:
                # Example: ($myvariable)
                variable_name: str = match.group("variable_name")
                
                variable_name = variable_name.replace(" ", "")
                
                # Get the variable name without the ($) part.
                variable_name = variable_name[2:-1]
                
                # Example: (32, 41)
                span: Tuple = match.span("variable_name")
                # print(match.group("variable_name"), match.span("variable_name"))
                
                variable_value = VariableHandler.variables.get(variable_name)
                if variable_value is None:
                    continue
                
                results.append((variable_value, span))
                
        return results
            
    def _fill_in_variables(self, values_and_spans: List, line: str) -> str:
        """
        Fill the given spans with values.
        
        Arguments:
        
        - values_and_spans: A list of tuples. The tuples contain a
        variable value and a span to replace the original string.
        Examples:
        [('Some value here', (17, 30)),
        ('200 value test', (32, 41))]
        
        - line: a string where the variable names need to get replaced
        with values.
        
        Return: a string with variable names replaced with variable values.
        """
        
        # Every time we replace a variable name with a variable value,
        # the span-position of the next variable to replace will change because
        # the variable names will likely be replaced with a value that is shorter
        # or longer than the original variable name, so we need to compensate
        # for the new length of the string each time a variable name gets replaced
        # with a value. We use this variable to keep know how much to change
        # the next span by.
        change_next_span_by = 0
        
        # Iterate through variable values and spans.
        # Example:
        # [('Some value here', (17, 30)),
        # ('200 value test', (32, 41))]    
        for variable_span in values_and_spans:
            
            # variable_span example:
            # ('Some value here', (17, 30)
            
            variable_value: str
            span: Tuple
    
            variable_value, span = variable_span
            span_from, span_to = span
            
            # Adjust the span range based on the last variable value that was
            # inserted into the string, if any.
            span_from += change_next_span_by
            span_to += change_next_span_by
            
            # Consider by how much the next span's position will change
            # based on the variable value that was just inserted/replaced.
            change_next_span_by += len(variable_value) - (span_to - span_from)
        
            # Replace the variable name with the variable value.
            line = variable_value.join([line[:span_from],
                                        line[span_to:]])
            
        return line
            
        
if __name__ == "__main__":
    mystring = r"<character_show: ($myvariable),          (         $mytest   )        , ($thirdvariable)>"
        
    handler = VariableHandler()
    mystring = handler.find_and_replace_variables(mystring)
    
    print(mystring)