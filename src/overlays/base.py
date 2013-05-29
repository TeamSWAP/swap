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
import win32gui, win32api, win32process
from win32con import *
import config
import overlays

class BaseOverlay(wx.Frame):
	dragPoint = None

	def __init__(self, title="DPS meter"):
		wx.Frame.__init__(self, wx.GetApp().GetTopWindow(), title="TB_OVERLAY", size=(300, 100), style=wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR)

		# UI
		self.panel = wx.Panel(self)
		self.box = wx.BoxSizer(wx.VERTICAL)

		# Title
		self.title = wx.StaticText(self.panel, -1, title)
		self.title.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.title.SetSize(self.title.GetBestSize())
		self.box.Add(self.title, 0, wx.ALL & ~wx.BOTTOM, 10)

		# DPS
		self.dps = wx.StaticText(self.panel, -1, "2100.35")
		self.dps.SetFont(wx.Font(24, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.dps.SetSize(self.dps.GetBestSize())
		self.box.Add(self.dps, 0, wx.ALL, 10)

		self.panel.SetSizer(self.box)
		self.panel.Layout()

		# For some reason, frames with no caption do not layout properly.
		self.panel.SetSize(self.GetSize())

		self.panel.Bind(wx.EVT_MOTION, self.OnMouseMove)

		self.topTimer = wx.Timer(self)
		self.topTimer.Start(250)
		self.Bind(wx.EVT_TIMER, self.OnTopTimer, self.topTimer)

		self.hwnd = self.GetHandle()
		self.setFocusable(False)
		self.setAlpha(150)
		self.updateColors()

		savedPosition = config.Get("overlay_%s_pos"%self.GetDerivedName())
		if savedPosition != None:
			self.SetPosition(savedPosition)

		savedSize = config.Get("overlay_%s_size"%self.GetDerivedName())
		if savedSize != None:
			self.SetSize(savedSize)

	# Always on Top isn't always so, well, on top. This is a hack to fix those
	# situations. Example: Tabbing to client, then clicking SWTOR, then tabbing
	# back then clicking SWTOR again hides the overlays. We have the taskbar icon
	# hidden and pop the overlay back on top at a regular interval.
	def OnTopTimer(self, event):
		# Only enforce while you're tabbed to SWTOR
		fgHwnd = win32gui.GetForegroundWindow()
		if win32gui.GetWindowText(fgHwnd).find(': The Old Republic') != -1:
			topMost = win32gui.GetWindow(self.GetHandle(), GW_HWNDFIRST)
			topMostTitle = win32gui.GetWindowText(topMost)
			if topMostTitle == self.GetTitle() or topMostTitle == 'MSCTFIME UI':
				return
			if overlays.IsOverlayBeingDragged():
				return
			self.PushToTop()

	def PushToTop(self):
		pos = self.GetPosition()
		size = self.GetSize()
		win32gui.SetWindowPos(self.GetHandle(), HWND_TOPMOST, pos[0], pos[1], size[0], size[1], SWP_NOACTIVATE)

	# Because writing self.__class__.__name__ everywhere is ugly.
	def GetDerivedName(self):
		return self.__class__.__name__

	def getForegroundColor(self):
		return config.Get("overlayFgColor")

	def updateColors(self):
		self.panel.SetBackgroundColour(config.Get("overlayBgColor"))
		self.title.SetForegroundColour(self.getForegroundColor())
		self.dps.SetForegroundColour(self.getForegroundColor())
		self.Refresh()

	def setFocusable(self, isFocusable):
		style = win32gui.GetWindowLong(self.hwnd, GWL_EXSTYLE)
		if isFocusable:
			style &= ~WS_EX_NOACTIVATE
		else:
			style |= WS_EX_NOACTIVATE
		win32gui.SetWindowLong(self.hwnd, GWL_EXSTYLE, style)

	def setAlpha(self, alpha):
		self.SetTransparent(alpha)

	# Mouse movement event
	def OnMouseMove(self, event):
		if not event.Dragging():
			if self.dragPoint:
				self.panel.ReleaseMouse()
				self.dragPoint = None
				self.sizePoint = None
				self.dragSize = None
				config.Set("overlay_%s_pos"%self.GetDerivedName(), self.GetPositionTuple())
				config.Set("overlay_%s_size"%self.GetDerivedName(), self.GetSizeTuple())
				overlays.SetOverlayBeingDragged(False)
			return

		(sw, sh) = (win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1))

		pos = event.GetPosition()
		if not self.dragPoint:
			self.panel.CaptureMouse()
			self.dragPoint = pos
			self.sizePoint = pos
			self.dragSize = self.GetSize()
			overlays.SetOverlayBeingDragged(True)
			self.PushToTop()

		diff = pos - self.dragPoint
		position = self.GetPosition() + diff

		if event.ShiftDown():
			sdiff = pos - self.sizePoint
			sz = self.dragSize + (sdiff[0], sdiff[1])
			self.dragPoint += (diff[0], diff[1])
			self.SetSize(sz)
			return

		# Cap top left, top right
		position[0] = 0 if position[0] < 20 else position[0]
		position[1] = 0 if position[1] < 20 else position[1]

		# Cap bottom left, bottom right
		size = self.GetSizeTuple()
		extent = position + size
		position[0] = sw - size[0] if extent[0] > sw-20 else position[0]
		position[1] = sh - size[1] if extent[1] > sh-20 else position[1]

		self.SetPosition(position)
