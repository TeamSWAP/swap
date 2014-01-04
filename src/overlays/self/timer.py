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

import time
import locale
import util
from threading import Thread, Event

import wx

import log_analyzer
from overlays.base import BaseOverlay
from logging import prnt

class FightTimerOverlay(BaseOverlay):
    def __init__(self):
        BaseOverlay.__init__(self, title="Fight Timer")

        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnClose)

        analyzer = log_analyzer.get()
        analyzer.registerFrame(self)
        self.onAnalyzerTick(analyzer)

    def createUI(self):
        BaseOverlay.createUI(self)

        # Timer
        self.timer = wx.StaticText(self.panel, -1, "")
        self.timer.SetFont(wx.Font(24, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.timer.SetSize(self.timer.GetBestSize())
        self.box.Add(self.timer, 0, wx.ALL, 10)

    def updateColors(self):
        self.timer.SetForegroundColour(self.getForegroundColor())
        BaseOverlay.updateColors(self)

    def OnClose(self, event):
        log_analyzer.get().unregisterFrame(self)

    def onAnalyzerTick(self, analyzer):
        self.timer.SetLabel(util.formatDuration(analyzer.combatDurationLinear))
