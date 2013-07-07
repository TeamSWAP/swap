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

import ext.fuzion as fuzion

from constants import *
from logging import prnt

node = None

def Init():
	global node

	fuzion.setDebug(lambda *x: prnt("Fuzion:", *x))
	node = fuzion.Node()
	node.setNodeServer(NODE_SERVER_ADDR)
