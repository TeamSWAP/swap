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

import os
import time
import datetime
import ctypes
import re
import threading
import traceback
import atexit
from ctypes.wintypes import MAX_PATH

import log_analyzer
import events
from logging import prnt

# [18:36:21.225] [Cartel Patrol Droid {2981965728841728}:3535188148330] [@Bellestarr] [Explosive Round {827176341471232}] [ApplyEffect {836045448945477}: Damage {836045448945501}] (1216 kinetic {836045448940873}) <1216>

DISAPPEAR_GRACE = 15
DISAPPEAR_ABILITIES = (
	'2276212407795712', # Scoundrel
	'2278037768896512', # Operative
	'2271612497821696', # Shadow
	'2271329029980160', # Assassin
)

# Global variables
parserThread = None

class GameEvent(object):
	TYPE_ABILITY_ACTIVATE   = 0x1
	TYPE_ABILITY_DEACTIVATE = 0x2
	TYPE_ABILITY_CANCEL     = 0x3
	TYPE_APPLY_BUFF         = 0x4
	TYPE_REMOVE_BUFF        = 0x5
	TYPE_ENTER_COMBAT       = 0x6
	TYPE_EXIT_COMBAT        = 0x7
	TYPE_DAMAGE             = 0x8
	TYPE_DEATH              = 0x9
	TYPE_HEAL               = 0x10

	def __init__(self):
		self.type = 0x0
		self.outgoing = False
		self.actor = None
		self.target = None
		self.ability = None
		self.abilityName = None
		self.actionType = None
		self.actionTypeName = None
		self.damage = 0
		self.healing = 0
		self.time = 0
		self.readTime = 0
		self.threat = 0
		self.enterEvent = False
		self.exitEvent = False
		self.inCombat = False
		self.recent = False

class Fight(object):
	def __init__(self):
		self.events = []
		self.enterEvent = None
		self.enterTime = 0
		self.exitEvent = None
		self.exitTime = 0
		self.priorityTargets = {}

