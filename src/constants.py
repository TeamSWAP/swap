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

VERSION = "1.0"
VERSION_INT = 1
URL_CHECK = "http://faultexception.com/torbot/check.php"
IS_COMPILED = 'frozen' in dir(sys)

# Static Messages
MSG_CLOSE_CONFIRM_TEXT = "Are you sure you want to close SWAP? This will end your parsing session."
MSG_CLOSE_CONFIRM_TITLE = "Confirm Exit"

# Menu ID
MENU_ID_EXIT = wx.NewId()
MENU_ID_PREFERENCES = wx.NewId()
MENU_ID_OVERLAY_DARK = wx.NewId()

# Menu Title
MENU_TITLE_EXIT = "Exit"
MENU_TITLE_PREFERENCES = "Preferences"
MENU_TITLE_OVERLAY_DARK = "Dark Overlays"

# Menu Tip
MENU_TIP_EXIT = "Exits the program."
MENU_TIP_PREFERENCES = "Change program settings"
MENU_TIP_OVERLAY_DARK = "Toggles dark theme for overlays"
MENU_TIP_OVERLAY_SELECT = "Toggle selected overlay"
