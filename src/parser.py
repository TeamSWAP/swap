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
import ctypes
import re
import threading
import traceback
from ctypes.wintypes import MAX_PATH

# [18:36:21.225] [Cartel Patrol Droid {2981965728841728}:3535188148330] [@Bellestarr] [Explosive Round {827176341471232}] [ApplyEffect {836045448945477}: Damage {836045448945501}] (1216 kinetic {836045448940873}) <1216>

class GameEvent:
	TYPE_ABILITY_ACTIVATE   = 0x1
	TYPE_ABILITY_DEACTIVATE = 0x2
	TYPE_ABILITY_CANCEL     = 0x3
	TYPE_APPLY_BUFF         = 0x4
	TYPE_REMOVE_BUFF        = 0x5
	TYPE_ENTER_COMBAT       = 0x6
	TYPE_EXIT_COMBAT        = 0x7
	TYPE_DAMAGE             = 0x8

	def __init__(self):
		self.type = 0x0
		self.outgoing = False
		self.actor = None
		self.target = None
		self.ability = None
		self.damage = 0
		self.time = 0

class Parser:
	"""docstring for Parser"""

	def __init__(self):
		self.linePat = re.compile("^\[(?P<hour>\d{1,2})\:(?P<minute>\d{2})\:(?P<second>\d{2})\.(?P<ms>\d{3})\] \[(?P<actor>[^\[\]]*)\] \[(?P<target>[^\[\]]*)\] \[(?:(?P<ability>[^{}]+))?(?: {(?P<abilityid>\d*)})?\] \[(?P<action>[^{}]+) {(?P<actionid>\d*)}: (?P<actiontype>[^{}]+) {(?P<actiontypeid>\d*)}\] \((?:(?P<result>[^\<\>]+))?\)(?: \<(?P<threat>\d*)\>)?$")
		self.logLocation = None
		self.events = []
		self.me = None
		pass

	def getDocs(self):
	 	dll = ctypes.windll.shell32
		buf = ctypes.create_unicode_buffer(MAX_PATH + 1)
		if dll.SHGetSpecialFolderPathW(None, buf, 0x0005, False):
		    self.logLocation = buf.value + "\\Star Wars - The Old Republic\\CombatLogs"
		    return True
		else:
		    return False

	def getNewestLog(self):
		return max(os.listdir(self.logLocation))

	def run(self, hasStopped):
		if self.logLocation == None:
			print "No log location set. Did you forget to call getDocs?"

		self.events = []
		log = open(self.logLocation + "\\" + self.getNewestLog(),'r')
		inCombat = False
		runningTime = 0
		lastTime = 0
		try:
			while not hasStopped.isSet():
				line = log.readline()
				if line == "":
					continue
				else:
					res = self.linePat.match(line)	
					if res:
						#print "\n"
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
						actionTime = (hour * 3600000) + (minute * 60000) + (second * 1000) + ms

						# If previous event is "after" this event, we must have passed midnight,
						# update running time.
						if actionTime < lastTime:
							runningTime = lastTime
						if runningTime != 0:
							actionTime += runningTime

						lastTime = actionTime

						# Serious introspection here, man
						if self.me == None and actor == target:
							print "Found me:", actor
							self.me = actor

						event = GameEvent()
						event.type = self.resolveEventType(actionId, actionTypeId)
						event.actor = actor
						event.target = target
						event.ability = abilityId
						event.inCombat = inCombat
						event.time = actionTime

						if event.type == GameEvent.TYPE_ENTER_COMBAT:
							inCombat = True
						elif event.type == GameEvent.TYPE_EXIT_COMBAT:
							inCombat = False

						if event.type == GameEvent.TYPE_DAMAGE:
							sp = result.split(' ')
							dmg = sp[0]
							dmgType = sp[1]
							dmgTypeId = sp[2]
							if dmg.endswith('*'):
								dmg = dmg[:-1]
							dmg = int(dmg)
							event.damage = dmg

						self.events.append(event)
						
				time.sleep(.0001)
		except Exception:
			print "Parser: Parser has crashed!"
			print traceback.format_exc()
		log.close()

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
		elif actionId == '836045448945477': # ApplyEffect
			if actionTypeId == '836045448945501':
				return GameEvent.TYPE_DAMAGE
		return None

if __name__ == '__main__':
	parser = Parser()
	if not parser.getDocs():
		print "ERROR: Failed to get combat logs location."
		exit(1)
	hasStopped = threading.Event()
	def pRun():
		global hasStopped
		while not hasStopped.isSet():
			print "ParserThread: Starting parser"
			parser.run(hasStopped)
			print "ParserThread: Parser stopped!"
	tParser = threading.Thread(target=pRun, name="ParserThread")
	tParser.start()

	try:
		while True:
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
				print "Damage dealt: ",totalDamage,"time:",tx
				print "DPS: ", round(totalDamage / tx, 1)
			time.sleep(.01)
	except:
		print traceback.format_exc()
		hasStopped.set()
		tParser.join()
