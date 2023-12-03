"""
Copyright 2023 Jobin Rezai

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
Changes:

Nov 23, 2023 (Jobin Rezai) - Added 'Colors' toolbar button. 
"""

import tkinter as tk
from tkinter import ttk
import pathlib
import pygubu
import re
import json
import subprocess
import sys
import webbrowser
from shared_components import Story
from story_details_window import StoryDetailsWindow
from font_sprite_properties_window import FontSpriteWindow
from project_snapshot import ProjectSnapshot, SubPaths, FontSprite, LetterProperties
from new_project_window import ProjectFolderWindow
from input_string_window import InputStringWindow
from input_ask_new_folder_where import WhereNewFolderWindow
from delete_confirmation import DeleteConfirmationWindow
from tkinter import filedialog, messagebox, PhotoImage
from pathlib import Path
from enum import Enum, auto
from typing import Dict, List, Tuple
from shutil import copy2
from story_compiler import StoryCompiler, CompilePart, CompileMode
from wizard_window import WizardWindow
from play_error_window import PlayErrorWindow
from fixed_font_converter_window import TraceToolApp
from about_window import AboutWindow
from snap_handler import SnapHandler
from custom_pygubu_widgets import LVNAuthEditorWidget
from edit_colors_window import EditColorsWindow


PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "ui" / "editor_main.ui"


class FileType(Enum):
    DIALOG_IMAGE = auto()
    AUDIO = auto()


# Used for knowing which 'New folder' or 'Add...' buttons are clicked
# ie: from the images section or audio section.
class SectionChosen(Enum):
    IMAGES = auto()
    AUDIO = auto()
    REUSABLES = auto()


