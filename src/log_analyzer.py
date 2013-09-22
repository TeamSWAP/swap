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
from const import abl, evt
from log_parser import GameEvent, Fight
from logging import prnt

ROLLING_SAMPLE = 20

analyzerThread = None

class FightAnalysis(object):
	def __init__(self):
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
		self.abilityBreakdown = {}
		self.dps = 0
		self.hps = 0
		self.tfbOrb = 0
		self.realtime = False

class AnalyzerThread(threading.Thread):
	def __init__(self, parserThread):
		threading.Thread.__init__(self)
		self.setDaemon(True)

		self.parserThread = parserThread
		self.parserThread.waitTillUp()
		self.parser = self.parserThread.parser
		self.running = False
		self.updateFrames = []
		self.stopEvent = threading.Event()
		self.updatePing = threading.Event()
		
		self.currentAnalysis = FightAnalysis()
		self.historicFights = {}
		self.currentLogFile = None

	def run(self):
		crashCounter = 0
		while crashCounter < 6:
			self.running = True
			if not self.analyzerMain():
				prnt("AnalyzerThread: Analyzer has crashed! Restarting... counter=%d"%crashCounter)
				crashCounter += 1
			else:
				break
			self.running = False

	def analyzeFight(self, fight=-1, realtime=False):
		analysis = FightAnalysis()
		analysis.realtime = realtime

		sampleDamage = 0
		sampleHeal = 0
		buffs = []
		now = time.time()

		if self.parser.fights:
			if not isinstance(fight, Fight):
				fight = self.parser.fights[fight]
			events = fight.events
		else:
			events = []

		if events:
			analysis.combatStartTime = events[0].time
			analysis.combatEndTime = events[-1].time
			startWasRecent = events[0].recent

		for ev in events:
			# Damage Event
			if ev.type == evt.DAMAGE:
				# From Me
				if ev.actor == self.parser.me:
					analysis.totalDamage += ev.damage
					if ev.readTime > now - ROLLING_SAMPLE and ev.recent:
						sampleDamage += ev.damage 
					if not ev.abilityName in analysis.abilityBreakdown:
						analysis.abilityBreakdown[ev.abilityName] = {'damage': 0,
							'healing': 0, 'threat': 0}
					analysis.abilityBreakdown[ev.abilityName]['damage'] += ev.damage

				# To Me
				if ev.type == evt.DAMAGE and ev.target == self.parser.me:
					analysis.totalDamageTaken += ev.damage

			# Heal Event
			if ev.type == evt.HEAL:
				# From Me
				if ev.actor == self.parser.me:
					analysis.totalHealing += ev.healing
					if ev.readTime > now - ROLLING_SAMPLE and ev.recent:
						sampleHeal += ev.healing 
					if not ev.abilityName in analysis.abilityBreakdown:
						analysis.abilityBreakdown[ev.abilityName] = {'damage': 0,
							'healing': 0, 'threat': 0}
					analysis.abilityBreakdown[ev.abilityName]['healing'] += ev.healing

				# To Me
				if ev.target == self.parser.me:
					analysis.totalHealingReceived += ev.healing

			# Apply threat
			if ev.actor == self.parser.me and ev.threat > 0:
				analysis.totalThreat += ev.threat
				if not ev.abilityName in analysis.abilityBreakdown:
					analysis.abilityBreakdown[ev.abilityName] = {'damage': 0,
						'healing': 0, 'threat': 0}
				analysis.abilityBreakdown[ev.abilityName]['threat'] += ev.threat

			# Handle buffs
			if ev.type == evt.APPLY_BUFF:
				buffs.append(ev.actionType)
			elif ev.type == evt.REMOVE_BUFF:
				if ev.actionType in buffs:
					buffs.remove(ev.actionType)

			eventTimeDelta = ev.time - ev.readTime

		analysis.combatDuration = analysis.combatEndTime - analysis.combatStartTime

		if len(events) > 0 and self.parser.inCombat and startWasRecent:
			combatNow = time.time() + eventTimeDelta
			analysis.combatDurationLinear = combatNow - analysis.combatStartTime
			if analysis.combatDurationLinear < 0:
				analysis.combatDurationLinear = analysis.combatDuration
		else:
			analysis.combatDurationLinear = analysis.combatDuration

		# Avg DPS calculation
		analysis.avgDps = util.div(analysis.totalDamage, analysis.combatDuration)
		analysis.avgHps = util.div(analysis.totalHealing, analysis.combatDuration)

		if realtime:
			# Rolling calculations
			analysis.dps = util.div(sampleDamage, min(analysis.combatDuration, ROLLING_SAMPLE))
			analysis.hps = util.div(sampleHeal, min(analysis.combatDuration, ROLLING_SAMPLE))

			# TFB HM Op-9 Colors
			if '2957991221395456' in buffs: # Blue
				analysis.tfbOrb = 1
			elif '2958167315054592' in buffs: # Orange
				analysis.tfbOrb = 2
			elif '2958188789891072' in buffs: # Purple
				analysis.tfbOrb = 3
			elif '2958193084858368' in buffs: # Yellow
				analysis.tfbOrb = 4

		return analysis

	def analyzerMain(self):
		prnt("Analyzer: Starting...")

		self.ready = False
		lastUpdate = 0
		try:
			while not self.stopEvent.isSet():
				if not self.parser.ready:
					time.sleep(0.1)
					continue

				now = time.time()
				if now - lastUpdate >= 1 or self.updatePing.isSet():
					lastUpdate = now
					self.updatePing.clear()

					for fight in self.parser.fights:
						if fight not in self.historicFights and fight != self.parser.fight:
							self.historicFights[fight] = self.analyzeFight(fight)

					# FIXME: Move this to an analysis variable instead?
					self.__dict__ = dict(self.__dict__.items() +
						self.analyzeFight(realtime=True).__dict__.items())
					
					if not self.ready:
						self.ready = True

					self.notifyFrames()

				time.sleep(0.01)
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

def start(parserThread):
	global analyzerThread
	analyzerThread = AnalyzerThread(parserThread)
	analyzerThread.start()

	atexit.register(shutdown)

def shutdown():
	global analyzerThread
	if analyzerThread != None:
		analyzerThread.stop()
		analyzerThread.join()
		analyzerThread = None

def get():
	return analyzerThread
