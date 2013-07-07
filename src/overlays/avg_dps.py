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

import wx, random, time, locale, util
import log_analyzer

from threading import Thread, Event
from base import BaseOverlay
from logging import prnt

class AverageDPSOverlay(BaseOverlay):
	def __init__(self):
		BaseOverlay.__init__(self, title="Avg. DPS")

		self.Bind(wx.EVT_WINDOW_DESTROY, self.OnClose)

		analyzer = log_analyzer.Get()
		analyzer.registerFrame(self)
		self.OnAnalyzerTick(analyzer)

	def createUI(self):
		BaseOverlay.createUI(self)

		# DPS
		self.dps = wx.StaticText(self.panel, -1, "2100.35")
		self.dps.SetFont(wx.Font(24, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.dps.SetSize(self.dps.GetBestSize())
		self.box.Add(self.dps, 0, wx.ALL, 10)

	def updateColors(self):
		self.dps.SetForegroundColour(self.getForegroundColor())
		BaseOverlay.updateColors(self)

	def OnClose(self, event):
		log_analyzer.Get().unregisterFrame(self)

	def OnAnalyzerTick(self, analyzer):
		self.dps.SetLabel(locale.format("%.2f", analyzer.avgDps, grouping=True))

