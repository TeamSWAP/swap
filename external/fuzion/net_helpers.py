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

import threading
import struct

class SocketQueue(object):
    """Queue for sending data safely in a multithreaded architecture"""

    def __init__(self, socket):
        self.queue = []
        self.lock = threading.Lock()
        self.sock = socket

    def processNext(self):
        with self.lock:
            if len(self.queue) == 0:
                return
            data = self.queue.pop(0)

            total = len(data)
            sent = 0
            tries = 0
            while sent < total and tries < 2000:
                sent = self.sock.send(data)
                tries += 1

    def push(self, data):
        with self.lock:
            self.queue.append(data)

class Packer(object):
    """Packs/Unpacks 'packets' for TCP transmission"""

    def __init__(self):
        self.packets = []
        self.inPacket = False
        self.currentStream = ""
        self.currentPacket = ""
        self.currentPacketLength = 0
        self.packets = []

    def popPacket(self):
        if len(self.packets) == 0:
            return None
        return self.packets.pop(0)

    def pack(self, data):
        return struct.pack('i', len(data)) + data

    def read(self, data=""):
        dataLen = len(data)

        if not self.inPacket:
            # Append new data to stream
            self.currentStream += data

            # If we do not have enough to read a packet length yet, just wait.
            if len(self.currentStream) < 4:
                return

            # Read packet length
            self.currentPacketLength = struct.unpack('i', self.currentStream[:4])[0]

            # Move data to packet and clear stream
            self.inPacket = True

            # Fall through to packet handling:
            data = self.currentStream[4:]
            dataLen = len(self.currentStream) - 4
            self.currentStream = ""

        if dataLen == 0:
            return

        # Calculate number of bytes left in packet
        packetLeft = self.currentPacketLength - len(self.currentPacket)

        # Calculate excess in this stream segment
        excess = (dataLen - packetLeft) if (dataLen >= packetLeft) else 0

        # Push data into packet
        self.currentPacket += data[:packetLeft]

        if dataLen >= packetLeft:
            # Packet is done.
            self.packets.append(self.currentPacket)
            self.inPacket = False
            self.currentPacket = ""
            self.currentPacketLength = 0

        # Handle excess
        if excess > 0:
            self.currentStream = data[packetLeft:]

            # Process the excess
            self.read()
