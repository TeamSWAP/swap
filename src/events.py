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

from logging import prnt

class EventSource(object):
    def __init__(self):
       self.observers = {}

    def registerObserver(self, event, observer):
       if not event in self.observers:
          self.observers[event] = []
       self.observers[event].append(observer)

    def unregisterObserver(self, event, observer):
       if event in self.observers and observer in self.observers[event]:
          del self.observers[event]

    def notifyEvent(self, event, *args, **kwargs):
       if event in self.observers:
          observers = self.observers[event]
          for observer in observers:
             observer(*args, **kwargs)
