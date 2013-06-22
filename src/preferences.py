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

class PreferencesDialog(wx.Dialog):
	def __init__(self, parent):
		wx.Dialog.__init__(self, parent, -1, "Preferences", size=(700, 500))

		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.notebook = wx.Notebook(self)

		# -----------------------------------
		# Overlay
		# -----------------------------------
		self.overlayPanel = wx.Panel(self.notebook)
		self.overlaySizer = wx.BoxSizer(wx.VERTICAL)

		# List font size
		self.listFontSizeBox = wx.BoxSizer(wx.VERTICAL)
		self.listFontSizeLabel = wx.StaticText(self.overlayPanel, -1, "List Font Size (ex. Raid Damage)")
		self.listFontSizeSlider = wx.Slider(self.overlayPanel, -1, 8, 5, 18, style=wx.SL_HORIZONTAL | wx.SL_AUTOTICKS | wx.SL_LABELS, size=(500, 100))
		self.listFontSizeSlider.SetTickFreq(1, 1)
		self.listFontSizeSlider.SetValue(config.Get("overlayListFontSize"))
		self.listFontSizeBox.Add(self.listFontSizeLabel, 0, wx.ALL, 5)
		self.listFontSizeBox.Add(self.listFontSizeSlider, 0, wx.ALL, 5)
		self.overlaySizer.Add(self.listFontSizeBox, 0, wx.ALL, 10)

		self.overlayPanel.SetSizer(self.overlaySizer)
		self.overlayPanel.Layout()
		self.notebook.AddPage(self.overlayPanel, "Overlay")

		self.sizer.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)

		# Create bottom buttons
		self.sizer.Add(self.CreateButtonSizer(wx.OK | wx.CANCEL), 0, wx.BOTTOM | wx.ALIGN_RIGHT, 5)

		self.SetSizer(self.sizer)
		self.Bind(wx.EVT_BUTTON, self.OnOK, id=wx.ID_OK)

	def OnOK(self, event):
		config.Set("overlayListFontSize", self.listFontSizeSlider.GetValue())
		self.Destroy()
