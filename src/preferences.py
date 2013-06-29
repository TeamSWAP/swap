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
from constants import *
from logging import prnt
import config
import log_parser

class PreferencesDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, "Preferences", size=(700, 500))

		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.notebook = wx.Notebook(self)

		headerFont = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
		nameFont = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL)

		# -----------------------------------
		# Overlay
		# -----------------------------------
		self.overlayPanel = wx.Panel(self.notebook)
		self.overlaySizer = wx.BoxSizer(wx.VERTICAL)

		header = wx.StaticText(self.overlayPanel, -1, "All Overlays")
		header.SetFont(headerFont)
		self.overlaySizer.Add(header, 0, wx.ALL, 10)

		# Header font size
		self.headerFontSizeBox = wx.BoxSizer(wx.HORIZONTAL)
		self.headerFontSizeLabel = wx.StaticText(self.overlayPanel, -1, "Header font size")
		self.headerFontSizeLabel.SetFont(nameFont)
		self.headerFontSizeSlider = wx.Slider(self.overlayPanel, -1, 8, 5, 18, style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS, size=(200, 20))
		self.headerFontSizeSlider.SetTickFreq(1, 1)
		self.headerFontSizeSlider.SetValue(config.Get("overlayHeaderFontSize"))
		self.headerFontSizeBox.Add(self.headerFontSizeLabel, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
		self.headerFontSizeBox.Add(self.headerFontSizeSlider, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
		self.overlaySizer.Add(self.headerFontSizeBox, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

		header = wx.StaticText(self.overlayPanel, -1, "Raid Lists")
		header.SetFont(headerFont)
		self.overlaySizer.Add(header, 0, wx.ALL, 10)

		# List font size
		self.listFontSizeBox = wx.BoxSizer(wx.HORIZONTAL)
		self.listFontSizeLabel = wx.StaticText(self.overlayPanel, -1, "Font size")
		self.listFontSizeLabel.SetFont(nameFont)
		self.listFontSizeSlider = wx.Slider(self.overlayPanel, -1, 8, 5, 18, style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS, size=(200, 20))
		self.listFontSizeSlider.SetTickFreq(1, 1)
		self.listFontSizeSlider.SetValue(config.Get("overlayListFontSize"))
		self.listFontSizeBox.Add(self.listFontSizeLabel, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
		self.listFontSizeBox.Add(self.listFontSizeSlider, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
		self.overlaySizer.Add(self.listFontSizeBox, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

		# List me size (RGB slider)
		self.listRGBBox = wx.BoxSizer(wx.HORIZONTAL)
		self.listRGBLabel = wx.StaticText(self.overlayPanel, -1, "Self indicator color")
		self.listRGBLabel.SetFont(nameFont)
		self.listRGBButton = wx.Button(self.overlayPanel, -1, log_parser.GetThread().parser.me, size=(100, -1))
		self.listRGBButton.SetForegroundColour(config.GetColor("overlayListSelfColor"))
		self.listRGBButton.Bind(wx.EVT_BUTTON, self.OnListSelfColorClick)
		self.listRGBBox.Add(self.listRGBLabel, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
		self.listRGBBox.Add(self.listRGBButton, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
		self.overlaySizer.Add(self.listRGBBox, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

		self.overlayPanel.SetSizer(self.overlaySizer)
		self.overlayPanel.Layout()
		self.notebook.AddPage(self.overlayPanel, "Overlay")

		self.sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)

		# Create bottom buttons
		self.sizer.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.BOTTOM | wx.ALIGN_RIGHT, 5)

		self.SetSizer(self.sizer)
		self.Bind(wx.EVT_BUTTON, self.OnOK, id=wx.ID_OK)

	def OnOK(self, event):
		config.Set("overlayHeaderFontSize", self.headerFontSizeSlider.GetValue())
		config.Set("overlayListFontSize", self.listFontSizeSlider.GetValue())
		config.SetColor("overlayListSelfColor", self.listRGBButton.GetForegroundColour())
		self.Destroy()

	def OnListSelfColorClick(self, event):
		dialog = wx.ColourDialog(self)
		if dialog.ShowModal() == wx.ID_OK:
			(red, green, blue) = dialog.GetColourData().GetColour().Get()
			color = wx.Colour(red, green, blue, 255)
			self.listRGBButton.SetForegroundColour(color)
