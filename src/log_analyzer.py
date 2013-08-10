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

ROLLING_SAMPLE = 20

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
		self.dps = 0
		self.hps = 0

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
		
		self.fightId = -1
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
				sampleDamage = 0
				sampleHeal = 0
				buffs = []
				now = time.time()

				if self.parser.fights:
					events = self.parser.fights[self.fightId].events
				else:
					events = []

				if events:
					combatStartTime = events[0].time
					combatEndTime = events[-1].time
					startWasRecent = events[0].recent

				for ev in events:
					if ev.type == GameEvent.TYPE_DAMAGE and ev.actor == self.parser.me:
						totalDamage += ev.damage
						if ev.readTime > now - ROLLING_SAMPLE and ev.recent:
							sampleDamage += ev.damage 
						if not ev.abilityName in damageBreakdown:
							damageBreakdown[ev.abilityName] = 0
						damageBreakdown[ev.abilityName] += ev.damage
					if ev.type == GameEvent.TYPE_DAMAGE and ev.target == self.parser.me:
						totalDamageTaken += ev.damage
					if ev.type == GameEvent.TYPE_HEAL and ev.actor == self.parser.me:
						totalHealing += ev.healing
						if ev.readTime > now - ROLLING_SAMPLE and ev.recent:
							sampleHeal += ev.healing 
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

				# Rolling calculations
				self.dps = util.div(sampleDamage, min(combatDuration, ROLLING_SAMPLE))
				self.hps = util.div(sampleHeal, min(combatDuration, ROLLING_SAMPLE))

				# -----------------------------------
				# Mechanics
				# -----------------------------------

				# TFB HM Op-9 Colors
				self.tfbOrb = 0
				if '2957991221395456' in buffs: # Blue
					self.tfbOrb = 1
				elif '2958167315054592' in buffs: # Orange
					self.tfbOrb = 2
				elif '2958188789891072' in buffs: # Purple
					self.tfbOrb = 3
				elif '2958193084858368' in buffs: # Yellow
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
			wx.CallAfter(frame.onAnalyzerTick, self)

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
