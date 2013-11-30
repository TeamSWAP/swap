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

import struct

class ByteStreamException(Exception):
    pass

class ByteStream:
    def __init__(self, data=""):
       self.data = data
       self.length = len(data)
       self.position = 0

    def _assertDataPosition(self, size):
       if (self.position + size > self.length):
          raise ByteStreamException("Not enough data: position=%d > length=%d"%(self.position + size, self.length))

    def _unpackInc(self, expr, size):
       self._assertDataPosition(size)
       x = struct.unpack('!' + expr, self.data[self.position:self.position+size])[0]
       self.position += size
       return x

    def _read(self, size):
       self._assertDataPosition(size)
       x = self.data[self.position:self.position+size]
       self.position += size
       return x

    def readByte(self):
       return ord(self._read(1))

    def writeByte(self, byte):
       self.data += chr(byte)
       self.length += 1

    def readBoolean(self):
       return self.readByte() == 1

    def writeBoolean(self, bool):
       self.writeByte(1 if bool else 0)
       self.length += 1

    def readInt(self):
       return self._unpackInc('i', 4)

    def writeInt(self, number):
       self.data += struct.pack('!i', number)
       self.length += 4

    def readString(self):
       length = self.readByte()
       return self._read(length)

    def writeString(self, string):
       strlen = len(string)
       self.writeByte(strlen)
       self.data += string
       self.length += strlen

    def readFloat(self):
       return self._unpackInc('f', 4)

    def writeFloat(self, number):
       self.data += struct.pack('!f', number)
       self.length += 4

    def reset(self):
       self.position = 0

    def toString(self):
       return self.data

    def __len__(self):
       return self.length
