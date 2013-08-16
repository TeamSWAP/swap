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
import log_parser
from constants import *
from logging import prnt

class PreferencesDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, "Preferences", size=(700, 500))

		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.notebook = wx.Notebook(self)

		self.sliderOptions = {}
		self.checkOptions = {}
		self.colorOptions = {}

		self.headerFont = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
		self.nameFont = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.NORMAL)

		# -----------------------------------
		# General
		# -----------------------------------
		self.generalPanel = wx.Panel(self.notebook)
		self.generalSizer = wx.BoxSizer(wx.VERTICAL)

		self.addHeader("Performance", self.generalPanel, self.generalSizer)
		self.addCheckOption("neverUpdateInSWTOR", "Never update the main UI when SWTOR is in the foreground",
			self.generalPanel, self.generalSizer)

		self.generalPanel.SetSizer(self.generalSizer)
		self.generalPanel.Layout()
		self.notebook.AddPage(self.generalPanel, "General")

		# -----------------------------------
		# Overlay
		# -----------------------------------
		self.overlayPanel = wx.Panel(self.notebook)
		self.overlaySizer = wx.BoxSizer(wx.VERTICAL)

		self.addHeader("All Overlays", self.overlayPanel, self.overlaySizer)
		self.addSliderOption("overlayOpacity", "Opacity", 0, 255, self.overlayPanel, self.overlaySizer)
		self.addSliderOption("overlayHeaderFontSize", "Header font size", 8, 18, self.overlayPanel, self.overlaySizer)
		self.addColorOption("overlayBgColor", "Background color", self.overlayPanel, self.overlaySizer)
		self.addColorOption("overlayFgColor", "Foreground color", self.overlayPanel, self.overlaySizer)

		self.addHeader("Raid Lists", self.overlayPanel, self.overlaySizer)
		self.addSliderOption("overlayListFontSize", "List font size", 8, 18, self.overlayPanel, self.overlaySizer)
		self.addColorOption("overlayListSelfColor", "Self indicator color", self.overlayPanel, self.overlaySizer)

		self.overlayPanel.SetSizer(self.overlaySizer)
		self.overlayPanel.Layout()
		self.notebook.AddPage(self.overlayPanel, "Overlay")

		self.sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)

		# Create bottom buttons
		self.sizer.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.BOTTOM | wx.ALIGN_RIGHT, 5)

		self.SetSizer(self.sizer)
		self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)

  	def addHeader(self, header, parent, sizer):
		header = wx.StaticText(parent, -1, header)
		header.SetFont(self.headerFont)
		sizer.Add(header, 0, wx.ALL, 10)

	def addSliderOption(self, key, label, minValue, maxValue, parent, sizer):
		box = wx.BoxSizer(wx.HORIZONTAL)

		nameLabel = wx.StaticText(parent, -1, label)
		nameLabel.SetFont(self.nameFont)

		slider = wx.Slider(parent, -1, 1, minValue, maxValue, style=wx.SL_HORIZONTAL, size=(200, 20))
		slider.SetTickFreq(1, 1)
		slider.SetValue(config.get(key))

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

	def addCheckOption(self, key, label, parent, sizer):
		box = wx.BoxSizer(wx.HORIZONTAL)

		check = wx.CheckBox(parent, -1, label, size=(100, -1))
		check.SetValue(config.get(key))
		
		box.Add(check, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

		self.checkOptions[key] = check

		sizer.Add(box, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

	def addColorOption(self, key, label, parent, sizer):
		box = wx.BoxSizer(wx.HORIZONTAL)

		nameLabel = wx.StaticText(parent, -1, label)
		nameLabel.SetFont(self.nameFont)
		
		button = wx.Button(parent, -1, "", size=(100, -1))
		button.SetBackgroundColour(config.getColor(key))
		
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

	def onOK(self, event):
		for key in self.sliderOptions:
			config.set(key, self.sliderOptions[key].GetValue())
		for key in self.checkOptions:
			config.set(key, self.checkOptions[key].GetValue())
		for key in self.colorOptions:
			config.setColor(key, self.colorOptions[key].GetBackgroundColour())
		self.Destroy()
