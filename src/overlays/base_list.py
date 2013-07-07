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
import log_analyzer
import raid, config

from threading import Thread, Event
from base import BaseOverlay
from logging import prnt

class BaseListOverlay(BaseOverlay):
	LEFT = wx.ALIGN_LEFT
	RIGHT = wx.ALIGN_RIGHT
	CENTER = wx.ALIGN_CENTRE

	def __init__(self, title="", size=(300, 100)):
		self.defaultTextColor = 0
		self.columnCount = 0
		self.columnShare = []
		self.columnAlign = []
		self.rowData = []

		BaseOverlay.__init__(self, title=title, size=size)

	def createUI(self):
		BaseOverlay.createUI(self)

		self.raidListBox = wx.BoxSizer(wx.VERTICAL)

		self.box.Add(self.raidListBox, 1, wx.EXPAND | wx.ALL, 10)

	def updateUI(self):
		BaseOverlay.updateUI(self)
		self.listFont = wx.Font(config.Get("overlayListFontSize"), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial")

	def setColumns(self, cols, shares, aligns):
		i = 0
		for text in cols:
			self.columnShare.append(shares[i])
			self.columnAlign.append(aligns[i])
			i += 1
		self.columnCount = i

	def clearList(self):
		self.rowData = []

	def addRow(self, columns, rowColor=None):
		if rowColor == None:
			rowColor = self.defaultTextColor

		self.rowData.append({'columns': columns, 'rowColor': rowColor})

	def beginBatch(self):
		pass

	def endBatch(self):
		self.Freeze()

		sizerRowCount = len(self.raidListBox.GetChildren())
		delta = len(self.rowData) - sizerRowCount
		if delta > 0:
			for i in range(0, delta):
				rowBox = wx.BoxSizer(wx.HORIZONTAL)
				x = 0
				for share in self.columnShare:
					align = self.columnAlign[x]
					columnText = wx.StaticText(self.panel, -1, "", style=align)
					rowBox.Add(columnText, share)
					x += 1
				self.bindViews(rowBox)
				self.raidListBox.Add(rowBox, 0, wx.EXPAND)
				sizerRowCount += 1
		elif delta < 0:
			for i in range(0, -delta):
				self.raidListBox.Hide(sizerRowCount - 1)
				self.raidListBox.Remove(sizerRowCount - 1)
				sizerRowCount -= 1

		i = 0
		for row in self.rowData:
			rowBox = self.raidListBox.GetItem(i).GetSizer()
			x = 0
			for col in row['columns']:
				columnText = rowBox.GetItem(x).GetWindow()
				columnText.SetFont(self.listFont)
				columnText.SetLabel(col)
				columnText.SetForegroundColour(row['rowColor'])
				x += 1
			i += 1

		self.Thaw()

	def updateColors(self):
		self.defaultTextColor = self.getForegroundColor()
		BaseOverlay.updateColors(self)

