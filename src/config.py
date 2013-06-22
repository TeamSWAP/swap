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

import atexit, json, traceback, os
from logging import prnt

defaults = {
	'overlayBgColor': '#000000',
	'overlayFgColor': '#FFFFFF',
	'overlayListFontSize': 10
}

settings = defaults

def Load():
	global settings
	prnt("Loading settings...")

	# Setup a save on exit.
	atexit.register(Save)

	if not os.path.exists('settings.json'):
		return

	data = None
	try:
		f = open('settings.json', 'r')
		data = json.loads(f.read())
		f.close()
	except Exception, e:
		prnt(traceback.format_exc())
	if data != None:
		settings = data

def Save():
	f = open('settings.json', 'w')
	json.dump(settings, f, indent=4, sort_keys=True)
	f.close()

def Get(name):
	global settings
	if name in settings.keys():
		return settings[name]
	if name in defaults.keys():
		return defaults[name]
	return None

def GetXY(name):
	xy = Get(name)
	if xy == None:
		return None
	x = (xy >> 16) & 0xFFFF
	y = xy & 0xFFFF
	return [x, y]

def Set(name, value):
	settings[name] = value

def SetXY(name, value):
	x, y = value
	xy = x
	xy = (xy << 16) + y
	Set(name, xy)

def Remove(name):
	global settings
	if name in settings.keys():
		del settings[name]
