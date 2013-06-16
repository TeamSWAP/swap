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

import wx, os, shutil
from constants import *
import overlays
import logging
import config
import log_parser, log_analyzer
from logging import prnt

class MainFrame(wx.Frame):
	def __init__(self):
		wx.Frame.__init__(self, None, title="SWAP v%s"%VERSION, size=(700, 520), style=wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE_BOX)

		# Setup menu bar
		menuBar = wx.MenuBar()
		self.SetMenuBar(menuBar)

		# File
		menu = wx.Menu()
		menuBar.Append(menu, "&File")
		m_exit = menu.Append(MENU_ID_EXIT, MENU_TITLE_EXIT, MENU_TIP_EXIT)
		self.Bind(wx.EVT_MENU, self.OnClose, id=MENU_ID_EXIT)

		# Tools
		menu = wx.Menu()
		menuBar.Append(menu, "&Tools")
		m_preferences = menu.Append(MENU_ID_PREFERENCES, MENU_TITLE_PREFERENCES, MENU_TIP_PREFERENCES)

		# Overlay
		menu = wx.Menu()
		menuBar.Append(menu, "&Overlay")

		categoryMenus = {}
		for category in overlays.GetOverlayCategoryList():
			name = category['name']
			title = category['title']
			categoryMenus[name] = subMenu = wx.Menu()
			menu.AppendSubMenu(subMenu, title, "")

		self.m_overlays = {}
		for overlay in overlays.GetOverlayList():
			if overlay == '-':
				menu.AppendSeparator()
				continue
			id = wx.NewId()
			targetMenu = menu
			if overlay['category'] != None:
				targetMenu = categoryMenus[overlay['category']]
			self.m_overlays[id] = targetMenu.AppendCheckItem(id, overlay['title'], MENU_TIP_OVERLAY_SELECT)
			self.Bind(wx.EVT_MENU, (lambda n: lambda e: overlays.ToggleOverlay(n))(overlay['name']), id=id)

		menu.AppendSeparator()
		m_dark = menu.AppendCheckItem(MENU_ID_OVERLAY_DARK, MENU_TITLE_OVERLAY_DARK, MENU_TIP_OVERLAY_DARK)
		m_dark.Check(overlays.IsDarkTheme())
		self.Bind(wx.EVT_MENU, lambda e: overlays.ToggleDarkTheme(), id=MENU_ID_OVERLAY_DARK)

		m_reset = menu.Append(MENU_ID_OVERLAY_RESET, MENU_TITLE_OVERLAY_RESET, MENU_TIP_OVERLAY_RESET)
		self.Bind(wx.EVT_MENU, self.OnResetOverlays, id=MENU_ID_OVERLAY_RESET)

		m_close = menu.Append(MENU_ID_OVERLAY_CLOSE, MENU_TITLE_OVERLAY_CLOSE, MENU_TIP_OVERLAY_CLOSE)
		self.Bind(wx.EVT_MENU, self.OnCloseOverlays, id=MENU_ID_OVERLAY_CLOSE)

		# UI
		panel = wx.Panel(self)
		box = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer(box)
		panel.Layout()

		# Events
		self.Bind(wx.EVT_CLOSE, self.OnClose)

		log_analyzer.Get().registerFrame(self)

	def OnClose(self, event):
		# TODO: Check for parsing session
		if True:
			log_analyzer.Get().unregisterFrame(self)
			overlays.KillAllOverlays()
			self.Destroy()
			return
		dlg = wx.MessageDialog(self, MSG_CLOSE_CONFIRM_TEXT, MSG_CLOSE_CONFIRM_TITLE)
		result = dlg.ShowModal()
		dlg.Destroy()

		if result == wx.ID_OK:
			# TODO: End parsing now
			self.Destroy()

	def OnResetOverlays(self, event):
		overlays.ResetOverlays()
		overlays.KillAllOverlays()
		self.updateOverlayList()

	def OnCloseOverlays(self, event):
		overlays.KillAllOverlays()
		self.updateOverlayList()

	def updateOverlayList(self):
		for name, item in self.m_overlays.iteritems():
			if overlays.IsOverlayOpen(name):
				item.Check(True)
			else:
				item.Check(False)

	def OnAnalyzerTick(self, analyzer):
		if analyzer.parser.me:
			self.SetTitle("SWAP v%s - %s"%(VERSION, analyzer.parser.me))
		else:
			self.SetTitle("SWAP v%s"%VERSION)


logging.SetupLogging("swap")

prnt("SWAP v%s booting up..."%VERSION)

config.Load()
log_parser.Start()
log_analyzer.Start(log_parser.GetThread())

if os.path.isdir("pending"):
	prnt("Finalizing update...")
	
	for f in os.listdir("pending"):
		shutil.copyfile("pending/%s"%f, f)
	shutil.rmtree("pending")

	for f in os.listdir("."):
		if f.endswith('.old'):
			os.remove(f)

app = wx.App()
frame = MainFrame()
frame.Show()
app.MainLoop()