class Icons(Enum):

    # Custom
    BLUE_DOT_CUSTOM_OWN = r"iVBORw0KGgoAAAANSUhEUgAAAA8AAAAMCAYAAAC9QufkAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAKpJREFUKJGd0i0OAjEQhuF3FoJAgsciCZoDoBAbTsFluAKKhHugcVj+EgzcYBH7Yeim6ba7wCSfaeZJOtOaJP6tbnhgRgZMgCFwkrgktaQqoBx0A8nLHjT2+6p+Dy5BZQBdnqBRFIM6oHsCumxSeNoCBXqEOPuM3v9iubUeh4/AqwUfktsGrRuuXILmTdvugbYRWIBWsaey8IeZMQMWwAA4AzuJa2yOGv6l3sl+4+Ia0K20AAAAAElFTkSuQmCC"

    # ionicons
    EDIT_24_F = r"iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAOpJREFUSIm11MtNw0AUQNFDWqCIEAjOggVdhAaQ6INCqIAu6CASbBGsWJGQRLTw2IxRPp78PB5pFpZmzn2yJYsIJTcqvOAD4y7wJSLtz56y6xHnK89fpSbv4wFDzNP0S1Ql8BEWCX1Kr+kZo4hQEq/3/dqZlh90E1+g3zqQwX9xs3W2S/zoAAaYHoofFcjgc1Q77x2IX2Tw6713u8T3BtriOwMl8GygFN4YSPh3CXwrkMF/TsXXAumX24QPT8X/A2ny2QY+w1UbPNnOMOkCrwPjBvyyBF4HXlfwCQal8IjQS/Ab7nAbEe8Krj8A/edCIKo/QwAAAABJRU5ErkJggg=="    
    FOLDER_24_F = r"iVBORw0KGgoAAAANSUhEUgAAABkAAAATCAYAAABlcqYFAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAOVJREFUOI3tzb1KA2EQheF3xt0NbhdbBZFAIBAQQwRvQLCzUbC187JSJbWNgp1IkFQ2SWGjrdjvj6v5JpVBA0v8NJ17usMw55F+q3Voqh1KomY3Z5PJQ9n9JwkMjqOQizi2j8XjWyFa5HYC7P8JAdjaNDnoUls8pplxeaV7g3b7yFRHPsOhc8npeFzMkbLE67CzjT092zXTqY/Bu8g50FuKAHR2LWg2vPa5HVqe5TLvS5EohI26HxKsqfva1e/9d6mQCqmQ/4QEAC+vYnf3VqxqNMuJviGiOkwTC9NkVQSAIc49frYZBeVDcIWs5GIAAAAASUVORK5CYII="    
    REMOVE_16_F = r"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAARVJREFUOI2d0z9KQ0EQx/HPC6JnMCIWqdTkBBK1UTBVCk+hnkUMBL2ETVoTPYR/OhvjEbQMrMWbwPr0icnAwO7Mfn8zy85KKckdHVzhGZ/hLxFr/zifgWu4xgx3OMMJerEeR26I1W8CAT/gDXvVKlmRLqaYzEXmiZuA1+vgTKQZIsPY60RrtZVrOplht8AA2ymlYwtYURQTPDZwhNEicNgIRyvYxGumfBqiv9k4pXQb61dsNZBQLNFBgbSCd7Tm0ahwW0dl1sK0oRyQ/hId9IPVVj5Jd4FnPAhmZx4YKoej+Q94I649yCdxVTmeU+z/AR8GPJaPciYyjNYmOFd+pB4ucB+5gepnqlRp4xJP+Ah/ithu9fwXLSAxjr97p2oAAAAASUVORK5CYII="
    SAVE_24_F = r"iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAgVJREFUSIm11rtrVFEQBvDfmDWP1kIDIqISJWqhNhYSsVJECxGEVMHE0v/AVrC1sBEfsRNb0UCQFJJGxCYiQdAyhmg0jagkJjIW927YbB67WePAcOCcM/OdmW/uzJWZMIRJLCFb0AW8wP7MVKtROn+Ib3hbGmxW2tGHGZzJzI/VgyhfvhOH0YWz2NaE0wU8z8w5iIgh3MfnepAljGIPFptIR61+RVc1HYps/ME0ejJTBW3l5gVUcANvmojgEq7jFMYgM4cjQhnJy4joq9QYbC/Xicwca+Q9Inrr7KwBcreZXG9aMnMY4zhdG8FiuR6LiMXVZqvkUJ1dvfxCBwVZIwqSf9scybPorK/9kvAR5HIEmTkVEQdwTvNl+iwz5ze6VJsimTmFB004b1r+C8ktA0TErojo3nKAiDgfEe8VbWAmIiYj4uKWAETEZUVF7MZjPMFePI2IK82AJEbWKbUKvmAOB2v2exTd9xPaNyrTRhGcUHTae5n5YflFRad8VEbVu44tGqeos1x/rHH2s1zb/wVgQvF190dER3UzIjrRj3m8axkgM7/jNo5iPCIGIuIaXil60c1GXzLlwFmLqJKsNtyxcl4v4hYqG9iNYql2ZB7JzNn1XhER+3BSkbLXmTm9wd3u0u90YBDDilKc0NrQX+Efx7EDV6vhDCrIavW3pVaXSl8DmekvrhpARMXjI3kAAAAASUVORK5CYII="
    PLAY_24_F = r"iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAf5JREFUSImt1k9OFFEQBvBft8YF7NwYYSR6AYhu3Qou1NETeAEDnoAAC70DChtPoIkkLryHEBNiwgyJK0B044DPRVczf+ieGdCX1KK7qr6vXr2qei9LKalbWZbN4Cke4TYaoWrjGz7ifUpprxYkpXROAmgTJ0ghv9EK6fT8P8EGpiuxKsCf4TicW1jBHLIemxx3sRq7SfiB5lACvMRpRLiMiaqoBnwmIohO+C5VEkTkpzjAg1HAFUTzOAyMZh9B5Pw4orgw+ABJJ9I11UuwGXlcvix4D8lKYL0pK3QmKqFVlXNcx+syojEIJrEfmA1YDMaVGof7of8ZVXNtDJK18HkBn+JjbgRBKdujzilKOGELvkYT5WMSJPzBO9yo8cnjsLdF9ewNiaaKoJQDPKnxa+E4V6zM/19Z7NRObOd/puiKooq+5NjFVcyOGdkOFlJKz1NK32ts5oJkNxcnrRgVw9YvRfnNppQ+j7AtsbbglmI7bfWN9srFG62DRvlzw5Bmu+CoKJtsvXcWTSsGVAfz/wD+MLJxhJtnBKFsKkbt4WVIsKA7rs96Y9BoSffCWcXkmDlfi8hPsdinr3BoRrpSHNaaYrbkPTY57oVuP2yP8PgcXk1UU3ir/9LvRKW19V/6HayXOR+ULAArV5ZlDd1nyx3dZ0tL0aBb+JBSatdh/AXxopeXWnu8kwAAAABJRU5ErkJggg=="
    WAND_20_F = r"iVBORw0KGgoAAAANSUhEUgAAABQAAAAUCAYAAACNiR0NAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAS1JREFUOI2l071OAkEQwPH/bIgvYCyooKUxJJS21ib4HrZS0BCiwQahseU5bHgGEwuQRl5AQ+EDrMXNJeO6d87hJJvs7u3+9mY/iDGSK8AQ2AOhakyuBDRE5ISf0QG6QMuMaYlIoCaCwT5FZGa+RTtQRNrAKzCvA22KM0Wm2u4Bd1o/A96AD+C8LuV036bAc2Y/B8AW6P+1h6ITfoWIdIArYBNjXNemmcQ1MAJugZ4u0AW+dAsiMPeeMsC7mXivnTemrywLF1ixymUGdKEpdAoMtP5ooD2w9KAWa+vV2GSu0pO2RyUKxYFmQYrXsKW4Z/3kr0v0wYOWk4KmlL1nTVD3o/eibtCLNgI9aGNQkYUiE21PtD0+CqxAV8DhaDBBV8ALsPsXqOgYOAA74OIbDGPeQ0SrWs8AAAAASUVORK5CYII="
    WAND_24_F = r"iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAYVJREFUSImt1D1rVEEUxvHfEWEVtBGJxnRWNhZu5UJAg0QLscgH0A/hB4mlaKugdbCxsjSVKChYi5WNaEQlITsWntXhkr0vmwwcGM6def5znplzlVLMC5zCZ9xvW9cWx7SPs1jB5Y51c8c/QETciYjNiBh1bYqItYh4FBEnOwmVHZsoeIFR5s5jiofVunX8zFjusqgGjFK84HmVX8O5nF+pxG/2uYPmpY7wDE/nXPpVfOgrXkoRubHN71Us4VUp5Wun5weM07iYcaFx4idpWcEXTIY+U/hUiRTcyA+rjfwU34dCjuMBLmU1u3if86WmW/423suIuFVKed3Ln5bSzqQt00Yl+/jWt5KDhMezzZikLTPIG9zLSntBmuKzJvpY5WaQfdzN3G38xg9c69to1/1vovUGeJIn3sXGEEgt8hi/zGmiRSG1wAmsdLzpwZBBTbMIZDBgKGQhwBDIwoAWyEbVJ+NDAToge9g+NKAF8hY7RwJoQPbwLn8tW0cGSMgY29jBFpb/AEEYFltv0cCKAAAAAElFTkSuQmCC"
    CANCEL_24_F = r"iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAdxJREFUSImt1rtuk0EQBeBvkUhqQkViIqjyLkQyNCEiN9GiEHieAHkFLkVEEZoICQg8ACA7oQBaDKQMzlL84/jC70tsVtrC3jPnzM6ef3ZTzlm/kVKax00s4hoqsfQNX7CLFznnr31Jcs7/zCDawR9knKCG1zFr8V8OzBPMlXKVkN/CcQS/xSouleBmsIaDwP5GdaAAHqKJH1hCKsuqJyZhGY2I3SoViMybOMUepoaR9wgtoB4c1S6BqPlxZL4XW97F9BgijSjXbKfATpAu4SKeTSByJ2IftRw6H05406r5JCJxJgfBWYEHQbTSA5xEZD3iNuFleLrMimOJhIVPIkYNtQHgcUUO8Um4Z38I+Nwiii/++IJiJANGzvkEt/EcN/A0pTQ9KCY4T+Ez6iNue+Sd4AgfOw955n+J4HLnId8P8No5bDhQBHdj7R5cVXwU74zQ3IaJRO0/xA4qLfDjAC6PKtBPBCvxezvndi+aUzSoBhYmENnHz5hXzgQCWFW02voYIlN4FbZsYvFsrQe4FYCGoiuOeuGsRtZNbHatlwRUo1xZ0RXXyywcVtzA+8D+6sy8r0AEz8bBd176h9qX/mHP2nar5r2z1f9LR0qpov1sua772XKk/Wz53o/jLzj11RR4QENCAAAAAElFTkSuQmCC"
    CANCEL_SCRIPT_24_F = r"iVBORw0KGgoAAAANSUhEUgAAAB8AAAAYCAYAAAACqyaBAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAiBJREFUSInF1k1vTVEUBuBnk6gEZdAYqFmFESGSDhqRqoqYiBGSIqIGKn6DH2BAmoiPmanfwNAQg0ZFSny0jURU4qs+UroM7q573N57ey4XK9mDs/Y++33Xu96zzxYRGg0cwn3MIdowvuEBTkSEZsCHMd8m0HrjWMpAv0RKaT3G0YUJjGbWfxrLcQbbMNao6puZ3Rx2NmtNqwPDCy1YVqfqgyqSw4WIuNeGiovx/acKNazWYToze4SV7aw6Y5zM+0dt5aPoVjHa6Yj4UqPKspTSrZTSeEppc6PSUkoDKaWplNLlphoUGB1QdeLFBqxX4UteM41Nddb0Yzavedis8oVEJyZz8ilWN5HtqIrzA1PoKcztxsc89xa9ZcCv58Q8Bkv07bDqwTOJHvThfc59xO6leg57VA+TKy0Y53hBgckC8Hv0lTEcFVcvbNDZonOLLYjc6/7fdXur8RyfC8+vVTxTOvpVZb/aQtW9KqYKfFI5PAJPsLGU7DlxTdVw+0oA78AbVakHcKpA4DG6y4J34kVOPtP8U9uOmULFewtzwwUCE/UILALPycGC/JcaAHfgVQF4kUo4W9jnTinwPHEjT3zHrjovrlA5WGaxv4k65/Iet1sBX2uJHwvWoKuELzago/SnFhHvMJIft+C8moiIDxExU5uvs+5lRHxdalE91v/iMjH3P65RI9iq0TUqEzri714gh5aS6CDuau/VeQxDEeEHUnw6hWF+FLkAAAAASUVORK5CYII="
    COLORS_24_F = r"iVBORw0KGgoAAAANSUhEUgAAABkAAAAYCAYAAAAPtVbGAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAqxJREFUSIml1k2IllUUB/DfnRKmdFQ0RzNNamCIiKiggSYSkoJwIYiKRQ19LYM20S5CpBaCQZuoVS36gBZW4EoIso9NtpqCKAlRo4EmRkiL1Jpui3uemTu3ZyacLlye9/mfc/7nnHvOPc+bcs6WWimlQWzHAxjHZgxjADM4g89xLOd8vJck59y7sQ4vYhq52hfxY5D/1si+xv5/cS3i4An8GoaX8B4msLlHdxsexyeVs/exttcJVoZCxmW8ghuwCTuwstFfG/j6eB/H92F/AqsXOMEgPg6Fk7g78FtxPvBvcW3g63E28F+wtQq043mjdfJhCL7Cmgp/vjn3ewLf1eBPNvWcxixu7MCHQ/G7LvXK4M4odsZpDAW+MTLIkenNjd2hkD0D1+An/K206hhexURlMIK9WNcQbcK+7qgaWRf4YdgTLx/gOlyojmDPYi3+XxtPB8fBAexX1tu4HqvMr1HLXw/Fc5LSSVnpioQ3lYJNYuMys7gvOH6OcvgdM43S4P84pjFl3GQ81o2ty5haLmnjYHcEnXGgwp2N1FYEMISX8DpGrsDBDvyJv/BsI5u7nfcG8Jr57vrmCpx8FDYTrWxAaV1KX8OWqkPq31JKYymlXSml4Z5uuhTPkT75MP6Is9yGu/ADznVR4aoIpsvwPHY2mdxR1SPjM4zOzS4cCMFRDPQcxaMWzqmMKaRGb1SZFpOh82XtZFCZW1kpeGt8sMdJVn0zegI7qYyqoRq8SfniZbxr4SR+sMfB5BIO9kaNZpBa4S04ZX7iPoKrQ/ZCGHbfldt6yEfwTujM6i5jj+JqvFVFfAYvK38kNmBLD/FTSgvPhs0pbJ/TWSLlcRypDLt9IUimlGlRy07jOayquVJ3IxdbKaWtkcX9uD2y2aC0/XTU8Qt8iuM559mW4x9p7ExjTVL6WQAAAABJRU5ErkJggg=="
    OPEN_24_F = r"iVBORw0KGgoAAAANSUhEUgAAAB4AAAAYCAYAAADtaU2/AAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAATlJREFUSIntlk9Kw1AQh7/JIi220rXeoytxJ1iwHkcRD+CfG3kEtQu9g0J1bYutlPxcZB6E9CmmJl1l4EeSSTLfMDPJe0giCBgDE2AJqKQ5cAcMi+9sqiL0NAKLaQXcAoO6wBMPfAGkaw/CwIGrPyYYtAQegfFP4FDeNWgpgaGXfFYxAQEnMbAA1dG/UqIpcOnxH4Lf/CZmltMlo2Yzs9QrupTUBUjqhsRM0pefdor+lHxoqvZrU107k5stQoOuAF794qDuwYoM2qGzXoz8s+gBu5JmVXpX1cysD3wA8wR4d/9ek1C3fT++JcB0i+DAmLbgFtyCawMb+Qo1A7pAT9JnE0Qz23HOAugnkjLgGTDgzMw6vwXYENoBzp3xJCkLP+8jIKP5VSkDRuWtzwi4J761/a8WHvs48L4B1MwtHez0M+IAAAAASUVORK5CYII="
    EDIT_DETAILS_24_F = r"iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAVxJREFUSInt1r9KHFEUx/HPlS0MuxFNY2sp+ASJSAIRXIu8RKoUFj6EjVimMi8RAkZIAiYBd5G8QIRYBjFFSGEX0JNi78A4uOzMuOk8cIq55873d87h/ksRYdqWUurhLbozU6eP7DGe44+ImJqjh32sYB29Ti4pYTl7Z0J2VziJiPPyYG7LIdYQEfGqiC3gE6KBH1Uy7+Jzjh3jYRHrYC+X8w1fcV2jxx9LmXdxgGcYYDMiLsuTf+E3Zlv0fGzmpTkC3+8IH9wGby1QF95KIMO/VOFYxTssthYYB8+x3Tz+ovxP7Z2cV8t7PMUQ/epqKaaWPyZtqgLewwc8MWYpjrO6FbzM8GETeBOBOWxjowmcmi2KiJ0m0LL9r+P6XqCZQKhsjjuwqBz3M/iBpZTScltySumB0X0AZzdi2MJr/MXPlhqPMG90EfWj8lQpRE6NymtydRZ+gTeYrx6Q/wB3drfVSlf2YwAAAABJRU5ErkJggg=="
    COMPILE_24_F = r"iVBORw0KGgoAAAANSUhEUgAAABgAAAAaCAYAAACtv5zzAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAdNJREFUSInd1rtuE0EUBuBvo2CEZKcACQpzkVBSQQMVtJAKXiFKylSAQkNLR5Qur8BNgpZHABqgDLJEihQJNCkARUCwwEuxx2Swdu21BQ0jjTSe81/msnOO5XluVMccHuFj9IeYq8UdIdzEKr4jTwzymFtFc2wDZFjA+xD7hBU0oq/EXB6YBWS1DHABz4Pcw32cKMEdwzp+BPYVLlUa4OgA4TUu17ifi3hRtaA+aDk52w9YrNrykCNdDG7/rpYj5mlMdrGGVl3hEqNWaHRD88kU5hVtGu0ATdpaoTEdv+eF0za2YvwFd3F4jJUfwi18Do2d5Ljk6OBICH+LuXe4VkP8CjYcvI11xfvp/GGQEE4pvoQ8+jOcLRE+OQxXaZAAruJtycr6O/0asU1cL+EPNwhQA3ewF7it5K72Itao4I42SMBtPFY8pF6M2yM49Q0S0i52a2I7yKf84/Z/GGzidJZl5/6WaJZl53FG8VjddPCtr2Fm0kvGTGj0K+CNqnS9pCRdVxko0vWSsnSdgAYLzhsDBafMQFFwXgbnpyJ9HP8dL1lNZclMDYxbMku2PFj0b/cNYjxZ0R8wauIe9pMd9WK8H7Hx/7aUGM3igaIUdmM8W4f7C7EAm10DmY3dAAAAAElFTkSuQmCC"
    TRACE_TOOL_24_F = r"iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAQJJREFUSInt1k9KQzEQBvBfBF2JLlTwAG506doTuKvn6J+TSO1h6gl0607xBopYatGVPBgXLy0VbPoEBcEOzCb5vvmSTGYSOMMjouAv6ESEiIBeHitxHtBKOfg6biy2Q+xjBwnPOcB9gXOMd1ltOF3dV45Bxh1kDwyWcIaItcIKfsRWAv9AIGGMN1wWcCc4wl7mPOEOVwXOKTahg0q5KgPnc3e83wBfoZ0iQkppW12li2wSEaNPW09pF1sFzigiJtMcpAJw0fwyzsx6mh1Rf+6ILhrgK3STuiu++n6Sb3Fd4MySvGp2K4E/LpDUj/eGX3z0Wxlcqsox2nN3vJvHln5bPgBRQOv7+FNLDwAAAABJRU5ErkJggg=="
    DETAILS_24_F = r"iVBORw0KGgoAAAANSUhEUgAAABgAAAARCAYAAADHeGwwAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAQBJREFUOI3d1bErxVEUB/DP0U+SZ1U2qwwWozJTBn+CJKX8DWw2yvKysBnFbDSSUvwBL6RYvMnEMbz78sr2fu8tvnW6957hfPue+73nBlZwgBY2MvMZIqKBUf3jOzPb8IgssZ+ZsIqvnny/8VDhvYf1rayvhXiihgK4hXlcYheNzDTIiNKSoWFkqNW7BBGxGBEzwyAIHGFHxzXLmXkVEZNYx3jN+jfw4tdWzXInW+pbNPFR4QLbRcF5YT7D2CAUBCqd13yfma2aBf/gH9g0ImYj4jQi9sqAGygqNLFUzm0cRsQCTtSfRdcVpnoS3f005tRv4WdgDce4w2ZmPjG4/+AH9j6mdZ0DtAwAAAAASUVORK5CYII="
    HELP_24_F = r"iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAkxJREFUSImV1cuLzlEYB/DPOxshajLlMoz7pZQNdsoGG8rkmktsLEQuGfkDlI21nXspuYxrSlFslI2SiCKXsHENyWVmHIvf85qfd877vpw6nX6/7/f5fs95zjnPqaSU1GuVSqUd6zAfszACv/AKz3EFF1JKL+uKpJQGdIzDCfQiNem9OIT2rFZGfCU+R/B3nMQqjMdgDMV0rMEp/AjuZyxtaIAdkYKEs+jIzaomZhK6I6YP27MGWB3ifdjWTDhjtDti+8orqYId+BizGCCOebgWnG+4gw11TKrpai8bHK2mJRO0sbSyu7gdJgl7M/xqug5WT2g7evATE2rIbfiCN5hd+j8WD+MEddTETI6N7w2eHeF4OjObpYHtymDbAluWwU4HtrUFCxTtnIHtBnbicAabEuPbDHYxxsXwLNym/seJ2RRpfYxBGXx6aD4SOU4Y+g/Cg3A8+O8wpw5vmP7T5Ot/GBwI7i2Mb8AbEryv8CQ+pjURH64oHfdzacmcpIQXLYrjBnMzm1VubZGiqymlH024Va17LbgeH52NIlJKT7EI+5qIw/IYb8IYxcXoUXPRapbdqigFM5ukZ2JJb3RtqbjUIHB/cO40MTgfvGPlWjQKHwLYUydwCd5jXwPxrtD4pFzsAuzUX26zJk1m3qUoir/Q+ed/DWlLGCRcxsR/EJ6kKA3VB2fzX3gmoLOUrh7Fy7YeM2KjWxWlYC3OKKpwipjlA/TqzGokjuh/bxv1nxo8+pUQzLZKpTIaK7AwVtAW0Ec8UNyh7pTS63oavwGVD2+L019FOgAAAABJRU5ErkJggg=="
    ABOUT_24_F = r"iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAktJREFUSImtlr9rVEEQxz/zMEYEIeQuIkkM2gniD4z+Bf4ocibaSkJKLWKsBGuxFCyMxpiQwkILK1OkFDsL/QNUhLNQo42Y88AcXC5jsbO8fXdv33GSgWVh5zvf2Z2ZnV1RVWIiImPAFaACHAFGTfUN+AKsA2uq+jVKoqodw4hWgW1Ag7FlI1zbBlaA4VyuHPKrQN2MN4EF4AIwGGAGbe0RUDPsH2Cq0AFwC2gBO0ZcyttVm00ZeGxOWsB8rgOLdctCcC1C1gfsieimgYZxTGYcWMzrtvMY+QngN/ALOBPBzNhJaj4nXrFqioWCUNwNEnuvAPfEMMu+QsesEjaLYg6cBH5YeR4vwA3ZCZoWGea77b7XESR9LgEm7Eq8ar8jXkTknIi8EJGXInJfRPpiWJM1mycAPpu3gYIdPSB7uU53OUHJcB+x6tnqYrAfOA+8N8PxLnjBlXs9SaMgEjuvqv5V1de4Eu1FdhJgA+gHBno0LpISsA/YSICqLZ7dRQfjNlcTXMsF1yp2SzzXOsBh3EWrAUOR/nMDuAN8wiX5IXAbOJWDP4jrrE1gxC+umOFijsFlsiUajrc5+KemW1JVRFURkRHgA3AAmFHV5/6sItIPXMeV6l7D+Gp6o6rvAuws8MyicUxVf4aep3CttgFM/0d7mCVt15VMuw5ANw2guK7YkZNIzH1YWsBcRp9jMEn6DNZwjesiUA4wZeASsGgJ9c9rpYMvsqthYNkqof3Rb7StNYEl4FAelxhhrojIKOm35SjZb0uV9NvyPcbxDwweCInxErGPAAAAAElFTkSuQmCC"
    NEW_FOLDER_16_F = r"iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAASxJREFUOI2d0z1KA1EUBeBvQtA1GBGLVGpcQYjaRNDKIjuwENS1iIGgWLiDNGlNdBFGOxvjErQUnsXcgXH8QfPgwnv33nPOnXnnSSkpBzZxjge8RTxGrvWlvwRcxAXecYNj7GE/9uOoDbDwiSDAd3hGu6pSEulghklBUhQuA7z0E7hE0giSQZxtxmhflNFD74dJ3rGRoY+1lNKuysqy7BpSSoff1Ca4r6GLUbXhD2uEbh0reCox94IU2pG7ivM4pTSM/RNWa0jI5pggQ6rjBc0iGwrDUC7+wdE3BE3ManKDHMwxwUFgteRX0vnHNW4HZr1IDOTmaPzBSMvx2f2yExfk9pxh6xfwToDHylYukQxitAlO5A9pH6e4jVpf9TFVVFo4wxSvEdPIbVT7PwB38i/F7M5fOAAAAABJRU5ErkJggg=="
    AUDIO_16_F = r"iVBORw0KGgoAAAANSUhEUgAAABAAAAAOCAYAAAAmL5yKAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAQtJREFUKJGl00ErhGEQB/DfbHtTLlJOe/EBHJyURCnCTVEOPoSDz+CozdVdThzdnRU3sdIepDhQDm7j4Fm91r60mZpmnmae/zPP/GdkpkGKJg5wj/HavJrLozjDOxIbffEVrGWmhj6JiBbOMY3F/niRWRxGxEgzIhawVAlu4w0zmXkTEVXwmeLuYweb8IJHdIoeYaxS7tcX0MZl8U9w+i2hph9VgLlynsQuuj968IdcFjtZqh4fFqDXkCx+DgswVWwHE3hq4BXtiOgUPYqIsRqAdVxl5p1PKi8C81iuJPVoXC00JjYz87jQGHjALbYGdb2FKzyXVwZN4h66aP5nlFdrd6GyTG1c+2WZPgC+yveQlTS6AQAAAABJRU5ErkJggg=="
    IMAGE_16_F = r"iVBORw0KGgoAAAANSUhEUgAAABAAAAAOCAYAAAAmL5yKAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAARVJREFUKJGV080qxGEUBvDfYcbOVilpFjQps5EotpOVlVuwxQXYSEKxRdlYugV7G2K4ADZWpMhHsWH8Lbwzja8xTj31dk7vc57zdA6UcIoqshZRxQlKgWMcYBMvWos8ZjAKryhmWeY3oCc1mEc+5Yp4zaE9SWoW28hhAg+JrIr2thYld+IC9+ldj28EEdEREeWI6G5Iz6EfZ9j6+idDX5qrC0e4Sd3GmvjSh6yuICIK2Mc1erGIvYgY/Wu+DJO4xA5yDV3mcYdhDOEcV5iqKagRPGIV8YPUBdwmrGAaz1hvJFhqMusgnrDckBtPhBlNFgkDyZO1H2plvNVW+RAbPq9yAbvYw9IX3/KYxQgfx1Tx/2OqoPQOfhPFLBN6WyEAAAAASUVORK5CYII="
    STARTUP_SCRIPT_16_F = r"iVBORw0KGgoAAAANSUhEUgAAABAAAAATCAYAAACZZ43PAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAOZJREFUOI3t0s8qhAEUhvHf0dQUO7b+LdTERnasFBaugP1ciJtwB7OUrCwtpeECpIhpigg7KYpjMd/ULHyf2bHw1rs4dc6zOQ+s4RCXeMETTrCLddQyU1kDj7jAER5QRwOrWMAz9nGAM7xiFpsISGx9R8c8dnBe7A32A59RDNuZuaciETGNRYyiizm0alVHg8nMbnHYB07ByLCAsvwD6H+hGRFNTOAd97jCKdqZeVcG6HvQwbGedTVM6tnYKHY6Bewab5jBBsYqRYqIcSxjBUt6CtdxizZaVKg8TH//C38DcIPSP/+ULyx4jHl3Hl9DAAAAAElFTkSuQmCC"
    
    
class Passer:
    toolbar = None
    statusbar = None
    editor = None
    chapter_scenes = None
    file_manager = None


