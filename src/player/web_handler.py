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

import niquests as requests
from queue import Queue
from threading import Thread
from enum import Enum, auto
from dataclasses import dataclass
from response_code import ServerResponseReceipt, ServerResponseCode
from typing import ClassVar, Callable, Dict, Optional



class WebLicenseType(Enum):
    SHARED = auto()
    PRIVATE = auto()
    

class WebKeys(Enum):
    WEB_ACCESS = "WebAccess"
    WEB_KEY = "WebKey"
    WEB_ADDRESS = "WebAddress"
    WEB_LICENSE_TYPE = "WebLicenseType"
    WEB_PUBLIC_CERTIFICATE = "WebPublicCertificate"
    WEB_BYPASS_CERTIFICATE = "WebBypassCertificate"


# Used for knowing whether a contact with a visual novel server
# was successful or not.
class WebResponse(Enum):
    SERVER_NOT_REACHABLE = auto()
    LICENSE_INVALID = auto()
    SUCCESSFUL = auto()
    
    
class WebRequestPurpose(Enum):
    VERIFY_LICENSE = "VERIFY"
    REMOTE_SAVE = "SAVE"
    REMOTE_GET = "GET"
    REMOTE_CALL = "CALL"
    REDEEM_OR_UPDATE_LICENSE_KEY = "REDEEM"
    

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
                 uri: str, 
                 data: Dict,
                 callback_method: Callable):
        Thread.__init__(self, daemon=True)
        
        self.uri = uri
        
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
        
        # Send the request to the server.
        try:
                
            web_public_certificate = self.data.pop("web_public_certificate")
            bypass_certificate = self.data.pop("web_bypass_certificate")
            
            if bypass_certificate:
                # Don't verify the certificate.
                # For local testing purposes, not for distributing
                # the visual novel to others.
                verify = False
                
            elif web_public_certificate:
                # Use a custom private certificate
                verify = web_public_certificate
                
            else:
                # Attempt to verify using regular/stock certificates.
                verify = True
            
            result = requests.post(self.uri, verify=verify, json=self.data)
        
        except requests.exceptions.SSLError:
            
            result = None
            response = ServerResponseCode.SSL_ERROR
            
        except requests.exceptions.ConnectionError:
            
            result = None
            response = ServerResponseCode.CONNECTION_ERROR
        
        else:
        
            # We're only interested in the text represetation.
            result = result.json()
    
            # Send a remote request.
            # result = proxy.verify_license(self.data)
    
            response =\
                ServerResponseCode.get_response_code_from_text(msg=result)
    

        # Send the response to the main GUI thread
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
    web_public_certificate: str
    web_bypass_certificate: bool
    web_license_type: WebLicenseType
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
                     purpose: WebRequestPurpose,
                     increment_usage_count=True):
        """
        Send data to the remote server and get a response back.
        This method is run from the main thread, but spawns a worker thread.
        
        Arguments:
        
        - data: dictionary data to send to FastAPI
        
        - callback_method: the method to run when we receive a response
        from the server.
        
        - purpose: so we know which URL to request data from.
        
        - increment_usage_count: we use this to know whether we need to
        increment the count of web workers when a web worker thread is
        created in this method.
        
        When using the <remote_> command, we want this to be True, because
        the main script (non-reusable scripts) will need to pause and wait
        for a remote script when the thread count is more than zero.
        
        On the other hand, when the launch window is checking for a
        valid license, so we don't want to increment the number of threads
        during a license check.
        """
        
        # Required data to send to the remote server.
        default_required_data =\
            {"license_key": self.web_key,
             "vn_name": self.vn_name,
             "web_public_certificate": self.web_public_certificate,
             "web_bypass_certificate": self.web_bypass_certificate,}        

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
                   args=(data, purpose, callback_method))
        t.start()
        
    def _send_request(self, data: Dict, purpose: WebRequestPurpose,
                      callback_method: Callable):
        """
        Send a request to the server. This method is run in a
        worker thread.
        """
        
        if purpose == WebRequestPurpose.VERIFY_LICENSE:
            address = self.web_address + "/verify"
            
        elif purpose == WebRequestPurpose.REMOTE_GET:
            address = self.web_address + "/remote_get"
            
        elif purpose == WebRequestPurpose.REMOTE_SAVE:
            address = self.web_address + "/remote_save"
            
        elif purpose == WebRequestPurpose.REMOTE_CALL:
            address = self.web_address + "/remote_call"
            
        elif purpose == WebRequestPurpose.REDEEM_OR_UPDATE_LICENSE_KEY:
            address = self.web_address + "/redeem_process"
        
        reader = WebWorker(uri=address,
                           data=data,
                           callback_method=callback_method)     
        
        reader.start()        
