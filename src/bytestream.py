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

class ByteStream:
	data = ""
	position = 0

	def __init__(self, data=""):
		self.data = data

	def readByte(self):
		byte = ord(self.data[self.position])
		self.position += 1
		return byte

	def writeByte(self, byte):
		self.data += chr(byte)

	def readBoolean(self):
		return self.readByte() == 1

	def writeBoolean(self, bool):
		self.writeByte(1 if bool else 0)

	def readInt(self):
		number = struct.unpack('!i', self.data[self.position:self.position + 4])[0]
		self.position += 4
		return number

	def writeInt(self, number):
		self.data += struct.pack('!i', number)

	def readUnsignedInt(self):
		number = struct.unpack('!I', self.data[self.position:self.position + 4])[0]
		self.position += 4
		return number

	def writeUnsignedInt(self, number):
		self.data += struct.pack('!I', number)

	def readString(self):
		length = self.readByte()
		string = self.data[self.position:self.position + length]
		self.position += length
		return string

	def writeString(self, string):
		self.writeByte(len(string))
		self.data += string

	def readFloat(self):
		number = struct.unpack('!f', self.data[self.position:self.position + 4])[0]
		self.position += 4
		return number

	def writeFloat(self, number):
		self.data += struct.pack('!f', number)

	def toString(self):
		return self.data

	def length(self):
		return len(self.data)