class EditorMainApp:
    def __init__(self, master=None):
        
        """
        Initialize and show the main editor window.
        
        Arguments:
        
        - master: the parent window (which is always the startup window)

        """
        
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow = builder.get_object("main_window", master)
        
        # The master will be the startup toplevel window
        self.master = master
        
        builder.connect_callbacks(self)
        
        self.mainwindow.protocol("WM_DELETE_WINDOW", self.on_window_close)

        # Maximize the editor window
        self.mainwindow.wm_attributes("-zoomed", True)
        
        # Debug button (uncomment the two lines below if debugging)
        self.btn_debug = builder.get_object("btn_debug")
        self.btn_debug.grid_forget()

        self.style = ttk.Style()
        self.style.configure("LVNAuth.Treeview", rowheight=35)

        # For deleting images that haven't been saved in the project.
        self.delete_files_upon_exit = []

        # New chapter and new scene menus
        self.menubutton_chapters_scenes = builder.get_object("menubutton_chapters_scenes")
        self.mnu_chapters_scenes = builder.get_object("mnu_chapters_scenes")

        self.menubutton_chapters_scenes.configure(menu=self.mnu_chapters_scenes)
        self.mnu_chapters_scenes = builder.get_object("mnu_chapters_scenes")

        # Play image
        play_image = PhotoImage(data=Icons.PLAY_24_F.value)        

        self.menubutton_play = builder.get_object("menubutton_play")
        self.mnu_play = builder.get_object("mnu_play")
        
        self.menubutton_play.image = play_image
        self.menubutton_play.configure(menu=self.mnu_play,
                                       image=self.menubutton_play.image)

        # Setup bindings for Play Current Script and Play from Beginning menus
        self.mnu_play.entryconfigure(index=0, command=self.on_play_current_scene)
        self.mnu_play.entryconfigure(index=1, command=self.on_play_from_beginning)
        
        # Wizard button and image
        self.btn_wizard = builder.get_object("btn_wizard")
        wizard_image = PhotoImage(data=Icons.WAND_24_F.value)
        self.btn_wizard.image = wizard_image
        self.btn_wizard.configure(image=self.btn_wizard.image)

        # Statusbar label
        self.lbl_status = builder.get_object("lbl_status")

        # Setup bindings for New chapter and New scene menus
        self.mnu_chapters_scenes.entryconfigure(index=0, command=self.on_new_chapter_clicked)
        self.mnu_chapters_scenes.entryconfigure(index=1, command=self.on_new_scene_clicked)

        self.folder_image = PhotoImage(data=Icons.FOLDER_24_F.value)
        self.blue_dot_image = PhotoImage(data=Icons.BLUE_DOT_CUSTOM_OWN.value)

        # Get references to all the treeview widgets
        self.treeview_reusables = builder.get_object("treeview_reusables")     
        
        self.treeview_characters = builder.get_object("treeview_characters")
        self.treeview_backgrounds = builder.get_object("treeview_backgrounds")
        self.treeview_objects = builder.get_object("treeview_objects")
        self.treeview_font_sprites = builder.get_object("treeview_font_sprites")
        self.treeview_dialog_rectangle = builder.get_object("treeview_dialog_rectangle")

        self.treeview_sounds = builder.get_object("treeview_sounds")
        self.treeview_music = builder.get_object("treeview_music")

        for treeview_widget in (self.treeview_reusables,
                                self.treeview_characters,
                                self.treeview_backgrounds,
                                self.treeview_objects,
                                self.treeview_font_sprites,
                                self.treeview_dialog_rectangle,
                                self.treeview_sounds,
                                self.treeview_music):
            treeview_widget.tag_configure("folder_row", image=self.folder_image)
            treeview_widget.tag_configure("normal_row", image=self.blue_dot_image)

        self.treeview_scripts: ttk.Treeview
        self.treeview_scripts = builder.get_object("treeview_scripts")
        self.treeview_scripts.configure(style="LVNAuth.Treeview")
        self.treeview_scripts.tag_configure("startup_script", background="lightgreen", foreground="darkblue")

        self.treeview_reusables.configure(style="LVNAuth.Treeview")

        # The main text widget
        self.text_script: LVNAuthEditorWidget
        self.text_script = builder.get_object("text_script")
        self.text_script.bind("<<Modified>>", self._on_script_modified)
        self.text_script.bind("<KP_Enter>", self._on_num_pad_enter_key_pressed)
        self.text_script.configure(font=("tkDefaultText", 19, "normal"),
                                   wrap=tk.NONE)

        # Connect scrollbars to text widget.
        sb_horizontal_text = builder.get_object("sb_horizontal_text")
        sb_horizontal_text.configure(command=self.text_script.xview)
        self.text_script.configure(xscrollcommand=sb_horizontal_text.set)
        
        sb_vertical_text = builder.get_object("sb_vertical_text")
        sb_vertical_text.configure(command=self.text_script.yview)
        self.text_script.configure(yscrollcommand=sb_vertical_text.set)        

        Passer.toolbar = Toolbar(self)
        Passer.statusbar = StatusBar(self.lbl_status)
        Passer.editor = self
        Passer.chapter_scenes = ChapterSceneManager(self.treeview_scripts,
                                                    self.treeview_reusables,
                                                    self.blue_dot_image)
        Passer.file_manager = FileManager()

        self.treeview_reusables.bind("<<TreeviewSelect>>", Passer.chapter_scenes.on_reusables_treeview_item_selected)

        self.treeview_font_sprites.bind("<Double-1>", self.on_font_sprite_treeview_double_clicked)

        # Add Audio button
        add_audio_image = PhotoImage(data=Icons.AUDIO_16_F.value)
        self.btn_add_audio = builder.get_object("btn_add_audio")
        self.btn_add_audio.image = add_audio_image
        self.btn_add_audio.configure(image=self.btn_add_audio.image)
        
        # Add Image button
        add_image = PhotoImage(data=Icons.IMAGE_16_F.value)
        self.btn_add_image = builder.get_object("btn_add_image")
        self.btn_add_image.image = add_image
        self.btn_add_image.configure(image=self.btn_add_image.image)        

        # Remove Image button
        remove_image = PhotoImage(data=Icons.REMOVE_16_F.value)
        self.btn_remove_image = builder.get_object("btn_remove_image")
        self.btn_remove_image.image = remove_image
        self.btn_remove_image.configure(image=self.btn_remove_image.image)
        
        # Remove Audio button
        self.btn_remove_audio = builder.get_object("btn_remove_audio")
        self.btn_remove_audio.image = remove_image
        self.btn_remove_audio.configure(image=self.btn_remove_audio.image)
        
        # Remove Main Script button
        self.btn_remove_main_script = builder.get_object("btn_remove_main_script")
        self.btn_remove_main_script.image = remove_image
        self.btn_remove_main_script.configure(image=self.btn_remove_main_script.image)
        
        # Remove Reusable Script button
        self.btn_remove_script = builder.get_object("btn_remove_script")
        self.btn_remove_script.image = remove_image
        self.btn_remove_script.configure(image=self.btn_remove_script.image)        

        # Set as Startup button
        startup_image = PhotoImage(data=Icons.STARTUP_SCRIPT_16_F.value)
        self.btn_set_as_startup = builder.get_object("btn_set_as_startup")
        self.btn_set_as_startup.image = startup_image
        self.btn_set_as_startup.configure(image=self.btn_set_as_startup.image)  
        
        # New folder buttons
        self.btn_new_folder = builder.get_object("btn_new_folder")
        self.btn_new_folder_audio = builder.get_object("btn_new_folder_audio")
        self.btn_new_folder_reusable = builder.get_object("btn_new_folder_reusable")

        new_folder_image = PhotoImage(data=Icons.NEW_FOLDER_16_F.value)
        for btn_widget in (self.btn_new_folder, self.btn_new_folder_audio, self.btn_new_folder_reusable):
            btn_widget.image = new_folder_image
            btn_widget.configure(image=new_folder_image)

        # Save image
        save_image = PhotoImage(data=Icons.SAVE_24_F.value)

        # Binding for the 'Save Script' button
        self.btn_save_script = builder.get_object("btn_save_script")
        self.btn_save_script.image = save_image
        self.btn_save_script.configure(command=Passer.chapter_scenes.on_save_script_button_clicked,
                                       image=self.btn_save_script.image)

        # Colors image
        colors_image = PhotoImage(data=Icons.COLORS_24_F.value)

        # Binding for the 'Colors' button
        self.btn_colors = builder.get_object("btn_colors")
        self.btn_colors.image = colors_image
        self.btn_colors.configure(command=self.on_colors_button_clicked,
                                  image=self.btn_colors.image)

        # Cancel image
        cancel_image = PhotoImage(data=Icons.CANCEL_SCRIPT_24_F.value)
    
        self.btn_cancel_script = builder.get_object("btn_cancel_script")
        self.btn_cancel_script.image = cancel_image
        self.btn_cancel_script.configure(command=Passer.chapter_scenes.on_cancel_changes_button_clicked,
                                         image=self.btn_cancel_script.image)

        self.mainwindow.bind("<<SavedProjectSuccessfully>>", Passer.statusbar.show_saved_successfully)

        # Cause the main window to show it self so we can position the sash.
        # Without doing this, setting the position of the sash won't work as expected.
        self.mainwindow.update_idletasks()
        self.set_initial_sash_position()
        
        self._connect_scrollbars()
        
    def on_colors_button_clicked(self):
        """
        Show the color settings window.
        
        The 'Colors' button has been clicked.
        """
        edit_colors_window = EditColorsWindow(self.mainwindow,
                                              self.text_script.refresh_colors)
    
    def _on_num_pad_enter_key_pressed(self, event):
        """
        Insert a new line in the text widget, because the num pad
        enter key has been pressed.
        """
        self.text_script: LVNAuthEditorWidget
        self.text_script.insert("insert lineend", "\n")

    def _connect_scrollbars(self):
        """
        Connect the vertical scrollbars.
        """
        # Chapters and Scenes scrollbar
        self.sb_vertical_chapters_scenes =\
            self.builder.get_object("sb_vertical_chapters_scenes")
        
        self.sb_vertical_chapters_scenes.configure(command=self.treeview_scripts.yview)
        self.treeview_scripts.configure(yscrollcommand=self.sb_vertical_chapters_scenes.set)        
        
        
        # Reusables scrollbar
        self.sb_vertical_reusables =\
            self.builder.get_object("sb_vertical_reusables")
        
        self.sb_vertical_reusables.configure(command=self.treeview_reusables.yview)
        self.treeview_reusables.configure(yscrollcommand=self.sb_vertical_reusables.set)        
        
    
        # Characters
        self.sb_vertical_characters =\
            self.builder.get_object("sb_vertical_characters")
        
        self.sb_vertical_characters.configure(command=self.treeview_characters.yview)
        self.treeview_characters.configure(yscrollcommand=self.sb_vertical_characters.set)
        
        # Backgrounds
        self.sb_vertical_backgrounds =\
            self.builder.get_object("sb_vertical_backgrounds")
        
        self.sb_vertical_backgrounds.configure(command=self.treeview_backgrounds.yview)
        self.treeview_backgrounds.configure(yscrollcommand=self.sb_vertical_backgrounds.set)
                
        # Objects
        self.sb_vertical_objects =\
            self.builder.get_object("sb_vertical_objects")
        
        self.sb_vertical_objects.configure(command=self.treeview_objects.yview)
        self.treeview_objects.configure(yscrollcommand=self.sb_vertical_objects.set)
        
        # Font sprites
        self.sb_vertical_font_sprites =\
            self.builder.get_object("sb_vertical_font_sprites")
        
        self.sb_vertical_font_sprites.configure(command=self.treeview_font_sprites.yview)
        self.treeview_font_sprites.configure(yscrollcommand=self.sb_vertical_font_sprites.set)
                
        # Dialog rectangle
        self.sb_vertical_dialog_rectangle =\
            self.builder.get_object("sb_vertical_dialog_rectangle")
        
        self.sb_vertical_dialog_rectangle.configure(command=self.treeview_dialog_rectangle.yview)
        self.treeview_dialog_rectangle.configure(yscrollcommand=self.sb_vertical_dialog_rectangle.set)
        
        # Sounds
        self.sb_vertical_sounds =\
            self.builder.get_object("sb_vertical_sounds")
        
        self.sb_vertical_sounds.configure(command=self.treeview_sounds.yview)
        self.treeview_sounds.configure(yscrollcommand=self.sb_vertical_sounds.set)
                
        
        # Music
        self.sb_vertical_music =\
            self.builder.get_object("sb_vertical_music")
        
        self.sb_vertical_music.configure(command=self.treeview_music.yview)
        self.treeview_music.configure(yscrollcommand=self.sb_vertical_music.set)

    def _remove_chapter_or_scene_item(self):
        """
        Remove the selected chapter or scene script.
        """
        self.treeview_scripts: ttk.Treeview
        
        selected_item_iid = self.treeview_scripts.selection()
        if not selected_item_iid:
            return
        
        # Convert it from a single-item tuple to a string
        selected_item_iid = selected_item_iid[0]
        
        # Get the item details, specifically the text.
        selected_item_details = self.treeview_scripts.item(selected_item_iid)
        text = selected_item_details.get("text")        
        
        # Find out whether a chapter is being removed or a scene.
        chapter_iid = self.treeview_scripts.parent(selected_item_iid)
        
        chapter_text = None        
        scene_text = None

        if chapter_iid:
            # A scene is being deleted
            scene_text = text
            
            # Get the chapter name
            item_details = self.treeview_scripts.item(item=chapter_iid)
            chapter_text = item_details.get("text")
            
            delete_chapter = False
        else:
            # A chapter is being deleted
            chapter_iid = selected_item_iid
            chapter_text = text
            
            delete_chapter = True
            

        """
        Confirm deletion with the user.
        """
    
        if not delete_chapter:
            msg = "Confirm scene deletion:\n\n"\
            f"'{text}'\n\n"
            
        elif delete_chapter:
            msg = f"Confirm chapter deletion:\n\n'{text}'\n\n"\
                "This will also delete all the scenes in this chapter."            


        result = messagebox.askokcancel(parent=self.mainwindow, 
                                        title="Confirm",
                                        message=msg)
        if not result:
            return
        
        
        # ProjectSnapshot.chapters_and_scenes
        # Key (str): chapter name, Value: [ chapter script,  another dict {Key: scene name (str): Value script (str)} ]
        
        if delete_chapter:
            del ProjectSnapshot.chapters_and_scenes[chapter_text]
        
        else:
            # Deleting a scene in a chapter
            
            # Get the value of the chapter
            chapter_value = ProjectSnapshot.chapters_and_scenes[chapter_text]
            
            # Get just the scenes dictionary
            scenes_dict = chapter_value[1]
            
            # Delete the specific scene from the scenes dictionary
            del scenes_dict[scene_text]
            
            """
            ProjectSnapshot.chapters_and_scenes will get updated
            automatically with the changes of the deleted scene.
            
            There's no need for us to update it manually.
            """

        # If it's a folder, the sub-items will be removed from the treeview too.
        self.treeview_scripts.delete(selected_item_iid)
        
        # Get the active script name
        if isinstance(Passer.chapter_scenes.active_script, tuple):
            
            active_chapter_name = Passer.chapter_scenes.active_script[0]
            active_scene_name = Passer.chapter_scenes.active_script[1]
            
            reset_widgets = False
            
            if all(Passer.chapter_scenes.active_script):
                # A scene is the active script.
                if not delete_chapter:
                    if scene_text == active_scene_name:
                    
                        # The script that was deleted is the same as the one that's
                        # currently being edited, so clear the text widget.
                        reset_widgets = True
                        
            else:
                # A chapter is the active script, not a scene.
                if delete_chapter:
                    if chapter_text == active_chapter_name:
                        reset_widgets = True
                        
                        
            if reset_widgets:
                
                # There is no active script selected any more.
                Passer.chapter_scenes.active_script = None
                
                # Clear the text widget and disable the 'Save' and 'Cancel' buttons
                # to start fresh.        
                Passer.chapter_scenes.reset_script_widgets()                
                
        
        # So the user knows a save is needed.
        Passer.statusbar.show_save_dirty()              
            
    def _remove_reusable_script_item(self):
        """
        Remove the selected reusable script.
        
        If a folder is selected (tag: "folder_row", then remove
        all reusable scripts within that folder.)
        """
        

        selected_item_iid = self.treeview_reusables.selection()
        if not selected_item_iid:
            return
        
        # Find out whether a folder is being removed or a normal row.
        # folders will have the tag: "folder_row", while regular rows
        # will have the tag, "normal_row".
        selected_item_details = self.treeview_reusables.item(selected_item_iid)
        tags = selected_item_details.get("tags")
        text = selected_item_details.get("text")

        """
        Confirm deletion with the user.
        """
    
        if "normal_row" in tags:
            msg = f"Confirm deletion of:\n\n'{text}'"
            folder_deleted = False
            
        elif "folder_row" in tags:
            msg = "Confirm deletion of folder:\n\n"\
            f"'{text}'\n\n"\
            "This will also delete everything inside the folder."
            
            folder_deleted = True

        result = messagebox.askokcancel(parent=self.mainwindow, 
                                        title="Confirm",
                                        message=msg)
        if not result:
            return
        
        
        # Start with the iid that's currently selected.
        iids_to_remove = [selected_item_iid[0]]
        
        def get_children_iids(item):
            """
            Add the given child item iid to the remove-list
            and also add the children of the given item to the remove-list
            (if any)
            
            Arguments:
            
            - item: a child item iid
            """
            
            # Add the given child item iid to the remove-list.
            iids_to_remove.append(item)
            
            # Does the given item iid have any children? If so,
            # add them to the remove-list too.
            item_children = self.treeview_reusables.get_children(item)
            if item_children:
                for sub_item in item_children:
                    get_children_iids(sub_item)
        
        # Append a list of iids to remove
        for item in self.treeview_reusables.get_children(selected_item_iid):
            get_children_iids(item=item)
            
        # Go through the list of iids to remove and get their reusable 
        for remove_iid in iids_to_remove:
            
            # Example:
            # {'text': 'go right animation', 'image': '', 'values': '', 'open': 0, 'tags': ['normal_row']}
            item_details = self.treeview_reusables.item(remove_iid)
            item_text = item_details.get("text")
            tag = item_details.get("tags")
            
            # Folders are not stored in dictionaries, they're only stored and displayed
            # in treeview widgets, so if we're iterating over a folder, skip it,
            # because there is no folder to delete in the reusables dictionary.
            if "folder_row" in tag:
                continue                
            
            # Delete the reusable script from the reusables dictionary.
            if item_text in ProjectSnapshot.reusables:
                del ProjectSnapshot.reusables[item_text]

        # Delete the selected item from the reusables dictionary.
        # If it's a folder, the sub-items will be removed from the treeview too.
        self.treeview_reusables.delete(selected_item_iid)
        
        # If the last selected reusable item iid no longer exists,
        # clear the record of the last selected item reusable script
        # (which would have been used for changing its item row icon
        # from edit-mode to a blue dot).
        if self.treeview_reusables.last_selected_item_iid:
            if self.treeview_reusables.last_selected_item_iid in \
               iids_to_remove:
                
                # The reusable item row no longer exists, so
                # remove the reference to it.
                self.treeview_reusables.last_selected_item_iid = None
    
    
        # Get the reusable script name
        active_script_name = Passer.chapter_scenes.active_script
        
        # Clear the script in the text widget if the single-removed script
        # was the same as the one that's being actively edited.        
        if not folder_deleted and text == active_script_name:
            
            # The script that was deleted is the same as the one that's
            # currently being edited, so clear the text widget.
            
            # There is no active script selected any more.
            Passer.chapter_scenes.active_script = None
            
            # Clear the text widget and disable the 'Save' and 'Cancel' buttons
            # to start fresh.        
            Passer.chapter_scenes.reset_script_widgets()
        
        # So the user knows a save is needed.
        Passer.statusbar.show_save_dirty()        
                
    def on_remove_script_button_clicked(self):
        self._remove_chapter_or_scene_item()
                
    def on_remove_reusable_script_button_clicked(self):
        self._remove_reusable_script_item()
        
    def hide_pencil_icon(self, hide_icon_in_reusables_treeview: bool):
        """
        Remove the pencil icon from either the main scripts treeview widget
        or the reusable scripts treeview widget.

        Purpose: when a script is selected in the reusables scripts section, none of the
                 main scripts should be shown as selected.

                 Similarly, when a main script gets selected, none of the reusable scripts
                 should be shown as selected.

                 This method is used to prevent the 'other' treeview widget
                 from showing a pencil icon.

        :param hide_icon_in_reusables_treeview: used for indicating whether we should hide the pencil icon
                                                in the reusables treeview (True)
                                                or the main scripts treeview (False).

        :return: None
        """
        if hide_icon_in_reusables_treeview:
            treeview_widget = self.treeview_reusables
            selected_item = self.treeview_reusables.last_selected_item_iid
        else:
            treeview_widget = self.treeview_scripts
            selected_item = treeview_widget.selection()
            if selected_item:
                selected_item = selected_item[0]

        if not selected_item:
            return
        

        treeview_widget.item(item=selected_item,
                             image="")
        #
        # # If we're not hiding the pencil icon in the reusables treeview widget,
        # # then that means the user has selected a reusables script, so set the active script to None.
        # if not hide_icon_in_reusables_treeview:
        #     # The user has selected a reusables script, so set the active script to None
        #     # because we can't directly play a reusable script from the editor.
        #     Passer.chapter_scenes.active_script = None

    def set_initial_sash_position(self):
        """
        Set the new sash position (the separator between the text editor and the notebook widgets on the left).

        Purpose: causes all the notebook tabs to display their text better.
        :return: None
        """
        pane4 = self.builder.get_object("pane4")
        pane4.sashpos(index=0, newpos=450)

    def on_set_as_startup_clicked(self):
        """
        Set the startup script, which will be the first script to run in the visual novel.

        Set the scene's treeview item to a different colour, to show that it's the startup script.

        :return: None
        """

        # Make sure the selected item in the treeview widget has a parent, because only scenes have parents.
        selected_item = self.treeview_scripts.focus()

        self.set_as_startup_script(selected_item)

    def set_as_startup_script(self, item_iid: str):
        """
        Change the colour of the selected item in the scripts treeview widget
        to show that the selected scene is the startup script.
        :param item_iid:
        :return: None
        """

        item_parent = self.treeview_scripts.parent(item_iid)
        if not item_parent:
            messagebox.showwarning(parent=self.mainwindow, 
                                   title="Not a Scene",
                                   message="Only scenes can be set as a startup script.")
            return

        # Make sure none of the items have a 'startup_script' tag.
        for root_item in self.treeview_scripts.get_children():

            # Get the children of the current root item
            item_children = self.treeview_scripts.get_children(root_item)

            for c_item in item_children:
                item_tags = list(self.treeview_scripts.item(c_item).get("tags"))
                if "startup_script" in item_tags:
                    item_tags.remove("startup_script")
                    self.treeview_scripts.item(item=c_item, tags=item_tags)

        # Now set the selected item to contain a tag that shows it's the startup script.
        item_tags = list(self.treeview_scripts.item(item_iid).get("tags"))
        item_tags.append("startup_script")
        self.treeview_scripts.item(item=item_iid, tags=item_tags)

    def get_startup_chapter_and_scene(self) -> Tuple | None:
        """
        Return the (chapter name, scene name) that is set as a default or None if none is set.
        :return: Tuple (chapter name, scene name) both as strings.
        """

        startup_scene_item_iid = self.get_startup_scene_item_iid()
        if startup_scene_item_iid is None:
            return

        # Get the scene name (from the item iid)
        scene_name = self.treeview_scripts.item(startup_scene_item_iid).get("text")

        # Get the parent name (chapter name)
        parent_iid = self.treeview_scripts.parent(startup_scene_item_iid)
        if not parent_iid:
            return

        chapter_name = self.treeview_scripts.item(parent_iid).get("text")

        return chapter_name, scene_name

    def get_startup_scene_item_iid(self) -> str:
        """
        Get the treeview item iid of the startup scene.

        We use this when saving a project file (.lvnap) and also when playing the script
        from the beginning.
        :return: item iid str
        """

        # Look for the sub-item that has a tag of 'startup_script'.

        # Iterate through the root items first (the chapters)
        for root_item in self.treeview_scripts.get_children():

            # The startup script will be a descendant of a chapter item.
            # Iterate through the parent's items.
            for c_item in self.treeview_scripts.get_children(root_item):
                item_details = self.treeview_scripts.item(c_item)
                item_tags = item_details.get("tags")

                if "startup_script" in item_tags:
                    return c_item

    def on_font_sprite_treeview_double_clicked(self, event):
        """
        An item in the font sprite treeview has been double-clicked.
        """
        selected_items = self.treeview_font_sprites.selection()

        if not selected_items:
            return
        else:
            item_iid = selected_items[0]
            item_text = self.treeview_font_sprites.item(item_iid, "text")

            file_name = ProjectSnapshot.font_sprites.get(item_text)
            if not file_name:
                return
            
            font_properties = ProjectSnapshot.font_sprite_properties.get\
                (item_text)
            if not font_properties:
                return

            font_window = FontSpriteWindow(master=self.mainwindow,
                                           font_sprite_name=item_text,
                                           font_file_name=file_name,
                                           font_sprite_details=font_properties)

    def on_play_current_scene(self):
        """
        Play the active scene script.

        Only scene scripts can be played directly.
        Chapter scripts and reusable scripts cannot be played directly.
        
        We only include binary files (images, audio) that have a <load-..>
        script for them in either a chapter script or scene script.
        For example <load_character: rave_happy, Rave>

        This method checks to make sure that the active script is a scene script.
        """

        active_script = Passer.chapter_scenes.active_script
        message = None

        if not active_script:
            messagebox.showwarning(parent=self.mainwindow,
                                   title="No Script",
                                   message="Select a scene script to play.")
            return

        # We can't play a reusable script
        elif isinstance(active_script, str):
            message = "Reusable scripts cannot be played directly. They need to be called from main scripts."
            messagebox.showwarning(parent=self.mainwindow,
                                   title="Reusable Script",
                                   message=message)
            return

        active_chapter_name, active_scene_name = active_script

        if not active_scene_name:
            message = "Only scene scripts can be played directly.\nSelect a scene script."
            messagebox.showwarning(parent=self.mainwindow,
                                   title="Scene Script",
                                   message=message)
            return

        # Make sure there is an active scene selected.
        
        if active_chapter_name and active_scene_name:

            ## Include only the active chapter script and scene script
            #active_script = {active_chapter_name: ProjectSnapshot.chapters_and_scenes[active_chapter_name]}

            # For playing/testing the story
            draft_path = SnapHandler.get_draft_path()
            compile_path = Path(draft_path)              

            compiler = StoryCompiler(compile_part=CompilePart.CURRENT_SCENE,
                                     startup_scene_name=active_scene_name,
                                     startup_chapter_name=active_chapter_name,
                                     save_file_path=compile_path,
                                     story_reusables_dict=ProjectSnapshot.reusables)
            success = compiler.compile(compile_mode=CompileMode.DRAFT)
            if not success:
                return

            # Play the .lvna file
            EditorMainApp.play_lvna_file(lvna_file_path=compile_path,
                                         error_window_master=self.mainwindow)
            
    @staticmethod
    def play_lvna_file(lvna_file_path: Path,
                       error_window_master: tk.Toplevel = None, 
                       show_launch_window: bool = False,
                       regular_play_mode: bool = False):
        """
        Run a compiled .lvna file in a player window.
        
        After the player window closes, delete the draft .lvna file.
        
        Purpose: after a draft .lvna file (draft.lvna) has been compiled
        (ie: play current scene or play from beginning),
        then this method is called to play the visual novel.
        
        This method is also used for playing finished/non-draft .lvna files.
        
        Arguments:
        
        - lvna_file_path: a Path object to the .lvna file to play.
        
        - error_window_master: the parent window of the error message window,
        which will either be the editor window or the startup window.
        
        - show_launch_window: whether to show a list of chapters and scenes
        in the player, allowing the viewer to choose what to play.
        This is True for 'play all' and False for 'play current scene'.
        
        - regular_play_mode: True if the visual novel is being played from
        the startup window (not in the editor). We need to know so that
        we can re-show the startup window if an error occurs.
        """

        player_script_file: Path
        # Get the path to main.py (the player Python script file.)
        player_script_file = SnapHandler.get_lvnauth_player_python_file()
        
        # Get the path to the Python interpreter that's being used now.
        # This is the recommended way when using subprocess.run()
        python_executable = sys.executable

        # subprocess.Popen(["python3", str(player_script_file), "--file", str(compile_path)],
                         # text=True)
        
        result = subprocess.run([python_executable,
                        player_script_file,
                        "--file",
                        lvna_file_path,
                        "--show-launch",
                        str(show_launch_window)],
                       text=True,
                       capture_output=True)
        
        # A return code of 0 means a success
        # 1 means an error occurred.
        if result.returncode != 0:
            # An error occurred while playing the visual novel.
            
            # Show the Python exception to the user in a new window
            # that has a text widget.
            error_window = PlayErrorWindow(error_window_master)
            error_window.show_text(result.stderr)
            
            # An error occurred while attempting to play the visual novel,
            # so re-show the startup window.
            if regular_play_mode:
                error_window_master.deiconify()
            
            # Make the error window on top of the other LVNAuth windows.
            # and wait for the error window to close.
            error_window.mainwindow.transient(error_window_master)
            error_window.mainwindow.update_idletasks()
            error_window.mainwindow.grab_set()
            error_window.mainwindow.wait_window(error_window.mainwindow)            
            
            


        ## Delete the compiled .lvna file
        ## because the player window has closed.
        #lvna_file_path.unlink(missing_ok=True)    

    def on_play_from_beginning(self):
        """
        Compile the entire visual novel by including files that are
        requested to be loaded in the chapter scripts and/or the scene scripts.
        
        We only include binary files (images, audio) that have a <load-..>
        script for them in either a chapter script or scene script.
        For example <load_character: rave_happy, Rave>
        
        Include all chapter scripts and scene scripts
        in the compiled .lvna file.
        
        Then play the startup scene script.

        Note: only scene scripts can be played directly.
        Chapter scripts and reusable scripts cannot be played directly.
        """

        # For playing/testing the story
        draft_path = SnapHandler.get_draft_path()
        compile_path = Path(draft_path)     

        compile_result = self.compile(lvna_full_path=compile_path,
                                      draft_mode=True)
        
        if not compile_result:
            return

        # Play the .lvna file
        EditorMainApp.play_lvna_file(lvna_file_path=compile_path,
                                     error_window_master=self.mainwindow, 
                                     show_launch_window=True)
        
    def save_final_lvna(self):
        
        file_types = [("Visual Novel", ".lvna")]
        save_full_path = filedialog.asksaveasfilename(parent=self.mainwindow,
                                                      filetypes=file_types,
                                                      title="Compile to File")
        
        if not save_full_path:
            return
        
        compile_result = self.compile(lvna_full_path=save_full_path,
                                      draft_mode=False)  
        
        if compile_result:
            messagebox.showinfo(parent=self.mainwindow, 
                                title="Finished",
                                message="Your visual novel has been compiled successfully.")
        else:
            messagebox.showerror(parent=self.mainwindow, 
                                 title="Error",
                                 message="An error occurred when attempting to compile your visual novel.")            

    def compile(self, lvna_full_path: [str, Path], draft_mode: bool):
        """
        Compile a 'play from beginning' .lvna file.
        
        This method can be used for compiling a draft or a release version.
        
        Arguments:
        
        - lvna_full_path: the path to the .lvna file to be saved.
        
        - draft_mode: True if it's being played from within the editor
        or False if the user wants to save a final .lvna file, ready to be
        shared with others.
        """
        
        startup_info = self.get_startup_chapter_and_scene()
        if not startup_info:
            messagebox.showerror(parent=self.mainwindow, 
                                 title="No Startup Scene",
                                 message="Please choose a scene that should start first.")
            return

        startup_chapter_name = startup_info[0]
        startup_scene_name = startup_info[1]
        
        if draft_mode:
            mode = CompileMode.DRAFT
        else:
            mode = CompileMode.FINAL

        compiler = StoryCompiler(compile_part=CompilePart.ALL_SCENES,
                                 startup_scene_name=startup_scene_name,
                                 startup_chapter_name=startup_chapter_name,
                                 save_file_path=lvna_full_path,
                                 story_reusables_dict=ProjectSnapshot.reusables)
        success = compiler.compile(compile_mode=mode)
        return success

    def on_new_folder_button_clicked(self, widget_id: str):
        """
        The 'Create new folder' button has been clicked,
        but it could be from one of many buttons.

        Arguments:
        - widget_id: (str) This tells us which widget name was clicked,
        so we know the section.
        
        return: None
        """

        if widget_id == "btn_new_folder":
            section_chosen = SectionChosen.IMAGES
        elif widget_id == "btn_new_folder_audio":
            section_chosen = SectionChosen.AUDIO
        elif widget_id == "btn_new_folder_reusable":
            section_chosen = SectionChosen.REUSABLES

        Passer.file_manager.on_create_new_folder_button_clicked(section_chosen=section_chosen)

    def add_to_delete_file_upon_close(self, full_path_to_file: Path):
        """
        Add a Path object to a list that will be iterate over when the application closes.
        The files in this list will be deleted upon the application closing.

        Purpose: when adding a new image to the project, if the user doesn't save
                 the project when the application closes, then we need to cleanup/delete the
                 images that were added to the project's images folder.

        This method is called when adding new images to the project, before the project has been saved.
        
        Arguments:
        - full_path_to_file: Path object to a full image path
        """
        self.delete_files_upon_exit.append(full_path_to_file)

    def clear_delete_files_upon_close(self):
        """
        Clear the list that is used to delete images upon the application closing
        when the project hasn't been saved.

        This method is called when the project has been saved.
        """
        self.delete_files_upon_exit.clear()

    def on_window_close(self):
        """
        Delete images that haven't been saved in the project
        and close the editor window and startup window.
        """

        # Delete images that haven't been saved in the project.
        for file_path in self.delete_files_upon_exit:
            if file_path.exists():
                if file_path.is_file():
                    file_path.unlink()

        # Close the editor window
        self.mainwindow.destroy()
        
        # Close the startup window
        self.master.destroy()

    @staticmethod
    def set_dirty():
        Passer.chapter_scenes.enable_save_button()
        Passer.chapter_scenes.enable_cancel_changes_button()
        Passer.statusbar.show_save_dirty()

    def set_clean(self):
        Passer.chapter_scenes.disable_save_button()
        Passer.statusbar.show_saved_successfully()

        # Reset 'changed' flag.
        self.text_script.edit_modified(False)

    def is_dirty(self):
        """
        Return whether the text widget needs saving or not.
        :return: bool
        """
        return self.text_script.edit_modified()

    def _on_script_modified(self, event):
        """
        The text widget has been modified.
        :return:
        """
        if self.text_script.edit_modified():
            print("Modified")
            self.set_dirty()

    def _check_project_folder_exists(self):
        """
        Make sure a project folder is known. If not, prompt the user to select it.
        :return: project folder (str)
        """
        if not ProjectSnapshot.project_path:
            project_folder_window = ProjectFolderWindow(master=self.mainwindow)

        return ProjectSnapshot.project_path

    def on_add_file_clicked(self, widget_id: str):

        if not self._check_project_folder_exists():
            return

        if widget_id == "btn_add_image":
            section_chosen = SectionChosen.IMAGES
        elif widget_id == "btn_add_audio":
            section_chosen = SectionChosen.AUDIO

        Passer.file_manager.browse_for_files(section_chosen=section_chosen)

    def on_remove_dialog_box_clicked(self, widget_id: str):

        if widget_id == "btn_remove_image":
            section = SectionChosen.IMAGES
        elif widget_id == "btn_remove_audio":
            section = SectionChosen.AUDIO

        Passer.file_manager.remove_selected_file(section=section)

    def on_new_reusable_script_clicked(self):
        Passer.chapter_scenes.create_new_reusable_script()

    def on_new_chapter_clicked(self):
        Passer.chapter_scenes.create_new_chapter()

    def on_new_scene_clicked(self):
        Passer.chapter_scenes.create_new_scene()

    def on_wizard_button_clicked(self):
        """
        Open the wizard toplevel window.
        """
        if not Passer.chapter_scenes.active_script:
            messagebox.showwarning(parent=self.mainwindow, 
                                   title="Select a script",
                                   message="Open a chapter/scene or reusable script before using commands.")
            return
        
        wizard = WizardWindow(self.mainwindow)

        wizard.mainwindow.transient(self.mainwindow)
        wizard.mainwindow.update_idletasks()
        wizard.mainwindow.grab_set()
        wizard.mainwindow.wait_window(wizard.mainwindow)
        
        # The wizard window was cancelled? Return.
        if not wizard.generated_command:
            return
        
        self.insert_command(wizard.generated_command)

    def insert_command(self, command: str):
        """
        Insert the text in the command variable.
        
        If the cursor in the textbox is on a new line, insert the
        command right there.
        
        If the cursor in the textbox is on an existing line, insert
        the command on a new line.
        """

        # Get the text on the current line the cursor is on.
        current_line_text =\
            self.text_script.get("insert linestart", "insert lineend")

        # If there is any text, add the command on a new line.
        if current_line_text:
            possible_new_line = "\n"
            
            # We need to move the insert cursor to the next line
            # so the colorization gets done on the newly added line.
            line_number = self.text_script.get_current_line_number()
            line_number += 1

        else:
            possible_new_line = ""

        # Insert the command into the text widget.
        self.text_script.insert("insert lineend", possible_new_line + command)
        
        # Move the insert cursor to the new line?
        if possible_new_line:
            # So that colorization can occur on the newly added line.
            self.text_script.mark_set("insert", f"{line_number}.0")
            
        # Colorize the modified line.
        self.text_script.reevaluate_current_line()

    def on_debug_button_clicked(self):
        
        current = self.text_script.get("insert linestart", "insert lineend")
        if current:
            add_new_line = "\n"
        else:
            add_new_line = ""

        self.text_script.insert("insert lineend", add_new_line + "ok")
        self.text_script.reevaluate_entire_contents()

    def run(self):
        self.mainwindow.mainloop()