class Parser(events.EventSource):
	"""docstring for Parser"""

	# Events
	EVENT_FIGHT_BEGIN = 1
	EVENT_FIGHT_END = 2
	EVENT_NEW_LOG = 3
	EVENT_READY = 4

	def __init__(self):
		events.EventSource.__init__(self)

		self.linePat = re.compile("^\[(?P<hour>\d{1,2})\:(?P<minute>\d{2})\:(?P<second>\d{2})\.(?P<ms>\d{3})\] \[(?P<actor>[^\[\]]*)\] \[(?P<target>[^\[\]]*)\] \[(?:(?P<ability>[^{}]+))?(?: {(?P<abilityid>\d*)})?\] \[(?P<action>[^{}]+) {(?P<actionid>\d*)}: (?P<actiontype>[^{}]+) {(?P<actiontypeid>\d*)}\] \((?:(?P<result>[^\<\>]+))?\)(?: \<(?P<threat>-?\d*)\>)?$")
		self.logLocation = None
		self.fights = []
		self.ready = False
		self.me = None
		self.inCombat = False
		self.getDocs()

	def getDocs(self):
	 	dll = ctypes.windll.shell32
		buf = ctypes.create_unicode_buffer(MAX_PATH + 1)
		if dll.SHGetSpecialFolderPathW(None, buf, 0x0005, False):
		    self.logLocation = buf.value + "\\Star Wars - The Old Republic\\CombatLogs"
		    return True
		else:
		    return False

	def getNewestLog(self, onlyFilename=False):
		if os.path.exists(self.logLocation):
			filename = max(os.listdir(self.logLocation))
			fullPath = self.logLocation + "\\" + filename
			if onlyFilename:
				return filename
			return (filename, fullPath)
		return None

	def getMidnightTimestampForFile(self, filename):
		timestamp = os.path.getctime(filename)
		dt = datetime.datetime.fromtimestamp(timestamp)
		midnight = dt.replace(hour=0, minute=0, second=0, microsecond=0)
		midnightTimestamp = time.mktime(midnight.timetuple())
		return midnightTimestamp

	def run(self, hasStopped):
		prnt("Parser: Starting...")

		log = None
		try:
			if self.logLocation == None:
				raise Exception("No log location set. Did you forget to call getDocs?")

			logInfo = self.getNewestLog()
			if logInfo == None:
				prnt("Parser: Waiting for log...")
				while not hasStopped.isSet():
					logInfo = self.getNewestLog()
					if logInfo != None:
						break
					time.sleep(0.4)
				if hasStopped.isSet():
					return True
			(logFile, logPath) = logInfo

			log = open(logPath, 'r')

			self.inCombat = False
			self.fights = []
			self.fight = None
			self.ready = False
			self.disappearEvent = None

			inUpdate = False

			logCursor = 0
			logDay = self.getMidnightTimestampForFile(logPath)
			logLastActionTime = 0

			prnt("Parser: Began parsing %s"%logFile)
			prnt("Parser: Log day is %s"%datetime.datetime.fromtimestamp(logDay))

			lastLogFileCheck = time.time()

			while not hasStopped.isSet():
				if time.time() - lastLogFileCheck > 1:
					if logFile != self.getNewestLog(onlyFilename=True):
						(logFile, logPath) = self.getNewestLog()

						prnt("Parser: Switched to parsing %s"%logFile)

						# Close previous log, and open new one.
						log.close()
						log = open(logPath, 'r')

						# Reset vars
						self.inCombat = False
						self.fights = []
						self.fight = None
						self.ready = False
						self.me = None
						self.disappearEvent = None

						inUpdate = False

						logCursor = 0
						logDay = self.getMidnightTimestampForFile(logPath)
						logLastActionTime = 0
						prnt("Parser: Log day is %s"%datetime.datetime.fromtimestamp(logDay))

						self.notifyEvent(Parser.EVENT_NEW_LOG)
					lastLogFileCheck = time.time()
				logCursor = log.tell()
				line = log.readline()
				if line == "":
					# Once we reach EOF mark us as ready for analyzation.
					if not self.ready:
						self.ready = True
						self.notifyEvent(Parser.EVENT_READY)
					if inUpdate:
						inUpdate = False
						analyzer = log_analyzer.get()
						analyzer.updatePing.set()
					time.sleep(.25)
					continue
				inUpdate = True
			
				res = self.linePat.match(line)	
				if res:
					hour = int(res.group('hour'))
					minute = int(res.group('minute'))
					second = int(res.group('second'))
					ms = int(res.group('ms'))
					actor = res.group('actor')
					target = res.group('target')
					ability = res.group('ability')
					abilityId = res.group('abilityid')
					action = res.group('action')
					actionId = res.group('actionid')
					actionType = res.group('actiontype')
					actionTypeId = res.group('actiontypeid')
					result = res.group('result')
					threat = int(res.group('threat')) if res.group('threat') else 0

					actionTime = logDay + (hour * 3600) + (minute * 60) + second + (ms / 1000.0)
					# Check for date rollover.
					if actionTime < logLastActionTime:
						logDay += 86400
						actionTime += 86400
						prnt("Parser: Rollover, day is now %s"%datetime.datetime.fromtimestamp(logDay))
					logLastActionTime = actionTime

					# Serious introspection here, man
					if self.me == None and actor == target and actor.find(':') == -1:
						prnt("Parser: Identified %s as me"%actor)
						self.me = actor

					event = GameEvent()
					event.type = self.resolveEventType(actionId, actionTypeId)
					event.actor = actor
					event.target = target
					event.ability = abilityId
					event.abilityName = ability
					event.actionType = actionTypeId
					event.actionTypeName = actionType
					event.inCombat = self.inCombat
					event.time = actionTime
					event.readTime = time.time()
					event.threat = threat
					event.enterEvent = False
					event.exitEvent = False
					event.recent = self.ready

					if event.type == GameEvent.TYPE_ENTER_COMBAT:
						event.enterEvent = True
					elif event.type == GameEvent.TYPE_EXIT_COMBAT:
						event.exitEvent = True
					elif event.type == GameEvent.TYPE_DEATH and self.inCombat and event.target == self.me:
						event.exitEvent = True
					elif event.type == GameEvent.TYPE_APPLY_BUFF and event.actionType == '973870949466372' and self.inCombat:
						# Safe Login Immunity
						event.exitEvent = True

					# Detect disappear
					if self.fights and event.type == GameEvent.TYPE_ABILITY_ACTIVATE and event.ability in DISAPPEAR_ABILITIES:
						lastFight = self.fights[-1]
						exitBluff = False
						# Look back for exit combat.
						for e in reversed(lastFight.events):
							if e.exitEvent:
								e.exitEvent = False
								exitBluff = True
								break
							if event.time - e.time > 0.100:
								break
						if exitBluff:
							self.disappearEvent = event

					# Clear disappear flag if out of grace period
					if self.disappearEvent and event.time - self.disappearEvent.time > DISAPPEAR_GRACE:
						self.disappearEvent = None

					if event.enterEvent:
						newFight = True
						if self.disappearEvent:
							# Continue fight if within grace period
							if event.time - self.disappearEvent.time <= DISAPPEAR_GRACE:
								self.fight = self.fights[-1]
								self.inCombat = True
								newFight = False
							self.disappearEvent = None
						if newFight:
							fight = Fight()
							fight.enterEvent = event
							fight.enterTime = event.time
							self.fights.append(fight)
							self.fight = fight
							self.inCombat = True
							if self.ready:
								self.notifyEvent(Parser.EVENT_FIGHT_BEGIN)
					elif event.exitEvent:
						self.inCombat = False

					if event.type == GameEvent.TYPE_DAMAGE:
						sp = result.split(' ')
						if len(sp) > 2:
							dmg = sp[0]
							dmgType = sp[1]
							dmgTypeId = sp[2]
							if dmg.endswith('*'):
								dmg = dmg[:-1]
							dmg = int(dmg)
							if len(sp) == 6:
								fourth = sp[3]
								fifth = sp[4]
								sixth = sp[5]
								if fifth == 'absorbed' and event.target == self.me:
									absorbAmount = int(fourth[1:])
									dmg -= absorbAmount
						else:
							dmg = 0
						event.damage = dmg

					if event.type == GameEvent.TYPE_HEAL:
						heal = result
						if heal.endswith('*'):
							heal = heal[:-1]
						event.healing = int(heal)

					if self.fight and event.damage > 0:
						actorFriendly = event.actor
						if '{' in actorFriendly:
							actorFriendly = actorFriendly[:actorFriendly.find('{') - 1]
						targetFriendly = event.target
						if '{' in targetFriendly:
							targetFriendly = targetFriendly[:targetFriendly.find('{') - 1]
						for name in (actorFriendly, targetFriendly):
							if not name:
								continue
							if name == self.me:
								continue
							priority = event.damage + event.threat + 1
							if name in self.fight.priorityTargets:
								self.fight.priorityTargets[name] += priority
								continue
							self.fight.priorityTargets[name] = priority

					if self.fight != None:
						self.fight.events.append(event)
					
					if event.exitEvent and self.fight:
						self.fight.exitEvent = event
						self.fight.exitTime = event.time
						self.fight = None
						if self.ready:
							self.notifyEvent(Parser.EVENT_FIGHT_END)
				elif line[-1] != '\n' and line[-1] != '\r':
					prnt("Parser: Corrupted line! Backtracking to %d"%logCursor)
					log.seek(logCursor)
					time.sleep(0.2)
				
				time.sleep(.0001)
		except Exception:
			if log != None:
				log.close()
			prnt(traceback.format_exc())
			return False
		log.close()
		prnt("Parser: Exiting normally...")
		return True

	def resolveEventType(self, actionId, actionTypeId):
		if actionId == '836045448945472': # Event
			if actionTypeId == '836045448945479':
				return GameEvent.TYPE_ABILITY_ACTIVATE
			elif actionTypeId == '836045448945480':
				return GameEvent.TYPE_ABILITY_DEACTIVATE
			elif actionTypeId == '836045448945481':
				return GameEvent.TYPE_ABILITY_CANCEL
			elif actionTypeId == '836045448945489':
				return GameEvent.TYPE_ENTER_COMBAT
			elif actionTypeId == '836045448945490':
				return GameEvent.TYPE_EXIT_COMBAT
			elif actionTypeId == '836045448945493':
				return GameEvent.TYPE_DEATH
		elif actionId == '836045448945477': # ApplyEffect
			if actionTypeId == '836045448945501':
				return GameEvent.TYPE_DAMAGE
			elif actionTypeId == '836045448945500':
				return GameEvent.TYPE_HEAL
			else:
				return GameEvent.TYPE_APPLY_BUFF
		elif actionId == '836045448945478': # RemoveEffect
			return GameEvent.TYPE_REMOVE_BUFF
		return None

