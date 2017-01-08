# coding=utf-8

import argparse
import os
import subprocess
from Queue import Queue, Empty
from threading import Thread

from asciimatics.exceptions import ResizeScreenError
from asciimatics.screen import Screen

os.system("@echo off | chcp 1250 | @echo on")  # Turn on console colors on Windows

# cmd = "netstat -a"
const_wait = "- waiting for device -"
const_ignore = "ignore:"
version = "0.3"
app_name = "Smart Logcat"
buffer = []
buffer_filtered = []
words = []
ignore = []
exit_commands = ""
conf_file = "default.cfg"
current_dir = ""
source_info = "https://github.com/zendorx/smart-logcat"
contacts_info = "zendorx@gmail.com"

line = ""
user_command = ""
last_user_command = ""
indent = 0  # from bot
user_filter = ""
show_info = True
view_line = None
last_saved_fname = ""
show_help = False
adb_path = "adb.exe"
interupt_command = "__interupt_command__"
execute_cmd = "adb logcat"
clean_cmd = "adb logcat -c"

def set_current_dir(value):
    global current_dir
    current_dir = value
    if current_dir == ".":
        current_dir = ""
    if current_dir != "" and not (current_dir.endswith("\\") or current_dir.endswith("/")):
        current_dir += "/"
    return current_dir


## Args

parser = argparse.ArgumentParser(prog=app_name,
                                 usage="\n  1)Install android SDK\n  "
                                       "2)Add '{$SDK}\platform-tools\\adb.exe' to PATH or setup -adb <path>\n  "
                                       "3)Run programm\n  "
                                       "4)Type :h for more help \n\n"
                                       "Or specify your own commands by passing -execute and -clean params\n"
                                       "e.g  smartlog -execute \"netstat -a\" -clean \"\"",
                                 description="Program prints stream output and provides bunch of useful features like filter, highlight. Type :h in program for more help.")
parser.add_argument("-ec", default=exit_commands,
                    help="Commands that will executed on exit splited by ';' e.g:  'w;q' will write file and open explorer. To see more commands type :h")
parser.add_argument("-cf", default=conf_file, help="Specifies config file name. By default is '%s'" % (conf_file,))
parser.add_argument("-cd", default=current_dir, help="Specifies directory where log files will be saved")
parser.add_argument("-cs", default=False, action='store_const', const=True, help="Execute clean command on startup. By default %s" % clean_cmd)
parser.add_argument("--init", default=False, action='store_const', const=True,
                    help="Creates default config file in app folder")
parser.add_argument('--version', "-v", action='version', version="%s %s" % (app_name, version))
parser.add_argument('-execute', default=execute_cmd, help="Specifies execute command that will output log stream. By default is %s" % execute_cmd)
parser.add_argument('-clean', default=clean_cmd, help="Specifies clean command e.g. 'adb logcat -c'. Can be \"\"")
_args = parser.parse_args()

exit_commands = _args.ec
conf_file = _args.cf
exec_cmd = _args.execute_cmd
clean_cmd = _args.clean
set_current_dir(_args.cd)

# def cmd_exists(cmd):
#     return subprocess.call("type " + cmd, shell=True,
#         stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0
#
# if cmd_exists(adb_path):
#     print "Error: adb.exe not found. Current path: %s" % adb_path


help_string = """
Available commands:

:q                          Quit.
:o                          Open current folder.
:w [file name]              Write current log to file.
:wf [file name]             Write filtered log into file.
:wq [file name]             Write log into file and quit.
:wl                         Write log to the last saved file.
:i <Any string>             Add ignore string to filter buffer.
:c                          Clean device log and current buffer.
:cd [directory]             Change or show directory where log files will be saved.
/[text]                     Apply fast buffer filtering, press Enter to save filter.
                                press ESC to clean filter

UP,DOWN,PAGE_DOWN,PAGE_UP   Navigation, press ESC to return normal mode



contacts:   %s
source:     %s


press ESC to close help
""" % (contacts_info, source_info)

##
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