class ChapterSceneManager:
    """
    Handles creating new chapters and scenes.

    It puts the chapter/scene in the treeview widget
    and also populates the appropriate dictionary that contains the chapter scripts and scene scripts.

    Chapter scripts are normal scripts that are read only once for the first-played scene
    in that chapter.
    
    Arguments:
    
    - treeview_widget: main chapters and scenes treeview widget
    
    - treeview_reusables: reusable scripts treeview widget
    
    - blue_dot_image: image of a regular blue dot. We need this
    to restore the blue dot in the reusables treeview,
    after a reusable script is no longer being edited.
    """
    def __init__(self,
                 treeview_widget,
                 treeview_reusables, 
                 blue_dot_image):

        # Main scripts treeview widget
        self.treeview_widget: ttk.Treeview = treeview_widget

        # Reusables treeview widget
        self.treeview_reusables: ttk.Treeview = treeview_reusables
              
        # Used for restoring a reusable script treeview row's blue dot icon.
        # when selection is moved away from a reusable script.
        self.treeview_reusables.last_selected_item_iid = None             
        
        # If a reusable script is no longer being edited,
        # the item needs re-show a blue image, so we use this image to restore
        # the blue dot image.
        self.blue_dot_image = blue_dot_image

        self.lbl_title = Passer.editor.builder.get_object("lbl_title")
        self.btn_save_script = Passer.editor.builder.get_object("btn_save_script")
        self.btn_cancel_script = Passer.editor.builder.get_object("btn_cancel_script")

        # This will hold the name of the active script.
        # It will be a tuple (chapter name, scene name)
        # This is used for knowing which script to play when playing the active script.
        self.active_script = None

        self.treeview_widget.bind("<<TreeviewSelect>>", self.on_treeview_item_selected)
        
        # Disable the 'Save script' and 'Cancel' buttons on startup.
        self.reset_script_widgets()

    def reset_script_widgets(self):
        """
        Clear the text widget and disable the 'Save' and 'Cancel' buttons
        to start fresh.
        
        Purpose: used when starting the application and also when a script
        is deleted from the treeview widget.
        """
        
        # Initialize/reset the 'Save Script' and 'Cancel Changes' buttons 
        # so they're disabled
        self.btn_save_script.state(["disabled"])
        self.btn_cancel_script.state(["disabled"])
        
        # Clear the active chapter/scene title label.
        self.lbl_title.configure(text="")
        
        # Delete any text that's in the text widget.
        Passer.editor.text_script.delete("1.0", "end")
        
        # Set flag to indiciate the text widget has not been modified.
        Passer.editor.text_script.edit_modified(False)
        

    def show_reusable_script(self, reusable_script_name: str):
        """
        Show the reusable script of the specified name (case-sensitive)
        in the text widget.

        Show the script in the main text widget.

        :param reusable_script_name:
        :return: None
        """

        if not reusable_script_name:
            return

        script = ProjectSnapshot.get_reusable_script(script_name=reusable_script_name)

        self.lbl_title.configure(text=f"{reusable_script_name} [Reusable Script]")

        Passer.editor.text_script.delete("1.0", "end")
        Passer.editor.text_script.insert("1.0", script)
        Passer.editor.text_script.reevaluate_entire_contents()
        Passer.editor.text_script.edit_modified(False)

    def on_reusables_treeview_item_selected(self, event):
        """
        A script or scene has been selected (or unselected).
        Get the item iid from the treeview.
        """

        if Passer.editor.is_dirty():
            return

        selected_item = self.treeview_reusables.focus()
        last_selected_item = self.treeview_reusables.last_selected_item_iid

        # No selection? return
        if not selected_item:
            return
        
        # Same selection as the one that's currently selected? Return
        elif selected_item == last_selected_item:
            return

        item_details = self.treeview_reusables.item(selected_item)
        selected_item_text = item_details.get("text")
        if not selected_item_text:
            return

        # Is the selected row a folder? return
        tags = item_details.get("tags")
        if "folder_row" in tags:
            return

        # Make sure the main text widget is enabled because
        # we have a script selected now.
        Passer.editor.text_script.configure(state="normal")

        # Show the script in the text widget.
        self.show_reusable_script(reusable_script_name=selected_item_text)

        edit_icon = PhotoImage(data=Icons.EDIT_24_F.value)

        # The selected reusable script should have a pencil icon
        self.treeview_reusables.item(item=selected_item, 
                                     image=edit_icon)
        

        # The image field will have a reference to the image so that it doesn't
        # get garbage collected.
        #
        # Any previously selected item will have its image
        # garbage collected as soon as we set this image variable below.
        self.treeview_reusables.image = edit_icon
        
        # Hide the pencil icon in the main scripts treeview widget (if any).
        Passer.editor.hide_pencil_icon(hide_icon_in_reusables_treeview=False)

        # This is used for knowing which script to play 
        # when playing the active script.
        # Format: (current chapter, current scene)
        # or
        # just the reusable script name, if it's a reusable script.
        self.active_script = selected_item_text
        
        # Change the last-selected item's icon from a pencil/edit icon
        # to a blue dot.
        if self.treeview_reusables.last_selected_item_iid:
            self.treeview_reusables.item(item=self.treeview_reusables.last_selected_item_iid,
                                         image=self.blue_dot_image)
            
        # Record the current selected item iid, so we can change the row's
        # icon to a blue dot once the user clicks away from it.
        self.treeview_reusables.last_selected_item_iid = selected_item

    def enable_cancel_changes_button(self):
        """
        Enable the 'Cancel Changes' button.

        This is called when changes are made to the main text widget.

        :return: None
        """
        self.btn_cancel_script.state(["!disabled"])

    def enable_save_button(self):
        """
        Enable the 'Save Script' button.

        This is called when changes are made to the main text widget.

        :return: None
        """
        self.btn_save_script.state(["!disabled"])

    def disable_save_button(self):
        """
        Disable the 'Save Script' button.

        This is called after the project has been saved.

        :return: None
        """
        self.btn_save_script.state(["disabled"])

    def _disable_cancel_changes_button(self):
        """
        Disable the 'Cancel Changes' button.

        This is called after the project has been saved.

        :return: None
        """
        self.btn_cancel_script.state(["disabled"])

    def on_cancel_changes_button_clicked(self):
        """
        Load the last saved content of the current chapter or scene.

        The user does not want to save the changes of the current script.
        :return: None
        """

        # Is the active script a reusable script? (we'll know if it's a string, and not a tuple)
        if isinstance(self.active_script, str):
            # The active script is a reusable script.

            reusable_script_name = self.active_script
            subject = reusable_script_name

            current_script = ProjectSnapshot.reusables.get(reusable_script_name)
        else:
            # The active script is a chapter or scene.

            current_chapter, current_scene = self.active_script

            if not current_scene:
                current_script = ProjectSnapshot.get_chapter_script(current_chapter)
                subject = current_chapter
            else:
                current_script = ProjectSnapshot.get_scene_script(current_chapter, current_scene)
                subject = current_scene

        msgbox_result = messagebox.askyesno(parent=self.lbl_title.winfo_toplevel(), 
                                            title="Cancel Changes?",
                                            message=f"Cancel changes and load the last save for '{subject}'?")

        if not msgbox_result:
            return

        Passer.editor.text_script.delete("1.0", "end")
        Passer.editor.text_script.insert("1.0", current_script)
        Passer.editor.text_script.reevaluate_entire_contents()

        self._disable_cancel_changes_button()
        self.disable_save_button()

        # Reset 'changed' flag.
        Passer.editor.text_script.edit_modified(False)

    def on_save_script_button_clicked(self):
        """
        Save the current text in the text widget to the chapter/scene dictionary.
        :return: None
        """
        self.save_current_script()

    def save_current_script(self):
        """
        Save the current text in the text widget to the chapter/scene dictionary.
        :return: None
        """

        if not self.active_script:
            return
        elif not Passer.editor.is_dirty():
            return

        # Get the contents of the text widget.
        content = Passer.editor.text_script.get("1.0", "end-1c")

        reusable_script_name = None
        current_chapter = None
        current_scene = None

        # If it's a string, then the active script is a reusable script.
        # If it's a tuple, then the active script is a main script.
        if isinstance(self.active_script, str):
            # The active script is a reusable script.

            reusable_script_name = self.active_script

            ProjectSnapshot.update_reusable_script(script_name=reusable_script_name,
                                                   new_content=content)

        else:
            # The active script is a main script.

            current_chapter = self.active_script[0]
            current_scene = self.active_script[1]

            if not current_scene:
                ProjectSnapshot.update_chapter_script(chapter_name=current_chapter,
                                                      new_content=content)
            else:
                ProjectSnapshot.update_scene_script(chapter_name=current_chapter,
                                                    scene_name=current_scene,
                                                    new_content=content)

        # Reset 'changed' flag.
        Passer.editor.text_script.edit_modified(False)

        # The 'Save Script' has been clicked, so now disable it.
        self.disable_save_button()

        # Disable the 'Cancel Changes' button, because it is now saved.
        self._disable_cancel_changes_button()

    def on_treeview_item_selected(self, event):
        """
        A chapter or scene has been selected (or unselected).
        Get the item iid from the treeview.
        """

        if Passer.editor.is_dirty():
            return

        selected_item = self.treeview_widget.focus()

        # No selection? return
        if not selected_item:
            return

        selected_item_text = self.treeview_widget.item(selected_item).get("text")
        if not selected_item_text:
            return

        # Make sure the main text widget is enabled because
        # we have a script selected now.
        Passer.editor.text_script.configure(state="normal")

        # If the selected item has a parent, then the selection is a scene.
        parent_iid = self.treeview_widget.parent(selected_item)
        if not parent_iid:
            # The selection is a chapter, because it has no parent.
            self.show_chapter_script(selected_item_text)
        else:
            # The selection is a scene
            parent_text = self.treeview_widget.item(parent_iid).get("text")
            self.show_scene_script(chapter_name=parent_text,
                                   scene_name=selected_item_text)

        edit_icon = PhotoImage(data=Icons.EDIT_24_F.value)

        # Show the selected item in the treeview as selected.
        self.treeview_widget.item(item=selected_item,
                                  image=edit_icon)

        # The image field will have a reference to the image so that it doesn't
        # get garbage collected.
        #
        # Any previously selected item will have its image
        # garbage collected as soon as we set this image variable below.
        self.treeview_widget.image = edit_icon

        # Hide the pencil icon in the reusable scripts treeview widget (if any).
        Passer.editor.hide_pencil_icon(hide_icon_in_reusables_treeview=True)
        
        # Reset the last-selected reusables row, because
        # a reusables item is no longer selected.
        self.treeview_reusables.last_selected_item_iid = None

    def create_new_reusable_script(self, prefill_script_name=None):
        """
        Add a new reusable script to the treeview widget and the reusable scripts dictionary.

        This method will check for duplicate script names.

        Arguments:
        - param prefill_script_name: if duplicate script name (used if this method is called again
                                                              when there's a duplicate)
        """

        input_window = InputStringWindow(master=self.treeview_reusables.winfo_toplevel(),
                                         title="New Reusable Script",
                                         msg="Type a new script name below:",
                                         prefill_entry_text=prefill_script_name)

        if not input_window.user_input:
            return

        user_input_lcase = input_window.user_input.lower()

        # Commas should not be allowed in reusable script names
        # because arguments are separated with commas in the <call> command.
        if "," in user_input_lcase:
            messagebox.showwarning(parent=self.treeview_widget.winfo_toplevel(),
                                   title="Commas not allowed",
                                   message="Reusable script names cannot contain commas.")
            self.create_new_reusable_script(prefill_script_name=input_window.user_input)
            return

        for reusable_script_name in ProjectSnapshot.reusables:
            reusable_script_name = reusable_script_name.lower()

            if user_input_lcase == reusable_script_name:
                messagebox.showwarning(parent=self.treeview_widget.winfo_toplevel(), 
                                       title="Already Exists",
                                       message=f"The reusable script name, {input_window.user_input}, already exists.")
                self.create_new_reusable_script(prefill_script_name=input_window.user_input)
                return

        # Get the selected item so we know which folder to put the image under.
        selected_item = self.treeview_reusables.focus()

        # If the selected item is not a folder, get the parent item
        # (the parent item will be a folder or root),
        # so the newly added file gets added to that folder.
        tag = self.treeview_reusables.item(selected_item).get("tags")
        if "folder_row" not in tag:
            selected_item = self.treeview_reusables.parent(selected_item)

        item_iid = self.treeview_reusables.insert(index="end",
                                                  parent=selected_item,
                                                  tags=("normal_row",),
                                                  text=input_window.user_input)

        # Add to reusables dictionary, with empty content.
        ProjectSnapshot.update_reusable_script(script_name=input_window.user_input,
                                               new_content="")

    def create_new_chapter(self, prefill_chapter_name=None):
        """
        Create a new chapter if the name doesn't already exist (case-insensitive search)

        Where it needs to check for duplicates is the dictionary that contains chapter names.

        :return: None
        """

        input_window = InputStringWindow(master=self.treeview_widget.winfo_toplevel(),
                                         title="New Chapter",
                                         msg="Type a new chapter name below:",
                                         prefill_entry_text=prefill_chapter_name)

        if not input_window.user_input:
            return

        user_input_lcase = input_window.user_input.lower()

        # Make sure the chapter name doesn't already exist (case-insensitive search)
        for chapter_name in ProjectSnapshot.chapters_and_scenes:
            if user_input_lcase == chapter_name.lower():
                messagebox.showwarning(parent=self.lbl_title.winfo_toplevel(), 
                                       title="Chapter Name Already Exists",
                                       message="That chapter name already exists.\nPlease type a different name.")
                self.create_new_chapter(prefill_chapter_name=input_window.user_input)
                return

        # Add to dictionary
        # Key (str): chapter name, Value: [ chapter script,  another dict {Key: scene name (str): Value script (str)} ]
        ProjectSnapshot.chapters_and_scenes[input_window.user_input] = ["", {}]

        # Add the chapter to the treeview widget.
        self.treeview_widget.insert(parent="",
                                    index="end",
                                    text=input_window.user_input)


    def create_new_scene(self, prefill_scene_name=None):
        """
        Create a new scene if the name doesn't already exist in the chapter (case-insensitive search)

        Where it needs to check for duplicates is the dictionary that contains chapter names and scene names.

        :return: None
        """

        selected_item = self.treeview_widget.focus()
        if not selected_item:
            messagebox.showwarning(parent=self.treeview_widget.winfo_toplevel(), 
                                   title="Select a Chapter",
                                   message="Select a chapter to create a scene in.")
            return

        # We need the parent name, because that will contain the chapter
        # that the scene will be created in.
        parent_item = self.treeview_widget.parent(selected_item)

        if not parent_item:
            # Create a scene in the current selected item.
            chapter_item = selected_item
        else:
            # Create a scene in the selected item's parent.
            chapter_item = parent_item

        # Use the selected text as the chapter name
        chapter_name = self.treeview_widget.item(chapter_item).get("text")

        input_window = InputStringWindow(master=self.treeview_widget.winfo_toplevel(),
                                         title="New Scene",
                                         msg="Type a new scene name below.",
                                         prefill_entry_text=prefill_scene_name)

        if not input_window.user_input:
            return

        user_input_lcase = input_window.user_input.lower()

        # Get the scene dictionary (key: Scene name, Value: scene script)
        scenes_dict = ProjectSnapshot.chapters_and_scenes.get(chapter_name)[1]

        # Make sure the scene name doesn't already exist in the chapter
        # (case-insensitive search)
        for scene in scenes_dict:
            if user_input_lcase == scene.lower():
                messagebox.showwarning(parent=self.treeview_widget.winfo_toplevel(), 
                                       title="Scene Name Already Exists",
                                       message="That scene name already exists.\nPlease type a different name.")
                self.create_new_scene(prefill_scene_name=input_window.user_input)
                return

        # Add empty scene to dictionary
        # This will update the main scenes dictionary too (it's a reference, not a copy)
        scenes_dict[input_window.user_input] = ""

        # Add the scene to the treeview widget.
        self.treeview_widget.insert(parent=chapter_item,
                                    index="end",
                                    text=input_window.user_input)

    def show_chapter_script(self, chapter_name: str):
        """
        Show the script of the specified chapter name (case-sensitive)
        in the text widget.

        Show the script in the main text widget.

        :param chapter_name:
        :return: None
        """

        if not chapter_name:
            return

        chapter_script = ProjectSnapshot.get_chapter_script(chapter_name)

        self.lbl_title.configure(text=f"{chapter_name} [Chapter]")

        # Set the type of script that is currently active so we know.
        # None means there is no scene
        self.active_script = (chapter_name, None)

        Passer.editor.text_script.delete("1.0", "end")
        Passer.editor.text_script.insert("1.0", chapter_script)
        Passer.editor.text_script.reevaluate_entire_contents()
        Passer.editor.text_script.edit_modified(False)
        
    def show_scene_script(self, chapter_name: str, scene_name: str):
        """
        Show the scene that has the given name (case-sensitive)
        in the given chapter (case-sensitive).

        Show the script in the main text widget.
        :param chapter_name:
        :param scene_name:
        :return: None

        Changes:
        Nov 4, 2023 (Jobin Rezai) - Show the text, 'Hidden Scene', in the editor's header
        if the scene being edited starts with a period.
        """
        scene_script = ProjectSnapshot.get_scene_script(chapter_name, scene_name)

        # Show the scene heading as 'Hidden Scene' if the scene name starts with a period.
        if scene_name.startswith("."):
            scene_heading = "Hidden Scene"
        else:
            scene_heading = "Scene"

        self.lbl_title.configure(text=f"{chapter_name} -> {scene_name} [{scene_heading}]")

        # Set the type of script that is currently active so we know.
        self.active_script = (chapter_name, scene_name)

        Passer.editor.text_script.delete("1.0", "end")
        Passer.editor.text_script.insert("1.0", scene_script)
        Passer.editor.text_script.reevaluate_entire_contents()
        Passer.editor.text_script.edit_modified(False)

