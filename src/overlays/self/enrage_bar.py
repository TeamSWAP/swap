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
import config
from overlays.base import BaseOverlay
from overlays.base_list import ShareBar
from logging import prnt

class EnrageBarOverlay(BaseOverlay):
    def __init__(self):
        BaseOverlay.__init__(self, title="Enrage")

        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnClose)

        analyzer = log_analyzer.get()
        analyzer.registerFrame(self)
        self.onAnalyzerTick(analyzer)

    def createUI(self):
        BaseOverlay.createUI(self)

        self.bar = ShareBar(self.panel, -1)
        self.bar.SetValue(0.0)
        self.bar.SetLabel("")
        self.bar.SetReversed(True)
        self.bar.SetSize(self.bar.GetBestSize())
        self.bar.SetForegroundColour("red")
        self.box.Add(self.bar, 1, wx.EXPAND | wx.ALL, 10)

    def updateColors(self):
        self.bar.SetBackgroundColour(self.getBackgroundColor())
        BaseOverlay.updateColors(self)

    def OnClose(self, event):
        log_analyzer.get().unregisterFrame(self)

    def onAnalyzerTick(self, analyzer):
        enrageTime = config.get("customEnrageTime")
        if not enrageTime:
            self.bar.SetValue(0)
            self.bar.SetLabel("")
            return

        enrageTime = float(enrageTime)

        self.bar.SetValue(1.0 - util.div(analyzer.combatDuration, enrageTime))
        self.bar.SetLabel(util.formatDuration(enrageTime - analyzer.combatDuration))
