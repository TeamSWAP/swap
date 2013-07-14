#
# Copyright 2013 Fuzion
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

import socket, threading, time
from select import select
from bytestream import ByteStream

FUZION_VERSION = 0

# ----------------------------------
# Packet codes
# ----------------------------------
P_REGISTER                    = 1
P_CONNECT_REQUEST             = 2
P_CONNECT_RESPONSE            = 3
P_TUNNEL_INFO                 = 4
P_RELAY_PACKET                = 9

# P2P connection messages
P_TUNNEL_SYNACK               = 5
P_DATA                        = 6
P_CLOSE                       = 7
P_KEEP_ALIVE                  = 8

# ----------------------------------
# Error codes
# ----------------------------------
ERR_NO_ERROR                  = 0
ERR_NO_NODE                   = 1
ERR_REJECTED                  = 2
ERR_CLOSED_BY_REMOTE          = 3
ERR_CLOSED_BY_SELF            = 4
ERR_TIMED_OUT                 = 5

# ----------------------------------
# Connection state
# ----------------------------------
CS_REQUESTED         = 0
CS_ACCEPTED          = 1
CS_TUNNEL_AWAIT_INFO = 2
CS_GOT_TUNNEL_INFO   = 3
CS_TUNNELING         = 4
CS_CONNECTED         = 5
CS_FAILED_BASE       = 100
CS_FAILED_NO_NODE    = CS_FAILED_BASE + 0
CS_FAILED_REJECTED   = CS_FAILED_BASE + 1
CS_FAILED_TUNNEL     = CS_FAILED_BASE + 2

# ----------------------------------
# Node state
# ----------------------------------
NS_NOT_CONNECTED     = 0
NS_CONNECTING        = 1
NS_CONNECTED         = 2
NS_FAILED            = 3
NS_REGISTERED        = 4

printLock = threading.Lock()

def debug(*args):
	global printLock
	with printLock:
		print ' '.join(map(lambda x:str(x), args))

def formatError(code):
	if code == ERR_NO_ERROR:
		return "ERR_NO_ERROR"
	elif code == ERR_NO_NODE:
		return "ERR_NO_NODE"
	elif code == ERR_REJECTED:
		return "ERR_REJECTED"
	elif code == ERR_CLOSED_BY_REMOTE:
		return "ERR_CLOSED_BY_REMOTE"
	elif code == ERR_CLOSED_BY_SELF:
		return "ERR_CLOSED_BY_SELF"
	elif code == ERR_TIMED_OUT:
		return "ERR_TIMED_OUT"

