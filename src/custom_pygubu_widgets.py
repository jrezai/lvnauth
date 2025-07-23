"""
Copyright 2023, 2024, 2025 Jobin Rezai

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

from lvnauth_editor_widget import LVNAuthEditorWidget
from treeview_edit_widget import TreeviewEdit
from entry_limit import EntryWithLimit
from pygubu.api.v1 import BuilderObject, register_widget
from pygubu.plugins.tk.tkstdwidgets import TKText
from pygubu.plugins.ttk.ttkstdwidgets import TTKTreeviewBO, TTKEntry



class LVNAuthWidgetBuilder(TKText):
    class_ = LVNAuthEditorWidget
    
class TreeviewEditBuilder(TTKTreeviewBO):
    class_ = TreeviewEdit
    
class EntryWithLimitBuilder(TTKEntry):
    class_ = EntryWithLimit


register_widget("lvnauthwidgets.editorwidget", LVNAuthWidgetBuilder,
    "LVNAuthWidget",("ttk", "LVNAuth Widgets"))

register_widget("lvnauthwidgets.treeviewedit", TreeviewEditBuilder,
    "TreeviewEdit",("ttk", "LVNAuth Widgets"))

register_widget("lvnauthwidgets.entrylimitwidget", EntryWithLimitBuilder,
                'EntryWithLimit', ('ttk', 'LVNAuth Widgets'))
