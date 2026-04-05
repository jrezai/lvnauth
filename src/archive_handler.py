"""
Copyright 2023-2026 Jobin Rezai

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

import threading
import queue
import shutil
import os
import time
import tkinter as tk
import pygubu
from container_handler import ContainerHandler
from tkinter import messagebox
from pathlib import Path


PROJECT_PATH = Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "archiving_loading_window.ui"
RESOURCE_PATHS = [PROJECT_PATH]


class ArchiveLoadingWindowUI:
    def __init__(self,
                 master=None,
                 translator=None,
                 on_first_object_cb=None,
                 data_pool=None,
                 cancel_method=None):
        
        self.builder = pygubu.Builder(
            translator=translator,
            on_first_object=on_first_object_cb,
            data_pool=data_pool
        )
        self.builder.add_resource_paths(RESOURCE_PATHS)
        self.builder.add_from_file(PROJECT_UI)
        
        # Main widget
        self.mainwindow: tk.Toplevel = self.builder.get_object(
            "archive_loading_window", master)
        self.builder.connect_callbacks(self)
        
        # Redirects the 'X' button to the cancel button logic
        self.mainwindow.protocol("WM_DELETE_WINDOW",
                                 self.on_cancel_button_clicked)        
        
        # Indeterminate progress bar
        self.progressbar1 = self.builder.get_object("progressbar1")
        # The argument for .start() is the speed/interval in milliseconds.
        # Lower will make the animation faster.
        self.progressbar1.start(35)
        
        # So we can change the label to 'Cancelling...'
        self.lbl_creating_archive =\
            self.builder.get_object("lbl_creating_archive")
        
        # So we can disable the 'Cancel' button when the cancel
        # button has been clicked.
        self.btn_cancel = self.builder.get_object("btn_cancel")
        
        # The method to run if the Cancel button is clicked
        self.cancel_method = cancel_method
        
        # Make the 'loading' window always-on-top
        self.mainwindow.focus()
        self.mainwindow.transient(master)
        self.mainwindow.grab_set()      

    def center(self, event):
        wm_min = self.mainwindow.wm_minsize()
        wm_max = self.mainwindow.wm_maxsize()
        screen_w = self.mainwindow.winfo_screenwidth()
        screen_h = self.mainwindow.winfo_screenheight()
        """
        `winfo_width` / `winfo_height` at this point return
        `geometry` size if set.
        """
        x_min = min(screen_w, wm_max[0],
                    max(self.main_w, wm_min[0],
                        self.mainwindow.winfo_width(),
                        self.mainwindow.winfo_reqwidth()))
        y_min = min(screen_h, wm_max[1],
                    max(self.main_h, wm_min[1],
                        self.mainwindow.winfo_height(),
                        self.mainwindow.winfo_reqheight()))
        x = screen_w - x_min
        y = screen_h - y_min
        self.mainwindow.geometry(f"{x_min}x{y_min}+{x // 2}+{y // 2}")
        self.mainwindow.unbind("<Map>", self.center_map)

    def run(self, center=False):
        if center:
            """ If `width` and `height` are set for the main widget,
            this is the only time TK returns them. """
            self.main_w = self.mainwindow.winfo_reqwidth()
            self.main_h = self.mainwindow.winfo_reqheight()
            self.center_map = self.mainwindow.bind("<Map>", self.center)
        self.mainwindow.mainloop()

    def on_cancel_button_clicked(self):
        """
        Run the specified method, which is from the ArchiveHandler class,
        now that the cancel button has been clicked.
        """
        self.cancel_method()


class MakeArchiveReceipt:
    
    def __init__(self):
        
        # Plain string message, if any.
        self.response_text = None
        
        # Detailed string message, if any.
        self.response_text_detail = None        



class ArchiveHandler:
    """
    Used for creating archives that contain the visual novel
    and the VN player engine. It is multi-threaded to keep the GUI
    responsive and it shows a 'Loading...' window.
    """
    
    # For sending messages to the GUI thread.
    the_queue = queue.Queue()    
    
    def __init__(self, editor_window):
        
        self.loading_window: ArchiveLoadingWindowUI
        self.loading_window = None
        
        # So the messagebox has a parent
        self.editor_window = editor_window
        
        # So we can call <<CheckQueue>> if the user cancels
        self.event_generate_method = editor_window.event_generate
        
        # Thread-safe flag to set if the user cancels
        self.cancel_flag = threading.Event()
        
        # This will contain the second thread
        # for when the archive is being created.
        self.thread_create_archive: threading.Thread
        self.thread_create_archive = None

        # Track the final file path for cleanup if the user cancels
        # the make archive process.
        self.target_archive_path: Path = None        
        
    def check_queue(self, event):
        """
        Check the result from a secondary thread.
        
        This runs on the main GUI thread.
        """
        try:
            # Check if there is anything in the queue.
            msg = ArchiveHandler.the_queue.get()
            
            # If we got a message, the thread is done. Process it.
            if msg:
                
                # Show the result to the user.
                self.on_make_archive_message_received(msg)
                
        except queue.Empty:
            # Nothing in the queue yet. 
            pass
       
    @staticmethod
    def has_gz_tar_support() -> bool:
        """
        Return whether creating .gz.tar tarball files is supported
        (if the zlib module is available).
        """
        supported_formats = shutil.get_archive_formats()
        
        for name, description in supported_formats:
            if name == "gztar":
                return True
        
        return False
    
    @staticmethod
    def has_zip_support() -> bool:
        """
        Return whether creating .zip files is supported
        (if the zlib module is available).
        """
        supported_formats = shutil.get_archive_formats()
        
        for name, description in supported_formats:
            if name == "zip":
                return True
        
        return False
       
    def cancel_archive(self):
        """
        Cancel the archive creation process.
        
        This runs on the secondary thread.
        """
        
        # Is the cancel flag already set? return.
        # This might happen when the user clicks 'X' multiple times to close
        # the window. Each time 'X' is clicked, it runs the this method,
        # so we should notify the GUI thread only once, when the cancel
        if self.cancel_flag.is_set():
            return
        
        # Set the cancel flag so that the GUI thread can show 'Cancelling...'
        # on the loading window, and so we know to delete the archive after 
        # it's created. We can't technically cancel a thread, we have to wait 
        # for it to finish and then delete the archive.
        self.cancel_flag.set()
        
        # Create a receipt to send to the GUI thread.
        receipt = MakeArchiveReceipt()
        receipt.response_text = "Cancelled"
        
        # Send the receipt to the queue so the main GUI thread can read it.
        ArchiveHandler.the_queue.put(receipt)
        
        # To let the main GUI thread know there's a new message to read.
        self.event_generate_method("<<CheckQueue>>")  
       
    def start_create_archive(self,
                             save_full_path_no_extension: Path,
                             archive_format: str,
                             archive_directory: Path,
                             os_name: str):
        """
        Spawn a thread that creates an archive.
        
        Arguments: see the docstring of the create_archive() method.
        """
        
        # Record the final file path so we can delete it if cancelled
        ext = ".tar.gz" if archive_format == "gztar" else ".zip"
        self.target_archive_path = Path(str(save_full_path_no_extension) + ext)        
    
        # Show the 'loading' window.
        self.loading_window =\
            ArchiveLoadingWindowUI(master=self.editor_window,
                                   cancel_method=self.cancel_archive)

        # Spawn a new thread.
        self.thread_create_archive =\
            threading.Thread(target=self.create_archive,
                             args=(save_full_path_no_extension,
                                   archive_format,
                                   archive_directory,
                                   os_name,
                                   self.event_generate_method))
        
        self.thread_create_archive.daemon = True
        self.thread_create_archive.start()     
        
    @staticmethod
    def sanitize_timestamps_for_zip(archive_directory: Path):
        """
        Look for files that have a timestamp older than 1981 and
        set them to the current date/time.
        
        Flatpak apparently changes the timestamps of files to 1970.
        However, the ZIP format does not support dates before 1980, so
        we use this function to look for older-timestamped files
        and we change them to the current date/time.
        
        Arguments:
        
        - archive_directory: the path to look for files in.
        """
        # 315532800 is Jan 1, 1980. We use 347155200 (1981) to be safe.
        safe_epoch = 347155200
        
        # Unix timestamp (floating point value)
        current_time = time.time()
        
        # Enumerate through all the files in the given path.
        for filepath in archive_directory.rglob("*"):
            
            if filepath.is_file():
                try:
                    # Get the file's details
                    stat = filepath.stat()
                    
                    # Is the file older than 1981?
                    if stat.st_mtime < safe_epoch:
                        
                        # Set it to the current date/time.
                        os.utime(filepath, (current_time, current_time))
                        
                except PermissionError:
                    # If a file is locked by the OS, we just skip it
                    pass
        
    @staticmethod
    def create_archive(save_full_path_no_extension: Path,
                       archive_format: str,
                       archive_directory: Path,
                       os_name: str,
                       event_generate_method):
        
        """
        Create a .tar.gz or .zip archive.
        
        This method runs in a separate thread.
        
        Arguments:
        
        - save_full_path_no_extension: a Path to where to create the archive,
        including the file name, but with no extension. We don't supply
        the extension because the make_archive() method will automatically add
        the extension based on the given format.
        
        - archive_format: a string that represents the archive type to create.
        Example: "gztar" or "zip"
        The format will automatically set the extension of the archive that's
        being saved.
        
        - archive_directory: a Path to the directory that needs to be archived.
        """
        
        # We use this receipt to send a response to the main GUI thread.
        archive_result = MakeArchiveReceipt()
        
        try:
            
            # Look for files that have a timestamp older than 1981 and
            # set them to the current date/time. The ZIP format does not
            # support timestamps before 1980.
            ArchiveHandler.\
                sanitize_timestamps_for_zip(archive_directory=archive_directory)
            
            # Create an archive.
            result_path = \
                shutil.make_archive(
                    base_name=save_full_path_no_extension,
                    format=archive_format,
                    root_dir=archive_directory)
            
            if os_name == "Linux":
                instructions = "extract and run 'sh run.sh'"
            else:
                instructions = "extract and run 'player.exe'"
            
            # Success
            archive_result.response_text = "ok"
            archive_result.response_text_detail = f"An archive file has been created successfully.\n\nThis file includes the visual novel engine and your visual novel.\n\nInstructions for your viewers on {os_name}: {instructions}"

        except PermissionError:
            archive_result.response_text = "error"
            archive_result.response_text_detail = "Permission Denied. Try saving to a different folder."
            
        except FileNotFoundError:
            archive_result.response_text = "error"
            archive_result.response_text_detail = "The release folder could not be found."

        except Exception as e:
            # Catch-all for unexpected errors (Disk full, etc.)
            archive_result.response_text = "error"
            archive_result.response_text_detail = f"An unexpected error occurred: {e}"
            
        # Put the result in the queue.
        ArchiveHandler.the_queue.put(archive_result)
        
        # Let the GUI thread know the result so the user can be notified.
        event_generate_method("<<CheckQueue>>")
            
    def on_make_archive_message_received(self, receipt: MakeArchiveReceipt):
        """
        Read the response that was sent to us from the archive creation
        thread.
        
        This is a callback method that is run when an archive creation
        (.tar.gz or .zip) has finished either successfully or with an error,
        or if it's been cancelled by the user.
        
        This method runs on the GUI thread.
        """

        # So the messagebox has a parent.
        parent_window = self.editor_window
        
        # Initial 'cancel' message?
        if self.cancel_flag.is_set() and receipt.response_text == "Cancelled":
            # The user has just cancelled the archiving process.
            
            # Disable the Cancel button and change the label's text.
            self.loading_window.btn_cancel.state(["disabled"])
            self.loading_window.\
                lbl_creating_archive.configure(text="Cancelling...")
            
            # The next time this method runs is when the archive is finished
            # being created.
            
            return
        
        elif self.cancel_flag.is_set():
            
            # The archive creation process has finished (either successfully
            # or with an error), but it doesn't matter because we need to now
            # delete the newly created archive, since the user had already
            # requested to cancel it.
            
            # We can't cancel a thread, unlike a secondary process, so now
            # that we've waited for the thread to finish, we need to delete
            # the newly created archive.
            
            # Delete the archive file
            if self.target_archive_path \
               and self.target_archive_path.exists()\
               and self.target_archive_path.is_file():
                self.target_archive_path.unlink()        

        # Delete the release folder now that no archive is currently
        # being created.
        ContainerHandler.cleanup_release_path()
        
        # Close the 'loading' window
        if self.loading_window and self.loading_window.mainwindow:
            self.loading_window.mainwindow.destroy()
    
        # Notify the user
        
        if self.cancel_flag.is_set():
            # Reset the cancel flag.
            self.cancel_flag.clear()
            
            messagebox.showwarning(parent=self.editor_window,
                                   title="Cancelled",
                                   message="Archive creation was aborted.")              

        elif receipt.response_text == "ok":
            messagebox.showinfo(parent=parent_window,
                                title="Finished",
                                message=receipt.response_text_detail)
            
        elif receipt.response_text == "error":
            messagebox.showerror(parent=parent_window,
                                 title="Error",
                                 message=receipt.response_text_detail)

    
if __name__ == "__main__":
    window = ArchiveLoadingWindowUI()
    window.mainwindow.mainloop()
