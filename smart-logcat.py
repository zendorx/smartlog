import subprocess
import os


os.system("@echo off | chcp 1250 | @echo on")#Turn on console colors on Windows

cmd = "adb logcat"
const_wait = "- waiting for device -"
const_ignore = "ignore:"


buffer = []
buffer_filtered = []
words = []
ignore = []

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	SYSTEM = '\033[46m'
	UNDERLINE = '\033[4m'

def getSystemColor():
	return bcolors.SYSTEM

def getColor(v):
	if v == "g":
		return bcolors.OKGREEN
	if v == "e":
		return bcolors.HEADER
	if v == "w":
		return bcolors.WARNING
	if v == "i":
		return bcolors.BOLD
	if v == "c":
		return bcolors.FAIL

	return ""

def important(color, line):
	global buffer_filtered
	index = len(buffer) - 1
	line = "[%d]" % index + line
	buffer_filtered.append(line)
	print getColor(color), line, bcolors.ENDC

#read config
conf = []
conf.append("g;Firebase;")
conf.append("w;SDL;ASsert")
conf.append("e;SDL;Error")
conf.append("e;NOTNULL")
conf.append("c;Anr")
conf.append("    ")
conf.append("i;SDL;token")
conf.append("ignore:smd Interface open failed errno")
conf.append("ignore:Diag_LSM_Init: Failed to open handle to diag driver")
conf.append("ignore:BatteryMeterView")
conf.append("ignore:VoIPInterfaceManager")
conf.append("ignore:Recents_TaskView")
conf.append("ignore:ConnectivityService")
conf.append("ignore:DisplayPowerController")
conf.append("ignore:TimaService")
conf.append("ignore:SurfaceFlinger")
conf.append("ignore:NetworkStats")
conf.append("ignore:NetworkController")
conf.append("ignore:InputManager")
conf.append("ignore:DataRouter")
conf.append("ignore:BatteryService")
conf.append("ignore:STATUSBAR-WifiQuickSettingButton")



#add from args



for c in conf:
	cl = c.strip(' \t\n\r');
	if len(cl) == 0:
		continue

	if cl.startswith(const_ignore):
		ignore.append(cl[len(const_ignore):].lower())
		continue

	data = c.lower().split(";")

	if len(data) == 0:
		print "Wrong params in " + c
		exit()

	color = data[0]
	req = data[1].split(",")
	add = None
	if len(data) > 2:
		add = data[2].split(",")
	words.append( (color, req, add) )

def checkLine(line):
	l = line.lower()

	for ig in ignore:
		if ig in l:
			return

	index = len( buffer )
	line_c = "[%d]" % index + line
	buffer.append(line_c)

	if const_wait in line:
		print getSystemColor(), line, bcolors.ENDC

	for w in words:
		found = True
		for req in w[1]:
			if not req in l:
				found = False
				break

		if not found:
			continue

		found = False
		if w[2]:
			for add in w[2]:
				if add.lower() in l:
					found = True
					break
		else:
			found = True

		if found:
			important(w[0], line)
			break

running = True

def makeCoroutine():
	process = subprocess.Popen( cmd, stdout=subprocess.PIPE )
	return iter(lambda: process.stdout.read(1), '')

cor_read = makeCoroutine()
line = ""

try:
	while running:
		try:
			c = cor_read.next()
		except StopIteration:
			checkLine(line)
			line = ""
			cor_read = makeCoroutine()
			continue

		if (c == '\n'):
			checkLine(line.strip())
			line = ""
		else:
			line += c
except KeyboardInterrupt:
	pass

dt = "1.1.2017"

with open( '%s.txt' % dt, 'w' ) as f:
	for line in buffer:
		f.write( "%s\n" % line )

with open( '%s_filtered.txt' % dt, 'w' ) as f:
		for line in buffer_filtered:
			f.write( "%s\n" % line )

os.system("adb logcat -c")

print "Done!"