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

from enum import Enum
from typing import Tuple


class ConditionOperator(Enum):
    EQUALS = "is"
    DOES_NOT_EQUAL = "is not"
    MORE_THAN = "more than"
    SAME_OR_MORE_THAN = "same or more than"
    LESS_THAN = "less than"
    SAME_OR_LESS_THAN = "same or less than"
    BETWEEN = "between"
    NOT_BETWEEN = "not between"
    
    @classmethod
    def get_values(cls) -> Tuple[str]:
        """
        Return a tuple of enum values.
        
        This is used when populating the operators combobox
        in the Wizard window.
        """
        return (cls.EQUALS.value,
                cls.DOES_NOT_EQUAL.value,
                cls.MORE_THAN.value,
                cls.SAME_OR_MORE_THAN.value,
                cls.LESS_THAN.value,
                cls.SAME_OR_LESS_THAN.value,
                cls.BETWEEN.value,
                cls.NOT_BETWEEN.value)
    

class Condition:
    """
    Used for verifying whether a condition is True or False.
    
    Arguments:
    
    - value1: this value will be checked against value2
    
    - value2: this value will be checked against value1
    
    - operator: what kind of check we are doing, such as "is not"
    """
    
    def __init__(self,
                 value1: str,
                 value2: str, 
                 operator: str):
        
        self.value1 = value1
        self.value2 = value2
        self.operator = operator
        
    @staticmethod
    def evaluate_line_check(script_line: str, 
                            false_condition_name: str) -> bool:
        """
        Determine whether the given script line should be read by
        the story reader or not.
        
        This method is called when each script line is read,
        when the story reader is in 'skip-mode', meaning that
        a condition (sometime before) evaluated to False and
        now it's skipping the script's lines.
        
        When a line such as <case_end>, <or_case>
        is reached, however, those should be evaluated when the reader is in
        skip-mode.
        That's what this method checks for.
        
        Arguments:
        
        - script_line: the string line to be evaluated.
        
        Return: True if the current line should be evaluated by the reader
        or False if it the line should be skipped by the reader.
        """
        
        # No false condition name provided? Assume that means
        # that the story reader is not in skip-mode, so it's OK
        # to read the current script line.
        if not false_condition_name:
            return True
        
        script_line = script_line.strip()
        if script_line.startswith("<case_end>") or \
           script_line.startswith("<or_case") or \
           script_line.startswith("<case_else>"):
            return True
        else:
            return False
        
    def evaluate(self) -> bool:
        """
        Evaluate value1 and value2.
        
        Return True if the evaluation satisfies the operator or
        False if otherwise.
        """
        
        operator_type: ConditionOperator
        operator_type = self.get_operator_enum(operator=self.operator)
        if not operator_type:
            return False
        
        if self.value1 is None or self.value2 is None:
            return False
        
        # Check whether we are comparing numeric values or not.
        # If we are, record the numeric values.
        comparing_numbers = False
        
        # Between is dealt with differently because it contains 2 values.
        if operator_type in (ConditionOperator.BETWEEN, ConditionOperator.NOT_BETWEEN):
            
            # Remove double spaces, if any.
            self.value2 = self.value2.strip()
            while "  " in self.value2:
                self.value2 = self.value2.replace("  ", " ")
            
            # Example: "5 and 10" 
            # becomes
            # ['-5', 'and', '10']
            between_values = self.value2.split()
            
            try:
                # The syntax should expect an 'and'
                # when using the between operator (such as '5 and 10').
                if between_values[1].lower() != "and":
                    return
                
                num_value1 = float(self.value1)
                _from_value = float(between_values[0])
                _to_value = float(between_values[2])
                
            except (IndexError, ValueError):
                raise ValueError(f"Cannot read 'between' operator values: {self.value1}, {self.value2}")
        
        else:
            # Not a 'between' operator, so there's only 1 value to read.
            
            try:
                num_value1 = float(self.value1)
                num_value2 = float(self.value2)
                
                comparing_numbers = True
            except ValueError:
                comparing_numbers = False
            
        
        match operator_type:
            case ConditionOperator.EQUALS:
                return True if self.value1 == self.value2 else False

            case ConditionOperator.DOES_NOT_EQUAL:
                return True if self.value1 != self.value2 else False
                    
            case ConditionOperator.LESS_THAN:
                if not comparing_numbers:
                    return False
                else:
                    return True if num_value1 < num_value2 else False
            
            case ConditionOperator.MORE_THAN:
                if not comparing_numbers:
                    return False
                else:
                    return True if num_value1 > num_value2 else False
                
            case ConditionOperator.SAME_OR_LESS_THAN:
                if not comparing_numbers:
                    return False
                else:
                    return True if num_value1 <= num_value2 else False
                
            case ConditionOperator.SAME_OR_MORE_THAN:
                if not comparing_numbers:
                    return False
                else:
                    return True if num_value1 >= num_value2 else False
                
            case ConditionOperator.BETWEEN | ConditionOperator.NOT_BETWEEN:
                is_variable_between_range =\
                    num_value1 >= _from_value and \
                    num_value1 <= _to_value
                
                # Within range and using 'between' operator? return True
                if is_variable_between_range and \
                   operator_type == ConditionOperator.BETWEEN:
                    return True
                
                # Not within range and using 'not between' operator? return True
                elif not is_variable_between_range and \
                   operator_type == ConditionOperator.NOT_BETWEEN:
                    return True
                
                
                else:
                    # 'between' or 'not between' not satisfied
                    return False

    def get_operator_enum(self, operator: str) -> ConditionOperator | None:
        """
        Convert a string operator to an enum.
        Example: "is" will return ConditionOperator.EQUALS
        """
        
        try:
            enum_type = ConditionOperator(value=operator)
            
        except ValueError:
            return None
        
        return enum_type
        
        
if __name__ == "__main__":
    
    run = Condition(name="Test",
                    value1="1",
                    value2="6 and 5", 
                    operator="not between")
    
    print(run.evaluate())
    
    # print(run.get_operator_enum(operator="is"))
    
    