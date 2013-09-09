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

import wx, random, time, locale, math
import log_analyzer
import raid, config

from threading import Thread, Event
from base import BaseOverlay
from logging import prnt

class ShareBar(wx.PyControl):
	def __init__(self, parent, id, style=wx.NO_BORDER):
		wx.PyControl.__init__(self, parent, id, style=style)

		self.value = 0
		self.label = None
		self.reversed = False
		self.Bind(wx.EVT_PAINT, self.OnPaint)

	def SetValue(self, v):
		self.value = v

	def SetLabel(self, text):
		self.label = text

	def SetReversed(self, r):
		self.reversed = r

	def DoGetBestSize(self):
		best = wx.Size(0, 15)
		return best

	def OnPaint(self, event):
		dc = wx.BufferedPaintDC(self)
		width, height = self.GetClientSize()
		if not width or not height:
			return

		fillWidth = round(float(width) * self.value)

		bgColor = self.GetBackgroundColour()
		bgR, bgG, bgB = bgColor.Get(False)
		iBgR = 255 - bgR
		iBgG = 255 - bgG
		iBgB = 255 - bgB
		bgColor.Set(iBgR + (bgR - iBgR) * 0.5, iBgG + (bgG - iBgG) * 0.5, iBgB + (bgB - iBgB) * 0.5, 255)
		bgBrush = wx.Brush(bgColor, wx.SOLID)

		fgColor = self.GetForegroundColour()
		fgBrush = wx.Brush(fgColor, wx.SOLID)

		dc.SetBackground(bgBrush)
		dc.Clear()

		dc.SetBrush(fgBrush)
		dc.SetPen(wx.TRANSPARENT_PEN)

		if self.reversed:
			dc.DrawRectangle(width - fillWidth, 0, width, height)
		else:
			dc.DrawRectangle(0, 0, fillWidth, height)

		dc.SetFont(self.GetFont())
		dc.SetTextForeground((bgR, bgG, bgB))

		if self.label:
			text = self.label
		else:
			text = "%.2f%%"%(float(self.value) * 100.0)
		textWidth, textHeight = dc.GetTextExtent(text)

		dc.DrawText(text, (width / 2) - (textWidth / 2), (height / 2) - (textHeight / 2))

class ColoredRect(wx.PyControl):
	def __init__(self, parent, id, style=wx.NO_BORDER):
		wx.PyControl.__init__(self, parent, id, style=style)

		self.Bind(wx.EVT_PAINT, self.OnPaint)

	def DoGetBestSize(self):
		best = wx.Size(15, 15)
		return best

	def OnPaint(self, event):
		dc = wx.BufferedPaintDC(self)
		width, height = self.GetClientSize()
		if not width or not height:
			return

		fgColor = self.GetForegroundColour()
		fgBrush = wx.Brush(fgColor, wx.SOLID)

		dc.SetBackground(fgBrush)
		dc.Clear()

class BaseListOverlay(BaseOverlay):
	LEFT = wx.ALIGN_LEFT
	RIGHT = wx.ALIGN_RIGHT
	CENTER = wx.ALIGN_CENTRE

	def __init__(self, title="", size=(300, 100)):
		self.defaultTextColor = 0
		self.columnCount = 0
		self.columnTypes = []
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
		self.listFont = wx.Font(config.get("overlayListFontSize"), wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, False, "Arial")

	def setColumns(self, cols, shares, aligns):
		i = 0
		for text in cols:
			self.columnTypes.append(cols[i])
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
					colType = self.columnTypes[x]
					if colType == 'ShareBar':
						columnView = ShareBar(self.panel, -1)
					elif colType == 'ColoredRect':
						columnView = ColoredRect(self.panel, -1)
					else:
						columnView = wx.StaticText(self.panel, -1, "", style=align)
					rowBox.Add(columnView, share, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
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
				colType = self.columnTypes[x]
				columnView = rowBox.GetItem(x).GetWindow()
				if colType == 'ShareBar':
					columnView.SetValue(col)
					columnView.SetBackgroundColour(self.getBackgroundColor())
					columnView.SetForegroundColour(row['rowColor'])
				elif colType == 'ColoredRect':
					columnView.SetForegroundColour(col)
				else:
					columnView.SetFont(self.listFont)
					columnView.SetLabel(col)
					columnView.SetForegroundColour(row['rowColor'])
				x += 1
			i += 1

		self.Thaw()

	def updateColors(self):
		self.defaultTextColor = self.getForegroundColor()
		BaseOverlay.updateColors(self)