class StatusBar:
    def __init__(self, lbl_status):
        self.lbl_status = lbl_status

    def show_saved_successfully(self, *args):
        self.lbl_status.configure(text=ProjectSnapshot.save_full_path)

    def show_save_dirty(self):
        self.lbl_status.configure(text=f"(Unsaved) {ProjectSnapshot.save_full_path}")

    def clear_text(self):
        self.lbl_status.configure(text="")

    def show_text(self, text: str):
        self.lbl_status.configure(text=text)

class Toolbar:
    def __init__(self, editor_object: EditorMainApp):
        self.editor_object = editor_object

        self.frame_toolbar = editor_object.builder.get_object("frame_toolbar")

        # Edit details image
        edit_details_image = PhotoImage(data=Icons.DETAILS_24_F.value)

        self.btn_story_details = editor_object.builder.get_object("btn_story_details")
        self.btn_story_details.image = edit_details_image
        self.btn_story_details.configure(command=self.on_story_details_button_clicked,
                                         image=self.btn_story_details.image)
        
        # Trace Tool image
        trace_tool_image = PhotoImage(data=Icons.TRACE_TOOL_24_F.value)

        self.btn_trace_tool = editor_object.builder.get_object("btn_trace_tool")
        self.btn_trace_tool.image = trace_tool_image
        self.btn_trace_tool.configure(command=self.on_trace_tool_button_clicked,
                                      image=self.btn_trace_tool.image)
        
        
        # Compile image
        compile_image = PhotoImage(data=Icons.COMPILE_24_F.value)

        self.btn_compile = editor_object.builder.get_object("btn_compile")
        self.btn_compile.image = compile_image
        self.btn_compile.configure(command=self.on_compile_button_clicked,
                                   image=self.btn_compile.image)        
        
        
        # Help image
        help_image = PhotoImage(data=Icons.HELP_24_F.value)

        self.btn_help = editor_object.builder.get_object("btn_help")
        self.btn_help.image = help_image
        self.btn_help.configure(command=self.on_help_button_clicked,
                                image=self.btn_help.image)           
        
        
        # About image
        about_image = PhotoImage(data=Icons.ABOUT_24_F.value)

        self.btn_about = editor_object.builder.get_object("btn_about")
        self.btn_about.image = about_image
        self.btn_about.configure(command=self.on_about_button_clicked,
                                 image=self.btn_about.image)           

        # Save image
        save_image = PhotoImage(data=Icons.SAVE_24_F.value)

        self.btn_save = editor_object.builder.get_object("btn_save")
        self.btn_save.image = save_image
        self.btn_save.configure(command=self.on_save_button_clicked,
                                image=self.btn_save.image)

        # Open image
        open_image = PhotoImage(data=Icons.OPEN_24_F.value)
        
        self.btn_open = editor_object.builder.get_object("btn_open")
        self.btn_open.image = open_image
        self.btn_open.configure(command=self.on_open_button_clicked,
                                image=self.btn_open.image)

        self.story_details_window = None

    def on_trace_tool_button_clicked(self):
        trace_tool_window = TraceToolApp(self.editor_object.mainwindow)
        
    def on_help_button_clicked(self):
        """
        Open the tutorials website.
        """
        webbrowser.open_new(r"https://lvnauth.org/pages/tutorials.html")
        
    def on_about_button_clicked(self):
        about_window = AboutWindow(self.editor_object.mainwindow)

    def on_story_details_button_clicked(self):
        self.story_details_window = StoryDetailsWindow(self.editor_object.mainwindow,
                                                       existing_details=ProjectSnapshot.details)
        if self.story_details_window.details:
            ProjectSnapshot.details = self.story_details_window.details
            
    def on_compile_button_clicked(self):
        self.editor_object.save_final_lvna()

    def on_save_button_clicked(self):
        self.save_project()

    def on_open_button_clicked(self):
        open_manager = OpenManager(parent=self.editor_object.mainwindow)
        open_manager.open()

    @staticmethod
    def save_project():
        """
        Save the JSON project file.

        :return: None
        """
        save_manager = SaveManager()

        # Save the script that's being edited (if any).
        Passer.chapter_scenes.save_current_script()

        save_manager.save()


