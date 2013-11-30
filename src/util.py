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
import ctypes
import ConfigParser
from ctypes.wintypes import MAX_PATH
from threading import Lock

import wx

from logging import prnt

def wxFunc(x):
    return lambda *args, **kwargs: wx.CallAfter(x, *args, **kwargs)

def formatDuration(s):
    if s < 1:
       return "%.1fs"%s
    elif s < 60:
       return "%02ds"%s
    elif s < 3600:
       return "%02dm %02ds"%(s / 60, s%60)
    else:
       return "%dh %02dm %02ds"%((s / 3600), (s%3600) / 60, s%60)

def getAccountIni():
    dll = ctypes.windll.shell32
    buf = ctypes.create_unicode_buffer(MAX_PATH + 1)
    if dll.SHGetSpecialFolderPathW(None, buf, 0x1C, False):
       path = buf.value + "\\SWTOR\\swtor\\settings\\"
       if not os.path.exists(path):
          return None
       files = os.listdir(path)
       accountFiles = []
       for f in files:
          if f.endswith('_Account.ini'):
             accountFiles.append(path + f)
       accountFile = max(accountFiles, key=os.path.getmtime)
       return accountFile
    return None

def isCombatLoggingEnabled():
    ini = getAccountIni()
    if ini:
       config = ConfigParser.RawConfigParser()
       config.read(ini)
       cabf4 = config.get("Settings", "cabf_4")
       if long(cabf4) & (1 << 14):
          return True
       if cabf4 != None and cabf4 != "":
          return False
    return True

def enableCombatLogging():
    ini = getAccountIni()
    if ini:
       config = ConfigParser.RawConfigParser()
       config.read(ini)
       cabf4 = config.get("Settings", "cabf_4")
       config.set("Settings", "cabf_4", long(cabf4) | (1 << 14))
       with open(ini, 'wb') as configFile:
          config.write(configFile)

def div(x, y):
    if y == 0:
       return 0
    return float(x) / float(y)

class SimpleThreadInterface(object):
    """Provides a simple message queue system using existing
    methods."""

    def __init__(self):
       self.__msgs = []
       self.__lock = Lock()

    def processNextMessage(self):
       with self.__lock:
          if not self.__msgs:
             return

          top = self.__msgs.pop(0)
       top()

    def callThread(self, func, *args, **kwargs):
       with self.__lock:
          self.__msgs.append(lambda:func(*args, **kwargs))

    def wrappedCallThread(self, func, *args, **kwargs):
       return lambda:self.callThread(func, *args, **kwargs)
