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

import multiprocessing
import queue
import shutil
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
    
    def __init__(self, editor_window):
        
        self.loading_window: ArchiveLoadingWindowUI
        self.loading_window = None
        
        # So the messagebox has a parent
        self.editor_window = editor_window
        
        # For sending messages to the GUI process.
        self.the_queue = multiprocessing.Queue()
        
        # This will contain the second process
        # for when the archive is being created.
        self.process_create_archive: multiprocessing.Process
        self.process_create_archive = None
        
        # Used for checking the queue every few milliseconds.
        self.poll_job = None
        
        # Track the final file path for cleanup if the user cancels
        # the make archive process.
        self.target_archive_path: Path = None        
        
    def poll_queue(self):
        """
        Check for results from a second process.
        
        This runs on the main GUI process.
        """
        try:
            # Check if there is anything in the queue (non-blocking)
            msg = self.the_queue.get_nowait()
            
            # If we got a message, the process is done. Process it.
            if msg:
                
                # Show the result to the user.
                self.on_make_archived_finished(msg)
                
                # Stop polling
                return
                
        except queue.Empty:
            # Nothing in the queue yet. 
            pass
            
        # Check again in 100 milliseconds
        self.poll_job = self.editor_window.after(100, self.poll_queue)
       
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
        """
        # 1. Kill the background process
        if self.process_create_archive and self.process_create_archive.is_alive():
            self.process_create_archive.terminate()
            
            # Wait until the process terminates
            self.process_create_archive.join()
    
        # Stop the polling loop so it doesn't keep running
        if self.poll_job:
            self.editor_window.after_cancel(self.poll_job)
            self.poll_job = None
    
        # Delete the partially created archive file
        if self.target_archive_path \
           and self.target_archive_path.exists()\
           and self.target_archive_path.is_file():
            self.target_archive_path.unlink()
    
        # Close the 'loading' window
        if self.loading_window and self.loading_window.mainwindow:
            self.loading_window.mainwindow.destroy()
    
        # Delete up the release folder, including the files in it
        ContainerHandler.cleanup_release_path()
    
        # Notify the user
        messagebox.showwarning(parent=self.editor_window,
                               title="Cancelled",
                               message="Archive creation was aborted.")        
       
    def start_create_archive(self,
                             save_full_path_no_extension: Path,
                             archive_format: str,
                             archive_directory: Path,
                             os_name: str):
        """
        Spawn a process that creates an archive.
        
        Arguments: see the docstring of the create_archive() method.
        """
        
        # Record the final file path so we can delete it if cancelled
        ext = ".tar.gz" if archive_format == "gztar" else ".zip"
        self.target_archive_path = Path(str(save_full_path_no_extension) + ext)        
    
        # Show the 'loading' window.
        self.loading_window =\
            ArchiveLoadingWindowUI(master=self.editor_window,
                                   cancel_method=self.cancel_archive)

        # Spawn a new process.
        self.process_create_archive =\
            multiprocessing.Process(target=self.create_archive,
                                    args=(save_full_path_no_extension,
                                          archive_format,
                                          archive_directory,
                                          os_name, 
                                          self.the_queue))
        
        self.process_create_archive.start()
        
        # 3. Start polling the queue from the main GUI thread
        self.poll_queue()        
        
    @staticmethod
    def create_archive(save_full_path_no_extension: Path,
                       archive_format: str,
                       archive_directory: Path,
                       os_name: str, 
                       mp_queue: multiprocessing.Queue):
        
        """
        Create a .tar.gz or .zip archive.
        
        This method runs in a separate process.
        
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
        
        - mp_queue: a multiprocessing queue. We populate this queue which will
        get read by the main GUI process, to let the user know the result
        of the archive creation process. We don't use event_generate because
        event_generate doesn't appear to work for multiprocessing, just for
        multithreading.
        """
        
        # We use this receipt to send a response to the main GUI process.
        archive_result = MakeArchiveReceipt()
        
        try:
            
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
        mp_queue.put(archive_result)
            
    def on_make_archived_finished(self, receipt: MakeArchiveReceipt):
        """
        Read the response that was sent to us from the archive creation
        process.
        
        This is a callback method that is run when an archive creation
        (.tar.gz or .zip) has finished either successfully or with an error.
        
        This method runs on the GUI process.
        """

        # So the messagebox has a parent.
        parent_window = self.editor_window
        
        # Close the 'loading' window.
        self.loading_window.mainwindow.destroy()
        
        # Delete the release folder now that no archive is currently
        # being created.
        ContainerHandler.cleanup_release_path()        

        if receipt.response_text == "ok":
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
