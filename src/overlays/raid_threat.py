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

import wx, wx.grid, random, time, locale, math
import config
import log_analyzer
import raid

from threading import Thread, Event
from base_list import BaseListOverlay
from logging import prnt

class RaidThreatOverlay(BaseListOverlay):
	def __init__(self):
		BaseListOverlay.__init__(self, title="Raid Threat", size=(300, 150))

		self.Bind(wx.EVT_WINDOW_DESTROY, self.OnClose)

		analyzer = log_analyzer.Get()
		analyzer.registerFrame(self)
		self.OnAnalyzerTick(analyzer)

	def createUI(self):
		BaseListOverlay.createUI(self)

		self.setColumns(["Player", "Threat", "%"], [2, 2, 1], [BaseListOverlay.LEFT, BaseListOverlay.LEFT, BaseListOverlay.RIGHT])

	def OnClose(self, event):
		if event.GetEventObject() == self:
			log_analyzer.Get().unregisterFrame(self)

	def OnAnalyzerTick(self, analyzer):
		self.beginBatch()
		self.clearList()

		def sortf(x, y):
			x = x['totalThreat']
			y = y['totalThreat']
			if x == y:
				return 0
			elif x < y:
				return 1
			else:
				return -1

		index = 0
		raidTotalThreat = 0
		for player in raid.playerData:
			raidTotalThreat += player['totalThreat']

		for player in sorted(raid.playerData, sortf):
			if player['totalThreat'] == 0:
				continue
			if raidTotalThreat > 0:
				percent = "%.2f"%((float(player['totalThreat']) / float(raidTotalThreat)) * 100.0)
			else:
				percent = "%.2f"%0

			color = self.getForegroundColor()
			if player['name'] == analyzer.parser.me:
				color = config.GetColor("overlayListSelfColor")

			self.addRow([player['name'][1:], locale.format("%d", player['totalThreat'], grouping=True), "%s%%"%percent], color)

			index += 1
		self.endBatch()
		self.panel.Layout()

