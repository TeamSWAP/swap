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
import time
import subprocess
import json
import os
import traceback
import logging
from zipfile import ZipFile
from threading import Thread
from urllib2 import urlopen, HTTPError

from constants import *
from logging import prnt

class UpdaterFrame(wx.Frame):
	def __init__(self):
		wx.Frame.__init__(self, None, title="SWAP Updater", size=(400, 150), style=wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE_BOX)

		panel = wx.Panel(self)
		box = wx.BoxSizer(wx.VERTICAL)

		self.title = wx.StaticText(panel, -1, "SWAP")
		self.title.SetFont(wx.Font(20, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
		self.title.SetSize(self.title.GetBestSize())
		box.Add(self.title, 0, wx.ALL & ~wx.BOTTOM, 10)

		self.status = wx.StaticText(panel, -1, "Contacting server...")
		self.status.SetFont(wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL))
		self.status.SetSize(self.status.GetBestSize())
		box.Add(self.status, 0, wx.ALL & ~wx.TOP, 10)

		self.progress = wx.Gauge(panel, -1, 100, size=(0, 20))
		self.progress.Pulse()
		box.Add(self.progress, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

		panel.SetSizer(box)
		panel.Layout()

		Thread(target=checkForUpdates, args=[self]).start()

	def launch(self):
		self.Destroy()

		prnt("")
		prnt("Launching SWAP...")
		prnt("-"*20)

		if IS_COMPILED:
			subprocess.Popen(["swap.exe", "--from-updater"])
		else:
			subprocess.Popen(["python", "swap.py"])

	def errorGettingInfo(self):
		dialog = wx.MessageDialog(self, "Whoops! We couldn't contact our servers to check for updates!", "Error: Couldn't check for update info", wx.ICON_ERROR | wx.OK)
		dialog.ShowModal()
		dialog.Destroy()

		self.launch()

	def errorDownloading(self):
		dialog = wx.MessageDialog(self, "Whoops! We couldn't download that update! Please tell the developers!", "Error: Couldn't download", wx.ICON_ERROR | wx.OK)
		dialog.ShowModal()
		dialog.Destroy()

		self.launch()

	def informUpdate(self, version):
		self.title.SetLabel("Updating to v%s"%version)
		self.status.SetLabel("Downloading...")

	def informApplying(self):
		self.status.SetLabel("Extracting update...")
		self.progress.SetValue(0)

	def setProgress(self, progress):
		self.progress.SetValue(progress * 100)

	def updateComplete(self, info):
		version = info['version']
		changelog = info['changelog']

		self.title.SetLabel("Update complete!")
		self.status.SetLabel("Launching SWAP...")
		self.progress.SetValue(100)

		dialog = wx.MessageDialog(self, changelog, "What's New in v%s"%version, wx.OK)
		dialog.ShowModal()
		dialog.Destroy()

		self.Hide()

		self.launch()

def checkForUpdates(frame):
	prnt("Checking for updates...")

	try:
		url = urlopen(URL_CHECK)
		data = url.read()
		url.close()
		info = json.loads(data)
		#print info
	except HTTPError, e:
		prnt("ERROR: %s"%e.reason)
		wx.CallAfter(frame.errorGettingInfo)
		return

	prnt("Latest version is %s, running %s"%(info['version'], VERSION))

	if info['versionInt'] > VERSION_INT:
		newVersion = info['versionInt']
		prnt("New version!")

		if IS_COMPILED:
			wx.CallAfter(frame.informUpdate, info['version'])
			downloadUpdate(frame, info)
		else:
			wx.CallAfter(frame.launch)
			prnt("Not downloading update because not SWAP is not compiled.")
	else:
		wx.CallAfter(frame.launch)

def downloadUpdate(frame, info):
	url = info['url']
	prnt("Downloading update from %s"%url)

	conn = None
	outputFile = None
	try:
		conn = urlopen(url)
		meta = conn.info()
		fileSize = int(meta.getheaders("Content-Length")[0])
		total = "%0.2f KiB"%(fileSize / 1024.0)

		# Start downloading the file
		blockSize = 8196
		bytesReceived = 0
		outputFile = open("tmp.zip", "wb")
		while True:
			buffer = conn.read(blockSize)
			if not buffer:
				break

			bytesReceived += len(buffer)
			outputFile.write(buffer)

			current = "%0.2f KiB"%(bytesReceived / 1024.0)

			prnt("Downloaded %s out of %s              \r"%(current, total))

			wx.CallAfter(frame.setProgress, float(bytesReceived) / float(fileSize))

		outputFile.close()
		conn.close()

		prnt() # clear return
		prnt("Download complete!")

		wx.CallAfter(frame.informApplying)

		applyUpdate(frame, info)
	except HTTPError, e:
		if conn != None:
			conn.close()
		if outputFile != None:
			outputFile.close()
		prnt("ERROR: %s"%e.reason)
		wx.CallAfter(frame.errorDownloading)
		return

def applyUpdate(frame, info):
	z = None
	if not os.path.exists('pending'):
		os.mkdir('pending')
	try:
		z = ZipFile("tmp.zip")
		nameList = z.namelist()
		current = 0
		total = len(nameList)
		for f in nameList:
			# Installed and zipped use different manifests
			if f in ('swap.exe.manifest', 'updater.exe.manifest'):
				continue
			
			prnt("Extracting %s"%f)
			if f.endswith('/'):
				if not os.path.isdir(f):
					os.mkdir(f)
				continue
			if f in ('updater.py', 'updater.exe'):
				z.extract(f, "pending")
				continue
			if os.path.exists(f):
				if os.path.exists(f + '.old'):
					os.rename(f + '.old', f + '.old.old')
				os.rename(f, f + '.old')
			z.extract(f)
			current += 1
			wx.CallAfter(frame.setProgress, float(current) / float(total))
		z.close()
	except Exception, e:
		prnt(traceback.format_exc())
		if z != None:
			z.close()
		os.remove("tmp.zip")
		wx.CallAfter(frame.launch)
		return

	if not IS_COMPILED:
		prnt("Cleaning out .pyc")

		pycList = [f for f in os.listdir(".") if f.endswith(".pyc")]
		for f in pycList:
			os.remove(f)
	os.remove("tmp.zip")

	wx.CallAfter(frame.updateComplete, info)

logging.SetupLogging("updater")

app = wx.App(redirect=False)
frame = UpdaterFrame()
frame.Show()
app.MainLoop()
