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
from logging import prnt
import config
import overlays

class BaseOverlay(wx.Frame):
	dragDiff = None

	def __init__(self, title="DPS meter", size=(300, 100)):
		wx.Frame.__init__(self, None, title=title, size=size, style=wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR)

		self.title = title

		# UI
		self.panel = wx.Panel(self)
		self.panel.SetDoubleBuffered(True)
		self.box = wx.BoxSizer(wx.VERTICAL)

		self.createUI()

		self.panel.SetSizer(self.box)
		self.panel.Layout()

		# For some reason, frames with no caption do not layout properly.
		self.panel.SetSize(self.GetSize())

		self.panel.Bind(wx.EVT_MOTION, self.OnMouseMove)

		# Bind EVT_MOTION in children and propogate upwards
		for child in self.box.GetChildren():
			child.GetWindow().Bind(wx.EVT_MOTION, lambda e: e.ResumePropagation(wx.EVENT_PROPAGATE_MAX) or e.Skip())

		self.topTimer = wx.Timer(self)
		self.topTimer.Start(250)
		self.Bind(wx.EVT_TIMER, self.OnTopTimer, self.topTimer)

		self.hwnd = self.GetHandle()
		self.setFocusable(False)
		self.setAlpha(150)
		self.updateColors()

		savedPosition = config.GetXY("overlay_%s_pos"%self.GetDerivedName())
		if savedPosition != None:
			self.SetPosition(savedPosition)

		savedSize = config.GetXY("overlay_%s_size"%self.GetDerivedName())
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

	def getBackgroundColor(self):
		return config.Get("overlayBgColor")

	def getForegroundColor(self):
		return config.Get("overlayFgColor")

	def updateColors(self):
		self.panel.SetBackgroundColour(self.getBackgroundColor())
		self.titleText.SetForegroundColour(self.getForegroundColor())
		self.Refresh()

	def createUI(self):
		# Title
		self.titleText = wx.StaticText(self.panel, -1, self.title)
		self.titleText.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.titleText.SetSize(self.titleText.GetBestSize())
		self.box.Add(self.titleText, 0, wx.ALL & ~wx.BOTTOM, 10)

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
			if self.dragDiff:
				self.panel.ReleaseMouse()
				self.dragDiff = None
				self.sizePoint = None
				self.dragSize = None
				config.SetXY("overlay_%s_pos"%self.GetDerivedName(), self.GetPositionTuple())
				config.SetXY("overlay_%s_size"%self.GetDerivedName(), self.GetSizeTuple())
				overlays.SetOverlayBeingDragged(False)
			return

		(sw, sh) = (win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1))

		x, y = win32gui.GetCursorPos()
		pos = wx.Point(x, y)
		if not self.dragDiff:
			self.panel.CaptureMouse()
			self.dragDiff = pos - self.GetPosition()
			self.sizePoint = pos
			self.dragSize = self.GetSize()
			overlays.SetOverlayBeingDragged(True)
			self.PushToTop()

		position = pos - self.dragDiff

		if event.ShiftDown():
			sdiff = pos - self.sizePoint
			sz = self.dragSize + (sdiff[0], sdiff[1])
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