class OpenManager:
    """
    handles opening an existing project file (JSON format)
    """

    def __init__(self, parent):
        # So we can set the parent of the Open file dialog
        self.parent = parent

        # This will contain the converted data from a JSON to dict
        self.dict_data = None

        self.keys_must_exist = ["DialogImages",
                                "CharacterImages",
                                "BackgroundImages",
                                "ObjectImages",
                                "LVNAuth-EditorVersion",
                                "ProjectInfo",
                                "ChaptersAndScenes"]

    def open(self, lvnap_file_path: str=None):
        """
        Open a lvnap project.
        
        Arguments:
        
        - lvnap_file_path: a full path to a lvnap project file to open.
        This is optional. If not supplied, an open file dialog will be shown.
        """

        # For debugging
        if lvnap_file_path:
            file_path = lvnap_file_path
        else:
            file_path = filedialog.askopenfilename(parent=self.parent,
                                                   filetypes=[("LVNAuth Project", ".lvnap")])

        if not file_path:
            return

        read_file = Path(file_path).read_text()

        # Attempt to copy the json text to a dictionary
        self.dict_data = json.loads(read_file)

        # The key, 'LVNAuth-EditorVersion', has to exist.
        # Otherwise, consider it an invalid file.
        project_editor_version = self.dict_data.get("LVNAuth-EditorVersion")
        if not project_editor_version:
            messagebox.showerror(parent=Passer.editor.treeview_scripts.winfo_toplevel(), 
                                 title="Error",
                                 message="Invalid Project File")
            return

        # Make sure the current editor application is the same version
        # or newer than the editor version that the project was saved in.
        project_editor_version = int(project_editor_version)
        if ProjectSnapshot.EDITOR_VERSION < project_editor_version:
            messagebox.showerror(parent=Passer.toolbar.frame_toolbar.winfo_toplevel(), 
                                 title="Out of Date",
                                 message="The project that you are trying to open was made in a newer "
                                         "version of LVNAuth that is not compatible with the version "
                                         "that you are using.\n\nA newer version of LVNAuth is required "
                                         "to open this project file.")
            return

        self._clear_project()
        self._load_project(file_path=file_path)

    @staticmethod
    def _clear_project():
        """
        If there is an existing editor window open, close it, and re-open
        a new instance.

        This is used in preparation for a new project file to be loaded.

        """

        ## Clear all the dictionaries.
        #ProjectSnapshot.character_images.clear()
        #ProjectSnapshot.background_images.clear()
        #ProjectSnapshot.object_images.clear()
        #ProjectSnapshot.font_sprites.clear()
        #ProjectSnapshot.font_sprite_properties.clear()
        #ProjectSnapshot.dialog_images.clear()

        #ProjectSnapshot.chapters_and_scenes.clear()
        #ProjectSnapshot.reusables.clear()

        #ProjectSnapshot.sounds.clear()
        #ProjectSnapshot.music.clear()

        ## Clear story details dictionary
        #ProjectSnapshot.details.clear()

        ## Clear file save variables
        #ProjectSnapshot.project_path = None
        #ProjectSnapshot.save_full_path = None

        #Passer.statusbar.clear_text()
        
        if Passer.editor:
            startup_window = Passer.editor.master
            Passer.editor.mainwindow.destroy()
            Passer.editor = EditorMainApp(startup_window)

    def _load_project(self, file_path: str):
        """
        Populate the project snapshot dictionary from the temporary dict

        file_path: the full path to the loaded .lvnap file.
                   we need this so we can know which file is open,
                   and so we can get the project's folder.

        :return: True if successful, False if an error occurs.
        """

        file_path = Path(file_path)

        # Make sure all the expected dictionary keys exist
        for key in self.keys_must_exist:
            if key not in self.dict_data:
                messagebox.showerror(parent=Passer.toolbar.frame_toolbar.winfo_toplevel(),
                                     title="Project File Error",
                                     message="The project file is missing one or more required keys.")  
                
                break
        else:
            # All the required dict keys exist, so populate the
            # actual dict for the loaded project.
            # ProjectSnapshot.dialog_images = self.dict_data["DialogImages"].copy()

            ProjectSnapshot.details = self.dict_data["ProjectInfo"].copy()
            
            # Get the story window size (width/height)
            ProjectSnapshot.story_window_size = tuple(self.dict_data["StoryWindowSize"])

            # The path to the loaded .lvnap file
            ProjectSnapshot.save_full_path = file_path

            # The path to the project's folder (Without the .lvnap file)
            ProjectSnapshot.project_path = file_path.parent

            # Show the .lvnap full path in the status bar
            Passer.statusbar.show_text(file_path)

            self._populate_treeview_widgets()
            
            self._populate_font_sprite_properties()

            self._populate_chapters_scenes_treeview()

    def _populate_font_sprite_properties(self):
        """
        Populate the font sprite properties dictionary from
        the newly loaded dict data.
        
        This will populate the font properties only if the font sprite
        with the same item name has already been populated in the font sprite
        dictionary. So the font sprite dict needs to be populated before
        running this method.
        """
        
        # Get the font properties from the newly loaded dict data.
        font_sprite_properties = self.dict_data.get("FontSpriteProperties")

        # Populate a sprite property only if the sprite font exists
        # in the sprite font dictionary (which it should unless the
        # project file was manually tampered with).
        for sprite_font_name, property_details \
                in font_sprite_properties.items():

            # Is the font name (the name as it appears in the treeview widget)
            # already loaded?
            if sprite_font_name in ProjectSnapshot.font_sprites:
                # The font sprite exists, so it's OK to load its properties.
                
                # Convert the rect positions of the letters to a tuple, because
                # JSON doesn't have tuples, and we need to store the rects
                # as tuples because we will use the rects as dict keys when
                # splitting them in the font sprite window.
                letters: Dict = property_details.get("Letters")

                # Put the kerning and rect_crop info into a LetterProperties object,
                # and update a new dictionary with the new LetterProperties objects.
                load_letters = {}
                for letter, details in letters.items():
                    rect_crop = details.get("rect_crop")
                    kerning_rules = details.get("kerning_rules")
                    letter_properties = LetterProperties(rect_crop=rect_crop,
                                                        kerning_rules=kerning_rules)
                    # New dictionary that will contain the LetterProperties
                    load_letters[letter] = letter_properties
                
                # letters = {key: tuple(value.get("rect_crop")) for key, value in letters.items()}

                properties = \
                    FontSprite(
                        width=property_details.get("Width", 0),
                        height=property_details.get("Height", 0),
                        padding_letters=property_details.get("PaddingLetters", 0),
                        padding_lines=property_details.get("PaddingLines", 0),
                        detect_letter_edges=property_details.get("DetectLetterEdges", False),
                        letters=load_letters)

                # Record the property of the font sprite
                ProjectSnapshot.font_sprite_properties[sprite_font_name] \
                    = properties

    def _populate_chapters_scenes_treeview(self):
        """
        Populate the chapters and scenes treeview from the newly loaded dict data.

        The loaded data is in self.dict_data

        :return: None
        """

        # Clear the scripts/scenes treeview widget because
        # we're about to populate it (it might be pre-populated from
        # a previous project)
        all_root_items = Passer.editor.treeview_scripts.get_children()
        if all_root_items:
            Passer.editor.treeview_scripts.delete(*all_root_items)
            

        chapters_scenes = self.dict_data.get("ChaptersAndScenes")

        # Get the item that should have a special tag in the treeview widget
        # to indicate that it's the startup scene.
        startup_script_item_iid = self.dict_data.get("StartupScriptItemiid")

        # Convert the keys to an int (so we can sort them)
        chapter_display_orders = [int(item) for item in chapters_scenes.keys()]
        chapter_display_orders.sort()

        # Loop through the chapter display orders
        for display_order in chapter_display_orders:

            chapter_dict = chapters_scenes.get(str(display_order))
            # The dictionary will look something like this:
            # {
            #     "My First Chapter": [
            #         "",
            #         {
            #             "0": [
            #                 "My First Scene",
            #                 "Some scene script\nThis is\nmultiple lines\n\n\nand spaces above.\nCoolright?"
            #             ]
            #         }
            #     ]
            # }
            
          

            for chapter_name, value in chapter_dict.items():

                # Add the chapter name to the treeview
                chapter_iid = Passer.editor.treeview_scripts.insert(parent="",
                                                                    index=display_order,
                                                                    text=chapter_name)

                # Value will contain something like this:
                # ["chapter script here",
                #     {
                #         "0": [
                #             "My First Scene",
                #             "Some scene script\nThis is\nmultiple lines\n\n\nand spaces above.\nCoolright?"
                #         ]
                #     }
                # ]

                chapter_script = value[0]
                scenes_dict = value[1]

                # Get the display orders as an int, so we can sort them.
                scenes_display_order = [int(item) for item in scenes_dict.keys()]
                scenes_display_order.sort()

                # All the scenes for a looped chapter will be added to this dictionary.
                # Then, they will all get added to the main dictionary for the given chapter.
                scenes = {}

                for scene_display_order in scenes_display_order:

                    scene_info = scenes_dict.get(str(scene_display_order))
                    # The value will look something like this:
                    # [
                    #     "My First Scene",
                    #     "Some scene script\nThis is\nmultiple lines\n\n\nand spaces above.\nCoolright?"
                    # ]

                    scene_name = scene_info[0]
                    scene_script = scene_info[1]

                    # Prepare the scene dictionary to be added to the 'main' scenes dictionary.
                    scenes[scene_name] = scene_script

                    # Add the scene to the treeview, as a sub-item.
                    Passer.editor.treeview_scripts.insert(parent=chapter_iid,
                                                          index=scene_display_order,
                                                          text=scene_name)

                ProjectSnapshot.chapters_and_scenes[chapter_name] = [chapter_script, scenes.copy()]

            # Is there a startup script? Set the tag for it in the treeview widget so it
            # shows as a different colour.
            if startup_script_item_iid:
                Passer.editor.treeview_scripts.item(startup_script_item_iid, tags=("startup_script",))

    def _populate_treeview_widgets(self):
        """
        Populate all the treeview widgets from the newly loaded dict data.
        :return: None
        """
        # Key: dict
        # Value: treeview widget

        # Key in the dictionary, treeview widget, data dictionary
        treeview_mapping = [("ReusableScripts", Passer.editor.treeview_reusables, ProjectSnapshot.reusables),
                            ("CharacterImages", Passer.editor.treeview_characters, ProjectSnapshot.character_images),
                            ("BackgroundImages", Passer.editor.treeview_backgrounds, ProjectSnapshot.background_images),
                            ("ObjectImages", Passer.editor.treeview_objects, ProjectSnapshot.object_images),
                            ("FontSprites", Passer.editor.treeview_font_sprites, ProjectSnapshot.font_sprites),
                            ("DialogImages", Passer.editor.treeview_dialog_rectangle, ProjectSnapshot.dialog_images),
                            ("Sounds", Passer.editor.treeview_sounds, ProjectSnapshot.sounds),
                            ("Music", Passer.editor.treeview_music, ProjectSnapshot.music)]


        # Iterate through all the treeview widgets and populate them
        # from their corresponding dictionaries.
        for mapping in treeview_mapping:
            dict_key, treeview_widget, project_dict = mapping
            
            if dict_key not in self.dict_data:
                messagebox.showerror(parent=Passer.editor.mainwindow, 
                                     title="Key Not Found",
                                     message=f"The project file is missing the key: '{dict_key}'\n\nThe project file "
                                             f"might be corrupted.")
                continue

            # Get the dictionary that we loaded from JSON.
            # Example dict_key: 'DialogImages'
            dict_buffer = self.dict_data.get(dict_key)

            # Clear the project's dictionary for the current item (example: DialogImages)
            # because we're about to populate new data.
            project_dict.clear()

            # Clear the treeview widget contents, because we're about to populate it.
            all_root_items = treeview_widget.get_children()
            if all_root_items:
                treeview_widget.delete(*all_root_items)

            # Sort the keys because the keys act as the display orders.
            # Convert the keys to an integer so we can sort the numbers.
            display_order_keys = [int(item) for item in dict_buffer.keys()]
            display_order_keys.sort()

            # Iterate through the display order keys so we can populate
            # the current treeview widget in the correct order.
            for key in display_order_keys:

                # Get the value for this item (example: image item or folder)
                value = dict_buffer[str(key)]

                item_text = value[0]
                file_name = value[1]
                item_iid = value[2]
                parent_iid = value[3]

                # Images will have a file_name, whereas folders will not have a file_name.
                # Folders will have null in the file name part in JSON (None in Python).
                if file_name is not None:
                    tag = ("normal_row",)

                    # It's an image row, so add it to the project's dictionary.
                    project_dict[item_text] = file_name

                else:
                    # Folders are not added to the project's dictionary.
                    # Folders are only used in treeview widgets, for the user to see.
                    tag = ("folder_row",)

                treeview_widget.insert(parent=parent_iid,
                                       index="end",
                                       iid=item_iid,
                                       text=item_text,
                                       tags=tag)