class Node:
	def __init__(self, nodeStateCallback=None):
		self.id = None
		self.ports = {}
		self.portsLock = threading.Lock()
		self.connections = []
		self.stateLock = threading.Lock()
		self.nodeState = NS_NOT_CONNECTED
		self.nodeStateCallback = nodeStateCallback

	# thread-safe: but only call once!
	def setNodeServer(self, server, reflectionServer=None):
		self.nodeServer = server.split(':')
		self.nodeServer = (self.nodeServer[0], int(self.nodeServer[1]))
		self.reflectionServer = reflectionServer.split(':') if reflectionServer else self.nodeServer
		self.reflectionServer = (self.reflectionServer[0], int(self.reflectionServer[1]))
		self.startThread()

	def updateNodeState(self, state):
		self.nodeState = state
		if self.nodeStateCallback:
			self.nodeStateCallback(self.nodeState)

	def startThread(self):
		t = threading.Thread(target=self.mainLoop, args=[])
		t.setDaemon(True)
		t.start()

	def send(self, data):
		if isinstance(data, ByteStream):
			data = data.toString()
		tries = 0
		size = len(data)
		sent = 0
		while sent < size and tries < 20:
			sent += self.sock.send(data[sent:])

	def recv(self):
		raw = self.sock.recv(2048)
		return ByteStream(raw)

	def mainLoop(self):
		debug("Connecting to node server @ %s"%repr(self.nodeServer))
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		while True:
			self.updateNodeState(NS_CONNECTING)
			try:
				self.sock.connect(self.nodeServer)
				break
			except:
				debug("Connect failed, trying again in 5s...")
				self.updateNodeState(NS_FAILED)
			time.sleep(5)

		self.updateNodeState(NS_CONNECTED)
		debug("Connected.")
		
		# send register packet
		debug("Registering with node server...")
		b = ByteStream()
		b.writeByte(P_REGISTER)
		self.send(b)

		while True:
			# communication with node server
			r, w, e = select([self.sock], [self.sock], [], 0)
			if r:
				d = self.recv()
				self.gotDataFromNodeServer(d)
			time.sleep(0.001)

		self.sock.close()

	def gotDataFromNodeServer(self, b):
		p = b.readByte()
		if p == P_REGISTER:
			with self.stateLock:
				self.id = b.readString()
			debug("Registered with node server, id is", self.id)
			self.updateNodeState(NS_REGISTERED)
		elif p == P_CONNECT_REQUEST:
			targetId = b.readString()
			targetPort = b.readString()
			port = self.getPort(targetPort)
			if port == None:
				debug("Rejecting unsilicited connection request from %s at port %s"%(targetId, targetPort))

				out = ByteStream()
				out.writeByte(P_CONNECT_RESPONSE)
				out.writeString(targetId)
				out.writeString(targetPort)
				out.writeBoolean(False)
				self.send(out)
			else:
				debug("Connection request from %s at port %s"%(targetId, targetPort))

				out = ByteStream()
				out.writeByte(P_CONNECT_RESPONSE)
				out.writeString(targetId)
				out.writeString(targetPort)
				out.writeBoolean(True)
				self.send(out)

				if targetId == self.id:
					# loopback
					pass
				else:
					conn = NodeConnection(self, targetId, targetPort)
					conn.state = CS_ACCEPTED
					conn.start()
					self.connections.append(conn)
		elif p == P_CONNECT_RESPONSE:
			targetId = b.readString()
			targetPort = b.readString()
			errorCode = b.readByte()
			state = CS_ACCEPTED
			if errorCode == ERR_NO_NODE:
				state = CS_FAILED_NO_NODE
			elif errorCode == ERR_REJECTED:
				state = CS_FAILED_REJECTED

			self.updateConnectionState(targetId, targetPort, state)
			if state == CS_ACCEPTED:
				self.startConnection(targetId, targetPort)
		elif p == P_TUNNEL_INFO:
			targetId = b.readString()
			targetPort = b.readString()
			privIp = b.readString()
			privPort = b.readInt()
			pubIp = b.readString()
			pubPort = b.readInt()

			conn = self.getConnection(targetId, targetPort)
			conn.gotTunnelInfo(privIp, privPort, pubIp, pubPort)
		elif p == P_RELAY_PACKET:
			targetId = b.readString()
			targetPort = b.readString()
			data = b.readString()

			conn = self.getConnection(targetId, targetPort)
			if conn:
				conn.injectRelayRead(data)

	# thread-safe
	def reflectAddress(self):
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.sendto('', self.reflectionServer)
		privIp, privPort = sock.getsockname()
		data = sock.recv(128)
		sock.close()
		response = ByteStream(data)
		pubIp = response.readString()
		pubPort = response.readInt()
		return (privPort, pubIp, pubPort)

	# thread-safe
	def bind(self, port):
		p = NodePort(port)
		with self.portsLock:
			self.ports[port] = p
		return p

	# thread-safe
	def getPort(self, port):
		p = None
		with self.portsLock:
			if port in self.ports:
				p = self.ports[port]
		return p

	# thread-safe: don't call from the main node thread!
	def connect(self, targetId, targetPort):
		self.waitForNS()

		debug("Connecting to %s"%targetId)

		out = ByteStream()
		out.writeByte(P_CONNECT_REQUEST)
		out.writeString(targetId)
		out.writeString(targetPort)
		self.send(out)

		conn = NodeConnection(self, targetId, targetPort)
		self.connections.append(conn)

		while True:
			# Wait till connected.
			if conn.state == CS_CONNECTED or conn.state >= CS_FAILED_BASE:
				if conn.state == CS_FAILED_NO_NODE:
					debug("Failed to connect: no such node")
				elif conn.state == CS_FAILED_REJECTED:
					debug("Failed to connect: rejected")
				break
			time.sleep(0.1)

		return conn

	# thread-safe
	def getConnection(self, targetId, targetPort):
		for conn in self.connections:
			if conn.targetId == targetId and conn.targetPort == targetPort:
				return conn

	# thread-safe
	def updateConnectionState(self, targetId, targetPort, state):
		for conn in self.connections:
			if conn.targetId == targetId and conn.targetPort == targetPort:
				conn.state = state

	# thread-safe
	def startConnection(self, targetId, targetPort):
		for conn in self.connections:
			if conn.targetId == targetId and conn.targetPort == targetPort and not conn.threadStarted:
				conn.start()

	# thread-safe
	def connectionDied(self, connection):
		self.connections.remove(connection)

	# thread-safe
	def sendTunnelInfo(self, targetId, targetPort, privIp, privPort, pubIp, pubPort):
		out = ByteStream()
		out.writeByte(P_TUNNEL_INFO)
		out.writeString(targetId)
		out.writeString(targetPort)
		out.writeString(privIp)
		out.writeInt(privPort)
		out.writeString(pubIp)
		out.writeInt(pubPort)
		self.send(out)

	# thread-safe
	def sendRelay(self, targetId, targetPort, data):
		out = ByteStream()
		out.writeByte(P_RELAY_PACKET)
		out.writeString(targetId)
		out.writeString(targetPort)
		out.writeString(data)
		self.send(out)

	# thread-safe
	def waitForNS(self):
		while True:
			with self.stateLock:
				if self.id != None:
					return
			time.sleep(0.1)

	# thread-safe
	def getId(self):
		return self.id

	# thread-safe: but only call once!
	def shutdown(self):
		# TODO: signal thread to end
		pass

