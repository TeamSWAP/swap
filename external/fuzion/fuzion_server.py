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

import socket
import threading
import time
import hashlib
import random
import sys
import traceback
import BaseHTTPServer
import urllib2
from select import select

import net_helpers
from bytestream import ByteStream
from logging import SetupLogging

NODE_SERVER_PORT = 57681
REFLECTION_SERVER_PORT = 57681
STATS_SERVER_PORT = 57682

FUZION_VERSION_REQUIRED = 0
FUZION_SERVER_VERSION = "0.1"

SERVER_GATEWAY_IP = "192.168.1.1"
SERVER_PUBLIC_IP = ""

PUBLIC_IP_UPDATE_INTERVAL = 4 * 60 * 60
PUBLIC_IP_UPDATE_LAST = 0

KEEPALIVE_INTERVAL = 60
KEEPALIVE_TIMEOUT = KEEPALIVE_INTERVAL * 5

# Packet codes
P_REGISTER                = 1
P_CONNECT_REQUEST           = 2
P_CONNECT_RESPONSE          = 3
P_TUNNEL_INFO              = 4
P_RELAY_PACKET             = 9

# Error codes
ERR_NO_ERROR               = 0
ERR_NO_NODE                = 1
ERR_REJECTED               = 2

printLock = threading.Lock()

def debug(*args):
    global printLock
    with printLock:
        sys.stdout.write(' '.join(map(lambda x:str(x), args)) + '\n')

def refreshPublicIP():
    global SERVER_PUBLIC_IP
    debug("Getting public IP...")
    u = urllib2.urlopen("http://curlmyip.com")
    ip = u.read().strip()
    u.close()
    if ip.count('.') != 3:
        debug("refreshPublicIP: ip returned not valid=%s"%ip)
        return
    SERVER_PUBLIC_IP = ip
    debug("IP is now %s"%ip)

SetupLogging("fuzion_server")

