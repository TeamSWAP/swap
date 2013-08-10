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

import wx

import config
import log_analyzer
import raid
import util
from overlays.base_list import BaseListOverlay
from logging import prnt

class TFBOp9Colors(BaseListOverlay):
	def __init__(self):
		BaseListOverlay.__init__(self, title="Operator IX", size=(300, 150))

		self.Bind(wx.EVT_WINDOW_DESTROY, self.OnClose)

		analyzer = log_analyzer.Get()
		analyzer.registerFrame(self)
		self.onAnalyzerTick(analyzer)

	def createUI(self):
		BaseListOverlay.createUI(self)

		self.setColumns(["ColoredRect", "String", "String"], [0, 1, 1], [BaseListOverlay.LEFT, BaseListOverlay.LEFT, BaseListOverlay.RIGHT])

	def OnClose(self, event):
		if event.GetEventObject() == self:
			log_analyzer.Get().unregisterFrame(self)

	def onAnalyzerTick(self, analyzer):
		self.beginBatch()
		self.clearList()

		playersPerColor = {
			1: [], 2: [], 3: [], 4: []
		}

		for player in raid.playerData:
			name = player['name'][1:]
			orb = player['tfbOrb']
			if orb:
				playersPerColor[orb].append(name)

		self.addRow([None, "Next Deletion", "Shields"])
		index = 0
		for colorId in ['blue', 'orange', 'purple', 'yellow']:
			index += 1

			count = 0
			nextDeletion = ""
			for player in playersPerColor[index]:
				if not nextDeletion:
					nextDeletion = player
				count += 1

			self.addRow([colorId, nextDeletion, str(count)])

		self.endBatch()
		self.panel.Layout()

