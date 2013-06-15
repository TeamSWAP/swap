import os,time
import ctypes
import re
from ctypes.wintypes import MAX_PATH
#[18:36:21.225] [Cartel Patrol Droid {2981965728841728}:3535188148330] [@Bellestarr] [Explosive Round {827176341471232}] [ApplyEffect {836045448945477}: Damage {836045448945501}] (1216 kinetic {836045448940873}) <1216>

class parser:
	"""docstring for parser"""
	logLocation = ""
	linepat = None
	def __init__(self):
		self.linepat = re.compile("^\[(?P<hour>\d{1,2})\:(?P<minute>\d{2})\:(?P<second>\d{2})\.(?P<ms>\d{3})\] \[(?P<actor>[^\[\]]*)\] \[(?P<target>[^\[\]]*)\] \[(?:(?P<ability>[^{}]+))?(?: {(?P<abilityid>\d*)})?\] \[(?P<action>[^{}]+) {(?P<actionid>\d*)}: (?P<actiontype>[^{}]+) {(?P<actiontypeid>\d*)}\] \((?:(?P<result>[^\<\>]+))?\)(?: \<(?P<threat>\d*)\>)?$")
		pass
	def getDocs(self):
	 	dll = ctypes.windll.shell32
		buf = ctypes.create_unicode_buffer(MAX_PATH + 1)
		if dll.SHGetSpecialFolderPathW(None, buf, 0x0005, False):
		    self.logLocation = buf.value+"\\Star Wars - The Old Republic\\CombatLogs"
		else:
		    return None
	def getNewestLog():
		pass


parse = parser()
parse.getDocs()
#print len(os.listdir(parse.logLocation))
logs = [parse.logLocation + "\\" + f for f in os.listdir(parse.logLocation)]
#newlog = max(logs, key=os.path.getmtime)
newlog = max(os.listdir(parse.logLocation))
log = open(parse.logLocation + "\\" +newlog,'r')
while 1:
	line = log.readline()
	if line == "":
		continue
	else:
		#os.system('cls')
		res = parse.linepat.match(line)	
		if res:
			print "\n"
			print res.groups(0)
	#time.sleep(.01)
log.close()