class SaveManager:
    """
    Handles saving a new or existing project file (JSON format).
    """

    def __init__(self):
        # So we can set the parent of the Save As file dialog
        self.parent = Passer.editor.mainwindow

        self.counter = 0

        # Eventually this variable will contain the project's json data that
        # will get saved to the file system.
        self.json_data = None

    def _treeview_to_dict(self, treeview_widget: ttk.Treeview, data_dict: Dict) -> Dict:
        """
        Iterate through each of the treeview widgets and populate a dictionary
        and return the dictionary.

        Parameters:
        - treeview_widget: the treeview widget that we're going to iterate through.
        - data_dict: the dictionary that has the data for the specified treeview.
                     the reason for this dictionary is for us to get the file names
                     of the items in the treeview, or in the case of reusable scripts,
                     to get the scripts of the reusables. This dictionary will have the
                     file names and scripts.

        Eventually the returned dictionary will be turned into JSON.
        :return: Dict
        """

        # Key: counter (acts as the display order)
        # Value: [display_name, file_name or script, item_iid, parent_iid]
        builder = {}

        # If it's a folder, the file_name should be set to None

        # Example:
        # "DialogImages": {"0": ["Rave", "Rave.png", "I001", null]},
        #                 {"1": ["New Folder", null(means it's a folder), "I002", null]},
        #                 {"2": ["Kite", "Kite.png", "I003", "I002"]}

        # Another example (this time for reusable scripts)
        # "ReusableScripts": {"0": ["Cool Animation", "<animation code>.....", "I001", null]},
        #                    {"1": ["New Folder", null(means it's a folder), "I002", null]},
        #                    {"2": ["Another cool script name", "<other command...>", "I003", "I002"]}

        # Initialize. This will act as the display order.
        self.counter = -1

        self.get_children_custom(dict_ref=data_dict,
                                 builder=builder,
                                 treeview_widget=treeview_widget,
                                 in_item_iid="")

        return builder

    def get_children_custom(self,
                            dict_ref: Dict,
                            builder: Dict,
                            treeview_widget: ttk.Treeview,
                            in_item_iid: str):
        """
        Iterate over the treeview items that are within the argument 'in_item_iid'.
        If that variable is a blank string, that means the root items will be iterated over.

        :param dict_ref: the dictionary that contains the file name of the item.
        :param builder: the dictionary that is being appended-to while iterating over the treeview.
        :param treeview_widget: the treeview widget that we're building a dictionary from.
        :param in_item_iid: the item iid that we want to get the children for. A blank string means root.

        :return: None
        """

        # Iterate over items in the specified treeview widget
        for item_iid in treeview_widget.get_children(in_item_iid):

            # We don't use enumerate in this for-loop because we'll
            # need to keep incrementing this variable even outside of this method,
            # since this method will call itself below.
            self.counter += 1

            item_details = treeview_widget.item(item_iid)
            tags = item_details.get("tags")
            item_text = item_details.get("text")

            # If the current item is a folder, set the file_name to None
            # or in the case of a reusable script, the script part will be set to None.
            if "folder_row" in tags:
                file_name_or_script = None
            else:
                file_name_or_script = dict_ref.get(item_text)

            # Append the current item to the dictionary, which will be turned into JSON later on.
            builder[self.counter] = [item_text, file_name_or_script, item_iid, in_item_iid]

            # Run this method again for the current item,
            # because if the current item has any children, we'll need to iterate over those too.
            self.get_children_custom(dict_ref=dict_ref,
                                     builder=builder,
                                     treeview_widget=treeview_widget,
                                     in_item_iid=item_iid)

    def _get_chapters_and_scenes(self) -> Dict:
        """
        Get the chapter names, chapter scripts, scene names and scene scripts and put them
        into a dictionary that will eventually get converted to JSON.
        :return: dict
        """

        # We'll use the chapters/scenes treeview to get the chapter/scene names, because that is
        # the correct order of the chapters and scenes.

        builder = {}

        Passer.editor.treeview_scripts: ttk.Treeview

        # Loop through the chapters
        for chapter_counter, chapter_item_iid in enumerate(Passer.editor.treeview_scripts.get_children()):

            chapter_name = Passer.editor.treeview_scripts.item(chapter_item_iid).get("text")

            value = ProjectSnapshot.chapters_and_scenes.get(chapter_name)
            # value should now have this format:
            # [ chapter script,  another dict {Key: scene name (str): Value script (str)} ]

            chapter_script = value[0]
            scenes_dict = value[1]

            scenes = {}

            # Loop through the scenes in the current chapter
            for scene_counter, scene_name_and_script in enumerate(scenes_dict.items()):

                # Get the values of the tuple
                scene_name, scene_script = scene_name_and_script

                # scene_counter is used for the display order
                scenes[scene_counter] = [scene_name, scene_script]

            # Put all the scenes of the current chapter into the 'final' dictionary
            builder[chapter_counter] = {chapter_name: [chapter_script, scenes.copy()]}

        return builder

    def _populate_save_dictionary(self):
        """
        Prepare the JSON file to be saved by first populating a dictionary
        with all the values and file paths of the story project.
        :return: None
        """     

        chapters_and_scenes = self._get_chapters_and_scenes()

        reusable_scripts = self._treeview_to_dict(treeview_widget=Passer.editor.treeview_reusables,
                                                  data_dict=ProjectSnapshot.reusables)

        character_images = self._treeview_to_dict(treeview_widget=Passer.editor.treeview_characters,
                                                  data_dict=ProjectSnapshot.character_images)

        background_images = self._treeview_to_dict(treeview_widget=Passer.editor.treeview_backgrounds,
                                                   data_dict=ProjectSnapshot.background_images)

        object_images = self._treeview_to_dict(treeview_widget=Passer.editor.treeview_objects,
                                               data_dict=ProjectSnapshot.object_images)

        font_sprites = self._treeview_to_dict(treeview_widget=Passer.editor.treeview_font_sprites,
                                              data_dict=ProjectSnapshot.font_sprites)

        dialog_images = self._treeview_to_dict(treeview_widget=Passer.editor.treeview_dialog_rectangle,
                                               data_dict=ProjectSnapshot.dialog_images)

        sounds = self._treeview_to_dict(treeview_widget=Passer.editor.treeview_sounds,
                                        data_dict=ProjectSnapshot.sounds)

        music = self._treeview_to_dict(treeview_widget=Passer.editor.treeview_music,
                                       data_dict=ProjectSnapshot.music)


        data = {"ProjectInfo": ProjectSnapshot.details,
                "StoryWindowSize": ProjectSnapshot.story_window_size,
                "LVNAuth-EditorVersion": ProjectSnapshot.EDITOR_VERSION,
                "StartupScriptItemiid": Passer.editor.get_startup_scene_item_iid(),
                "CharacterImages": character_images,
                "BackgroundImages": background_images,
                "ObjectImages": object_images,
                "FontSprites": font_sprites,
                "FontSpriteProperties": FontSprite.get_all_font_properties(),
                "DialogImages": dialog_images,
                "Sounds": sounds,
                "Music": music,
                "ChaptersAndScenes": chapters_and_scenes,
                "ReusableScripts": reusable_scripts}

        self.json_data = json.dumps(data,
                                    indent=4,
                                    sort_keys=True)

    def save(self):
        """
        Save the project to a JSON file (.lvnap extension).
        :return: True if successful, False if there was an error.
        """

        # try:

        # Prepare the data that will eventually get saved to a file.
        self._populate_save_dictionary()

        ProjectSnapshot.save_full_path.write_text(self.json_data)

        self.parent.event_generate("<<SavedProjectSuccessfully>>")

        # The project has been saved, so don't delete the images that were
        # added to the project.
        Passer.editor.clear_delete_files_upon_close()

        # except OSError as e:
        #     messagebox.showerror(title="Save Error",
        #                          message=f"Could not save project: {e}")
        #
        #     return False
        #
        # else:
        #     return True