# def checkLine(line):
#     l = line.lower()
#
#     for ig in ignore:
#         if ig in l:
#             return
#
#     index = len(buffer)
#     line_c = "[%d]" % index + line
#     buffer.append(line_c)
#
#     if const_wait in line:
#         print getSystemColor(), line, bcolors.ENDC
#
#     for w in words:
#         found = True
#         for req in w[1]:
#             if not req in l:
#                 found = False
#                 break
#
#         if not found:
#             continue
#
#         found = False
#         if w[2]:
#             for add in w[2]:
#                 if add.lower() in l:
#                     found = True
#                     break
#         else:
#             found = True
#
#         if found:
#             important(w[0], line)
#             break

def init_command():
    pass


def open_last_log_dir():
    os.system("start .")


def is_ignored(l):
    for ig in ignore:
        if ig in l.lower():
            return True
    return False


def try_add_to_buffer(l):
    global buffer
    if not is_ignored(l):
        buffer.append(l)


def update_buffer():
    global buffer
    buffer = [l for l in buffer if not is_ignored(l)]


def add_ignore_command(value):
    ignore.append(value.lower().strip())
    update_buffer()


def save_command(fname, bf):
    global last_saved_fname
    dt = "1.1.2017"
    if fname == "" or fname is None:
        fname = "%s%s.log" % (current_dir, dt)

    last_saved_fname = fname
    with open(fname, 'w') as f:
        for line in bf:
            f.write("%s\n" % line)


def clean_command():
    os.system(clean_cmd)
    buffer[:] = []


def filter_buffer():
    global buffer_filtered
    buffer_filtered[:] = []
    for line in buffer:
        # first check

        if len(user_filter):
            flist = user_filter.split(" ")
            con_all = True
            for fpart in flist:
                if not fpart.lower() in line.lower():
                    con_all = False
                    break
            if con_all:
                buffer_filtered.append(line)
        else:
            buffer_filtered.append(line)


def help_command():
    global show_help
    show_help = True


def cleen_up(screen, from_line):
    wh, ww = screen.dimensions
    for j in xrange(from_line, ww - 1):
        screen.print_at(("{0:%d}" % (ww)).format(" "), 0, j)


def print_help(screen):
    cleen_up(screen, 1)
    help = help_string.split("\n")
    posy = 0
    for l in help:
        screen.print_at(l, 0, posy)
        posy += 1


def print_buffer(screen):
    # TODO: optimize output
    global user_command
    wh, ww = screen.dimensions
    filter_buffer()

    max_count = wh - 2
    start_from = view_line if view_line else len(buffer_filtered)
    start = max(start_from - indent - max_count, 0)
    printy = 1
    for line in buffer_filtered[start: start + max_count]:
        value = ("{0:%d}" % (ww)).format(line)
        screen.paint(value, 0, printy)
        printy += 1

    cleen_up(screen, printy)


def handle_command(command):
    global user_filter

    if command.startswith("/"):
        return last_user_command

    if not command.startswith(":"):
        return "'%s' is not command. Type :h for help." % command

    if command == ":q":
        raise KeyboardInterrupt()
    elif command == ":h":
        help_command()
    elif command == ":o":
        open_last_log_dir()
    elif command.startswith(":cd"):
        value = command[3:].strip()
        if value == "":
            if current_dir == "":
                return os.getcwd()
            else:
                return current_dir
        else:
            return "New dir: " + set_current_dir(value)
    elif command.startswith(":wf"):
        pass
        fname = command[3:].strip()
        save_command(fname, buffer_filtered)
        return "Saved: " + last_saved_fname
    elif command.startswith(":wq"):
        command = command[:2] + command[3:]
        handle_command(command)
        raise KeyboardInterrupt()
    elif command.startswith(":i"):
        value = command[2:].strip()
        add_ignore_command(value)
        return "Ignored: '%s'" % value
    elif command.startswith(":wl"):
        save_command(last_saved_fname, buffer)
        return "Saved: " + last_saved_fname
    elif command.startswith(":w"):
        fname = command[2:].strip()
        save_command(fname, buffer)
        return "Saved: " + last_saved_fname
    elif command == ":clean" or command == ":c":
        clean_command()
    else:
        return "Unknown command: %s. Type :h for help." % command

    return command


