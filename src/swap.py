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

import os
import shutil
import locale
import time
import subprocess
import traceback
import threading
import sys
import urllib2
from urllib import urlencode

import wx
from wx.lib.mixins.listctrl import ColumnSorterMixin

import config
import overlays
import logging
import log_parser
import log_analyzer
import util
import raid
import net
import preferences
import ext.fuzion as fuzion
from constants import *
from logging import prnt

class SortList(wx.ListCtrl, ColumnSorterMixin):
	def __init__(self, parent, columns, style=wx.LC_REPORT):
		wx.ListCtrl.__init__(self, parent, style=style)
		self.itemDataMap = {}
		self.GetListCtrl = lambda: self
		ColumnSorterMixin.__init__(self, columns)

class MainFrame(wx.Frame):
	def __init__(self):
		wx.Frame.__init__(self, None, title="SWAP v%s"%VERSION, size=(700, 520))

		if not util.IsCombatLoggingEnabled():
			dlg = wx.MessageDialog(self, MSG_COMBAT_LOGGING_DISABLED_TEXT, MSG_COMBAT_LOGGING_DISABLED_TITLE, wx.OK | wx.CANCEL | wx.ICON_ERROR)
			result = dlg.ShowModal()
			dlg.Destroy()

			if result == wx.ID_OK:
				util.EnableCombatLogging()

		self.SetMinSize((700, 520))

		# Setup menu bar
		menuBar = wx.MenuBar()
		self.SetMenuBar(menuBar)

		# File
		menu = wx.Menu()
		menuBar.Append(menu, "&File")
		m_exit = menu.Append(MENU_ID_EXIT, MENU_TITLE_EXIT, MENU_TIP_EXIT)
		self.Bind(wx.EVT_MENU, self.onClose, id=MENU_ID_EXIT)

		# Tools
		menu = wx.Menu()
		menuBar.Append(menu, "&Tools")
		m_preferences = menu.Append(MENU_ID_PREFERENCES, MENU_TITLE_PREFERENCES, MENU_TIP_PREFERENCES)
		self.Bind(wx.EVT_MENU, self.onPreferences, id=MENU_ID_PREFERENCES)

		# Overlay
		menu = wx.Menu()
		menuBar.Append(menu, "&Overlay")

		categoryMenus = {}
		for category in overlays.getOverlayCategoryList():
			name = category['name']
			title = category['title']
			categoryMenus[name] = subMenu = wx.Menu()
			menu.AppendSubMenu(subMenu, title, "")

		self.m_overlays = {}
		for overlay in overlays.getOverlayList():
			targetMenu = menu
			if overlay['category'] != None:
				targetMenu = categoryMenus[overlay['category']]
			if overlay['name'] == '-':
				targetMenu.AppendSeparator()
				continue
			id = wx.NewId()
			self.m_overlays[id] = targetMenu.AppendCheckItem(id, overlay['title'], MENU_TIP_OVERLAY_SELECT)
			self.Bind(wx.EVT_MENU, (lambda n: lambda e: overlays.toggleOverlay(n))(overlay['name']), id=id)

		menu.AppendSeparator()
		m_dark = menu.AppendCheckItem(MENU_ID_OVERLAY_DARK, MENU_TITLE_OVERLAY_DARK, MENU_TIP_OVERLAY_DARK)
		m_dark.Check(overlays.isDarkTheme())
		self.Bind(wx.EVT_MENU, lambda e: overlays.ToggleDarkTheme(), id=MENU_ID_OVERLAY_DARK)

		m_sizeToGrid = menu.AppendCheckItem(MENU_ID_OVERLAY_SIZE_TO_GRID, MENU_TITLE_OVERLAY_SIZE_TO_GRID, MENU_TIP_OVERLAY_SIZE_TO_GRID)
		m_sizeToGrid.Check(config.Get("overlaySizeToGrid") == True)
		self.Bind(wx.EVT_MENU, lambda e: config.Set("overlaySizeToGrid", m_sizeToGrid.IsChecked()), id=MENU_ID_OVERLAY_SIZE_TO_GRID)

		m_snapOverlays = menu.AppendCheckItem(MENU_ID_OVERLAY_SNAP, MENU_TITLE_OVERLAY_SNAP, MENU_TIP_OVERLAY_SNAP)
		m_snapOverlays.Check(config.Get("overlaySnap") == True)
		self.Bind(wx.EVT_MENU, lambda e: config.Set("overlaySnap", m_snapOverlays.IsChecked()), id=MENU_ID_OVERLAY_SNAP)

		m_clickThrough = menu.AppendCheckItem(MENU_ID_OVERLAY_CLICK_THROUGH, MENU_TITLE_OVERLAY_CLICK_THROUGH, MENU_TIP_OVERLAY_CLICK_THROUGH)
		m_clickThrough.Check(config.Get("overlayClickThrough") == True)
		self.Bind(wx.EVT_MENU, lambda e: config.Set("overlayClickThrough", m_clickThrough.IsChecked()), id=MENU_ID_OVERLAY_CLICK_THROUGH)

		menu.AppendSeparator()

		m_reset = menu.Append(MENU_ID_OVERLAY_RESET, MENU_TITLE_OVERLAY_RESET, MENU_TIP_OVERLAY_RESET)
		self.Bind(wx.EVT_MENU, self.onResetOverlays, id=MENU_ID_OVERLAY_RESET)

		m_close = menu.Append(MENU_ID_OVERLAY_CLOSE, MENU_TITLE_OVERLAY_CLOSE, MENU_TIP_OVERLAY_CLOSE)
		self.Bind(wx.EVT_MENU, self.onCloseOverlays, id=MENU_ID_OVERLAY_CLOSE)

		# Help
		menu = wx.Menu()
		menuBar.Append(menu, "&Help")
		m_checkUpdates = menu.Append(MENU_ID_HELP_UPDATES, MENU_TITLE_HELP_UPDATES, MENU_TIP_HELP_UPDATES)
		m_openLog = menu.Append(MENU_ID_HELP_LOG, MENU_TITLE_HELP_LOG, MENU_TIP_HELP_LOG)
		m_sendLog = menu.Append(MENU_ID_HELP_SEND_LOG, MENU_TITLE_HELP_SEND_LOG, MENU_TIP_HELP_SEND_LOG)
		menu.AppendSeparator()
		m_about = menu.Append(MENU_ID_HELP_ABOUT, MENU_TITLE_HELP_ABOUT, MENU_TIP_HELP_ABOUT)
		self.Bind(wx.EVT_MENU, self.onCheckUpdates, id=MENU_ID_HELP_UPDATES)
		self.Bind(wx.EVT_MENU, self.onOpenLog, id=MENU_ID_HELP_LOG)
		self.Bind(wx.EVT_MENU, self.onSendLog, id=MENU_ID_HELP_SEND_LOG)
		self.Bind(wx.EVT_MENU, self.onAbout, id=MENU_ID_HELP_ABOUT)

		# UI
		self.panel = wx.Panel(self)
		self.panel.SetDoubleBuffered(True)
		self.box = wx.BoxSizer(wx.VERTICAL)

		# -----------------------------------
		# Header
		# -----------------------------------

		headerBox = wx.BoxSizer(wx.HORIZONTAL)

		self.keyText = wx.StaticText(self.panel, -1, "Key:")
		self.keyBox = wx.TextCtrl(self.panel, -1, "", size=(150, -1))

		lastRaidKey = config.Get("lastRaidKey")
		if lastRaidKey:
			self.keyBox.SetValue(lastRaidKey)

		self.keyGenerateButton = wx.Button(self.panel, -1, "Generate")
		self.keyGenerateButton.Bind(wx.EVT_BUTTON, self.onGenerateButton)

		self.keyJoinButton = wx.Button(self.panel, -1, "Join Raid")
		self.keyJoinButton.Bind(wx.EVT_BUTTON, self.onJoinRaidButton)

		self.keyVanityCheck = wx.CheckBox(self.panel, -1, "Generate Vanity Key")
		self.keyStatus = wx.StaticText(self.panel, -1, "")

		headerBox.Add(self.keyText, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
		headerBox.Add(self.keyBox, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
		headerBox.Add(self.keyGenerateButton, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		headerBox.Add(self.keyJoinButton, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
		headerBox.Add(self.keyVanityCheck, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT)
		headerBox.Add(self.keyStatus, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
		self.box.Add(headerBox, 0, wx.ALL, 10)

		# -----------------------------------
		# Tabs
		# -----------------------------------

		self.tabs = wx.Notebook(self.panel)

		# Create Grid tab
		self.gridPanel = wx.Panel(self.tabs)
		self.gridSizer = wx.BoxSizer(wx.VERTICAL)
		self.gridPanel.SetSizer(self.gridSizer)
		self.gridPanel.Layout()
		self.createGridView(self.gridSizer, self.gridPanel)
		self.tabs.AddPage(self.gridPanel, "Grid")

		# Create Report tab
		self.reportPanel = wx.Panel(self.tabs)
		self.reportSizer = wx.BoxSizer(wx.VERTICAL)
		self.reportPanel.SetSizer(self.reportSizer)
		self.reportPanel.Layout()
		self.createReportView(self.reportSizer, self.reportPanel)
		self.tabs.AddPage(self.reportPanel, "Report")

		# Create Raid tab
		self.raidPanel = wx.Panel(self.tabs)
		self.raidSizer = wx.BoxSizer(wx.VERTICAL)
		self.raidPanel.SetSizer(self.raidSizer)
		self.raidPanel.Layout()
		self.createRaidView(self.raidSizer, self.raidPanel)
		self.tabs.AddPage(self.raidPanel, "Raid")

		# Create Ability Breakdown tab
		self.breakdownPanel = wx.Panel(self.tabs)
		self.breakdownSizer = wx.BoxSizer(wx.VERTICAL)
		self.breakdownPanel.SetSizer(self.breakdownSizer)
		self.breakdownPanel.Layout()
		self.createBreakdownView(self.breakdownSizer, self.breakdownPanel)
		self.tabs.AddPage(self.breakdownPanel, "Ability Breakdown")

		self.box.Add(self.tabs, 1, wx.EXPAND | wx.ALL & ~wx.TOP, 10)

		self.panel.SetSizer(self.box)
		self.panel.Layout()

		# Events
		self.Bind(wx.EVT_CLOSE, self.onClose)

		log_analyzer.Get().registerFrame(self)

	def onPreferences(self, event):
		dialog = preferences.PreferencesDialog(self)
		dialog.ShowModal()

	def onCheckUpdates(self, event):
		if IS_COMPILED:
			subprocess.Popen(["updater.exe"])
		else:
			subprocess.Popen(["python", "updater.py"])
		self.Destroy()

	def onOpenLog(self, event):
		os.startfile("debug-swap.log")

	def onSendLog(self, event):
		def t():
			try:
				prnt("Sending SWAP log...")

				f = open("debug-swap.log", "r")
				log = f.read()
				f.close()
				
				request = urllib2.Request(LOG_SEND_URL)
				request.add_data(urlencode({"u": log}))
				urllib2.urlopen(request).close()

				prnt("Sent.")
			except:
				prnt(traceback.format_exc())
		threading.Thread(target=t).start()

	def onAbout(self, event):
		about = wx.AboutDialogInfo()
		about.SetName("SWAP")
		about.SetVersion("v%s"%VERSION)
		about.SetDescription("""SWAP is a open-source SWTOR combat log parser and analyzer.""")
		about.SetCopyright("(C) 2013 TeamSWAP")
		about.SetWebSite("http://github.com/TeamSWAP/swap/wiki")
		about.AddDeveloper("Solara (at The Bastion)")
		about.AddDeveloper("Nijiko (at The Bastion)")
		about.SetLicence("SWAP is licensed under the Apache 2.0 license.")
		wx.AboutBox(about)

	def onClose(self, event):
		if raid.IsInRaid():
			raid.LeaveRaid()
		log_analyzer.Get().unregisterFrame(self)
		overlays.killAllOverlays()
		self.Destroy()

	def onResetOverlays(self, event):
		overlays.resetOverlays()
		overlays.killAllOverlays()
		self.updateOverlayList()

	def onCloseOverlays(self, event):
		overlays.KillAllOverlays()
		self.updateOverlayList()

	def onGenerateButton(self, event):
		vanityKey = None
		if self.keyVanityCheck.IsChecked():
			vanityKey = self.keyBox.GetValue()

		self.keyStatus.SetLabel("Generating key...")
		self.keyBox.SetEditable(False)
		self.keyJoinButton.Disable()
		self.keyGenerateButton.Disable()
		self.keyVanityCheck.Disable()

		raid.GenerateKey(vanityKey, self.onGotKey, self.onFailedToGetKey)

	def onGotKey(self, key):
		self.keyBox.SetValue(key)
		self.keyBox.SetEditable(True)
		self.keyStatus.SetLabel("")
		self.keyJoinButton.Enable()
		self.keyGenerateButton.Enable()
		self.keyVanityCheck.Enable()

	def onFailedToGetKey(self):
		dlg = wx.MessageDialog(self, MSG_FAILED_KEY_GENERATION_TEXT, MSG_FAILED_KEY_GENERATION_TITLE, wx.OK)
		result = dlg.ShowModal()
		dlg.Destroy()
		self.keyBox.SetEditable(True)
		self.keyStatus.SetLabel("")
		self.keyJoinButton.Enable()
		self.keyGenerateButton.Enable()
		self.keyVanityCheck.Enable()

	def onJoinRaidButton(self, event):
		if not raid.IsInRaid():
			self.keyStatus.SetLabel("Joining raid...")
			self.keyBox.SetEditable(False)
			self.keyJoinButton.Disable()
			self.keyGenerateButton.Disable()
			self.keyVanityCheck.Disable()
			raid.JoinRaid(self.keyBox.GetValue().encode('ascii'), self.onJoinedRaid, self.onFailedToJoinRaid)
		else:
			raid.LeaveRaid()
			self.onLeftRaid()

	def onJoinedRaid(self):
		self.keyJoinButton.SetLabel("Leave Raid")
		self.keyJoinButton.Enable()
		self.keyStatus.SetLabel("")

		config.Set("lastRaidKey", self.keyBox.GetValue())

	def onFailedToJoinRaid(self, reason):
		titles = {
			'key_invalid': MSG_FAILED_JOIN_INVALID_KEY_TITLE,
			'update_required': MSG_FAILED_JOIN_UPDATE_REQUIRED_TITLE,
			'connect_failed': MSG_CONNECT_FAILED_TITLE,
			'node_connect_failed': MSG_NODE_CONNECT_FAILED_TITLE
		}
		texts = {
			'key_invalid': MSG_FAILED_JOIN_INVALID_KEY_TEXT,
			'update_required': MSG_FAILED_JOIN_UPDATE_REQUIRED_TEXT,
			'connect_failed': MSG_CONNECT_FAILED_TEXT,
			'node_connect_failed': MSG_NODE_CONNECT_FAILED_TEXT
		}

		dlg = wx.MessageDialog(self, texts[reason], titles[reason], wx.OK | wx.ICON_ERROR)
		result = dlg.ShowModal()
		dlg.Destroy()
		
		self.keyStatus.SetLabel("")
		self.keyBox.SetEditable(True)
		self.keyJoinButton.Enable()
		self.keyJoinButton.SetLabel("Join Raid")
		self.keyGenerateButton.Enable()
		self.keyVanityCheck.Enable()

	def onLeftRaid(self):
		self.keyJoinButton.SetLabel("Join Raid")
		self.keyStatus.SetLabel("")
		self.keyBox.SetEditable(True)
		self.keyGenerateButton.Enable()
		self.keyVanityCheck.Enable()

	def createReportView(self, parent=None, panelParent=None):
		parent = parent if parent else self.box
		panelParent = panelParent if panelParent else self.panel
		
		self.reportView = wx.ListCtrl(panelParent, style=wx.LC_REPORT | wx.NO_BORDER)
		self.reportView.InsertColumn(0, "Name"); self.reportView.SetColumnWidth(0, 300)
		self.reportView.InsertColumn(1, "Value"); self.reportView.SetColumnWidth(1, 200)

		self.reportUpdaters = {}
		def addDetailItem(name, getter):
			self.reportUpdaters[name] = getter

		addDetailItem("My Damage Dealt", lambda a: locale.format("%d", a.totalDamage, grouping=True))
		addDetailItem("My Damage Taken", lambda a: locale.format("%d", a.totalDamageTaken, grouping=True))
		addDetailItem("My Average DPS", lambda a: locale.format("%.2f", a.avgDps, grouping=True))
		addDetailItem("My Healing Done", lambda a: locale.format("%d", a.totalHealing, grouping=True))
		addDetailItem("My Healing Received", lambda a: locale.format("%d", a.totalHealingReceived, grouping=True))
		addDetailItem("My Average HPS", lambda a: locale.format("%.2f", a.avgHps, grouping=True))
		addDetailItem("My Threat", lambda a: locale.format("%d", a.totalThreat, grouping=True))
		addDetailItem("Combat Duration", lambda a: util.FormatDuration(a.combatDurationLinear))
		addDetailItem("Combat Duration (seconds)", lambda a: locale.format("%.2f", a.combatDurationLinear, grouping=True))
		addDetailItem("Combat Enter Time", lambda a: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(a.combatStartTime)))
		addDetailItem("Combat Exit Time", lambda a: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(a.combatEndTime)))

		index = 0
		for name in sorted(self.reportUpdaters.keys()):
			self.reportView.InsertStringItem(index, name)
			index += 1

		parent.Add(self.reportView, 1, wx.EXPAND, 0)

	def createRaidView(self, parent=None, panelParent=None):
		parent = parent if parent else self.box
		panelParent = panelParent if panelParent else self.panel
		
		self.raidView = SortList(panelParent, 9, style=wx.LC_REPORT | wx.NO_BORDER)
		self.raidView.InsertColumn(0, ""); self.raidView.SetColumnWidth(0, 20)
		self.raidView.InsertColumn(1, "Player"); self.raidView.SetColumnWidth(1, 100)
		self.raidView.InsertColumn(2, "Damage"); self.raidView.SetColumnWidth(1, 100)
		self.raidView.InsertColumn(3, "Damage Taken"); self.raidView.SetColumnWidth(1, 100)
		self.raidView.InsertColumn(4, "Avg. DPS"); self.raidView.SetColumnWidth(1, 100)
		self.raidView.InsertColumn(5, "Healing"); self.raidView.SetColumnWidth(1, 100)
		self.raidView.InsertColumn(6, "Healing Received"); self.raidView.SetColumnWidth(1, 100)
		self.raidView.InsertColumn(7, "Avg. HPS"); self.raidView.SetColumnWidth(1, 100)
		self.raidView.InsertColumn(8, "Threat"); self.raidView.SetColumnWidth(1, 100)

		parent.Add(self.raidView, 1, wx.EXPAND, 0)

	def createBreakdownView(self, parent=None, panelParent=None):
		parent = parent if parent else self.box
		panelParent = panelParent if panelParent else self.panel
		
		self.breakdownView = SortList(panelParent, 2, style=wx.LC_REPORT | wx.NO_BORDER)
		self.breakdownView.InsertColumn(0, "Ability"); self.breakdownView.SetColumnWidth(0, 200)
		self.breakdownView.InsertColumn(1, "Damage"); self.breakdownView.SetColumnWidth(1, 100)

		parent.Add(self.breakdownView, 1, wx.EXPAND, 0)

	def createGridView(self, parent=None, panelParent=None):
		parent = parent if parent else self.box
		panelParent = panelParent if panelParent else self.panel
		self.detailGrid = wx.GridSizer(4, 3, 10, 100)
		self.gridUpdaters = []

		def createDetailBlock(name, getter):
			detailBlock = wx.BoxSizer(wx.VERTICAL)

			header = wx.StaticText(panelParent, -1, name)
			header.SetFont(wx.Font(14, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
			header.SetSize(header.GetBestSize())
			detailBlock.Add(header, 0, wx.ALIGN_CENTER | (wx.ALL & ~wx.BOTTOM), 10)

			text = wx.StaticText(panelParent, -1, "N/A")
			text.SetFont(wx.Font(24, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
			text.SetSize(text.GetBestSize())
			detailBlock.Add(text, 0, wx.ALIGN_CENTER | (wx.ALL & ~wx.TOP), 10)

			self.detailGrid.Add(detailBlock, 0, wx.ALIGN_CENTER)

			self.gridUpdaters.append((lambda t,x: lambda a: t.SetLabel(getter(a)))(text, getter))

		createDetailBlock("Damage Dealt", lambda a: locale.format("%d", a.totalDamage, grouping=True))
		createDetailBlock("Damage Taken", lambda a: locale.format("%d", a.totalDamageTaken, grouping=True))
		createDetailBlock("Avg. DPS", lambda a: locale.format("%.2f", a.avgDps, grouping=True))
		createDetailBlock("Healing Done", lambda a: locale.format("%d", a.totalHealing, grouping=True))
		createDetailBlock("Healing Received", lambda a: locale.format("%d", a.totalHealingReceived, grouping=True))
		createDetailBlock("Avg. HPS", lambda a: locale.format("%.2f", a.avgHps, grouping=True))
		createDetailBlock("Combat Duration", lambda a: util.FormatDuration(a.combatDurationLinear))

		parent.Add(self.detailGrid, 0, wx.EXPAND | wx.ALL, 10)

	def updateOverlayList(self):
		for name, item in self.m_overlays.iteritems():
			if overlays.isOverlayOpen(name):
				item.Check(True)
			else:
				item.Check(False)

	def OnAnalyzerTick(self, analyzer):
		if analyzer.parser.me:
			self.SetTitle("SWAP v%s - %s"%(VERSION, analyzer.parser.me))
		else:
			self.SetTitle("SWAP v%s"%VERSION)

		index = 0
		for name in sorted(self.reportUpdaters.keys()):
			getter = self.reportUpdaters[name]
			self.reportView.SetStringItem(index, 1, getter(analyzer))
			index += 1

		self.raidView.DeleteAllItems()
		index = 0
		itemDataMap = {}
		for player in sorted(raid.playerData, key=lambda x: x['name']):
			connectionType = player['connType']
			name = player['name'][1:]
			self.raidView.InsertStringItem(index, connectionType)
			self.raidView.SetStringItem(index, 1, name)
			self.raidView.SetStringItem(index, 2, locale.format("%d", player['totalDamage'], grouping=True))
			self.raidView.SetStringItem(index, 3, locale.format("%d", player['totalDamageTaken'], grouping=True))
			self.raidView.SetStringItem(index, 4, locale.format("%.2f", player['avgDps'], grouping=True))
			self.raidView.SetStringItem(index, 5, locale.format("%d", player['totalHealing'], grouping=True))
			self.raidView.SetStringItem(index, 6, locale.format("%d", player['totalHealingReceived'], grouping=True))
			self.raidView.SetStringItem(index, 7, locale.format("%.2f", player['avgHps'], grouping=True))
			self.raidView.SetStringItem(index, 8, locale.format("%d", player['totalThreat'], grouping=True))
			self.raidView.SetItemData(index, index)
			itemDataMap[index] = [connectionType, name, player['totalDamage'], player['totalDamageTaken'], player['avgDps'],
				player['totalHealing'], player['totalHealingReceived'], player['avgHps'], player['totalThreat']]
			index += 1
		self.raidView.itemDataMap = itemDataMap
		self.raidView.SortListItems()

		self.breakdownView.DeleteAllItems()
		index = 0

		itemDataMap = {}
		for ability, damage in sorted(analyzer.damageBreakdown.iteritems(), key=lambda x:x[1], reverse=True):
			self.breakdownView.InsertStringItem(index, ability)
			self.breakdownView.SetStringItem(index, 1, locale.format("%d", damage, grouping=True))
			self.breakdownView.SetItemData(index, index)
			itemDataMap[index] = [ability, damage]
			index += 1
		self.breakdownView.itemDataMap = itemDataMap
		self.breakdownView.SortListItems()

		# Update grid
		for analyzerUpdater in self.gridUpdaters:
			analyzerUpdater(analyzer)
		self.gridPanel.Layout()

if __name__ == '__main__':
	logging.SetupLogging("swap")
	locale.setlocale(locale.LC_ALL, '')

	if IS_COMPILED:
		if len(sys.argv) != 2 or sys.argv[1] != '--from-updater':
			subprocess.Popen(["updater.exe"])
			exit()

	prnt("SWAP v%s booting up..."%VERSION)

	net.Init()
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

	app = wx.App(redirect=False)
	frame = MainFrame()
	frame.Show()
	app.MainLoop()
