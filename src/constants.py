#
# Copyright 2013 TeamSWAP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import wx, os, sys

VERSION = "0.6.2"
VERSION_INT = 11
URL_CHECK = "http://faultexception.com/swap/check_updates.php"
PARSER_SERVER_ADDR = ("swapserver.no-ip.biz", 57680)
IS_COMPILED = 'frozen' in dir(sys)

# Static Messages
MSG_FAILED_KEY_GENERATION_TEXT = "Failed to generate new key! Please report this to the developer."
MSG_FAILED_KEY_GENERATION_TITLE = "Error"
MSG_FAILED_JOIN_INVALID_KEY_TEXT = "No such key was found"
MSG_FAILED_JOIN_INVALID_KEY_TITLE = "Error"
MSG_FAILED_JOIN_UPDATE_REQUIRED_TEXT = "Your SWAP client is too old! Please close SWAP and run the SWAP shortcut (if installed), or run updater.exe"
MSG_FAILED_JOIN_UPDATE_REQUIRED_TITLE = "Error"
MSG_COMBAT_LOGGING_DISABLED_TEXT = "Combat logging is disabled. If SWTOR is running please enter enable Combat Logging in Preferences. If SWTOR is not running, click OK and we'll take care of it for you."
MSG_COMBAT_LOGGING_DISABLED_TITLE = "Whoops!"

# Menu ID
MENU_ID_EXIT = wx.NewId()
MENU_ID_PREFERENCES = wx.NewId()
MENU_ID_OVERLAY_DARK = wx.NewId()
MENU_ID_OVERLAY_SIZE_TO_GRID = wx.NewId()
MENU_ID_OVERLAY_SNAP = wx.NewId()
MENU_ID_OVERLAY_RESET = wx.NewId()
MENU_ID_OVERLAY_CLOSE = wx.NewId()

# Menu Title
MENU_TITLE_EXIT = "Exit"
MENU_TITLE_PREFERENCES = "Preferences"
MENU_TITLE_OVERLAY_DARK = "Dark Overlays"
MENU_TITLE_OVERLAY_SIZE_TO_GRID = "Size Overlays to Grid"
MENU_TITLE_OVERLAY_SNAP = "Snap Overlays to Edges"
MENU_TITLE_OVERLAY_RESET = "Reset Overlays"
MENU_TITLE_OVERLAY_CLOSE = "Close Overlays"

# Menu Tip
MENU_TIP_EXIT = "Exits the program."
MENU_TIP_PREFERENCES = "Change program settings"
MENU_TIP_OVERLAY_DARK = "Toggles dark theme for overlays"
MENU_TIP_OVERLAY_SIZE_TO_GRID = "Toggles sizing overlays to grid"
MENU_TIP_OVERLAY_SNAP = "Toggles snapping overlays to screen edges"
MENU_TIP_OVERLAY_RESET = "Reset all overlays' position and size"
MENU_TIP_OVERLAY_CLOSE = "Close all open overlays"
MENU_TIP_OVERLAY_SELECT = "Toggle selected overlay"
