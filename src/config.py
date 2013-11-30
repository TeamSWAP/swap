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

import atexit
import json
import traceback
import os

import wx

from logging import prnt

defaults = {
    'overlayBgColor': 0x000000,
    'overlayFgColor': 0xFFFFFF,
    'overlayListFontSize': 10,
    'overlayListSelfColor': 0x1EADFF,
    'overlayOpacity': 150,
    'overlayHeaderFontSize': 13,
    'overlaySizeToGrid': True,
    'overlayClickThrough': False,
    'overlaySnap': True,
    'neverUpdateInSWTOR': False
}

settings = defaults

def load():
    global settings
    prnt("Loading settings...")

    # Setup a save on exit.
    atexit.register(save)

    if not os.path.exists('settings.json'):
       return

    try:
       f = open('settings.json', 'r')
       data = json.loads(f.read())
       f.close()
    except Exception, e:
       prnt(traceback.format_exc())
    else:
       settings = data

    # Convert from old format
    bg = get("overlayBgColor")
    if isinstance(bg, basestring):
       prnt("Legacy overlay colors found, converting...")
       bg = int(bg[1:], 16)
       set("overlayBgColor", bg)

       fg = get("overlayFgColor")
       fg = int(fg[1:], 16)
       set("overlayFgColor", fg)

def save():
    f = open('settings.json', 'w')
    json.dump(settings, f, indent=4, sort_keys=True)
    f.close()

def get(name):
    global settings
    if name in settings.keys():
       return settings[name]
    if name in defaults.keys():
       return defaults[name]
    return None

def getXY(name):
    xy = get(name)
    if xy == None:
       return None
    x = (xy >> 16) & 0xFFFF
    y = xy & 0xFFFF
    return [x, y]

def getColor(name):
    xy = get(name)
    if xy == None:
       return None
    r = (xy >> 16) & 0xFF
    g = (xy >> 8) & 0xFF
    b = xy & 0xFF
    return wx.Colour(r, g, b, 255)

def set(name, value):
    settings[name] = value

def setXY(name, value):
    x, y = value
    xy = x
    xy = (xy << 16) + y
    set(name, xy)

def setColor(name, value):
    (r, g, b) = value.Get(False)
    xy = r
    xy = (xy << 8) + g
    xy = (xy << 8) + b
    set(name, xy)

def remove(name):
    global settings
    if name in settings.keys():
       del settings[name]
