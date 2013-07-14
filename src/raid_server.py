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
import log_parser, log_analyzer, net
import ext.fuzion as fuzion

from time import sleep, time
from select import select
from logging import prnt
from constants import *
from bytestream import ByteStream

REQUEST_UPDATE = 0x5
REQUEST_RAID_UPDATE = 0x6

class RaidServer(threading.Thread):
	def __init__(self, sock):
		threading.Thread.__init__(self)
		self.centralSock = sock
		self.node = None
		self.stoppedEvent = threading.Event()
		self.clientList = []
		self.lastRaidUpdateSent = 0
		self.lastRaidUpdatePoke = 0

	def run(self):
		prnt("RaidServer: Booting up...")

		self.port = net.node.bind("swap:raid")

		self.centralSock.setblocking(False)
		while not self.stoppedEvent.isSet():
			now = time()

			# Central server
			r, w, e = select([self.centralSock], [self.centralSock], [], 0)
			if r:
				data = self.centralSock.recv(1024)
				stream = ByteStream(data)
				packetType = stream.readByte()

			if self.port.connectionPending():
				conn = self.port.accept()
				self.clientList.append({ 'conn': conn, 'playerInfo': None })

			for client in self.clientList:
				conn = client['conn']
				if conn.recvPending():
					data = conn.recv()
					if data == None:
						playerName = client['playerInfo']['name'] if client['playerInfo'] else "<NoInfo>"
						prnt("Client (%s) left raid, reason=%s"%(playerName, fuzion.formatError(conn.closedReason)))
						self.lastRaidUpdatePoke = time()
						self.clientList.remove(client)
						continue
					packetType = data.readByte()
					if packetType == REQUEST_UPDATE:
						self.processPlayerUpdate(client, data)

			if now - self.lastRaidUpdateSent > 2 and now - self.lastRaidUpdatePoke < 5:
				self.sendRaidUpdate()
				self.lastRaidUpdateSent = now

			sleep(0.1)

		for client in self.clientList:
			conn = client['conn']
			conn.close()
		
		self.centralSock.close()

		prnt("RaidServer: Shutting down...")

	def stop(self):
		self.stoppedEvent.set()

	def processPlayerUpdate(self, client, stream):
		name = stream.readString()
		totalDamage = stream.readInt()
		totalDamageTaken = stream.readInt()
		avgDps = stream.readFloat()
		totalHealing = stream.readInt()
		totalHealingReceived = stream.readInt()
		avgHps = stream.readFloat()
		totalThreat = stream.readInt()

		prnt("RaidServer: Got player update from %s!"%name)

		conn = client['conn']
		connType = 'T'
		if conn.relay:
			connType = 'R'
		elif conn.loopback:
			connType = 'L'

		client['playerInfo'] = {
			'name': name,
			'connType': connType,
			'totalDamage': totalDamage,
			'totalDamageTaken': totalDamageTaken,
			'avgDps': avgDps,
			'totalHealing': totalHealing,
			'totalHealingReceived': totalHealingReceived,
			'avgHps': avgHps,
			'totalThreat': totalThreat
		}
		self.lastRaidUpdatePoke = time()

	def sendRaidUpdate(self):
		prnt("RaidServer: Sending raid update...")

		stream = fuzion.ByteStream()
		stream.writeByte(REQUEST_RAID_UPDATE)

		playerList = []
		for client in self.clientList:
			playerInfo = client['playerInfo']
			if playerInfo == None:
				continue
			playerList.append(playerInfo)

		stream.writeByte(len(playerList))
		for player in playerList:
			stream.writeString(player['name'])
			stream.writeString(player['connType'])
			stream.writeInt(player['totalDamage'])
			stream.writeInt(player['totalDamageTaken'])
			stream.writeFloat(player['avgDps'])
			stream.writeInt(player['totalHealing'])
			stream.writeInt(player['totalHealingReceived'])
			stream.writeFloat(player['avgHps'])
			stream.writeInt(player['totalThreat'])

		for client in self.clientList:
			conn = client['conn']
			conn.send(stream)
