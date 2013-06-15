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

def FormatDuration(ms):
	if ms < 1000:
		return "%d ms"%ms
	elif ms < 60000:
		return "%02ds"%(ms / 1000)
	elif ms < 3600000:
		return "%02dm %02ds"%(ms / 60000, (ms%60000) / 1000)
	else:
		return "%dh %02dm %02ds"%((ms / 3600000), (ms%3600000) / 60000, (ms%60000) / 1000)
