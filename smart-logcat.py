# coding=utf-8

import os
import subprocess
from Queue import Queue, Empty
from threading import Thread

from asciimatics.exceptions import ResizeScreenError
from asciimatics.screen import Screen

os.system("@echo off | chcp 1250 | @echo on")  # Turn on console colors on Windows

cmd = "adb logcat"
# cmd = "netstat -a"
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


# read config
conf = []
# conf.append("g;Firebase;")
# conf.append("w;SDL;ASsert")
# conf.append("e;SDL;Error")
# conf.append("e;NOTNULL")
# conf.append("c;Anr")
# conf.append("    ")
# conf.append("i;SDL;token")
# conf.append("ignore:smd Interface open failed errno")
# conf.append("ignore:Diag_LSM_Init: Failed to open handle to diag driver")
# conf.append("ignore:BatteryMeterView")
# conf.append("ignore:VoIPInterfaceManager")
# conf.append("ignore:Recents_TaskView")
# conf.append("ignore:ConnectivityService")
# conf.append("ignore:DisplayPowerController")
# conf.append("ignore:TimaService")
# conf.append("ignore:SurfaceFlinger")
# conf.append("ignore:NetworkStats")
# conf.append("ignore:NetworkController")
# conf.append("ignore:InputManager")
# conf.append("ignore:DataRouter")
# conf.append("ignore:BatteryService")
# conf.append("ignore:STATUSBAR-WifiQuickSettingButton")
# conf.append("ignore:STATUSBAR-QSTileView")
# conf.append("ignore:PowerManagerService")



# add from args



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
    words.append((color, req, add))


def checkLine(line):
    l = line.lower()

    for ig in ignore:
        if ig in l:
            return

    index = len(buffer)
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

line = ""
user_command = ""
last_user_command = ""
indent = 0  # from bot
user_filter = ""
show_info = True
view_line = None


def toggle_info_command():
    global show_info
    show_info = not show_info


def adb_clean_command():
    os.system("adb logcat -c")
    buffer[:] = []


def filterBuffer():
    global buffer_filtered
    buffer_filtered[:] = []
    for line in buffer:
        # first check

        if len(user_filter):
            if user_filter.lower() in line.lower():
                buffer_filtered.append(line)
        else:
            buffer_filtered.append(line)


def printBuffer(screen):
    #TODO: optimize output
    global user_command
    wh, ww = screen.dimensions
    filterBuffer()

    max_count = wh - 2
    start_from = view_line if view_line else len(buffer_filtered)
    start = max(start_from - indent - max_count, 0)
    printy = 1
    for line in buffer_filtered[start: start + max_count]:
        value = ("{0:%d}" % (ww-1)).format(line)
        screen.paint(value, 0, printy)
        printy += 1

    for j in xrange(printy, max_count + 1):
        screen.print_at(("{0:%d}" % (ww)).format(" "), 0, j)


def handleCommand(command):
    global user_filter
    if command == ":q":
        raise KeyboardInterrupt()
    elif command == ":clean" or command == ":c":
        adb_clean_command()

    elif command == ":info" or command == ":i":
        toggle_info_command()
    else:
        return "Unknown command: %s" % command

    return command


def move(steps):
    global indent
    global view_line
    lb = len(buffer_filtered)

    if not indent and steps:
        view_line = lb

    indent += steps
    indent = max(lb, indent)
    indent = min(indent, lb - 1)

    if not indent:
        view_line = None


def handleUserInput(c):
    global user_command
    global last_user_command
    global user_filter
    global view_line
    global indent
    if c:
        if c == Screen.KEY_ESCAPE:
            if view_line:
                view_line = None
                indent = 0
            else:
                user_command = ""
                user_filter = ""
        elif c == Screen.KEY_BACK:
            user_command = user_command[0:len(user_command) - 1]
            if len(user_command) == 0 and len(user_filter) != 0:
                user_filter = ""
        elif c == Screen.KEY_UP:
            move(1)
        elif c == Screen.KEY_DOWN:
            move(-1)
        elif c == Screen.KEY_PAGE_UP:
            move(25)
        elif c == Screen.KEY_PAGE_DOWN:
            move(-25)

        elif c == 13:
            last_user_command = handleCommand(user_command)
            user_command = ""
        elif c in xrange(32, 126):
            user_command += str(chr(c))

    if user_command.startswith("/"):
        user_filter = user_command[1:]


def printInfo(screen):
    if show_info:
        wh, ww = screen.dimensions
        value = "[%d:%d]     " % (len(buffer_filtered), len(buffer))
        if view_line:
            value += "indent: %d     " % indent
        if len(user_filter):
            value += "filter: %s   " % user_filter
        value = ("{0:%d}" % (ww, )).format(value)
        screen.paint(value, 0, 0)


def printUserCommand(screen):
    wh, ww = screen.dimensions
    mwc = ww - ww / 3
    value = ("{0:%d}" % (mwc,)).format(user_command)
    value2 = ("{:>%d}" % (ww - mwc,)).format(last_user_command)
    screen.print_at(value, 0, wh - 1)
    screen.print_at(value2, mwc, wh - 1)


def readOutput(q):
    try:
        while 1:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            for line in iter(p.stdout.readline, b''):
                q.put(line.strip())
    except KeyboardInterrupt:
        exit()


queue = Queue()
readThread = Thread(target=readOutput, args=(queue,))
readThread.daemon = True
readThread.start()


def update(screen):
    global user_command

    while True:

        # screen.print_at('Hello world!',
        #                 randint(0, screen.width), randint(0, screen.height),
        #                 colour=randint(0, screen.colours - 1),
        #                 bg=randint(0, screen.colours - 1))
        line = ""
        try:
            while 1:
                line = queue.get_nowait()  # or q.get(timeout=.1)
                buffer.append(line)

        except Empty:
            pass

        printInfo(screen)

        handleUserInput(screen.get_key())

        printBuffer(screen)

        printUserCommand(screen)

        screen.refresh()

        if screen.has_resized():
            raise ResizeScreenError("Screen resized")


while True:
    try:
        Screen.wrapper(update)
    except ResizeScreenError:
        continue
    except KeyboardInterrupt:
        break
        pass

dt = "1.1.2017"

with open('%s.txt' % dt, 'w') as f:
    for line in buffer:
        f.write("%s\n" % line)

print "Done!"
