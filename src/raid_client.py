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

import threading, socket
import log_parser, log_analyzer
import raid, net
import ext.fuzion as fuzion

from time import sleep, time
from select import select
from logging import prnt
from constants import *
from bytestream import ByteStream

REQUEST_PLAYER_UPDATE = 0x5
REQUEST_RAID_UPDATE = 0x6
TUNNEL_TIMEOUT = 10

class RaidClient(threading.Thread):
	def __init__(self, serverNode):
		threading.Thread.__init__(self)
		self.serverNode = serverNode
		self.lastUpdateSent = 0
		self.stoppedEvent = threading.Event()

	def run(self):
		prnt("RaidClient: Booting up...")

		self.conn = net.node.connect(self.serverNode, "swap:raid")
		connectionEnded = False

		while not self.stoppedEvent.isSet():
			if self.conn.recvPending():
				data = self.conn.recv()
				if data == None:
					connectionEnded = True
					break
				packet = data.readByte()
				if packet == REQUEST_RAID_UPDATE:
					self.gotRaidUpdate(data)

			now = time()
			if now - self.lastUpdateSent >= 2:
				self.sendPlayerUpdate()
				self.lastUpdateSent = now
			sleep(0.1)

		self.conn.close()

		if connectionEnded:
			# This means we didn't stop intentionally. Either our connection timed out,
			# or the host left the raid. Send a new raid join request, so we can connect
			# to the new host.
			prnt("RaidClient: Reconnecting to raid...")
			raid.RejoinRaid()
			return

		prnt("RaidClient: Shutting down...")

	def stop(self):
		self.stoppedEvent.set()
		self.join()

	def sendPlayerUpdate(self):
		prnt("RaidClient: Sending update...")
		stream = fuzion.ByteStream()
		stream.writeByte(REQUEST_PLAYER_UPDATE)
		stream.writeString(log_analyzer.Get().parser.me or "@NoPlayer")
		stream.writeInt(log_analyzer.Get().totalDamage)
		stream.writeInt(log_analyzer.Get().totalDamageTaken)
		stream.writeInt(log_analyzer.Get().totalHealing)
		stream.writeInt(log_analyzer.Get().totalHealingReceived)
		stream.writeInt(log_analyzer.Get().totalThreat)
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
			player['totalHealing'] = stream.readInt()
			player['totalHealingReceived'] = stream.readInt()
			player['totalThreat'] = stream.readInt()
			playerList.append(player)

		raid.playerData = playerList
		log_analyzer.Get().notifyFrames()
