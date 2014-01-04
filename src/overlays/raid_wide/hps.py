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

import random
import time
import locale
import math
from threading import Thread, Event

import wx

import config
import log_analyzer
import raid
import util
from overlays.base_list import BaseListOverlay
from logging import prnt

class RaidHPSOverlay(BaseListOverlay):
    def __init__(self):
        BaseListOverlay.__init__(self, title="Raid HPS", size=(300, 150))

        self.Bind(wx.EVT_WINDOW_DESTROY, self.OnClose)

        analyzer = log_analyzer.get()
        analyzer.registerFrame(self)
        self.onAnalyzerTick(analyzer)

    def createUI(self):
        BaseListOverlay.createUI(self)

        self.setColumns(["Player", "HPS", "ShareBar"], [1, 1, 1], [BaseListOverlay.LEFT, BaseListOverlay.LEFT, BaseListOverlay.RIGHT])

    def OnClose(self, event):
        if event.GetEventObject() == self:
            log_analyzer.get().unregisterFrame(self)

    def onAnalyzerTick(self, analyzer):
        self.beginBatch()
        self.clearList()

        index = 0
        raidTotalHealing = 0
        for player in raid.playerData:
            raidTotalHealing += player['totalHealing']

        for player in sorted(raid.playerData, key=lambda x:x['totalHealing'], reverse=True):
            if player['totalHealing'] == 0:
                continue
            if raidTotalHealing > 0:
                percent = "%.2f"%((float(player['totalHealing']) / float(raidTotalHealing)) * 100.0)
            else:
                percent = "%.2f"%0

            color = self.getForegroundColor()
            if player['name'] == analyzer.parser.me.rawName:
                color = config.getColor("overlayListSelfColor")

            hps = player['avgHps']
            percent = util.div(player['totalHealing'], raidTotalHealing)

            color = self.getForegroundColor()
            if player['name'] == analyzer.parser.me.rawName:
                color = config.getColor("overlayListSelfColor")

            self.addRow([player['name'][1:], locale.format("%.2f", hps, grouping=True), percent], color)

            index += 1
        self.endBatch()
        self.panel.Layout()