class FileManager:
    """
    Handles adding/removing images and sounds to a project.
    It does this by copying the files to the project's folder
    and populating the appropriate treeview widget.
    """

    def __init__(self):
        pass

    @staticmethod
    def get_active_treeview(section: SectionChosen) -> ttk.Treeview:
        """
        Return the treeview depending on which tab is open in the Notebook widget.
        :return: treeview widget
        """

        if section == SectionChosen.IMAGES:
            notebook_to_check: ttk.Notebook = Passer.editor.builder.get_object("notebook_images")
        elif section == SectionChosen.AUDIO:
            notebook_to_check: ttk.Notebook = Passer.editor.builder.get_object("notebook_audio")
        elif section == SectionChosen.REUSABLES:
            notebook_to_check: ttk.Notebook = Passer.editor.builder.get_object("notebook_editor")

        selected_tab_index = notebook_to_check.index("current")

        if section == SectionChosen.IMAGES:
            if selected_tab_index == 0:
                return Passer.editor.treeview_characters
            elif selected_tab_index == 1:
                return Passer.editor.treeview_backgrounds
            elif selected_tab_index == 2:
                return Passer.editor.treeview_objects
            elif selected_tab_index == 3:
                return Passer.editor.treeview_font_sprites
            elif selected_tab_index == 4:
                return Passer.editor.treeview_dialog_rectangle

        elif section == SectionChosen.AUDIO:
            if selected_tab_index == 0:
                return Passer.editor.treeview_sounds
            elif selected_tab_index == 1:
                return Passer.editor.treeview_music

        elif section == SectionChosen.REUSABLES:
            if selected_tab_index == 1:
                return Passer.editor.treeview_reusables

    @staticmethod
    def get_active_dictionary(section: SectionChosen) -> Dict:
        """
        Return a Dict for the active tab in the notebook.

        For example, if the dialog rectangle tab is open, then
        ProjectSnapshot.dialog_images will be returned.

        :param: section: (SectionChosen) So we know which notebook widget to look at.
        :return: Dict
        """

        return_dict = None

        if section == SectionChosen.IMAGES:
            notebook_widget: ttk.Notebook = Passer.editor.builder.get_object("notebook_images")
        elif section == SectionChosen.AUDIO:
            notebook_widget: ttk.Notebook = Passer.editor.builder.get_object("notebook_audio")

        selected_tab_index = notebook_widget.index("current")

        if section == SectionChosen.IMAGES:
            if selected_tab_index == 0:
                return_dict = ProjectSnapshot.character_images
            elif selected_tab_index == 1:
                return_dict = ProjectSnapshot.background_images
            elif selected_tab_index == 2:
                return_dict = ProjectSnapshot.object_images
            elif selected_tab_index == 3:
                return_dict = ProjectSnapshot.font_sprites
            elif selected_tab_index == 4:
                return_dict = ProjectSnapshot.dialog_images

        elif section == SectionChosen.AUDIO:
            if selected_tab_index == 0:
                return_dict = ProjectSnapshot.sounds
            elif selected_tab_index == 1:
                return_dict = ProjectSnapshot.music

        return return_dict

    @staticmethod
    def get_item_save_path(section: SectionChosen) -> Path:
        """
        Return a Path object that represents the file system path
        to save images into. The path will depend on which tab is currently
        open in the Notebook widget.

        :param: section: (SectionChosen) So we know which notebook widget to look at
                         and to know which path to return.
        :return: pathlib.Path object
        """

        if section == SectionChosen.IMAGES:
            notebook_widget: ttk.Notebook = Passer.editor.builder.get_object("notebook_images")
        elif section == SectionChosen.AUDIO:
            notebook_widget: ttk.Notebook = Passer.editor.builder.get_object("notebook_audio")

        selected_tab_index = notebook_widget.index("current")

        save_path = None

        if section == SectionChosen.IMAGES:

            if selected_tab_index == 0:
                save_path = ProjectSnapshot.project_path / SubPaths.CHARACTER_IMAGE_FOLDER.value
            elif selected_tab_index == 1:
                save_path = ProjectSnapshot.project_path / SubPaths.BACKGROUND_IMAGE_FOLDER.value
            elif selected_tab_index == 2:
                save_path = ProjectSnapshot.project_path / SubPaths.OBJECT_IMAGE_FOLDER.value
            elif selected_tab_index == 3:
                save_path = ProjectSnapshot.project_path / SubPaths.FONT_SPRITE_FOLDER.value
            elif selected_tab_index == 4:
                save_path = ProjectSnapshot.project_path / SubPaths.DIALOG_IMAGE_FOLDER.value

        elif section == SectionChosen.AUDIO:

            if selected_tab_index == 0:
                save_path = ProjectSnapshot.project_path / SubPaths.SOUND_FOLDER.value
            elif selected_tab_index == 1:
                save_path = ProjectSnapshot.project_path / SubPaths.MUSIC_FOLDER.value

        return save_path

    def browse_for_files(self, section_chosen: SectionChosen):
        """
        Show a file dialog and allow the user to select multiple files.

        :param: section_chosen: (SectionChosen) So we know which treeview/dict to add files to.
        :return: List of selected files or None if the user cancelled.
        """
        save_path = None

        # Get a reference to the treeview that we will need to insert into
        treeview_widget = self.get_active_treeview(section=section_chosen)

        dict_ref = self.get_active_dictionary(section=section_chosen)

        # Get the selected item so we know which folder to put the image under.
        selected_item = treeview_widget.focus()

        # If the selected item is not a folder, get the parent item
        # (the parent item will be a folder or root),
        # so the newly added file gets added to that folder.
        tag = treeview_widget.item(selected_item).get("tags")
        if "folder_row" not in tag:
            selected_item = treeview_widget.parent(selected_item)

        # Get the image path. This path will be where the image file will get copied.
        save_path = self.get_item_save_path(section=section_chosen)

        # Make sure the save path exists. If not, tell the user.
        if not save_path.exists():
            messagebox.showerror(parent=treeview_widget.winfo_toplevel(), 
                                 title="Project Folder Not Found",
                                 message="Project path does not exist.\n\n"
                                         f"{save_path}")
            return

        if section_chosen == SectionChosen.IMAGES:
            file_types = [("All Supported Images", ".png .jpg .gif"),
                          ("PNG images", ".png"),
                          ("JPG images", ".jpg"),
                          ("GIF images", ".gif")]
        elif section_chosen == SectionChosen.AUDIO:
            file_types = [("All Supported Audio Types", ".wav .ogg"),
                          ("WAV Audio", ".wav"),
                          ("OGG Audio", ".ogg")]

        selected_files =\
            filedialog.askopenfilenames(parent=treeview_widget.winfo_toplevel(),
                                        filetypes=file_types)

        # Go through the selected files
        for full_path in selected_files:
            path_object = Path(full_path)
            file_no_extension = path_object.stem
            file_name_only = path_object.name

            file_save_path = save_path / file_name_only

            if file_no_extension in dict_ref:
                messagebox.showwarning(parent=treeview_widget.winfo_toplevel(), 
                                       title="Already Exists",
                                       message=f"{file_no_extension} already exists in the project.\nThis file will "
                                               f"be skipped.")
                continue

            # Copy the file to the project's folder
            try:

                full_path_lcase = full_path.lower()
                save_path_lcase = str(file_save_path).lower()

                # If the source and destination paths are the same,
                # then skip copying this file.
                if full_path_lcase != save_path_lcase:
                    copy2(src=full_path, dst=str(file_save_path), follow_symlinks=False)

                    # If the project doesn't get saved upon the application closing,
                    # delete the file from the project's images folder.
                    copied_path = Path(file_save_path)
                    Passer.editor.add_to_delete_file_upon_close(full_path_to_file=copied_path)

            except OSError as e:
                print(f"Could not copy '{file_name_only}' to the project's folder.\n\n"
                      f"Details: {e}")

            item_iid = treeview_widget.insert(index="end",
                                              parent=selected_item,
                                              tags=("normal_row",),
                                              text=file_no_extension)

            # Add to the dictionary that will be used to save the project file.
            dict_ref[file_no_extension] = file_name_only
            
            if treeview_widget == Passer.editor.treeview_font_sprites:

                font_properties = FontSprite()
                ProjectSnapshot.font_sprite_properties[file_no_extension] = font_properties

                        
            # So the user knows the project changes are not saved yet.
            Passer.statusbar.show_save_dirty()

    def remove_selected_file(self, section: SectionChosen):
        """
        Remove the selected item from the treeview widget
        and also delete the file in the local project's folder.

        :return: None
        """

        treeview_widget = self.get_active_treeview(section=section)

        # Get a reference to the dictionary that we will remove the item from
        dict_ref = self.get_active_dictionary(section=section)

        # Get the selected item in the treeview widget
        selected_item = treeview_widget.focus()

        # Path to delete from
        image_folder = self.get_item_save_path(section=section)

        # Delete font properties?
        delete_font_properties = (treeview_widget is \
                                  Passer.editor.treeview_font_sprites)

        keys_to_remove = []

        if not selected_item:
            return

        # Get the item's text, because that text will be the dictionary key for it.
        item_details = treeview_widget.item(selected_item)
        item_text = item_details.get("text")
        item_tags = item_details.get("tags")

        full_paths = []

        if "folder_row" not in item_tags:
            # It's not a folder.

            # Get the file name so we can delete the file too
            file_name = dict_ref.get(item_text)

            # Show the item name to the user in the confirmation dialog.
            delete_prompt_text = f"Remove '{item_text}'?"

            # Show the user the full image path that will be deleted.
            delete_path = image_folder / file_name
            full_paths.append(str(delete_path))

            keys_to_remove.append(item_text)

        else:
            # It's a folder
            delete_prompt_text = f"Remove folder '{item_text}' and all its items?"

            # Get a list of all the items that will be deleted
            all_children_iid = self._get_all_children(treeview_widget, selected_item)

            # Iterate through all the items that will be deleted
            # and compile a list of their full image paths so the user can confirm the deletion.
            for iid in all_children_iid:
                item_details = treeview_widget.item(iid)

                item_text = item_details.get("text")
                item_file_name = dict_ref[item_text]

                delete_path = image_folder / item_file_name

                full_paths.append(str(delete_path))

                keys_to_remove.append(item_text)

        # Convert the list to a multiline string.
        path_deletions_display = "\n".join(full_paths)

        # Ask the user if it's OK to delete the selected item.
        delete_confirm = DeleteConfirmationWindow(master=Passer.editor.mainwindow,
                                                  prompt_text=delete_prompt_text,
                                                  items_to_delete=path_deletions_display)

        if not delete_confirm.user_answer:
            return

        # Remove the item from the dictionary
        for key in keys_to_remove:
            del dict_ref[key]
            
            # Delete the font property? (if we're deleting font sprite(s))
            if delete_font_properties:
                if key in ProjectSnapshot.font_sprite_properties:
                    del ProjectSnapshot.font_sprite_properties[key]

        # Remove from the dictionary
        treeview_widget.delete(selected_item)

        # Now delete the image files
        for full_path in full_paths:
            image_path = Path(full_path)

            if image_path.exists():
                if image_path.is_file():
                    image_path.unlink(missing_ok=True)

        Toolbar.save_project()

    def _get_all_children(self, treeview_widget, item) -> List[str]:
        """
        Return all the children of the specified item.

        Purpose of this method: to show the user a list of file names that will be deleted
                                from a folder in a treeview widget.

        :param treeview_widget:
        :param item: item iid
        :return: List (str)
        """

        overall_children = []

        item_children = treeview_widget.get_children(item)

        for item in item_children:
            item_details = treeview_widget.item(item)

            tags = item_details.get("tags")
            if "folder_row" in tags:

                sub_children = self._get_all_children(item=item, treeview_widget=treeview_widget)
                if sub_children:
                    overall_children.extend(sub_children)

            else:
                overall_children.append(item)

        return overall_children

    def on_create_new_folder_button_clicked(self, section_chosen: SectionChosen,
                                            create_under_item_iid=None,
                                            prefill_folder_name=None):
        """
        Ask the user for a new folder name, then create an item in the active treeview.

        :param section_chosen: (SectionChosen) so we know which Notebook section to create a
                                               folder in (ie: images or audio)
        :param create_under_item_iid: (str) whether to create the new folder in 'top' (root) or 'sub' of an existing item.
        :param prefill_folder_name: if the folder already exists, this method can be recalled with a value here.
        :return: None
        """

        treeview_widget = self.get_active_treeview(section_chosen)

        # Get the selected item iid in the treeview, if any
        if create_under_item_iid is not None:

            # This is a re-attempt, so use the value from the prior attempt.
            selected_item = create_under_item_iid
        else:
            selected_item = treeview_widget.focus()

        # If the selected item is not a folder, get the parent item
        # because the parent item will be a folder or root.
        tag = treeview_widget.item(selected_item).get("tags")
        if "folder_row" not in tag:
            selected_item = treeview_widget.parent(selected_item)

        # Ask the user if they want to create the new folder under
        # the selected item, or in the root.

        # But only ask the user if it's not a re-attempt.
        # If create_under_item_iid is None, then it's a *new* attempt.
        if selected_item and create_under_item_iid is None:

            # So we can show the user the name of the selected item.
            selected_item_text = treeview_widget.item(selected_item).get("text")

            where_new_folder = WhereNewFolderWindow(master=treeview_widget.winfo_toplevel(),
                                                    in_sub_folder_name=selected_item_text)

            if not where_new_folder.user_input:
                # The user clicked Cancel
                return

            elif where_new_folder.user_input == "top":
                # Create the new folder in the root/top level
                selected_item = ""

            # If the selection was to create the new folder in the sub,
            # then selected_item already contains the iid of the selected item.

        # Ask the user the name of the new folder.
        input_window = InputStringWindow(master=treeview_widget.winfo_toplevel(),
                                         title="New Folder",
                                         msg="Type a new folder name below.",
                                         prefill_entry_text=prefill_folder_name)

        if not input_window.user_input:
            # The user cancelled or has entered a blank string.
            return

        # Does the folder name exist in the same hierarchy level that it's about
        # to be created in?
        folder_exists = FileManager._folder_exists(treeview_widget, selected_item, input_window.user_input)

        if folder_exists:
            messagebox.showwarning(parent=Passer.editor.treeview_scripts.winfo_toplevel(), 
                                   title="Already Exists",
                                   message="The folder name already exists.")
            self.on_create_new_folder_button_clicked(
                                         section_chosen=section_chosen,
                                         create_under_item_iid=selected_item,
                                         prefill_folder_name=input_window.user_input)
            return

        treeview_widget.insert(parent=selected_item,
                               index="end",
                               tags=("folder_row",),
                               text=input_window.user_input)

        # So the user knows the project changes are not saved yet.
        Passer.statusbar.show_save_dirty()

    @staticmethod
    def _folder_exists(treeview_widget, selected_item, new_folder_name):
        """
        Return whether the new folder name exists in the same hierarchy level
        as the selected item.

        :param treeview_widget: the treeview widget to check
        :param selected_item: that item that is currently selected (if any)
                              in the treeview widget. We will check the hierarchy
                              level of the item here.
        :param new_folder_name: the name of the folder the user wants to create
        :return:
        """

        # Get the sibling item iid's of the selected item (or root)
        item_children = treeview_widget.get_children(selected_item)
        new_folder_name_lcase = new_folder_name.lower()

        # Get the text of all the item's children
        for item_iid in item_children:
            item_text = treeview_widget.item(item_iid).get("text")

            if item_text.lower() == new_folder_name_lcase:
                return True
        else:
            return False




mystring = "<character_name-Bob Smith>>"

result = re.findall(r"^<(\w+)-(.*)>$", mystring)


class StoryReader:
    def __init__(self):
        pass

    def read_next_line(self):
        line = Story.story_lines.pop(0)


if __name__ == "__main__":

    app = EditorMainApp()
    app.run()
