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
import net

from logging import prnt
from constants import *
from bytestream import ByteStream
from raid_server import RaidServer
from raid_client import RaidClient

REQUEST_GET_KEY = 0x1
REQUEST_JOIN_RAID = 0x2

# Global variables
currentKey = None
playerData = []
wasInCombat = True
extraTicks = 2

# This variable contains True if this client is currently hosting.
isHost = False
raidServer = None
raidClient = None

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
	t.daemon = True
	t.start()

def JoinRaid(key, successFunc, failureFunc):
	def thread():
		global currentKey, raidServer, raidClient

		# Connect to server...
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			sock.connect(PARSER_SERVER_ADDR)
		except:
			failureFunc()
			return

		# Write data
		stream = ByteStream()
		stream.writeByte(REQUEST_JOIN_RAID)
		stream.writeByte(VERSION_INT)
		stream.writeString(key)
		stream.writeString(net.node.getId())
		sock.send(stream.toString())

		# Read data
		data = sock.recv(1024)
		stream = ByteStream(data)
		
		# Process data
		success = stream.readBoolean()
		if success:
			currentKey = key
			isHost = stream.readBoolean()
			serverNode = net.node.getId()
			if isHost:
				prnt("Raid: Joined raid, became host")
				raidServer = RaidServer(sock)
				raidServer.start()
			else:
				prnt("Raid: Joined raid, didn't become host")
				serverNode = stream.readString()
				sock.close()
			raidClient = RaidClient(serverNode)
			raidClient.start()
			successFunc()
		else:
			reason = stream.readString()
			failureFunc(reason)
			sock.close()

	t = threading.Thread(target=thread)
	t.daemon = True
	t.start()

def RejoinRaid():
	global currentKey
	JoinRaid(currentKey, lambda:0, lambda:0)

def LeaveRaid():
	global currentKey

	# TODO: Stub.
	if raidServer != None:
		raidServer.stop()
	if raidClient != None:
		raidClient.stop()

	currentKey = None
	wasInCombat = False
	extraTicks = 0

def IsInRaid():
	return currentKey != None
