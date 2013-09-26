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

# Add externals to path
import sys
sys.path.append('../external')

import os
import shutil
import locale
import time
import subprocess
import traceback
import threading
import urllib2
import textwrap
from urllib import urlencode

import fuzion
import win32gui
import wx
import wx.html

import config
import overlays
import logging
import log_parser
import log_analyzer
import util
import raid
import net
import preferences
from ui.listbox import ListBox
from const import *
from logging import prnt

class ChangelogDialog(wx.Dialog):
	def __init__(self, changelog):
		wx.Dialog.__init__(self, None, -1, "SWAP Changelog", size=(500, 600))

		changelogLines = changelog.split("\n")
		changelogFinal = "\n".join(map(lambda x:"\n".join(textwrap.wrap(x, 55)), changelogLines))

		sizer = wx.BoxSizer(wx.VERTICAL)

		html = wx.html.HtmlWindow(self, -1, style=wx.STATIC_BORDER)
		html.SetPage("<pre>%s</pre>"%changelogFinal)
		sizer.Add(html, 1, wx.EXPAND | wx.ALL, 5)

		buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
		buttonSizer.Add((0, 0), 1, wx.EXPAND)
		buttonSizer.Add(wx.Button(self, wx.ID_OK, "OK"))
		sizer.Add(buttonSizer, 0, wx.EXPAND | wx.ALL, 5)

		self.SetSizer(sizer)

