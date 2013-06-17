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

import threading, urllib, urllib2, json
import log_parser, log_analyzer
from logging import prnt
from constants import *

# Global variables
currentKey = None
playerData = []
wasInCombat = True
extraTicks = 2

def GenerateKey(successFunc, failureFunc):
	def thread():
		f = urllib2.urlopen(URL_PARSER_SERVER + 'getkey')
		raw = f.read()
		f.close()

		data = json.loads(raw)
		if data['success']:
			successFunc(data['key'])
		else:
			failureFunc()

	t = threading.Thread(target=thread)
	t.start()

def JoinRaid(key, successFunc, failureFunc):
	def thread():
		global currentKey

		prnt("Checking key %s"%key)

		f = urllib2.urlopen(URL_PARSER_SERVER + 'jointest?key=' + key)
		raw = f.read()
		f.close()

		data = json.loads(raw)
		if data['success']:
			currentKey = key
			successFunc()

			prnt("Joined raid")
		else:
			failureFunc()
			
			prnt("Failed to join raid")

	t = threading.Thread(target=thread)
	t.start()

def LeaveRaid():
	global currentKey

	def thread(key):
		prnt("Leaving raid %s"%key)

		f = urllib2.urlopen(URL_PARSER_SERVER + 'leaveraid?key=' + key)
		raw = f.read()
		f.close()

		data = json.loads(raw)
		if data['success']:
			prnt("Left raid")
		else:
			prnt("Failed to leave raid, oh well")

	t = threading.Thread(target=thread, args=[currentKey])
	t.start()

	currentKey = None

def SendRaidUpdate(updateFunc):
	global extraTicks, wasInCombat
	parser = log_parser.GetThread().parser

	# Do two extra ticks after combat ends, to settle numbers.
	if not parser.inCombat:
		if wasInCombat:
			if extraTicks > 0:
				extraTicks -= 1
	else:
		wasInCombat = True
		extraTicks = 2

	if not currentKey or extraTicks == 0 or not wasInCombat:
		return

	def thread():
		global playerData
		
		me = parser.me
		analyzer = log_analyzer.Get()

		info = {
			'key': currentKey,
			'player': me,
			'totalDamage': analyzer.totalDamage
		}

		prnt("Sending raid update")

		f = urllib2.urlopen(URL_PARSER_SERVER + 'post?' + urllib.urlencode(info))
		raw = f.read()
		f.close()

		prnt("Sent raid update")

		data = json.loads(raw)
		if data['success']:
			playerData = data['players']
			for player in playerData:
				prnt("%s -> %d"%(player['name'], player['totalDamage']))
			updateFunc()

	t = threading.Thread(target=thread)
	t.start()

def IsInRaid():
	return currentKey != None