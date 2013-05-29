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

import wx, random, time, locale
from threading import Thread, Event
from base import BaseOverlay

class DamageDealtOverlay(BaseOverlay):
	def __init__(self):
		BaseOverlay.__init__(self, title="Damage Dealt")
		self.dps.SetLabel("1,750,600")

		self.updaterThread = DamageDealtOverlay.UpdaterThread(self)
		self.updaterThread.start()

		self.Bind(wx.EVT_WINDOW_DESTROY, self.OnClose)

	def OnClose(self, event):
		self.updaterThread.stop()

	def update(self, number):
		self.dps.SetLabel(number)

	class UpdaterThread(Thread):
		damageDone = 0

		def __init__(self, frame):
			Thread.__init__(self)

			self.frame = frame
			self.threadStopping = Event()

		def stop(self):
			self.threadStopping.set()

		def run(self):
			while not self.threadStopping.isSet():
				self.damageDone += random.randint(100,3400)
				wx.CallAfter(self.frame.update, locale.format("%d", self.damageDone, grouping=True))
				time.sleep(1)