class MainFrame(wx.Frame):
	def __init__(self):
		wx.Frame.__init__(self, None, title="SWAP v%s"%VERSION, size=(700, 520))

		if not util.isCombatLoggingEnabled():
			dlg = wx.MessageDialog(self, MSG_COMBAT_LOGGING_DISABLED_TEXT, MSG_COMBAT_LOGGING_DISABLED_TITLE, wx.OK | wx.CANCEL | wx.ICON_ERROR)
			result = dlg.ShowModal()
			dlg.Destroy()

			if result == wx.ID_OK:
				util.enableCombatLogging()

		# Check for changelog
		try:
			f = open('_changelog.txt', 'r')
		except IOError:
			pass
		else:
			with f:
				changelog = f.read()
			changelogDialog = ChangelogDialog(changelog)
			changelogDialog.ShowModal()
			changelogDialog.Destroy()
			os.remove('_changelog.txt')

		self.SetMinSize((700, 520))

		if IS_FROZEN:
			self.SetIcon(wx.Icon('swap.exe', wx.BITMAP_TYPE_ICO))
		else:
			self.SetIcon(wx.Icon('../etc/app.ico', wx.BITMAP_TYPE_ICO))

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

		menu.AppendSeparator()

		m_enrageTime = menu.Append(MENU_ID_ENRAGE_TIME, MENU_TITLE_ENRAGE_TIME, MENU_TIP_ENRAGE_TIME)
		self.Bind(wx.EVT_MENU, self.onSetEnrageTime, id=MENU_ID_ENRAGE_TIME)

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
		self.Bind(wx.EVT_MENU, lambda e: overlays.toggleDarkTheme(), id=MENU_ID_OVERLAY_DARK)

		m_sizeToGrid = menu.AppendCheckItem(MENU_ID_OVERLAY_SIZE_TO_GRID, MENU_TITLE_OVERLAY_SIZE_TO_GRID, MENU_TIP_OVERLAY_SIZE_TO_GRID)
		m_sizeToGrid.Check(config.get("overlaySizeToGrid") == True)
		self.Bind(wx.EVT_MENU, lambda e: config.set("overlaySizeToGrid", m_sizeToGrid.IsChecked()), id=MENU_ID_OVERLAY_SIZE_TO_GRID)

		m_snapOverlays = menu.AppendCheckItem(MENU_ID_OVERLAY_SNAP, MENU_TITLE_OVERLAY_SNAP, MENU_TIP_OVERLAY_SNAP)
		m_snapOverlays.Check(config.get("overlaySnap") == True)
		self.Bind(wx.EVT_MENU, lambda e: config.set("overlaySnap", m_snapOverlays.IsChecked()), id=MENU_ID_OVERLAY_SNAP)

		m_clickThrough = menu.AppendCheckItem(MENU_ID_OVERLAY_CLICK_THROUGH, MENU_TITLE_OVERLAY_CLICK_THROUGH, MENU_TIP_OVERLAY_CLICK_THROUGH)
		m_clickThrough.Check(config.get("overlayClickThrough") == True)
		self.Bind(wx.EVT_MENU, lambda e: config.set("overlayClickThrough", m_clickThrough.IsChecked()), id=MENU_ID_OVERLAY_CLICK_THROUGH)

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

		lastRaidKey = config.get("lastRaidKey")
		if lastRaidKey:
			self.keyBox.SetValue(lastRaidKey)

		self.keyGenerateButton = wx.Button(self.panel, -1, "Generate")
		self.keyGenerateButton.Bind(wx.EVT_BUTTON, self.onGenerateButton)

		self.keyJoinButton = wx.Button(self.panel, -1, "Join Raid")
		self.keyJoinButton.Bind(wx.EVT_BUTTON, self.onJoinRaidButton)

		self.keyVanityCheck = wx.CheckBox(self.panel, -1, "Generate Vanity Key")
		self.keyStatus = wx.StaticText(self.panel, -1, "")

		self.fightSelector = wx.Choice(self.panel, -1)
		self.fightSelector.Append("Latest Fight", None)
		self.fightSelector.SetSelection(0)
		self.fightSelector.Bind(wx.EVT_CHOICE, self.onFightSelected)

		log_parser.get().registerObserver(log_parser.Parser.EVENT_FIGHT_BEGIN, util.wxFunc(self.onFightBegin))
		log_parser.get().registerObserver(log_parser.Parser.EVENT_FIGHT_END, util.wxFunc(self.onFightEnd))
		log_parser.get().registerObserver(log_parser.Parser.EVENT_NEW_LOG, util.wxFunc(self.onNewLog))
		log_parser.get().registerObserver(log_parser.Parser.EVENT_READY, util.wxFunc(self.onParserReady))

		if log_parser.get().ready:
			self.onParserReady()

		self.dashboardFight = None

		headerBox.Add(self.keyText, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
		headerBox.Add(self.keyBox, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
		headerBox.Add(self.keyGenerateButton, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
		headerBox.Add(self.keyJoinButton, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
		headerBox.Add(self.keyVanityCheck, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT)
		headerBox.Add(self.keyStatus, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 10)
		headerBox.Add(self.fightSelector, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)
		self.box.Add(headerBox, 0, wx.EXPAND | wx.ALL, 10)

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

		# Create Ability tab
		self.abilityPanel = wx.Panel(self.tabs)
		self.abilitySizer = wx.BoxSizer(wx.VERTICAL)
		self.abilityPanel.SetSizer(self.abilitySizer)
		self.abilityPanel.Layout()
		self.createAbilityView(self.abilitySizer, self.abilityPanel)
		self.tabs.AddPage(self.abilityPanel, "By Ability")

		# Create Targets tab
		self.targetsPanel = wx.Panel(self.tabs)
		self.targetsSizer = wx.BoxSizer(wx.VERTICAL)
		self.targetsPanel.SetSizer(self.targetsSizer)
		self.targetsPanel.Layout()
		self.createTargetsView(self.targetsSizer, self.targetsPanel)
		self.tabs.AddPage(self.targetsPanel, "By Target")

		self.box.Add(self.tabs, 1, wx.EXPAND | wx.ALL & ~wx.TOP, 10)

		self.panel.SetSizer(self.box)
		self.panel.Layout()

		# Events
		self.Bind(wx.EVT_CLOSE, self.onClose)

		log_analyzer.get().registerFrame(self)

	def onPreferences(self, event):
		dialog = preferences.PreferencesDialog(self)
		dialog.ShowModal()

	def onCheckUpdates(self, event):
		if IS_FROZEN:
			subprocess.Popen(["updater.exe"], close_fds=True)
		else:
			subprocess.Popen(["python", "updater.py"], close_fds=True)
		self.Close()

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
		if raid.isInRaid():
			raid.leaveRaid()
		log_analyzer.get().unregisterFrame(self)
		overlays.killAllOverlays()
		self.Destroy()

	def onResetOverlays(self, event):
		overlays.resetOverlays()
		overlays.killAllOverlays()
		self.updateOverlayList()

	def onCloseOverlays(self, event):
		overlays.killAllOverlays()
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

		raid.generateKey(vanityKey, self.onGotKey, self.onFailedToGetKey)

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
		if not raid.isInRaid():
			# Encode key to ascii (for wx unicode)
			key = self.keyBox.GetValue().encode('ascii')

			self.keyStatus.SetLabel("Joining raid...")
			self.keyBox.SetEditable(False)
			self.keyJoinButton.Disable()
			self.keyGenerateButton.Disable()
			self.keyVanityCheck.Disable()

			raid.joinRaid(key, self.onJoinedRaid, self.onFailedToJoinRaid)
		else:
			raid.leaveRaid()
			self.onLeftRaid()

	def onJoinedRaid(self):
		self.keyJoinButton.SetLabel("Leave Raid")
		self.keyJoinButton.Enable()
		self.keyStatus.SetLabel("")

		config.set("lastRaidKey", self.keyBox.GetValue())

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

	def createReportView(self, parent, panelParent):
		self.reportView = ListBox(panelParent, ["Name", "Value"],
			[200, 200], style=wx.LC_REPORT | wx.NO_BORDER)
		self.reportView.SortListItems(0)

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
		addDetailItem("Combat Duration", lambda a: util.formatDuration(a.combatDurationLinear))
		addDetailItem("Combat Duration (seconds)", lambda a: locale.format("%.2f", a.combatDurationLinear, grouping=True))
		addDetailItem("Combat Enter Time", lambda a: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(a.combatStartTime)))
		addDetailItem("Combat Exit Time", lambda a: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(a.combatEndTime)))

		parent.Add(self.reportView, 1, wx.EXPAND, 0)

	def createRaidView(self, parent, panelParent):
		self.raidView = ListBox(panelParent,
			["", "Player", "Damage", "Damage Taken", "Avg. DPS", "Healing",
				"Healing Received", "Avg. HPS", "Threat"],
			[0, 100, 80, 80, 70, 80, 80, 70, 80], style=wx.LC_REPORT | wx.NO_BORDER)
		self.raidView.SortListItems(1)

		parent.Add(self.raidView, 1, wx.EXPAND, 0)

	def createAbilityView(self, parent, panelParent):
		self.abilityView = ListBox(panelParent,
			["Ability", "Damage", "Healing", "Threat"],
			[100, 100, 100, 100], style=wx.LC_REPORT | wx.NO_BORDER)
		self.abilityView.SortListItems(1, 0)

		parent.Add(self.abilityView, 1, wx.EXPAND, 0)

	def createTargetsView(self, parent, panelParent):
		self.targetsView = ListBox(panelParent,
			["Target", "Damage Dealt", "Damage Taken", "Healing Done",
			"Healing Received", "Threat Received"],
			[150, 100, 100, 100, 100, 100], style=wx.LC_REPORT | wx.NO_BORDER)
		self.targetsView.SortListItems(0, 0)

		parent.Add(self.targetsView, 1, wx.EXPAND, 0)

	def createGridView(self, parent, panelParent):
		self.detailGrid = wx.GridSizer(3, 3, 20, 20)
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
		createDetailBlock("Combat Duration", lambda a: util.formatDuration(a.combatDurationLinear))
		createDetailBlock("Rolling DPS", lambda a: locale.format("%.2f", a.dps, grouping=True))
		createDetailBlock("Rolling HPS", lambda a: locale.format("%.2f", a.hps, grouping=True))

		parent.Add(self.detailGrid, 0, wx.EXPAND | wx.ALL, 10)

	def updateOverlayList(self):
		for name, item in self.m_overlays.iteritems():
			if overlays.isOverlayOpen(name):
				item.Check(True)
			else:
				item.Check(False)

	def onAnalyzerTick(self, analyzer):
		if config.get("neverUpdateInSWTOR"):
			fgHwnd = win32gui.GetForegroundWindow()
			if win32gui.GetWindowText(fgHwnd).find(': The Old Republic') != -1:
				return

		if not analyzer.ready:
			return

		if analyzer.parser.me:
			self.SetTitle("SWAP v%s - %s"%(VERSION, analyzer.parser.me.name))
		else:
			self.SetTitle("SWAP v%s"%VERSION)

		if self.dashboardFight and self.dashboardFight in analyzer.historicFights:
			info = analyzer.historicFights[self.dashboardFight]
		else:
			info = analyzer

		self.updateReportView(info)
		self.updateGridView(info)
		self.updateRaidView(info)
		self.updateAbilityView(info)
		self.updateTargetsView(info)

	def updateReportView(self, analyzer):
		rows = []
		for name in sorted(self.reportUpdaters.keys()):
			getter = self.reportUpdaters[name]
			rows.append([name, getter(analyzer)])
		self.reportView.setRows(rows)

	def updateGridView(self, analyzer):
		for analyzerUpdater in self.gridUpdaters:
			analyzerUpdater(analyzer)
		self.gridPanel.Layout()

	def updateRaidView(self, analyzer):
		tabTitle = "Raid"
		if raid.playerData:
			tabTitle += " [%d players]"%len(raid.playerData)
		self.tabs.SetPageText(2, tabTitle)

		rows = []
		itemMap = []
		for player in raid.playerData:
			connectionType = player['connType']
			name = player['name'][1:]
			rows.append([
				connectionType,
				name,
				locale.format("%d", player['totalDamage'], grouping=True),
				locale.format("%d", player['totalDamageTaken'], grouping=True),
				locale.format("%.2f", player['avgDps'], grouping=True),
				locale.format("%d", player['totalHealing'], grouping=True),
				locale.format("%d", player['totalHealingReceived'], grouping=True),
				locale.format("%.2f", player['avgHps'], grouping=True),
				locale.format("%d", player['totalThreat'], grouping=True)
			])
			itemMap.append([connectionType, name, player['totalDamage'], player['totalDamageTaken'],
				player['avgDps'], player['totalHealing'], player['totalHealingReceived'], player['avgHps'],
				player['totalThreat']])
		self.raidView.setRows(rows, itemMap)

	def updateAbilityView(self, analyzer):
		totalDamage = sum([v['damage'] for v in analyzer.abilityBreakdown.values()])
		totalHealing = sum([v['healing'] for v in analyzer.abilityBreakdown.values()])
		totalThreat = sum([v['threat'] for v in analyzer.abilityBreakdown.values()])
		rows = []
		itemMap = []
		for ability, info in analyzer.abilityBreakdown.iteritems():
			damage = info['damage']
			healing = info['healing']
			threat = info['threat']
			rows.append([
				ability,
				locale.format("%d", damage, grouping=True) +
					" (%.2f%%)"%(util.div(damage, totalDamage) * 100),
				locale.format("%d", healing, grouping=True) +
					" (%.2f%%)"%(util.div(healing, totalHealing) * 100),
				locale.format("%d", threat, grouping=True) +
					" (%.2f%%)"%(util.div(threat, totalThreat) * 100)
			])
			itemMap.append([ability, damage, healing, threat])
		self.abilityView.setRows(rows, itemMap)

	def updateTargetsView(self, analyzer):
		totalDamage = sum([v['damage'] for v in analyzer.entityBreakdown.values()])
		totalDamageTaken = sum([v['damageTaken'] for v in analyzer.entityBreakdown.values()])
		totalHealing = sum([v['healing'] for v in analyzer.entityBreakdown.values()])
		totalHealingReceived = sum([v['healingReceived'] for v in analyzer.entityBreakdown.values()])
		totalThreatReceived = sum([v['threatReceived'] for v in analyzer.entityBreakdown.values()])
		rows = []
		itemMap = []
		for entity, info in analyzer.entityBreakdown.iteritems():
			damage = info['damage']
			damageTaken = info['damageTaken']
			healing = info['healing']
			healingReceived = info['healingReceived']
			threatReceived = info['threatReceived']
			rows.append([
				entity.name,
				locale.format("%d", damage, grouping=True) +
					" (%.2f%%)"%(util.div(damage, totalDamage) * 100),
				locale.format("%d", damageTaken, grouping=True) +
					" (%.2f%%)"%(util.div(damage, totalDamageTaken) * 100),
				locale.format("%d", healing, grouping=True) +
					" (%.2f%%)"%(util.div(healing, totalHealing) * 100),
				locale.format("%d", healingReceived, grouping=True) +
					" (%.2f%%)"%(util.div(healing, totalHealingReceived) * 100),
				locale.format("%d", threatReceived, grouping=True) +
					" (%.2f%%)"%(util.div(threatReceived, totalThreatReceived) * 100),
			])
			itemMap.append([entity.name, damage, damageTaken, healing,
				healingReceived, threatReceived])
		self.targetsView.setRows(rows, itemMap)

	def onFightBegin(self):
		self.fightSelector.SetSelection(0)
		self.dashboardFight = None
		self.onAnalyzerTick(log_analyzer.get())

	def onFightEnd(self):
		self.addFightToSelector(log_parser.get().fights[-1])

	def addFightToSelector(self, fight):
		for i in range(0, self.fightSelector.GetCount()):
			if self.fightSelector.GetClientData(i) == fight:
				return

		priority = sorted(fight.priorityTargets.keys(), key=lambda x: fight.priorityTargets[x], reverse=True)[:4]
		fightName = "  " + (", ".join(map(lambda x:x.name, priority)))
		if not len(priority):
			return
		if not fightName:
			fightName = "<Unknown Fight>"
		for mob in fight.priorityTargets.keys():
			name = mob.name
			nameLower = name.lower()
			if nameLower in MOB_BOSS_LIST:
				fightName = "%s"%name
				break
			if nameLower in MOB_BOSS_MAP_KEYS:
				fightName = "%s"%MOB_BOSS_MAP[nameLower]
				break
		fightTime = time.strftime("%H:%M", time.localtime(fight.enterTime))
		self.fightSelector.Insert("[%s] "%fightTime + fightName, 1, fight)

	def onFightSelected(self, event):
		self.dashboardFight = self.fightSelector.GetClientData(self.fightSelector.GetSelection())
		self.onAnalyzerTick(log_analyzer.get())

	def onParserReady(self):
		for fight in log_parser.get().fights:
			if fight == log_parser.get().fight:
				continue
			self.addFightToSelector(fight)

	def onNewLog(self):
		for i in range(1, self.fightSelector.GetCount()):
			self.fightSelector.Delete(1)
		self.fightSelector.SetSelection(0)
		self.dashboardFight = None
		self.onAnalyzerTick(log_analyzer.get())

	def onSetEnrageTime(self, event):
		dialog = wx.TextEntryDialog(self, "Set enrage timer (seconds)", "Enrage Timer", "0.0")

		enrageTime = config.get("customEnrageTime")
		if enrageTime:
			dialog.SetValue(enrageTime)

		if dialog.ShowModal():
			config.set("customEnrageTime", dialog.GetValue())

if __name__ == '__main__':
	logging.setupLogging("swap")
	locale.setlocale(locale.LC_ALL, '')

	if IS_FROZEN:
		if len(sys.argv) != 2 or sys.argv[1] != '--from-updater':
			subprocess.Popen(["updater.exe"], close_fds=True)
			exit()

	prnt("SWAP v%s booting up..."%VERSION)

	net.init()
	config.load()
	log_parser.start()
	log_analyzer.start(log_parser.getThread())

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
