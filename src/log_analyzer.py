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

import atexit
import os
import time
import threading
import traceback

import wx

import raid
import util
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
		self.totalDamageTaken = 0
		self.totalHealing = 0
		self.totalHealingReceived = 0
		self.totalThreat = 0
		self.combatStartTime = 0
		self.combatEndTime = 0
		self.combatDuration = 0
		self.combatDurationLinear = 0
		self.avgDps = 0
		self.avgHps = 0
		self.damageBreakdown = {}

		self.tfbOrb = 0

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
			combatStartLinearTime = 0
			eventTimeDelta = 0
			while not self.stopEvent.isSet():
				if not self.parser.ready:
					time.sleep(0.1)
					wasInCombat = self.parser.inCombat
					continue

				combatStartTime = 0
				combatEndTime = 0
				totalDamage = 0
				totalDamageTaken = 0
				totalHealing = 0
				totalHealingReceived = 0
				totalThreat = 0
				eventTimeDelta = 0
				damageBreakdown = {}
				buffs = []

				events = self.parser.events
				combatEvents = []

				stateInCombat = False
				startWasRecent = False
				for ev in reversed(events):
					if ev.exitEvent or (ev.inCombat and not stateInCombat):
						stateInCombat = True
					elif ev.enterEvent:
						stateInCombat = False
						startWasRecent = ev.recent
						break
					if not stateInCombat:
						continue
					combatEvents.insert(0, ev)

				if combatEvents:
					combatStartTime = combatEvents[0].time
					combatEndTime = combatEvents[-1].time

				for ev in combatEvents:
					if ev.type == GameEvent.TYPE_DAMAGE and ev.actor == self.parser.me:
						totalDamage += ev.damage
						if not ev.abilityName in damageBreakdown:
							damageBreakdown[ev.abilityName] = 0
						damageBreakdown[ev.abilityName] += ev.damage
					if ev.type == GameEvent.TYPE_DAMAGE and ev.target == self.parser.me:
						totalDamageTaken += ev.damage
					if ev.type == GameEvent.TYPE_HEAL and ev.actor == self.parser.me:
						totalHealing += ev.healing
					if ev.type == GameEvent.TYPE_HEAL and ev.target == self.parser.me:
						totalHealingReceived += ev.healing
					if ev.actor == self.parser.me:
						totalThreat += ev.threat

					if ev.type == GameEvent.TYPE_APPLY_BUFF:
						buffs.append(ev.actionType)
					elif ev.type == GameEvent.TYPE_REMOVE_BUFF:
						if ev.actionType in buffs:
							buffs.remove(ev.actionType)

					eventTimeDelta = ev.time - ev.readTime

				combatDuration = combatEndTime - combatStartTime

				self.totalDamage = totalDamage
				self.totalDamageTaken = totalDamageTaken
				self.totalHealing = totalHealing
				self.totalHealingReceived = totalHealingReceived
				self.totalThreat = totalThreat
				self.damageBreakdown = damageBreakdown
				self.combatStartTime = combatStartTime
				self.combatEndTime = combatEndTime
				self.combatDuration = combatDuration
				if len(events) > 0 and self.parser.inCombat and startWasRecent:
					combatNow = time.time() + eventTimeDelta
					self.combatDurationLinear = combatNow - combatStartTime
					if self.combatDurationLinear < 0:
						self.combatDurationLinear = combatDuration
				else:
					self.combatDurationLinear = combatDuration

				# Avg DPS calculation
				self.avgDps = util.div(totalDamage, combatDuration)
				self.avgHps = util.div(totalHealing, combatDuration)

				# -----------------------------------
				# Mechanics
				# -----------------------------------

				# TFB HM Op-9 Colors
				self.tfbOrb = 0
				if '2957991221395456' in buffs: # Blue
					self.tfbOrb = 1
				elif '2958167315054592' in buffs: # Orange
					self.tfbOrb = 2
				elif '2993785478840320' in buffs: # Purple (FIXME: id is probably wrong)
					self.tfbOrb = 3
				elif '2993789773807616' in buffs: # Yellow (FIXME: id is probably wrong)
					self.tfbOrb = 4

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
