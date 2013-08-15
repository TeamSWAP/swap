# Lint stub created by lintstub.py -- don't change!

# Constants
HIGHLIGHT_EVEN = None
HIGHLIGHT_ODD = None
SEL_FOC = None
locale = None
wx = None
wxEVT_DOPOPUPMENU = None

# Funcs
def EVT_DOPOPUPMENU(*x, **y): return None
def bisect(*x, **y): return None
def getListCtrlSelection(*x, **y): return None
def selectBeforePopup(*x, **y): return None

# Classes
class ListCtrlSelectionManagerMix(object):
   def OnLCSMDoPopup(*x, **y): return None
   def OnLCSMRightDown(*x, **y): return None
   def afterPopupMenu(*x, **y): return None
   def getPopupMenu(*x, **y): return None
   def getSelection(*x, **y): return None
   def setPopupMenu(*x, **y): return None


class ListRowHighlighter(object):
   def RefreshRows(*x, **y): return None
   def SetHighlightColor(*x, **y): return None
   def SetHighlightMode(*x, **y): return None


class ColumnSorterMixin(object):
   def GetColumnSorter(*x, **y): return None
   def GetColumnWidths(*x, **y): return None
   def GetSecondarySortValues(*x, **y): return None
   def GetSortImages(*x, **y): return None
   def GetSortState(*x, **y): return None
   def OnSortOrderChanged(*x, **y): return None
   def SetColumnCount(*x, **y): return None
   def SortListItems(*x, **y): return None
   def _ColumnSorterMixin__ColumnSorter(*x, **y): return None
   def _ColumnSorterMixin__OnColClick(*x, **y): return None
   def _ColumnSorterMixin__updateImages(*x, **y): return None


class ListCtrlAutoWidthMixin(object):
   def _doResize(*x, **y): return None
   def _onResize(*x, **y): return None
   def resizeColumn(*x, **y): return None
   def resizeLastColumn(*x, **y): return None
   def setResizeColumn(*x, **y): return None


class TextEditMixin(object):
   def CloseEditor(*x, **y): return None
   def OnChar(*x, **y): return None
   def OnItemSelected(*x, **y): return None
   def OnLeftDown(*x, **y): return None
   def OpenEditor(*x, **y): return None
   def _SelectIndex(*x, **y): return None
   def make_editor(*x, **y): return None


class CheckListCtrlMixin(object):
   def CheckItem(*x, **y): return None
   def IsChecked(*x, **y): return None
   def OnCheckItem(*x, **y): return None
   def ToggleItem(*x, **y): return None
   def _CheckListCtrlMixin__CreateBitmap(*x, **y): return None
   def _CheckListCtrlMixin__InsertStringItem_(*x, **y): return None
   def _CheckListCtrlMixin__OnLeftDown_(*x, **y): return None


