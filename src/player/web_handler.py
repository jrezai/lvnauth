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
(Jobin Rezai) - July 12, 2025 - Always send xml-rpc requests using 
proxy.verify_license() because each remote request will need the license key checked.
"""

import ssl
from xmlrpc.client import ServerProxy, Error
from queue import Queue
from threading import Thread
from enum import Enum, auto
from dataclasses import dataclass
from threading import Thread
from response_code import ServerResponseReceipt, ServerResponseCode
from typing import ClassVar, Callable, Tuple, Dict, Optional
from pathlib import Path


class WebLicenseType(Enum):
    SHARED = auto()
    PRIVATE = auto()
    
    
# The values are used for keys in a dictionary
class WebKeys(Enum):
    WEB_ACCESS = "WebAccess"
    WEB_KEY = "WebKey"
    WEB_ADDRESS = "WebAddress"
    WEB_LICENSE_TYPE = "WebLicenseType"
    WEB_CA_CERT = "WebCertificate"
    

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
    
    # Keep count of the number of web worker instances because
    # if there are any running, the main script reader must be paused.
    active_count = 0
    
    def __init__(self,
                 address_and_port: Tuple, 
                 data: Dict,
                 callback_method: Callable):
        Thread.__init__(self, daemon=True)
        
        self.address_and_port = address_and_port
        
        self.data = data
        self.callback_method = callback_method
        
        # If the request takes a long time, an outside thread might want to 
        # cancel this thread, so we use this flag to indicate that another 
        # thread wants this thread cancelled.
        # So even if this thread ends up completing successfully, it won't run 
        # the callback method.
        self.cancelled = False
        
    @classmethod
    def increase_usage_count(cls):
        """
        Increment the counter variable that keeps track of the number
        of web worker threads that are actively running.
        
        We have a method for this so we can more easily debug
        when this value changes.
        """
        cls.active_count += 1
        
    @classmethod
    def decrease_usage_count(cls):
        """
        Decrement the counter variable that keeps track of the number
        of web worker threads that are actively running.
        
        We have a method for this so we can more easily debug
        when this value changes.
        """        
        cls.active_count -= 1
        
    def create_secure_context(self) -> ssl.SSLContext:
        """
        Return a default SSL context for connecting to a TLS xml-rpc server.
        
        If there is a local 'server.pem' file, use it (typically for
        a non-production work.)
        """
        context = ssl.create_default_context()
        
        # If there's a custom server.pem file data, use that.
        server_pem_data = self.data.get(WebKeys.WEB_CA_CERT.value)
        if server_pem_data:
            context.load_verify_locations(cadata=server_pem_data)
            
            # Remove the web certificate from the data dictionary
            # because the server doesn't need it. So remove it before
            # we send a request.
            del self.data[WebKeys.WEB_CA_CERT.value]
        else:
            # Load default certs from the operating system
            context.load_default_certs(purpose=ssl.Purpose.SERVER_AUTH)
        
        return context

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
            
            # Decrease the worker thread count.
            self.active_count -= 1
            
            return
        
        # This will hold the text response from the server, if any.
        result = None
        
        # Get default values for connecting to a TLS xml-rpc server.
        secure_context = self.create_secure_context()
        
        try:
    
            with ServerProxy(self.address_and_port,
                             context=secure_context) as proxy:
                
                # Send a remote request.
                result = proxy.verify_license(self.data)

                response =\
                    ServerResponseCode.get_response_code_from_text(msg=result)

        except ConnectionRefusedError:
            response = ServerResponseCode.CONNECTION_ERROR
            
        except Error:
            response = ServerResponseCode.CONNECTION_ERROR
            
        except (ValueError, TypeError) as e:
            response = ServerResponseCode.UNKNOWN
            result = e
            
        except ConnectionResetError:
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
    web_certificate: str
    web_enabled: bool
    vn_name: str
    vn_episode: str
    
    # The method to run after we receive a reply from the web.
    # This method will run in the GUI thread and a ServerResponseReceipt
    # object will be passed to it.
    # The type-hint here is saying that ServerResponseReceipt is taken as
    # an argument, and None is the return value.
    # The Optional keyword is used to allow this to be unspecified during init,
    # because when we're previewing a visual novel without the launch window,
    # we need to set the callback method later on.
    callback_method_finished: Optional[Callable[[ServerResponseReceipt], None]] = None
    
    def send_request(self,
                     data: Dict,
                     callback_method: Callable,
                     increment_usage_count=True):
        """
        Send data to the remote xml rpc server and get a response back.
        This method is run from the main thread, but spawns a worker thread.
        
        Arguments:
        
        - data: arguments to send to xml rpc
        
        - callback_method: the method to run when we receive a response
        from the xml rpc server.
        
        - increment_usage_count: we use this to know whether we need to
        increment the count of web workers when a web worker thread is
        created in this method.
        
        When using the <remote> command, we want this to be True, because
        the main script (non-reusable scripts) will need to pause and wait
        for a remote script when the thread count is more than zero.
        
        On the other hand, when the launch window is checking for a
        valid license, so we don't want to increment the number of threads
        during a license check.
        """
        
        # Required data to send to the xml-rpc server.
        default_required_data =\
            {"LicenseKey": self.web_key,
             "VisualNovelName": self.vn_name,
             "WebCertificate": self.web_certificate,}        

        # Is there optional data to send? Combine it with the required data.
        if data:
            data = default_required_data | data
            
        else:
            # Required data only, no optional data was provided.
            data = default_required_data

        # Increment the web worker thread count, because the main
        # script reader must be paused if there are any web worker threads.
        if increment_usage_count:
            WebWorker.increase_usage_count()

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
