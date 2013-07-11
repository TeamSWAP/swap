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

import config

from base import BaseOverlay
from logging import prnt

# Import overlay classes
from self import *
from raid_wide import *

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
		'name': 'damage_dealt',
		'title': 'Damage Dealt',
		'category': 'self',
		'class': DamageDealtOverlay
	},
	{
		'name': 'avg_dps',
		'title': 'Avg. DPS',
		'category': 'self',
		'class': AverageDPSOverlay
	},
	{ 'name': '-', 'category': 'self' },
	{
		'name': 'healing_done',
		'title': 'Healing Done',
		'category': 'self',
		'class': HealingDoneOverlay
	},
	{
		'name': 'avg_hps',
		'title': 'Avg. HPS',
		'category': 'self',
		'class': AverageHPSOverlay
	},
	{ 'name': '-', 'category': 'self' },
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
	{
		'name': 'raid_damage_taken',
		'title': 'Damage Taken',
		'category': 'raid',
		'class': RaidDamageTakenOverlay
	},
	{
		'name': 'raid_avg_dps',
		'title': 'Average DPS',
		'category': 'raid',
		'class': RaidAvgDPSOverlay
	},
	{ 'name': '-', 'category': 'raid' },
	{
		'name': 'raid_healing',
		'title': 'Healing',
		'category': 'raid',
		'class': RaidHealingOverlay
	},
	{
		'name': 'raid_healing_received',
		'title': 'Healing Received',
		'category': 'raid',
		'class': RaidHealingReceivedOverlay
	},
	{
		'name': 'raid_avg_hps',
		'title': 'Average HPS',
		'category': 'raid',
		'class': RaidAvgHPSOverlay
	},
	{ 'name': '-', 'category': 'raid' },
	{
		'name': 'raid_threat',
		'title': 'Threat',
		'category': 'raid',
		'class': RaidThreatOverlay
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
		if overlay['name'] == '-':
			continue
		if overlay['name'] == name:
			class_ = overlay['class']
			break
	if class_ == None:
		prnt("ERROR: No such overlay as '%s'"%name)
		return
	inst = class_()
	inst.Show()
	openOverlays[name] = inst

def KillOverlay(name):
	global openOverlays
	if not (name in openOverlays.keys()):
		prnt("ERROR: Overlay '%s' not open."%name)
		return
	overlay = openOverlays[name]
	overlay.Destroy()
	del openOverlays[name]

def KillAllOverlays():
	prnt("Closing overlays...")
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
		config.Set("overlayBgColor", 0xFFFFFF)
		config.Set("overlayFgColor", 0x000000)
	else:
		config.Set("overlayBgColor", 0x000000)
		config.Set("overlayFgColor", 0xFFFFFF)
	for overlay in openOverlays.values():
		overlay.updateColors()

def IsDarkTheme():
	return config.Get("overlayBgColor") == 0

def SetOverlayBeingDragged(val):
	global isOverlayBeingDragged
	isOverlayBeingDragged = val

def IsOverlayBeingDragged():
	global isOverlayBeingDragged
	return isOverlayBeingDragged

def ResetOverlays():
	prnt("Resetting overlays...")
	for overlay in overlayList:
		if overlay['name'] == '-':
			continue
		config.Remove("overlay_%s_pos"%overlay['class'].__name__)
		config.Remove("overlay_%s_size"%overlay['class'].__name__)