def move(steps):
    global indent
    global view_line

    lb = len(buffer_filtered)

    if not indent and steps:
        view_line = lb

    indent += steps
    indent = max(0, indent)
    indent = min(indent, lb - 1)

    if not indent:
        view_line = None


def handle_user_input(c):
    global user_command
    global last_user_command
    global user_filter
    global view_line
    global indent
    global show_help
    ask = "Press ESC again to exit"

    if c:
        if c == Screen.KEY_ESCAPE:
            # last_user_command = ""
            if show_help:
                show_help = False
            elif view_line is None and user_filter == "" and user_command == "":
                if ask == last_user_command:
                    raise KeyboardInterrupt()
                last_user_command = ask
            elif view_line:
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
            move(3)
        elif c == Screen.KEY_DOWN:
            move(-3)
        elif c == Screen.KEY_PAGE_UP:
            move(35)
        elif c == Screen.KEY_PAGE_DOWN:
            move(-35)
        elif c == 13:
            last_user_command = handle_command(user_command)
            user_command = ""
        elif c in xrange(32, 126):
            user_command += str(chr(c))

            # if c != Screen.KEY_ESCAPE and last_user_command == ask:
            #     last_user_command = ""

    if user_command.startswith("/"):
        user_filter = user_command[1:]


def print_info(screen):
    if show_info:
        wh, ww = screen.dimensions
        value = "[%d:%d]     " % (len(buffer_filtered), len(buffer))
        if view_line:
            value += "indent: %d     " % indent
        if len(user_filter):
            value += "filter: %s   " % user_filter
        value = ("{0:%d}" % (ww,)).format(value)
        screen.paint(value, 0, 0, colour=Screen.COLOUR_YELLOW)


def print_user_command(screen):
    wh, ww = screen.dimensions
    v2 = ww - ww / 5
    value = ("{0:%d}" % (ww)).format(user_command)
    value2 = ("{:>%d}" % (v2)).format(last_user_command)
    screen.print_at(value, 0, wh - 1, colour=Screen.COLOUR_WHITE)
    screen.print_at(value2, ww - v2, wh - 1, colour=Screen.COLOUR_YELLOW)


def read_output(q):
    try:
        while 1:
            p = subprocess.Popen(exec_cmd, stdout=subprocess.PIPE)
            for line in iter(p.stdout.readline, b''):
                q.put(line.strip())
    except KeyboardInterrupt:
        exit()
    except Exception:
        print "Failed to execute command: '%s'. Check adb.exe added to PATH" % exec_cmd
        q.put(interupt_command)


queue = Queue()
readThread = Thread(target=read_output, args=(queue,))
readThread.daemon = True
readThread.start()


def update(screen):
    global user_command

    while True:

        # screen.print_at('Hello world!',
        #                 randint(0, screen.width), randint(0, screen.height),
        #                 colour=randint(0, screen.colours - 1),
        #                 bg=randint(0, screen.colours - 1))
        try:
            while 1:
                line = queue.get_nowait()  # or q.get(timeout=.1)
                if interupt_command == line:
                    raise KeyboardInterrupt()
                try_add_to_buffer(line)

        except Empty:
            pass

        print_info(screen)

        handle_user_input(screen.get_key())

        if show_help:
            print_help(screen)
        else:
            print_buffer(screen)

        print_user_command(screen)

        screen.refresh()

        if screen.has_resized():
            raise ResizeScreenError("Screen resized")


# Before startup

if _args.init:
    init_command()
    exit()

if _args.c:
    clean_command()

while True:
    try:
        Screen.wrapper(update)
    except ResizeScreenError:
        continue
    except KeyboardInterrupt:
        break
        pass

cmds = exit_commands.split(";")
for c in cmds:
    handle_command(":%s" % c)

print "Done!"