class NodePort:
	def __init__(self, port):
		self.port = port
		self.pendingConnections = []

	def accept(self):
		while len(self.pendingConnections) == 0:
			time.sleep(0.1)
		return self.pendingConnections.pop(0)

	def connectionPending(self):
		return len(self.pendingConnections) > 0

class NodeConnection(threading.Thread):
	def __init__(self, node, targetId, targetPort):
		threading.Thread.__init__(self)
		self.setDaemon(True)
		
		self.node = node
		self.targetId = targetId
		self.targetPort = targetPort
		self.loopback = self.targetId == self.node.id
		self.state = CS_REQUESTED
		self.tunnelSetup = False
		self.tunnelTicks = 0
		self.lastPacketSent = 0
		self.lastPacketReceived = 0
		self.pendingRecv = []
		self.threadStarted = False
		self.threadStopped = threading.Event()
		self.closed = False
		self.closedReason = 0
		self.relay = False
		self.relayedRead = []

	def start(self):
		self.threadStarted = True
		threading.Thread.start(self)

	def run(self):
		if self.state != CS_CONNECTED:
			if not self.loopback:
				# Get tunnel info
				privIp = socket.gethostbyname(socket.gethostname())
				while True:
					(privPort, pubIp, pubPort) = self.node.reflectAddress()

					self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
					try:
						self.sock.bind(('', privPort))
					except:
						debug("Fuzion: Port %d taken, selecting new port."%(privPort))
						continue
					break

				debug("Bound at", privPort)

				self.node.sendTunnelInfo(self.targetId, self.targetPort, privIp, privPort, pubIp, pubPort)
				if self.state == CS_ACCEPTED:
					self.state = CS_TUNNEL_AWAIT_INFO
				elif self.state == CS_GOT_TUNNEL_INFO:
					self.state = CS_TUNNELING
			else:
				self.state = CS_CONNECTED
				self.pushToPort()

		while not self.threadStopped.isSet():
			now = time.time()

			if self.state != CS_CONNECTED:
				self.updateNotConnected()
				time.sleep(0.2)
				continue

			if self.loopback:
				time.sleep(0.2)
				continue

			# Don't timeout immediately.
			if self.lastPacketReceived == 0:
				self.lastPacketReceived = time.time()

			if self.relay:
				r = len(self.relayedRead) > 0
				w = 1
				e = 0
			else:
				r, w, e = select([self.sock], [self.sock], [], 0)
			if r:
				try:
					data = ByteStream(self._recv())
				except:
					# UDP returns a ECONNRESET for IMCP failures, ignore them
					data = None
				if data != None:
					packetType = data.readByte()
					if packetType == P_DATA:
						self.pendingRecv.append(data.readString())
					elif packetType == P_CLOSE:
						self.closeInternal(ERR_CLOSED_BY_REMOTE)
						break
					elif packetType == P_KEEP_ALIVE:
						pass
					self.lastPacketReceived = now

			if now - self.lastPacketSent > 10:
				packet = ByteStream()
				packet.writeByte(P_KEEP_ALIVE)
				self._send(packet.toString())

				self.lastPacketSent = now

			if now - self.lastPacketReceived > 20:
				self.closeInternal(ERR_TIMED_OUT)
				break

			time.sleep(0.01)

	def send(self, data):
		if isinstance(data, ByteStream):
			data = data.toString()

		if self.loopback:
			self.pendingRecv.append(data)
			return

		packet = ByteStream()
		packet.writeByte(P_DATA)
		packet.writeString(data)
		data = packet.toString()

		tries = 0
		size = len(data)
		sent = 0
		while sent < size and tries < 20:
			sent += self._send(data[sent:])
		self.lastPacketSent = time.time()

	def recv(self, raw=False):
		while len(self.pendingRecv) == 0 and not self.closed:
			time.sleep(0.1)
		if self.closed:
			return None
		data = self.pendingRecv.pop(0)
		return ByteStream(data) if not raw else data

	def recvPending(self):
		if self.closed:
			return True
		return len(self.pendingRecv) > 0

	def close(self):
		if self.closed:
			return
		
		if not self.loopback:
			packet = ByteStream()
			packet.writeByte(P_CLOSE)
			self._send(packet.toString())

		self.closeInternal(ERR_CLOSED_BY_SELF)

	def closeInternal(self, reason):
		self.threadStopped.set()
		self.node.connectionDied(self)
		self.closed = True
		self.closedReason = reason
		if not self.loopback and not self.relay:
			self.sock.close()

	def pushToPort(self):
		# Push the connection into the listening port, if it's our port
		p = self.node.getPort(self.targetPort)
		if p != None:
			p.pendingConnections.append(self)

	def updateNotConnected(self):
		if self.state == CS_TUNNELING:
			debug("Tunneling")
			self.tunnelTicks += 1

			# 0.2 x 10 = 2s for tunnel establishment
			if self.tunnelTicks == 11:
				# Switch to relay for now :(
				debug("Fallback to relay.")
				self.state = CS_CONNECTED
				self.relay = True
				self.pushToPort()
				return

			mySyn = ByteStream()
			mySyn.writeByte(P_TUNNEL_SYNACK)
			mySyn.writeString(self.node.id)
			mySyn.writeString(self.targetPort)
			mySyn = mySyn.toString()

			theirSyn = ByteStream()
			theirSyn.writeByte(P_TUNNEL_SYNACK)
			theirSyn.writeString(self.targetId)
			theirSyn.writeString(self.targetPort)
			theirSyn = theirSyn.toString()

			r, w, e = select([self.sock], [self.sock], [], 0)
			if r:
				try:
					data, addr = self.sock.recvfrom(512)
				except:
					# UDP returns a ECONNRESET for IMCP failures, ignore them
					data = None
				if data == theirSyn:
					self.state = CS_CONNECTED

					# Lock in the address
					self.addr = addr
					self.sock.connect(addr)

					self.pushToPort()

					debug("Tunnel established.")

			debug('Sending priv =', self.tunnelPrivAddr, 'pub =', self.tunnelPubAddr)
			self.sock.sendto(mySyn, self.tunnelPrivAddr)
			self.sock.sendto(mySyn, self.tunnelPubAddr)

	def gotTunnelInfo(self, privIp, privPort, pubIp, pubPort):
		debug("Got tunnel info")
		self.tunnelPrivAddr = (privIp, privPort)
		self.tunnelPubAddr = (pubIp, pubPort)
		if self.state == CS_TUNNEL_AWAIT_INFO:
			self.state = CS_TUNNELING
		else:
			self.state = CS_GOT_TUNNEL_INFO

	def _send(self, data):
		if self.relay:
			self.node.sendRelay(self.targetId, self.targetPort, data)
			return len(data)
		return self.sock.send(data)

	def _recv(self):
		if self.relay:
			while len(self.relayedRead) == 0:
				time.sleep(0.001)
				continue
			return self.relayedRead.pop(0)
		return self.sock.recv(512)

	def injectRelayRead(self, data):
		self.relayedRead.append(data)
