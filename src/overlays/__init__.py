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

from base import BaseOverlay
import config

# Import overlay classes
from avg_dps import AverageDPSOverlay
from damage_dealt import DamageDealtOverlay
from timer import FightTimerOverlay
from raid_damage import RaidDamageOverlay

overlayCategories = [
	{
		'name': 'self',
		'title': 'Self'
	},
	{
		'name': 'raid',
		'title': 'Raid-wide'
	}
]

overlayList = [
# Self
	{
		'name': 'avg_dps',
		'title': 'Avg. DPS',
		'category': 'self',
		'class': AverageDPSOverlay
	},
	{
		'name': 'damage_dealt',
		'title': 'Damage Dealt',
		'category': 'self',
		'class': DamageDealtOverlay
	},
	{
		'name': 'fight_timer',
		'title': 'Fight Timer',
		'category': 'self',
		'class': FightTimerOverlay
	},
# Raid-wide
	{
		'name': 'raid_damage',
		'title': 'Damage',
		'category': 'raid',
		'class': RaidDamageOverlay
	},
]

# This variable will be filled with overlay objects keyed to the overlay
# name.
openOverlays = {}
isOverlayBeingDragged = False

def GetOverlayCategoryList():
	global overlayCategories
	return overlayCategories

def GetOverlayList():
	global overlayList
	return overlayList

def SpawnOverlay(name):
	global overlayList, openOverlays
	class_ = None
	for overlay in overlayList:
		if overlay == '-':
			continue
		if overlay['name'] == name:
			class_ = overlay['class']
			break
	if class_ == None:
		print "ERROR: No such overlay as '%s'"%name
		return
	inst = class_()
	inst.Show()
	openOverlays[name] = inst

def KillOverlay(name):
	global openOverlays
	if not (name in openOverlays.keys()):
		print "ERROR: Overlay '%s' not open."%name
		return
	overlay = openOverlays[name]
	overlay.Destroy()
	del openOverlays[name]

def KillAllOverlays():
	print "Closing overlays..."
	global openOverlays
	for name, overlay in openOverlays.iteritems():
		overlay.Destroy()
	openOverlays = {}

def IsOverlayOpen(targetName):
	for name, overlay in openOverlays.iteritems():
		if name == targetName:
			return True
	return False

def ToggleOverlay(name):
	global openOverlays
	if name in openOverlays.keys():
		KillOverlay(name)
	else:
		SpawnOverlay(name)

def ToggleDarkTheme():
	global openOverlays
	if IsDarkTheme():
		config.Set("overlayBgColor", "#FFFFFF")
		config.Set("overlayFgColor", "#000000")
	else:
		config.Set("overlayBgColor", "#000000")
		config.Set("overlayFgColor", "#FFFFFF")
	for overlay in openOverlays.values():
		overlay.updateColors()

def IsDarkTheme():
	return config.Get("overlayBgColor") == "#000000"

def SetOverlayBeingDragged(val):
	global isOverlayBeingDragged
	isOverlayBeingDragged = val

def IsOverlayBeingDragged():
	global isOverlayBeingDragged
	return isOverlayBeingDragged

def ResetOverlays():
	print "Resetting overlays..."
	for overlay in overlayList:
		config.Remove("overlay_%s_pos"%overlay['class'].__name__)
		config.Remove("overlay_%s_size"%overlay['class'].__name__)
