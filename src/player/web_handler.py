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
from xmlrpc.client import ServerProxy, Error
from queue import Queue
from threading import Thread
from enum import Enum, auto
from dataclasses import dataclass
from threading import Thread
from response_code import ServerResponseReceipt, ServerResponseCode
from typing import ClassVar, Callable, Tuple, Dict


class WebLicenseType(Enum):
    SHARED = auto()
    PRIVATE = auto()
    
    
# The values are used for keys in a dictionary
class WebKeys(Enum):
    WEB_ACCESS = "WebAccess"
    WEB_KEY = "WebKey"
    WEB_ADDRESS = "WebAddress"
    WEB_LICENSE_TYPE = "WebLicenseType"


# Used for knowing whether a contact with a visual novel server
# was successful or not.
class WebResponse(Enum):
    SERVER_NOT_REACHABLE = auto()
    LICENSE_INVALID = auto()
    SUCCESSFUL = auto()


class WebWorker(Thread):
    """
    This class is used for submitting data to the server in a worker thread.
    A callback method is run on the main thread when it's finished.
    """
    
    the_queue = Queue()
    
    def __init__(self,
                 address_and_port: Tuple, 
                 data: Dict,
                 callback_method: Callable):
        Thread.__init__(self, daemon=True)
        
        self.address_and_port = address_and_port
        self.action_name = data.get("Action")
        self.data = data
        self.callback_method = callback_method
        
        # If the request takes a long time, an outside thread might want to 
        # cancel this thread, so we use this flag to indicate that another 
        # thread wants this thread cancelled.
        # So even if this thread ends up completing successfully, it won't run 
        # the callback method.
        self.cancelled = False

    def run(self):
        """
        Send the request to the web server.
        
        This method is executed on a worker thread (secondary thread).
        """
        
        # Has an outside thread cancelled this thread?
        # Don't bother doing anything with the results that we just got 
        # from the server, because an outside thread has 
        # cancelled this thread.
        if self.cancelled:
            return
        
        # This will hold the text response from the server, if any.
        result = None
        
        try:
        
            with ServerProxy(self.address_and_port) as proxy:
                
                match self.action_name:
                    
                    case "verify-license":
                
                        vn_name = self.data.get("VisualNovelName")
                        license_key = self.data.get("LicenseKey")
                        result = proxy.verify_license(license_key, vn_name)
                
                    case _:
                        
                        raise ValueError(f"Unknown action name '{self.action_name}'")
                    
        
                response =\
                    ServerResponseCode.get_response_code_from_text(msg=result)
                

                
        except ConnectionRefusedError:
            response = ServerResponseCode.CONNECTION_ERROR
            
        
            
        except Error:
            response = ServerResponseCode.CONNECTION_ERROR
            
        finally:
            # Send the response to the main GUI thread, regardless
            # if there was an error or not.
            receipt =\
                ServerResponseReceipt(
                    callback_method=self.callback_method,
                    response_code=response,
                    response_text=result)
            WebHandler.the_queue.put(receipt)                



@dataclass
class WebHandler:
    
    # Class variable
    the_queue: ClassVar[Queue] = Queue()
    
    # Instance variables
    web_key: str
    web_address: str
    web_license_type: WebLicenseType
    web_enabled: bool
    vn_name: str
    
    # The method to run after we receive a reply from the web.
    # This method will run in the GUI thread and a ServerResponseReceipt
    # object will be passed to it.
    # The type-hint here is saying that ServerResponseReceipt is taken as
    # an argument, and None is the return value.
    callback_method_finished: [[ServerResponseReceipt], None]
    
    def send_request(self, data: Dict, callback_method: Callable):
        """
        Send data to the remote xml rpc server and get a response back.
        This method is run from the main thread, but spawns a worker thread.
        
        Arguments:
        
        - data: arguments to send to xml rpc
        
        - callback_method: the method to run when we receive a response
        from the xml rpc server.
        """
        t = Thread(target=self._send_request,
                   daemon=True,
                   args=(data, callback_method))
        t.start()
        
    def _send_request(self, data: Dict, callback_method: Callable):
        """
        Send a request to the xml rpc server. This method is run in a
        worker thread.
        """
        reader = WebWorker(address_and_port=self.web_address,
                           data=data,
                           callback_method=callback_method)     
        
        reader.start()        