class ParserThread(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.parser = None
		self.running = False
		self.setDaemon(True)

	def run(self):
		self.stopEvent = threading.Event()
		self.parser = Parser()
		crashCounter = 0
		while crashCounter < 6:
			self.running = True
			if not self.parser.run(self.stopEvent):
				prnt("ParserThread: Parser has crashed! Restarting... counter=%d"%crashCounter)
				crashCounter += 1
			else:
				break
			self.running = False

	def stop(self):
		self.stopEvent.set()

	def waitTillUp(self):
		while self.parser == None:
			time.sleep(0.0001)
			continue
	
	def isRunning(self):
		return self.running

	def getParser(self):
		return self.parser

def start():
	global parserThread
	parserThread = ParserThread()
	parserThread.start()

	atexit.register(shutdown)

def shutdown():
	global parserThread
	if parserThread != None:
		parserThread.stop()
		parserThread.join()
		parserThread = None

def get():
	return parserThread.parser

def getThread():
	return parserThread

if __name__ == '__main__':
	tParser = ParserThread()
	tParser.start()

	try:
		tParser.waitTillUp()
		parser = tParser.getParser()
		while tParser.isRunning():
			totalDamage = 0
			wasInCombat = False
			endTime = 0
			startTime = 0
			for ev in reversed(parser.events):
				if endTime == 0 and (ev.type == GameEvent.TYPE_EXIT_COMBAT or parser.events[-1].inCombat):
					wasInCombat = True
					endTime = ev.time
				if ev.type == GameEvent.TYPE_ENTER_COMBAT:
					startTime = ev.time
					break
				if ev.inCombat and ev.type == GameEvent.TYPE_DAMAGE:
					totalDamage += ev.damage
					wasInCombat = True
				
			tx = (endTime - startTime) / 1000.0
			if tx != 0:
				prnt("Damage dealt: %d, time: %d"%(totalDamage,tx))
				prnt("DPS: %d"%round(totalDamage / tx, 1))
			time.sleep(.01)
	except:
		prnt(traceback.format_exc())
		tParser.stop()
		tParser.join()
