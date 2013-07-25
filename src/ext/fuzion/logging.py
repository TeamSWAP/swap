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

import atexit
import sys
from datetime import datetime
from threading import Lock

DEBUG_TO_FILE = True

threadLock = Lock()
redirector = None

class LogRedirector:
	def __init__(self, tag):
		self.fileName = 'debug-%s.log'%tag
		self.fileLock = Lock()
		if DEBUG_TO_FILE:
			f = open(self.fileName, 'w')
			f.close()
		self.stdOut = sys.stdout
		self.stdErr = sys.stderr
		sys.stdout = self
		sys.stderr = self
		self.closed = False

	def write(self, text):
		time = datetime.now()
		timeTxt = "[%02d:%02d:%02d] "%(time.hour, time.minute, time.second)
		text = timeTxt + text
		if text.endswith("\n"):
			text = text[:-1].replace("\n", "\n" + timeTxt) + "\n"
		else:
			text = text.replace("\n", "\n" + timeTxt)
		if DEBUG_TO_FILE:
			with self.fileLock:
				f = open(self.fileName, 'a+')
				f.write(text)
				f.close()
		self.stdOut.write(text)

	def close(self):
		sys.stdout = self.stdOut
		sys.stderr = self.stdErr
		self.closed = True

	def __del__(self):
		if not self.closed:
			self.close()

def SetupLogging(tag):
	global redirector
	redirector = LogRedirector(tag)
	atexit.register(redirector.close)

def prnt(*text):
	text = ' '.join(map(lambda x:str(x), text))
	with threadLock:
		redirector.write(text + '\n')
