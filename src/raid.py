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

import threading, urllib, urllib2, json, socket, struct
import log_parser, log_analyzer
from logging import prnt
from constants import *
from bytestream import ByteStream

REQUEST_GET_KEY = 0x1
REQUEST_JOIN_TEST = 0x2
REQUEST_LEAVE_RAID = 0x3
REQUEST_POST_UPDATE = 0x4

# Global variables
currentKey = None
playerData = []
wasInCombat = True
extraTicks = 2

def GenerateKey(vanityKey, successFunc, failureFunc):
	vanityKeyLen = len(vanityKey) if vanityKey else 0
	vanityKey = vanityKey if vanityKey else ""

	def thread():
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			sock.connect(PARSER_SERVER_ADDR)
		except:
			failureFunc()

		stream = ByteStream()
		stream.writeByte(REQUEST_GET_KEY)
		stream.writeString(vanityKey)
		sock.send(stream.toString())

		data = sock.recv(1024)
		sock.close()

		stream = ByteStream(data)
		
		success = stream.readByte() == 1
		if success:
			key = stream.readString()
			successFunc(key)
		else:
			failureFunc()

	t = threading.Thread(target=thread)
	t.start()

def JoinRaid(key, successFunc, failureFunc):
	def thread():
		global currentKey
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			sock.connect(PARSER_SERVER_ADDR)
		except:
			failureFunc()
			return

		stream = ByteStream()
		stream.writeByte(REQUEST_JOIN_TEST)
		stream.writeString(key)
		stream.writeByte(VERSION_INT)
		sock.send(stream.toString())

		data = sock.recv(1024)
		sock.close()

		stream = ByteStream(data)
		
		success = stream.readByte() == 1
		if success:
			currentKey = key
			successFunc()
		else:
			reason = stream.readString()
			failureFunc(reason)

	t = threading.Thread(target=thread)
	t.start()

def LeaveRaid():
	global currentKey

	def thread(key):
		global currentKey
		me = log_analyzer.Get().parser.me
		if not me:
			return

		prnt("Leaving raid %s"%key)

		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			sock.connect(PARSER_SERVER_ADDR)
		except:
			failureFunc()
			return

		stream = ByteStream()
		stream.writeByte(REQUEST_LEAVE_RAID)
		stream.writeString(key)
		stream.writeString(me)
		sock.send(stream.toString())

		data = sock.recv(1024)
		sock.close()

		stream = ByteStream(data)
		
		success = stream.readByte() == 1
		if success:
			prnt("Left raid")
		else:
			prnt("Failed to leave raid, oh well")

	t = threading.Thread(target=thread, args=[currentKey])
	t.start()

	currentKey = None
	wasInCombat = False
	extraTicks = 0

def SendRaidUpdate(updateFunc):
	global extraTicks, wasInCombat, playerData
	parser = log_parser.GetThread().parser

	if not currentKey:
		return

	# Do two extra ticks after combat ends, to settle numbers.
	if not parser.inCombat:
		if wasInCombat:
			if extraTicks > 0:
				extraTicks -= 1
	else:
		wasInCombat = True
		extraTicks = 2

	if extraTicks == 0 or not wasInCombat:
		return

	def thread():
		global playerData
		
		me = parser.me
		analyzer = log_analyzer.Get()

		prnt("Sending raid update")

		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			sock.connect(PARSER_SERVER_ADDR)
		except:
			failureFunc()
			return

		stream = ByteStream()
		stream.writeByte(REQUEST_POST_UPDATE)
		stream.writeString(currentKey)
		stream.writeString(me)
		stream.writeInt(analyzer.totalDamage)
		stream.writeInt(analyzer.totalDamageTaken)
		stream.writeInt(analyzer.totalHealing)
		stream.writeInt(analyzer.totalHealingReceived)
		sock.send(stream.toString())

		data = sock.recv(1024)
		sock.close()

		stream = ByteStream(data)

		prnt("Sent raid update")

		success = stream.readByte() == 1
		if success:
			playerCount = stream.readByte()
			players = []
			for i in range(0, playerCount):
				player = {}
				player['name'] = stream.readString()
				player['totalDamage'] = stream.readInt()
				player['totalDamageTaken'] = stream.readInt()
				player['totalHealing'] = stream.readInt()
				player['totalHealingReceived'] = stream.readInt()
				players.append(player)
			playerData = players
			updateFunc()

	t = threading.Thread(target=thread)
	t.start()

def IsInRaid():
	return currentKey != None
