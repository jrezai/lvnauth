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

import pygubu
from response_code import ServerResponseReceipt

    
class QueueMsgReader:
    """
    Reads server responses and runs the appropriate methods.
    
    By the time the responses reach here, we're no longer in a secondary
    thread, but in the main GUI thread.
    """
    
    def __init__(self, builder: pygubu.Builder):
        """
        Arguments:
        
        - builder: for accessing widgets.
        """
        self.builder = builder
        
    def read_msg(self, msg: ServerResponseReceipt):
        
        msg.callback_method(msg)
