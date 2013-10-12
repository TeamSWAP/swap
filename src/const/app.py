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

import os
import sys

import wx

# Versioning
VERSION = "0.8.9a"
VERSION_INT = 43
IS_FROZEN = 'frozen' in dir(sys)

# Server addresses
UPDATES_URL = "http://faultexception.com/swap/check_updates.php"
LOG_SEND_URL = "http://faultexception.com/swap/sendlog.php"
PARSER_SERVER_ADDR = ("swapserver.no-ip.biz", 57680)
NODE_SERVER_ADDR = "swapserver.no-ip.biz:57681"

# Boss list
MOB_BOSS_LIST = map(str.lower, (
	# DF
	"Nefra, Who Bars the Way",
	"Gate Commander Draxus",
	"Grob'thok, Who Feeds the Forge",
	"Corruptor Zero",
	"Dread Master Brontes",
	# DP
	"Dread Master Bestia",
	"Dread Master Tyrans",
	"Dread Master Calphayus",
	"Dread Master Raptus",
	# Toborro's Courtyard
	"Golden Fury"
	# TFB
	"The Writhing Horror",
	"Operator IX",
	"Kephess the Undying",
	"The Terror from Beyond",
	# S&V
	"Dash'Roode",
	"Titan 6",
	"Thrasher",
	"Operations Chief",
	"Olok the Shadow",
	"Dread Master Styrak",
	# EC
	"Colonel Vorgath",
	"Warlord Kephess",
	# KP
	"Bonethrasher",
	"Foreman Crusher",
	"G4-B3 Heavy Fabricator",
	"Karagga the Unyielding",
	# EV
	"Annihilation Droid XRR-3",
	"Gharj",
))

MOB_BOSS_MAP = {
	# DP
	("Dread Larva", "Dread Monster"): "Dread Master Bestia",
	("Dread Master Bestia", "Dread Master Raptus"): "The Dread Masters",
	# TFB
	("Heirad", "Ciphas", "Kel'sara"): "The Dread Guard",
	# S&V
	("Captain Horric", "Vilus Garr", "Tu'chuk", "Sunder"): "The Cartel Warlords",
	# EC
	("Firebrand", "Stormcaller"): "Firebrand and Stormcaller Tanks",
	("Zorn", "Toth"): "Zorn and Toth",
	# KP
	("Jarg", "Sorno"): "Jarg & Sorno",
	# EV
	"Soa": "The Infernal One",
}
MOB_BOSS_MAP_KEYS = MOB_BOSS_MAP.keys()

# Static Messages
MSG_FAILED_KEY_GENERATION_TEXT = "Failed to generate new key! Please report this to the developer."
MSG_FAILED_KEY_GENERATION_TITLE = "Error"
MSG_FAILED_JOIN_INVALID_KEY_TEXT = "No such key was found"
MSG_FAILED_JOIN_INVALID_KEY_TITLE = "Error"
MSG_FAILED_JOIN_UPDATE_REQUIRED_TEXT = "Your SWAP client is too old! Please close SWAP and run the SWAP shortcut (if installed), or run updater.exe"
MSG_FAILED_JOIN_UPDATE_REQUIRED_TITLE = "Error"
MSG_COMBAT_LOGGING_DISABLED_TEXT = "Combat logging is disabled. If SWTOR is running please enter enable Combat Logging in Preferences. If SWTOR is not running, click OK and we'll take care of it for you."
MSG_COMBAT_LOGGING_DISABLED_TITLE = "Whoops!"
MSG_CONNECT_FAILED_TITLE = "Connection failed"
MSG_CONNECT_FAILED_TEXT = "Failed to connect to SWAP server. Please try again."
MSG_NODE_CONNECT_FAILED_TITLE = "Player connection failed"
MSG_NODE_CONNECT_FAILED_TEXT = "Failed to connect to the player hosting the raid. You may need to generate a new key. Sorry :/"

# Menu ID
MENU_ID_EXIT = wx.NewId()
MENU_ID_PREFERENCES = wx.NewId()
MENU_ID_ENRAGE_TIME = wx.NewId()
MENU_ID_OVERLAY_DARK = wx.NewId()
MENU_ID_OVERLAY_SIZE_TO_GRID = wx.NewId()
MENU_ID_OVERLAY_SNAP = wx.NewId()
MENU_ID_OVERLAY_CLICK_THROUGH = wx.NewId()
MENU_ID_OVERLAY_RESET = wx.NewId()
MENU_ID_OVERLAY_CLOSE = wx.NewId()
MENU_ID_HELP_UPDATES = wx.NewId()
MENU_ID_HELP_LOG = wx.NewId()
MENU_ID_HELP_SEND_LOG = wx.NewId()
MENU_ID_HELP_ABOUT = wx.NewId()

# Menu Title
MENU_TITLE_EXIT = "Exit"
MENU_TITLE_PREFERENCES = "Preferences"
MENU_TITLE_ENRAGE_TIME = "Set Enrage Timer..."
MENU_TITLE_OVERLAY_DARK = "Dark Overlays"
MENU_TITLE_OVERLAY_SIZE_TO_GRID = "Size Overlays to Grid"
MENU_TITLE_OVERLAY_SNAP = "Snap Overlays to Edges"
MENU_TITLE_OVERLAY_CLICK_THROUGH = "Click-through Overlays"
MENU_TITLE_OVERLAY_RESET = "Reset Overlays"
MENU_TITLE_OVERLAY_CLOSE = "Close Overlays"
MENU_TITLE_HELP_UPDATES = "Check for Updates..."
MENU_TITLE_HELP_LOG = "Open Debug Log"
MENU_TITLE_HELP_SEND_LOG = "Send Debug Log"
MENU_TITLE_HELP_ABOUT = "About SWAP"

# Menu Tip
MENU_TIP_EXIT = "Exits the program."
MENU_TIP_PREFERENCES = "Change program settings"
MENU_TIP_ENRAGE_TIME = "Set enrage timer"
MENU_TIP_OVERLAY_DARK = "Toggles dark theme for overlays"
MENU_TIP_OVERLAY_SIZE_TO_GRID = "Toggles sizing overlays to grid"
MENU_TIP_OVERLAY_SNAP = "Toggles snapping overlays to screen edges"
MENU_TIP_OVERLAY_CLICK_THROUGH = "Click-through Overlays"
MENU_TIP_OVERLAY_RESET = "Reset all overlays' position and size"
MENU_TIP_OVERLAY_CLOSE = "Close all open overlays"
MENU_TIP_OVERLAY_SELECT = "Toggle selected overlay"
MENU_TIP_HELP_UPDATES = "Check for Updates..."
MENU_TIP_HELP_LOG = "View Log"
MENU_TIP_HELP_SEND_LOG = "Send Log to Developers..."
MENU_TIP_HELP_ABOUT = "About"
