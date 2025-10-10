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

from enum import Enum, auto
from typing import Self


class ServerResponseCode(Enum):
    """
    This is for knowing whether the client was able to contact the server
    successfully or not. It's not used for knowing whether a postgres query
    returned "ok" or "error". It's just for the client-to-server handshake part.
    """
    SUCCESS = auto()
    CONNECTION_ERROR = auto()
    UNKNOWN = auto()
    SSL_ERROR = auto()
    LICENSE_KEY_MISSING = auto()
    LICENSE_KEY_NOT_FOUND = auto()
    LICENSE_KEY_ASSOCIATION_MISMATCH = auto()
    LICENSE_KEY_LOCKED = auto()
    LICENSE_KEY_OWING_BALANCE = auto()
    REMOTE_SCRIPT_ERROR = auto()
    OK_HEADER_NOT_RECEIVED = auto()
    
    # For redeeming a license key or updating a license key
    TRANSACTION_ID_NOT_FOUND = auto()
    ALREADY_REDEEMED = auto()
    VN_NOT_PART_OF_PACKAGE = auto()
    LICENSE_KEY_NOT_PRIVATE = auto()
    UPDATED_LICENSE = auto()
    

    # Generic errors we can use for various use-cases.
    NOT_FOUND = auto()

    @classmethod
    def to_enum(cls, string_representation):
        try:

            # We may have a string like this:
            # ServerResponseCode.SUCCESS
            # But we can't convert that to an enum because of the first part 
            # (ServerResponseCode).
            # We only need the SUCCESS part, so just get the part after the 
            # period.
            if "." in string_representation:
                string_representation = string_representation.split(".")[1]

            return cls[string_representation]

        except KeyError as e:
            return cls.UNKNOWN

    @staticmethod
    def get_response_code_from_text(msg: str) -> Self:
        """
        Convert a string representation such as "ok" to a ServerResponseCode,
        such as ServerResponseCode.SUCCESS
        """
        
        match msg:
            
            case "error-license_key_not_found":
                result = ServerResponseCode.LICENSE_KEY_NOT_FOUND
                
            case "error-license_key_not_associated_with_provided_vn":
                result = ServerResponseCode.LICENSE_KEY_ASSOCIATION_MISMATCH
                
            case "error-license_key_locked":
                result = ServerResponseCode.LICENSE_KEY_LOCKED
                
            case "error-license_key_owing_balance":
                result = ServerResponseCode.LICENSE_KEY_OWING_BALANCE
                
            case "error-script":
                result = ServerResponseCode.REMOTE_SCRIPT_ERROR
                
            case "error-transaction_id_not_found":
                result = ServerResponseCode.TRANSACTION_ID_NOT_FOUND
                
            case "error-already_redeemed":
                result = ServerResponseCode.ALREADY_REDEEMED
                
            case "error-vn_not_part_of_package":
                result = ServerResponseCode.VN_NOT_PART_OF_PACKAGE
                
            case "error-license_key_not_private":
                result = ServerResponseCode.LICENSE_KEY_NOT_PRIVATE
                
            case "ok-updated_license":
                result = ServerResponseCode.UPDATED_LICENSE
                
            case "ok" | "ok-save":
                result = ServerResponseCode.SUCCESS
                
            case _ if isinstance(msg, str) and msg.startswith("ok-script-"):
                result = ServerResponseCode.SUCCESS
                
            case _:
                result = ServerResponseCode.UNKNOWN
        
        return result

class ServerResponseReceipt:
    """
    This gets created in a secondary thread once a response has been
    received from the server.
    
    This is meant to be sent from a background thread to the GUI thread
    with all the information that the GUI thread needs. 
    """

    def __init__(self,
                 callback_method,
                 response_code: ServerResponseCode,
                 response_text: str = None):

        if not response_code:
            ValueError(
                "The parameter, response_code, requires an argument value.")

        elif isinstance(response_code, str):

            # Convert the string representation of the response code to a 
            # ServerResponseCode enum type.
            self.response_code = ServerResponseCode.to_enum(response_code)

        elif isinstance(response_code, ServerResponseCode):

            # The given argument is already an enum, just record it.
            self.response_code = response_code

        else:
            raise ValueError(
                "The response_code argument must be of type str or ServerResponseCode (enum)")

        # The method to run once the result is sent back to the GUI thread.
        self.callback_method = callback_method

        # Plain string message, if any.
        self.response_text = response_text

    def get_response_code(self):
        return self.response_code

    def get_response_text(self):
        return self.response_text
