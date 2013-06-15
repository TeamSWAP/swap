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

def FormatDuration(s):
	if s < 1:
		return "%.1fs"%s
	elif s < 60:
		return "%02ds"%s
	elif s < 3600:
		return "%02dm %02ds"%(s / 60, s%60)
	else:
		return "%dh %02dm %02ds"%((s / 3600), (s%3600) / 60, s%60)
