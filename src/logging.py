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

import sys, atexit
from constants import *
from threading import Lock

threadLock = Lock()
redirector = None

class LogRedirector:
	def __init__(self, tag):
		if IS_COMPILED:
			self.fileOut = open('debug-%s.log'%tag, 'w')
		else:
			self.fileOut = None
		self.stdOut = sys.stdout
		self.stdErr = sys.stderr
		sys.stdout = self
		sys.stderr = self
		self.closed = False

	def write(self, text):
		if self.fileOut:
			self.fileOut.write(text)
		self.stdOut.write(text)

	def close(self):
		sys.stdout = self.stdOut
		sys.stderr = self.stdErr
		if self.fileOut:
			self.fileOut.close()
		self.closed = True

	def __del__(self):
		if not self.closed:
			self.close()

def SetupLogging(tag):
	global redirector
	redirector = LogRedirector(tag)
	atexit.register(redirector.close)

def prnt(text):
	with threadLock:
		redirector.write(str(text) + '\n')
