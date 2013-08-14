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

import threading
import urllib
import urllib2
import json
import socket
import struct

import wx
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

def generateKey(vanityKey, successFunc, failureFunc):
	vanityKeyLen = len(vanityKey) if vanityKey else 0
	vanityKey = vanityKey if vanityKey else ""

	def thread():
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			sock.connect(PARSER_SERVER_ADDR)
		except:
			wx.CallAter(failureFunc)

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
			wx.CallAfter(successFunc, key)
		else:
			wx.CallAfter(failureFunc)

	t = threading.Thread(target=thread)
	t.daemon = True
	t.start()

def joinRaid(key, successFunc, failureFunc):
	def thread():
		global currentKey, raidServer, raidClient

		net.node.waitForNS()

		# Connect to server...
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.settimeout(5)
		try:
			sock.connect(PARSER_SERVER_ADDR)
		except:
			wx.CallAfter(failureFunc, "connect_failed")
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
			raidClient = RaidClient(serverNode, failureFunc, successFunc)
			raidClient.start()
		else:
			reason = stream.readString()
			wx.CallAfter(failureFunc, reason)
			sock.close()

	t = threading.Thread(target=thread)
	t.daemon = True
	t.start()

def getNewServerNode():
	global currentKey, raidServer

	# Connect to server...
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		sock.connect(PARSER_SERVER_ADDR)
	except:
		return

	# Write data
	stream = ByteStream()
	stream.writeByte(REQUEST_JOIN_RAID)
	stream.writeByte(VERSION_INT)
	stream.writeString(currentKey)
	stream.writeString(net.node.getId())
	sock.send(stream.toString())

	# Read data
	data = sock.recv(1024)
	stream = ByteStream(data)
	
	# Process data
	success = stream.readBoolean()
	if success:
		isHost = stream.readBoolean()
		serverNode = net.node.getId()
		if isHost:
			prnt("Raid: Became host")
			raidServer = RaidServer(sock)
			raidServer.start()
		else:
			prnt("Raid: Didn't become host")
			serverNode = stream.readString()
			sock.close()
		return serverNode
	return None

def leaveRaid():
	global currentKey, playerData

	if raidClient != None:
		raidClient.stop()
	if raidServer != None:
		raidServer.stop()

	currentKey = None
	wasInCombat = False
	playerData = []
	extraTicks = 0

def onNodeDisconnected():
	global currentKey
	if currentKey != None:
		prnt("Raid: Fuzion node disconnected, dropping server and pausing client.")
		if raidClient != None:
			raidClient.pause()
		if raidServer != None:
			raidServer.stop()

def onNodeReconnected():
	global currentKey
	if currentKey != None:
		prnt("Raid: Fuzion node reconnected, resuming client.")
		if raidClient != None:
			raidClient.resume()

def isInRaid():
	return currentKey != None
