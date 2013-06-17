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

import wx, wx.grid, random, time, locale
from threading import Thread, Event
from base import BaseOverlay
from logging import prnt
import log_analyzer
import raid

class RaidDamageOverlay(BaseOverlay):
	def __init__(self):
		BaseOverlay.__init__(self, title="Raid Damage", size=(300, 150))

		self.Bind(wx.EVT_WINDOW_DESTROY, self.OnClose)

		analyzer = log_analyzer.Get()
		analyzer.registerFrame(self)
		self.OnAnalyzerTick(analyzer)

	def createUI(self):
		BaseOverlay.createUI(self)

		# List
		self.grid = wx.grid.Grid(self.panel, -1)
		self.grid.CreateGrid(1, 3)
		self.grid.SetRowLabelSize(0)
		self.grid.SetColLabelSize(0)
		self.grid.SetSelectionBackground(wx.Colour(0, 0, 0, 0))
		self.grid.DisableDragColSize()
		self.grid.DisableDragRowSize()
		self.grid.DisableDragColMove()
		self.grid.EnableGridLines(False)
		self.grid.EnableEditing(False)

		self.grid.SetColLabelValue(0, "Player")
		self.grid.SetColLabelValue(1, "Damage")
		self.grid.SetColLabelValue(2, "%")

		self.box.Add(self.grid, 0, wx.EXPAND | wx.ALL, 10)

	def updateColors(self):
		self.grid.SetDefaultCellBackgroundColour(self.getBackgroundColor())
		self.grid.SetDefaultCellTextColour(self.getForegroundColor())
		BaseOverlay.updateColors(self)

	def OnClose(self, event):
		log_analyzer.Get().unregisterFrame(self)

	def OnAnalyzerTick(self, analyzer):
		self.grid.BeginBatch()
		currentRowCount = self.grid.GetNumberRows()
		if currentRowCount > 0:
			self.grid.DeleteRows(0, currentRowCount)
		count = len(raid.playerData)
		if count > 0:
			self.grid.AppendRows(count)

		index = 0
		for player in raid.playerData:
			self.grid.SetCellValue(index, 0, player['name'][1:])
			self.grid.SetCellValue(index, 1, locale.format("%d", player['totalDamage'], grouping=True))
			index += 1
		self.grid.AutoSizeColumns()
		self.grid.EndBatch()

