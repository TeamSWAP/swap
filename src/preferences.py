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

		self.sliderOptions = {}
		self.colorOptions = {}

		self.headerFont = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
		self.nameFont = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL)

		# -----------------------------------
		# Overlay
		# -----------------------------------
		self.overlayPanel = wx.Panel(self.notebook)
		self.overlaySizer = wx.BoxSizer(wx.VERTICAL)

		header = wx.StaticText(self.overlayPanel, -1, "All Overlays")
		header.SetFont(self.headerFont)
		self.overlaySizer.Add(header, 0, wx.ALL, 10)

		self.addSliderOption("overlayOpacity", "Opacity", 0, 255, self.overlayPanel, self.overlaySizer)
		self.addSliderOption("overlayHeaderFontSize", "Header font size", 8, 18, self.overlayPanel, self.overlaySizer)
		self.addColorOption("overlayBgColor", "Background color", self.overlayPanel, self.overlaySizer)
		self.addColorOption("overlayFgColor", "Foreground color", self.overlayPanel, self.overlaySizer)

		header = wx.StaticText(self.overlayPanel, -1, "Raid Lists")
		header.SetFont(self.headerFont)
		self.overlaySizer.Add(header, 0, wx.ALL, 10)

		self.addSliderOption("overlayListFontSize", "List font size", 8, 18, self.overlayPanel, self.overlaySizer)
		self.addColorOption("overlayListSelfColor", "Self indicator color", self.overlayPanel, self.overlaySizer)

		self.overlayPanel.SetSizer(self.overlaySizer)
		self.overlayPanel.Layout()
		self.notebook.AddPage(self.overlayPanel, "Overlay")

		self.sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)

		# Create bottom buttons
		self.sizer.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.BOTTOM | wx.ALIGN_RIGHT, 5)

		self.SetSizer(self.sizer)
		self.Bind(wx.EVT_BUTTON, self.OnOK, id=wx.ID_OK)

	def addSliderOption(self, key, label, minValue, maxValue, parent, sizer):
		box = wx.BoxSizer(wx.HORIZONTAL)

		nameLabel = wx.StaticText(parent, -1, label)
		nameLabel.SetFont(self.nameFont)

		slider = wx.Slider(parent, -1, 1, minValue, maxValue, style=wx.SL_HORIZONTAL, size=(200, 20))
		slider.SetTickFreq(1, 1)
		slider.SetValue(config.Get(key))

		valueLabel = wx.StaticText(parent, -1, "", size=(20, -1))
		valueLabelUpdater = lambda e: valueLabel.SetLabel(str(slider.GetValue()))
		valueLabelUpdater(None)

		slider.Bind(wx.EVT_SCROLL_CHANGED, valueLabelUpdater)
		slider.Bind(wx.EVT_SCROLL_THUMBTRACK, valueLabelUpdater)

		box.Add(nameLabel, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
		box.Add(slider, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
		box.Add(valueLabel, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

		self.sliderOptions[key] = slider

		sizer.Add(box, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

	def addColorOption(self, key, label, parent, sizer):
		box = wx.BoxSizer(wx.HORIZONTAL)

		nameLabel = wx.StaticText(parent, -1, label)
		nameLabel.SetFont(self.nameFont)
		
		button = wx.Button(self.overlayPanel, -1, "", size=(100, -1))
		button.SetBackgroundColour(config.GetColor(key))
		
		def buttonClick(e):
			data = wx.ColourData()
			data.SetChooseFull(True)
			data.SetColour(button.GetBackgroundColour())
			dialog = wx.ColourDialog(self, data)
			if dialog.ShowModal() == wx.ID_OK:
				(red, green, blue) = dialog.GetColourData().GetColour().Get()
				color = wx.Colour(red, green, blue, 255)
				button.SetBackgroundColour(color)
		button.Bind(wx.EVT_BUTTON, buttonClick)

		box.Add(nameLabel, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
		box.Add(button, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

		self.colorOptions[key] = button

		sizer.Add(box, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

	def OnOK(self, event):
		for key in self.sliderOptions:
			config.Set(key, self.sliderOptions[key].GetValue())
		for key in self.colorOptions:
			config.SetColor(key, self.colorOptions[key].GetBackgroundColour())
		self.Destroy()
