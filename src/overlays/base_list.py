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
import raid, config

class BaseListOverlay(BaseOverlay):
	LEFT = wx.ALIGN_LEFT
	RIGHT = wx.ALIGN_RIGHT
	CENTER = wx.ALIGN_CENTRE

	columnCount = 0
	columnShare = []
	columnAlign = []

	def __init__(self, title="", size=(300, 100)):
		BaseOverlay.__init__(self, title=title, size=size)

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

		self.box.Add(self.grid, 1, wx.EXPAND | wx.ALL, 10)

	def setColumns(self, cols, shares, aligns):
		i = 0
		for text in cols:
			self.grid.SetColLabelValue(i, text)
			self.columnShare.append(shares[i])
			self.columnAlign.append(aligns[i])
			i += 1
		self.columnCount = i

	def clearList(self):
		currentRowCount = self.grid.GetNumberRows()
		if currentRowCount > 0:
			self.grid.DeleteRows(0, currentRowCount)

	def addRow(self, columns, rowColor=wx.Colour(255, 255, 255, 255)):
		self.grid.AppendRows(1)
		row = self.grid.GetNumberRows() - 1
		i = 0
		for text in columns:
			self.grid.SetCellValue(row, i, text)
			self.grid.SetCellAlignment(row, i, self.columnAlign[i], wx.ALIGN_CENTRE)
			self.grid.SetCellFont(row, i, wx.Font(config.Get("overlayListFontSize"), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False, "Arial"))
			self.grid.SetCellTextColour(row, i, rowColor)
			i += 1

	def beginBatch(self):
		self.grid.BeginBatch()

	def endBatch(self):
		self.grid.EndBatch()

	def updateColors(self):
		self.grid.SetDefaultCellBackgroundColour(self.getBackgroundColor())
		self.grid.SetDefaultCellTextColour(self.getForegroundColor())
		BaseOverlay.updateColors(self)

	def OnSize(self, event):
		(width, height) = self.grid.GetSize()
		width -= 10

		self.grid.BeginBatch()
		for column in range(0, self.columnCount):
			share = self.columnShare[column]
			self.grid.SetColSize(column, width * share)
		self.grid.EndBatch()

		if event:
			event.Skip()

		self.panel.Layout()

