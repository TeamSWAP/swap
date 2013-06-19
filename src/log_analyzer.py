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

import os, time
import threading
import traceback
import atexit
import wx
import raid
from log_parser import GameEvent
from logging import prnt

analyzerThread = None

class AnalyzerThread(threading.Thread):
	def __init__(self, parserThread):
		threading.Thread.__init__(self)
		self.parserThread = parserThread
		self.parserThread.waitTillUp()
		self.parser = self.parserThread.parser
		self.running = False
		self.updateFrames = []
		self.stopEvent = threading.Event()
		self.setDaemon(True)

		self.totalDamage = 0
		self.avgDps = 0

	def run(self):
		crashCounter = 0
		while crashCounter < 6:
			self.running = True
			if not self.analyze():
				prnt("AnalyzerThread: Analyzer has crashed! Restarting... counter=%d"%crashCounter)
				crashCounter += 1
			else:
				break
			self.running = False

	def analyze(self):
		prnt("Analyzer: Starting...")
		try:
			lastRaidUpdate = time.time()
			stateInCombat = False
			while not self.stopEvent.isSet():
				combatStartTime = 0
				combatEndTime = 0
				totalDamage = 0
				totalDamageTaken = 0
				totalHealing = 0
				totalHealingReceived = 0

				events = self.parser.events
				for ev in reversed(events):
					if not stateInCombat and (ev.type == GameEvent.TYPE_EXIT_COMBAT or (combatEndTime == 0 and self.parser.inCombat)):
						combatEndTime = ev.time
						stateInCombat = True
					elif ev.type == GameEvent.TYPE_ENTER_COMBAT:
						combatStartTime = ev.time
						stateInCombat = False
						break

					if not stateInCombat:
						continue

					if ev.type == GameEvent.TYPE_DAMAGE and ev.actor == self.parser.me:
						totalDamage += ev.damage
					if ev.type == GameEvent.TYPE_DAMAGE and ev.target == self.parser.me:
						totalDamageTaken += ev.damage
					if ev.type == GameEvent.TYPE_HEAL and ev.actor == self.parser.me:
						totalHealing += ev.healing
					if ev.type == GameEvent.TYPE_HEAL and ev.target == self.parser.me:
						totalHealingReceived += ev.healing
				combatDuration = combatEndTime - combatStartTime

				self.totalDamage = totalDamage
				self.totalDamageTaken = totalDamageTaken
				self.totalHealing = totalHealing
				self.totalHealingReceived = totalHealingReceived
				self.combatDuration = combatDuration
				if len(events) > 0 and self.parser.inCombat:
					self.combatDurationLinear = time.time() - combatStartTime
					if self.combatDurationLinear < 0:
						self.combatDurationLinear = combatDuration
				else:
					self.combatDurationLinear = combatDuration

				# Avg DPS calculation
				self.avgDps = (totalDamage / combatDuration) if combatDuration > 0 else 0
				self.avgHps = (totalHealing / combatDuration) if combatDuration > 0 else 0
				
				now = time.time()
				if now - lastRaidUpdate >= 2.5 and self.parser.me:
					lastRaidUpdate = now
					raid.SendRaidUpdate(self.notifyFrames)

				self.notifyFrames()

				time.sleep(1) # tick
		except:
			print traceback.format_exc()
			return False
		prnt("Analyzer: Exiting normally...")
		return True

	def registerFrame(self, frame):
		self.updateFrames.append(frame)

	def unregisterFrame(self, frame):
		self.updateFrames.remove(frame)

	def notifyFrames(self):
		for frame in self.updateFrames:
			wx.CallAfter(frame.OnAnalyzerTick, self)

	def stop(self):
		self.stopEvent.set()

	def waitTillUp(self):
		while self.parser == None:
			time.sleep(0.0001)
			continue
	
	def isRunning(self):
		return self.running

def Start(parserThread):
	global analyzerThread
	analyzerThread = AnalyzerThread(parserThread)
	analyzerThread.start()

	atexit.register(Shutdown)

def Shutdown():
	global analyzerThread
	if analyzerThread != None:
		analyzerThread.stop()
		analyzerThread.join()
		analyzerThread = None

def Get():
	return analyzerThread
