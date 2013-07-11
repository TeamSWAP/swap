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
import config
import overlays

from win32con import *
from logging import prnt

class BaseOverlay(wx.Frame):
	dragDiff = None
	dragSize = None

	def __init__(self, title="DPS meter", size=(300, 100)):
		wx.Frame.__init__(self, None, title=title, size=size, style=wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR)

		self.title = title

		# UI
		self.panel = wx.Panel(self)
		self.panel.SetDoubleBuffered(True)
		self.box = wx.BoxSizer(wx.VERTICAL)

		self.createUI()
		self.updateUI()

		self.panel.SetSizer(self.box)
		self.panel.Layout()

		# For some reason, frames with no caption do not layout properly.
		self.panel.SetSize(self.GetSize())

		self.panel.Bind(wx.EVT_MOTION, self.OnMouseMove)

		self.bindViews(self.box)

		self.updateTimer = wx.Timer(self)
		self.updateTimer.Start(400)
		self.Bind(wx.EVT_TIMER, self.OnUpdateTimer, self.updateTimer)

		self.hwnd = self.GetHandle()
		self.setFocusable(False)
		self.updateColors()

		savedPosition = config.GetXY("overlay_%s_pos"%self.GetDerivedName())
		if savedPosition != None:
			self.SetPosition(savedPosition)

		savedSize = config.GetXY("overlay_%s_size"%self.GetDerivedName())
		if savedSize != None:
			self.SetSize(savedSize)

	def OnUpdateTimer(self, event):
		self.updateUI()

		# Always on Top isn't always so, well, on top. This is a hack to fix those
		# situations. Example: Tabbing to client, then clicking SWTOR, then tabbing
		# back then clicking SWTOR again hides the overlays. We have the taskbar icon
		# hidden and pop the overlay back on top at a regular interval.
		fgHwnd = win32gui.GetForegroundWindow()
		if win32gui.GetWindowText(fgHwnd).find(': The Old Republic') != -1:
			topMost = win32gui.GetWindow(self.GetHandle(), GW_HWNDFIRST)
			topMostTitle = win32gui.GetWindowText(topMost)
			if topMostTitle == self.GetTitle() or topMostTitle == 'MSCTFIME UI':
				return
			if overlays.isOverlayBeingDragged():
				return
			self.PushToTop()

	def bindViews(self, v):
		for child in v.GetChildren():
			if isinstance(child, wx.Sizer):
				bindViews(child.GetSizer())
			cv = child.GetWindow()
			if hasattr(cv, 'GetGridWindow'):
				cv.GetGridWindow().Bind(wx.EVT_MOTION, lambda e: self.OnMouseMove(e))
			elif hasattr(cv, 'Bind'):
				cv.Bind(wx.EVT_MOTION, lambda e: self.OnMouseMove(e))

	def PushToTop(self):
		pos = self.GetPosition()
		size = self.GetSize()
		win32gui.SetWindowPos(self.GetHandle(), HWND_TOPMOST, pos[0], pos[1], size[0], size[1], SWP_NOACTIVATE)

	# Because writing self.__class__.__name__ everywhere is ugly.
	def GetDerivedName(self):
		return self.__class__.__name__

	def getBackgroundColor(self):
		return config.GetColor("overlayBgColor")

	def getForegroundColor(self):
		return config.GetColor("overlayFgColor")

	def updateColors(self):
		self.panel.SetBackgroundColour(self.getBackgroundColor())
		self.titleText.SetForegroundColour(self.getForegroundColor())
		self.setAlpha(config.Get("overlayOpacity"))
		self.Refresh()

	def createUI(self):
		# Title
		self.titleText = wx.StaticText(self.panel, -1, self.title)
		self.titleText.SetSize(self.titleText.GetBestSize())
		self.box.Add(self.titleText, 0, wx.ALL & ~wx.BOTTOM, 10)

	def updateUI(self):
		self.titleText.SetFont(wx.Font(config.Get("overlayHeaderFontSize"), wx.SWISS, wx.NORMAL, wx.BOLD))
		self.updateColors()

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
				self.dragSize = None
				self.sizePoint = None
				config.SetXY("overlay_%s_pos"%self.GetDerivedName(), self.GetPositionTuple())
				config.SetXY("overlay_%s_size"%self.GetDerivedName(), self.GetSizeTuple())
				overlays.setOverlayBeingDragged(False)
			return

		(sw, sh) = (win32api.GetSystemMetrics(0), win32api.GetSystemMetrics(1))

		x, y = win32gui.GetCursorPos()
		pos = wx.Point(x, y)
		if not self.dragDiff:
			self.panel.CaptureMouse()
			self.dragDiff = pos - self.GetPosition()
			overlays.setOverlayBeingDragged(True)
			self.PushToTop()

		if event.ShiftDown():
			if not self.dragSize:
				self.dragSize = self.GetSize()
				self.sizePoint = pos
		else:
			if self.dragSize:
				sdiff = pos - self.sizePoint
				self.dragDiff = self.dragDiff + sdiff
				self.dragSize = None
				self.sizePoint = None

		position = pos - self.dragDiff

		if event.ShiftDown():
			p = self.GetPosition()
			sdiff = pos - self.sizePoint
			sz = self.dragSize + (sdiff[0], sdiff[1])

			# Cap size
			if config.Get("overlaySnap"):
				for monitor in win32api.EnumDisplayMonitors():
					(sx, sy, sw, sh) = monitor[2]
					if p[0] > sx and p[0] < sx + sw and p[1] > sy and p[1] < sy + sh:
						xd = sx + sw - (p[0] + sz[0])
						yd = sy + sh - (p[1] + sz[1])
						sz[0] = (sz[0] + xd) if xd < 0 else sz[0]
						sz[1] = (sz[1] + yd) if yd < 0 else sz[1]

			if config.Get("overlaySizeToGrid"):
				sz[0] = int(round(sz[0] / 10.0) * 10)
				sz[1] = int(round(sz[1] / 10.0) * 10)

			self.SetSize(sz)
			return

		snapThreshold = 20

		if config.Get("overlaySnap"):
			for monitor in win32api.EnumDisplayMonitors():
				(sx, sy, sr, sb) = monitor[2]
				sw = sr - sx
				sh = sb - sy

				# Cap top left, top right
				position[0] = sx if position[0] < sx + snapThreshold and position[0] > sx - snapThreshold else position[0]
				position[1] = sy if position[1] < sy + snapThreshold and position[1] > sy - snapThreshold else position[1]

				# Cap bottom left, bottom right
				size = self.GetSizeTuple()
				extent = position + size
				position[0] = sx + sw - size[0] if extent[0] > sx + sw - snapThreshold and extent[0] < sx + sw + snapThreshold else position[0]
				position[1] = sy + sh - size[1] if extent[1] > sy + sh - snapThreshold and extent[1] < sy + sh + snapThreshold else position[1]

		self.SetPosition(position)
