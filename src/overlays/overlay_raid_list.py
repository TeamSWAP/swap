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

		self.Bind(wx.EVT_SIZE, self.OnSize)
		self.OnSize(None)

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

		self.box.Add(self.grid, 1, wx.EXPAND | wx.ALL, 10)

	def updateColors(self):
		self.grid.SetDefaultCellBackgroundColour(self.getBackgroundColor())
		self.grid.SetDefaultCellTextColour(self.getForegroundColor())
		BaseOverlay.updateColors(self)

	def OnClose(self, event):
		log_analyzer.Get().unregisterFrame(self)

	def OnSize(self, event):
		(width, height) = self.grid.GetSize()
		width -= 10

		self.grid.BeginBatch()
		self.grid.SetColSize(0, width * 0.40)
		self.grid.SetColSize(1, width * 0.40)
		self.grid.SetColSize(2, width * 0.20)
		self.grid.EndBatch()

		if event:
			event.Skip()

	def OnAnalyzerTick(self, analyzer):
		self.grid.BeginBatch()
		currentRowCount = self.grid.GetNumberRows()
		if currentRowCount > 0:
			self.grid.DeleteRows(0, currentRowCount)
		count = len(raid.playerData)
		if count > 0:
			self.grid.AppendRows(count)

		def sortf(x, y):
			x = x['totalDamage']
			y = y['totalDamage']
			if x == y:
				return 0
			elif x < y:
				return 1
			else:
				return -1

		index = 0
		raidTotalDamage = 0
		for player in raid.playerData:
			raidTotalDamage += player['totalDamage']

		for player in sorted(raid.playerData, sortf):
			if player['totalDamage'] == 0:
				continue
			if raidTotalDamage > 0:
				percent = "%.2f"%((float(player['totalDamage']) / float(raidTotalDamage)) * 100.0)
			else:
				percent = "%.2f"%0

			color = self.getForegroundColor()
			if player['name'] == analyzer.parser.me:
				color = wx.Colour(30, 173, 255, 255)

			self.grid.SetCellValue(index, 0, player['name'][1:])
			self.grid.SetCellValue(index, 1, locale.format("%d", player['totalDamage'], grouping=True))
			self.grid.SetCellValue(index, 2, percent + "%")

			# Configure cells
			self.grid.SetCellAlignment(index, 0, wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
			self.grid.SetCellAlignment(index, 1, wx.ALIGN_LEFT, wx.ALIGN_CENTRE)
			self.grid.SetCellAlignment(index, 2, wx.ALIGN_RIGHT, wx.ALIGN_CENTRE)
			self.grid.SetCellFont(index, 0, wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))
			self.grid.SetCellFont(index, 1, wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))
			self.grid.SetCellFont(index, 2, wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))
			self.grid.SetCellTextColour(index, 0, color)
			self.grid.SetCellTextColour(index, 1, color)
			self.grid.SetCellTextColour(index, 2, color)

			index += 1
		self.grid.EndBatch()
		self.panel.Layout()
