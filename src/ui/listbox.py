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

import wx
from wx.lib.mixins.listctrl import ColumnSorterMixin

from logging import prnt

class ListBox(wx.ListCtrl, ColumnSorterMixin):
	def __init__(self, parent, columns, columnWidths,
			style=wx.NO_BORDER):
		wx.ListCtrl.__init__(self, parent, style=style | wx.LC_REPORT |
			wx.LC_VIRTUAL)

		# Init ColumnSorterMixin
		self.itemDataMap = []
		self.GetListCtrl = lambda: self
		ColumnSorterMixin.__init__(self, len(columns))

		# Setup our variables
		self.rows = []
		self.rowIndexMap = {}
		self.SetItemCount(0)

		# Setup our columns
		if len(columns) != len(columnWidths):
			raise Exception("columnWidths must be the same size as columns!")
		for index in xrange(0, len(columns)):
			name = columns[index]
			width = columnWidths[index]
			self.InsertColumn(index, name)
			self.SetColumnWidth(index, width)

	def setRows(self, rows, itemMap=None):
		if not itemMap:
			itemMap = rows
		
		self.rows = rows
		self.itemDataMap = itemMap
		self.rowIndexMap = range(0, len(itemMap))
		self.SetItemCount(len(rows))

		self.SortListItems()

	def OnGetItemText(self, row, col):
		return self.rows[self.rowIndexMap[row]][col]

	def SortItems(self, sorter=cmp):
		items = list(self.rowIndexMap)
		items.sort(sorter)
		self.rowIndexMap = items
		self.Refresh()
