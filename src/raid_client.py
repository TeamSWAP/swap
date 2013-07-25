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
import socket
from time import sleep, time
from select import select

import ext.fuzion as fuzion
import wx

import log_parser
import log_analyzer
import raid
import net
from logging import prnt
from constants import *
from bytestream import ByteStream

REQUEST_PLAYER_UPDATE = 0x5
REQUEST_RAID_UPDATE = 0x6

class RaidClient(threading.Thread):
	def __init__(self, serverNode, failureFunc):
		threading.Thread.__init__(self)
		self.serverNode = serverNode
		self.lastUpdateSent = 0
		self.lastTicks = 1
		self.stoppedEvent = threading.Event()
		self.pausedEvent = threading.Event()
		self.failureFunc = failureFunc

	def run(self):
		prnt("RaidClient: Booting up...")

		self.conn = net.node.connect(self.serverNode, "swap:raid")
		if self.conn.state != fuzion.CS_CONNECTED:
			raid.LeaveRaid()
			wx.CallAfter(self.failureFunc, "node_connect_failed")
			prnt("RaidClient: Connection failed, shutting down...")
			return

		while not self.stoppedEvent.isSet():
			if self.pausedEvent.isSet():
				sleep(0.4)
				continue

			if self.conn.recvPending():
				data = self.conn.recv()
				if data == None:
					if self.conn.closedReason != 0:
						# If we're paused, we don't want to reconnect yet.
						if self.pausedEvent.isSet():
							continue

						prnt("RaidClient: Connection lost, reason=%s"%fuzion.formatError(self.conn.closedReason))

						# Fetch new raid info
						self.serverNode = None
						self.conn = None
						while self.serverNode == None or self.conn == None:
							prnt("RaidClient: Reconnecting...")
							self.serverNode = raid.GetNewServerNode()
							if self.serverNode == None:
								prnt("RaidClient: Failed to get new server node...")
								sleep(2)
								continue
							conn = net.node.connect(self.serverNode, "swap:raid")
							if conn.state == fuzion.CS_CONNECTED:
								self.conn = conn
								self.lastTicks = 2
								continue
							else:
								prnt("RaidClient: Failed to connect to new node! Connection state = %d"%conn.state)
							sleep(2)
					continue
				packet = data.readByte()
				if packet == REQUEST_RAID_UPDATE:
					self.gotRaidUpdate(data)

			now = time()
			if now - self.lastUpdateSent >= 2 and (log_parser.GetThread().parser.inCombat or self.lastTicks >= 1):
				if not log_parser.GetThread().parser.inCombat:
					self.lastTicks -= 1
				else:
					self.lastTicks = 2
				self.sendPlayerUpdate()
				self.lastUpdateSent = now
			sleep(0.1)

		self.conn.close()

		prnt("RaidClient: Shutting down...")

	def pause(self):
		self.pausedEvent.set()

	def resume(self):
		self.pausedEvent.clear()

	def stop(self):
		self.stoppedEvent.set()

	def sendPlayerUpdate(self):
		prnt("RaidClient: Sending update...")
		analyzer = log_analyzer.Get()
		stream = fuzion.ByteStream()
		stream.writeByte(REQUEST_PLAYER_UPDATE)
		stream.writeString(analyzer.parser.me or "@NoPlayer")
		stream.writeInt(analyzer.totalDamage)
		stream.writeInt(analyzer.totalDamageTaken)
		stream.writeFloat((float(analyzer.totalDamage) / float(analyzer.combatDuration)) if analyzer.combatDuration else 0)
		stream.writeInt(analyzer.totalHealing)
		stream.writeInt(analyzer.totalHealingReceived)
		stream.writeFloat((float(analyzer.totalHealing) / float(analyzer.combatDuration)) if analyzer.combatDuration else 0)
		stream.writeInt(analyzer.totalThreat)
		self.conn.send(stream)

	def gotRaidUpdate(self, stream):
		prnt("RaidClient: Got raid update.")

		playerCount = stream.readByte()
		playerList = []
		for i in range(0, playerCount):
			player = {}
			player['name'] = stream.readString()
			player['connType'] = stream.readString()
			player['totalDamage'] = stream.readInt()
			player['totalDamageTaken'] = stream.readInt()
			player['avgDps'] = stream.readFloat()
			player['totalHealing'] = stream.readInt()
			player['totalHealingReceived'] = stream.readInt()
			player['avgHps'] = stream.readFloat()
			player['totalThreat'] = stream.readInt()
			playerList.append(player)

		raid.playerData = playerList
		log_analyzer.Get().notifyFrames()
