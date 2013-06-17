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

def JoinRaid(key):
	global currentKey
	currentKey = key

def SendRaidUpdate(updateFunc):
	if not currentKey:
		return

	def thread():
		me = log_parser.GetThread().parser.me
		analyzer = log_analyzer.Get()

		info = {
			'key': currentKey,
			'player': me,
			'totalDamage': analyzer.totalDamage
		}

		prnt("Sending raid update: %s"%(URL_PARSER_SERVER + 'post?' + urllib.urlencode(info)))

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