class ConnectionHandler(threading.Thread):
    def __init__(self, ns, connection, addr):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.ns = ns
        self.sock = connection
        self.sockQueue = net_helpers.SocketQueue(self.sock)
        self.sockPacker = net_helpers.Packer()
        self.addr = addr
        self.id = None

        now = time.time()

        self.lastKeepAliveSent = now
        self.lastPacketReceived = now

    def run(self):
        while True:
            now = time.time()

            r, w, e = select([self.sock], [self.sock], [self.sock], 0)
            if r or e:
                try:
                    data = self.sock.recv(2048)
                except socket.error as e:
                    debug("%s: .recv() died! errno=%d"%(self.id, e.errno))
                    break
                if not data:
                    if self.id:
                        debug("%s: closed"%self.id)
                    else:
                        debug("lost unknown connection")
                    break
                self.sockPacker.read(data)
                self.lastPacketReceived = now

            packet = self.sockPacker.popPacket()
            if packet:
                packet = ByteStream(packet)
                try:
                    self.handlePacket(packet)
                except:
                    debug("handlePacket crashed.")
                    debug(traceback.format_exc())

            if now - self.lastPacketReceived > KEEPALIVE_TIMEOUT:
                debug("%s: timed out."%self.id)
                self.sock.close()
                break

            if w:
                if now - self.lastKeepAliveSent > KEEPALIVE_INTERVAL:
                    self.lastKeepAliveSent = now
                    self.send('')

                self.sockQueue.processNext()
            time.sleep(0.01)
        self.ns.nodeDied(self.id)

    def send(self, data):
        if isinstance(data, ByteStream):
            data = data.toString()
        self.sockQueue.push(self.sockPacker.pack(data))

    def handlePacket(self, data):
        packet = data.readByte()
        if packet == P_REGISTER:
            self.id = self.ns.pushNode(self)

            out = ByteStream()
            out.writeByte(P_REGISTER)
            out.writeString(self.id)
            self.send(out)
        elif packet == P_CONNECT_REQUEST:
            # from source node
            targetId = data.readString()
            targetPort = data.readString()
            debug("%s: requesting connect to %s"%(self.id, targetId))
            self.ns.sendConnectRequest(self, targetId, targetPort)
        elif packet == P_CONNECT_RESPONSE:
            # from target nodef
            targetId = data.readString()
            targetPort = data.readString()
            accepted = data.readBoolean()
            debug("%s: response for %s=%s"%(self.id, targetId, repr(accepted)))
            if accepted:
                self.ns.sendConnectSuccess(self, targetId, targetPort)
            else:
                self.ns.sendConnectRejected(self, targetId, targetPort)
        elif packet == P_TUNNEL_INFO:
            targetId = data.readString()
            targetPort = data.readString()
            privIp = data.readString()
            privPort = data.readInt()
            pubIp = data.readString()
            pubPort = data.readInt()
            debug("%s: sending tunnel info to %s"%(self.id, targetId))
            self.ns.sendTunnelInfo(self, targetId, targetPort, privIp, privPort, pubIp, pubPort)
        elif packet == P_RELAY_PACKET:
            targetId = data.readString()
            targetPort = data.readString()
            data = data.readString()
            self.ns.sendRelayPacket(self, targetId, targetPort, data)

    # thread-safe
    def sendConnectRequest(self, sourceId, targetPort):
        """ Sends the connection request from sourceId to this node. """
        out = ByteStream()
        out.writeByte(P_CONNECT_REQUEST)
        out.writeString(sourceId)
        out.writeString(targetPort)
        self.send(out)

    # thread-safe
    def sendConnectFailed(self, targetId, targetPort, errorCode):
        """ Sends the connection failed packet back to node. """
        out = ByteStream()
        out.writeByte(P_CONNECT_RESPONSE)
        out.writeString(targetId)
        out.writeString(targetPort)
        out.writeByte(errorCode)
        self.send(out)

    # thread-safe
    def sendConnectSuccess(self, targetId, targetPort):
        """ Sends the connection success packet back to node. """
        out = ByteStream()
        out.writeByte(P_CONNECT_RESPONSE)
        out.writeString(targetId)
        out.writeString(targetPort)
        out.writeByte(ERR_NO_ERROR)
        self.send(out)

    # thread-safe
    def sendTunnelInfo(self, targetId, targetPort, privIp, privPort, pubIp, pubPort):
        """ Sends tunnel info to a node. """
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
    def sendRelayPacket(self, targetId, targetPort, data):
        """ Sends tunnel info to a node. """
        out = ByteStream()
        out.writeByte(P_RELAY_PACKET)
        out.writeString(targetId)
        out.writeString(targetPort)
        out.writeString(data)
        self.send(out)


class NodeServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.nodes = {}
        self.nodesLock = threading.Lock()

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', NODE_SERVER_PORT))
        self.sock.listen(1)

        debug("Node Server listening on %d"%NODE_SERVER_PORT)

        while True:
            r, w, e = select([self.sock], [self.sock], [], 0)
            if r:
                connection, addr = self.sock.accept()

                debug("Connection request from %s"%repr(addr))

                nh = ConnectionHandler(self, connection, addr)
                nh.start()
            time.sleep(0.01)
        self.sock.close()

    # thread-safe
    def getNewNodeId(self):
        md = hashlib.md5(str(random.random()) + str("_") + str(time.time())).hexdigest()
        return md

    # thread-safe
    def pushNode(self, node):
        id = self.getNewNodeId()
        with self.nodesLock:
            self.nodes[id] = node
        return id

    # thread-safe
    def nodeDied(self, id):
        with self.nodesLock:
            if id == None or not id in self.nodes:
                return
            del self.nodes[id]

    def findNode(self, id):
        try:
            return self.nodes[id]
        except KeyError:
            return None

    # thread-safe, called from the source ConnectionHandler
    def sendConnectRequest(self, sourceNode, targetId, targetPort):
        """ Sends a connection request to target initiated from source """
        with self.nodesLock:
            sourceId = sourceNode.id
            targetNode = self.findNode(targetId)
            if targetNode != None:
                targetNode.sendConnectRequest(sourceId, targetPort)
            else:
                debug("No such node...")
                sourceNode.sendConnectFailed(targetId, targetPort, ERR_NO_NODE)

    # thread-safe, called from the target ConnectionHandler
    def sendConnectRejected(self, targetNode, sourceId, targetPort):
        """ Sends connection request rejected packet initiated from target """
        with self.nodesLock:
            targetId = targetNode.id
            sourceNode = self.findNode(sourceId)
            if sourceNode != None:
                sourceNode.sendConnectFailed(targetId, targetPort, ERR_REJECTED)

    # thread-safe, called from the target ConnectionHandler
    def sendConnectSuccess(self, targetNode, sourceId, targetPort):
        """ Sends connection request success packet initiated from target """
        with self.nodesLock:
            targetId = targetNode.id
            sourceNode = self.findNode(sourceId)
            if sourceNode != None:
                sourceNode.sendConnectSuccess(targetId, targetPort)

    # thread-safe, called from ConnectionHandler
    def sendTunnelInfo(self, sourceNode, targetId, targetPort, privIp, privPort, pubIp, pubPort):
        """ Sends tunnel info """
        with self.nodesLock:
            sourceId = sourceNode.id
            targetNode = self.findNode(targetId)
            if targetNode != None:
                targetNode.sendTunnelInfo(sourceId, targetPort, privIp, privPort, pubIp, pubPort)
            else:
                debug("sendTunnelInfo: No such node as %s"%targetNode)

    # thread-safe, called from ConnectionHandler
    def sendRelayPacket(self, sourceNode, targetId, targetPort, data):
        """ Relays a packet """
        with self.nodesLock:
            sourceId = sourceNode.id
            targetNode = self.findNode(targetId)
            if targetNode != None:
                targetNode.sendRelayPacket(sourceId, targetPort, data)


class ReflectionServer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.setDaemon(True)

    def run(self):
        global PUBLIC_IP_UPDATE_LAST
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', REFLECTION_SERVER_PORT))

        debug("Reflection Server listening on %d"%REFLECTION_SERVER_PORT)

        refreshPublicIP()
        PUBLIC_IP_UPDATE_LAST = time.time()

        while True:
            r, w, e = select([self.sock], [self.sock], [], 0)
            if r:
                data, addr = self.sock.recvfrom(1024)
                ip = addr[0]
                port = addr[1]
                if ip == SERVER_GATEWAY_IP:
                    ip = SERVER_PUBLIC_IP

                out = ByteStream()
                out.writeString(ip)
                out.writeInt(port)
                self.sock.sendto(out.toString(), addr)

            now = time.time()
            if now - PUBLIC_IP_UPDATE_LAST > PUBLIC_IP_UPDATE_INTERVAL:
                PUBLIC_IP_UPDATE_LAST = now
                threading.Thread(target=refreshPublicIP).start()

            time.sleep(0.01)
        self.sock.close()

class StatsServer(threading.Thread):
    def __init__(self, ns):
        threading.Thread.__init__(self)
        self.ns = ns
        self.setDaemon(True)

    def run(self):
        debug("Stats Server starting on %d"%STATS_SERVER_PORT)
        httpd = BaseHTTPServer.HTTPServer(('', STATS_SERVER_PORT), lambda *x: StatsServer.StatsHandler(self.ns, *x))
        httpd.serve_forever()

    class StatsHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def __init__(self, ns, *args):
            self.ns = ns
            BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, *args)

        def log_request(self, *args):
            pass

        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write("%d nodes connected."%len(self.ns.nodes))

if __name__ == '__main__':
    debug("Fuzion Server v%s starting"%FUZION_SERVER_VERSION)

    ns = NodeServer()
    ns.start()

    rs = ReflectionServer()
    rs.start()

    ss = StatsServer(ns)
    ss.start()

    # Breakable!
    while True:
        time.sleep(60)
