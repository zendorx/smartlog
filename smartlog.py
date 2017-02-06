# coding=utf-8

import argparse
import os
import subprocess
from Queue import Queue, Empty
from threading import Thread
import time
from asciimatics.exceptions import ResizeScreenError
from asciimatics.screen import Screen
import getpass
from logging import getLogger
L = getLogger(__name__)

os.system("@echo off | chcp 1250 | @echo on")  # Turn on console colors on Windows

# cmd = "netstat -a"
const_wait = "- waiting for device -"
const_ignore = "ignore:"
version = "0.3"
app_name = "SmartLog"
buffer = []  # original buffer
buffer_compiled = []  # Cashed highlighted buffer with tags and lower cased lines,  (index, tag, text)
highlights = []  # Rules for highlight (tag, [req], [nreq])
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
default_file_name = "{t} {uid}.log"
last_saved_fname = ""
show_help = False
adb_path = "adb.exe"
interrupt_command = "__interrupt_command__"
execute_cmd = "adb logcat"
clean_cmd = "adb logcat -c"

process_id = ""
process_lookup = ""
process_lookup_enabled = False

# logging.basicConfig(filename="log.log", filemode="w", level=logging.DEBUG)

need_reprint_buffer = True





## Args

parser = argparse.ArgumentParser(prog=app_name,#todo: move to description
                                 usage="\n  1)Install android SDK\n  "
                                       "2)Add '{$SDK}\platform-tools\\adb.exe' to the PATH or setup -adb <path>\n  "
                                       "3)Run program\n  "
                                       "4)Type :h for more help \n\n"
                                       "Or specify your own commands by passing -execute and -clean params\n"
                                       "e.g  smartlog -execute \"netstat -a\" -clean \"\"",
                                 description="Program prints stream output and provides bunch of useful features like filter, highlight. Type :h in program for more help.")
parser.add_argument("-ec", default=exit_commands,
                    help="commands that will executed on exit splited by ';' e.g:  \"w;q\" will write file and open explorer. To see more commands type :h")
parser.add_argument("-cf", default=conf_file, help="specifies config file name. By default is '%s'" % (conf_file,))
parser.add_argument("-cd", default=current_dir, help="specifies directory where log files will be saved")
parser.add_argument("-cs", default=False, action='store_const', const=True,
                    help="execute clean command on startup. By default %s" % clean_cmd)
parser.add_argument("-pc", default=process_lookup, help="specifies process lookup string")
parser.add_argument("--init", default=False, action='store_const', const=True,
                    help="creates default config file in app folder")
parser.add_argument('--version', "-v", action='version', version="%s %s" % (app_name, version))
parser.add_argument('-execute', default=execute_cmd,
                    help="specifies execute command that will output log stream. By default is %s" % execute_cmd)
parser.add_argument('-clean', default=clean_cmd, help="specifies clean command e.g. \"adb logcat -c\". Can be \"\"")
_args = parser.parse_args()

exit_commands = _args.ec
conf_file = _args.cf
exec_cmd = _args.execute
clean_cmd = _args.clean
set_current_dir(_args.cd)
process_lookup = _args.pc

if len(process_lookup) > 0:
    process_lookup_enabled = True
    print "PC: '%s'" % process_lookup

help_string = """
Available commands:

:q                          Quit.
:o                          Open current folder.
:w  [file name]              Write current log to file.
:wf [file name]             Write filtered log into file.code
:wq [file name]             Write log into file and quit.
:wl                         Write log to the last saved file.
:wc [file name]             Write all changes to config file
:cc <file name>             Change current config file
:rc [file name]             Read current config file
:i <Any string>             Add ignore string to filter buffer.
:c                          Clean device log and current buffer.
:cd [directory]             Change or show directory where log files will be saved.
:pc [string]                Turn on/off process lookup.
/[text]                     Apply fast buffer filtering, press Enter to save filter.
                                press ESC to clean filter

UP,DOWN,PAGE_DOWN,PAGE_UP   Navigation, press ESC to return normal mode



contacts:   %s
source:     %s


press ESC to close help
""" % (contacts_info, source_info)

weights = { "e": 10, "w": 9, "d": 7, "l": 100, "n": 1 }

line_tags = {  # Line tags
    "e": Screen.COLOUR_RED,  # Error
    "w": Screen.COLOUR_YELLOW,  # Warning
    "d": Screen.COLOUR_MAGENTA,  # Debug
    "l": Screen.COLOUR_GREEN,  # Lookup
    "n": Screen.COLOUR_WHITE,  # Normal
}

conf = []


def get_line_process(text):
    s = text.find("(")
    e = text.find(")")
    return text[s + 1:e].strip()

def find_process_id():
    if not process_lookup:
        return ""

    for b in buffer:
        if process_lookup in b:
            return get_line_process(b)
    else:
        return ""

def check_process_lookup_line(line):
    global process_id
    global need_reprint_buffer

    if not process_lookup_enabled:
        return

    if process_id != "":
        return

    if process_lookup == "":
        return

    if process_lookup.lower() in line.lower():
        process_id = get_line_process(line)
        filter_buffer()
        need_reprint_buffer = True



def save_command(fname, bf):
    global last_saved_fname

    uid = getpass.getuser()
    t = time.strftime("%m.%d (%H-%M)")
    if fname == "" or fname is None:
        name = default_file_name.replace("{uid}", uid)
        name = name.replace("{t}", t)
        fname = current_dir + name

    last_saved_fname = fname
    with open(fname, 'w') as f:
        for line in bf:
            print line
            f.write("%s\n" % str(line))


last_filtered_value = ""


def filter_buffer():
    L.info("filter_buffer")
    global last_filtered_value
    global buffer_filtered
    buffer_filtered[:] = []

    if user_filter == "" and not process_lookup_enabled:
        return

    for line in buffer_compiled:
        if not is_line_filtered(line[2]):
            buffer_filtered.append(line)

    last_filtered_value = user_filter


def is_line_filtered(line):
    if len(user_filter):
        words = user_filter.lower().split(" ")
        for word in words:
            if not word in line.lower():
                return True     # Trash line

    if process_lookup_enabled and process_id != "":
        lpid = get_line_process(line)
        if process_id != lpid:
            return True

    return False


def try_add_to_buffer(l):
    if is_ignored(l):
        return

    global buffer
    global buffer_filtered
    global buffer_compiled
    global need_reprint_buffer

    need_reprint_buffer = True

    buffer.append(l)
    comp = precompile_line(l, len(buffer) - 1)
    buffer_compiled.append(comp)
    if user_filter != "" and not is_line_filtered(comp[2]):
        buffer_filtered.append(comp)

    check_process_lookup_line(comp[2])


def process_lookup_command(value):
    global process_lookup_enabled
    global process_lookup
    global process_id
    global need_reprint_buffer
    result = value
    if value == "":
        process_lookup_enabled = not process_lookup_enabled
        if process_lookup_enabled:
            result = "pc: ON"
        else:
            result = "pc: OFF"
    else:
        process_lookup_enabled = True
        process_lookup = value
        process_id = find_process_id()


    filter_buffer()
    need_reprint_buffer = True
    return result


def check_ignores():
    global buffer
    buffer = [l for l in buffer if not is_ignored(l)]
    precompile_buffer()


def add_highlight_rule(l):
    global highlights
    tag = l[0]
    right = l[2:].split(";")
    req = [x.strip().lower() for x in right[0].split(",") if len(x.strip())]
    nreq = []
    if len(right) > 1:
        nreq = [x.strip().lower() for x in right[1].split(",") if len(x.strip())]

    result = (tag, req, nreq)
    current = 0
    for h in highlights:
        if weights[tag] >= weights[h[0]]:
            highlights.insert(current, result)
            return
        current += 1
    else:
        highlights.append(result)



def precompile_line(line, index):
    tag = "n"
    ll = line.lower()
    for h in highlights:
        for r in h[1]:
            if not r in ll:
                break
        else:
            if len(h[2]) == 0:
                tag = h[0]
            else:
                for nr in h[2]:
                    if nr in ll:
                        tag = h[0]
                        break

        if tag != "n":
            break

    return (index, tag, line)


def precompile_buffer():
    global need_reprint_buffer
    L.info("precompile_buffer")
    global buffer_compiled
    buffer_compiled[:] = []
    index = 0
    for l in buffer:
        buffer_compiled.append(precompile_line(l, index))
        index += 1
    need_reprint_buffer = True


def read_file_command(fname, bf):
    L.info("read_file_command")
    with open(fname, "r") as f:
        for line in f:
            bf.append(line)


def add_ignore_command(value):
    L.info("add_ignore_command")
    ignore.append(value.lower().strip())


def read_conf_command():
    if not os.path.isfile(conf_file):
        return
    L.info("read_conf_command")

    global ignore
    global conf

    conf[:] = []
    read_file_command(conf_file, conf)
    for l in conf:
        if l.startswith("#"):
            continue
        if l.strip() == "":
            continue
        if l.startswith("ignore:"):
            add_ignore_command(l[7:])
            continue
        add_highlight_rule(l)
    precompile_buffer()


def save_conf(fname):
    L.info("save_conf")
    save_command(fname, conf)


def init_command():
    L.info("init_command")
    conf.append("#Syntax:   <TAG>;[RequiredWord1],[RequiredWord2]...;[NotRequiredWord1]..")
    conf.append("#Tags:")
    conf.append("#  'e' - Error, red color")
    conf.append("#  'w' - Warning, yellow color")
    conf.append("#  'd' - Debug, magenta color")
    conf.append("#  'l' - Lookup, green color, don't use this color in config. ")
    conf.append("#        Type command in program :l MyAppName;Password "
                "for highlight password lines(or something else) in you program")
    conf.append("")
    conf.append("# Few examples: ")
    conf.append("e;MyApp;Error,Crash")
    conf.append("w;MyApp;Warning,not found,")
    conf.append("d;;Debug,")
    conf.append("d;Anr(")
    conf.append("")
    conf.append("")
    conf.append("#Ingore next items(Also you can type :i <str> command while program run: ")
    conf.append("#ignore will completely remove lines from output")
    conf.append("ignore:smd Interface open failed errno")
    conf.append("ignore:Diag_LSM_Init: Failed to open handle to diag driver")
    conf.append("ignore:BatteryMeterView")
    conf.append("ignore:VoIPInterfaceManager")
    conf.append("ignore:Recents_TaskView")
    conf.append("ignore:ConnectivityService")
    conf.append("ignore:DisplayPowerController")
    conf.append("ignore:TimeService")
    conf.append("ignore:SurfaceFlinger")
    conf.append("ignore:NetworkStats")
    conf.append("ignore:NetworkController")
    conf.append("ignore:InputManager")
    conf.append("ignore:DataRouter")
    conf.append("ignore:BatteryService")
    conf.append("ignore:STATUSBAR-WifiQuickSettingButton")
    conf.append("ignore:STATUSBAR-QSTileView")
    conf.append("ignore:PowerManagerService")
    save_conf(conf_file)
    print "Config saved: %s" % conf_file
    exit()


def open_last_log_dir():
    L.info("open_last_log_dir")
    os.system("start .")


def is_ignored(l):
    for ig in ignore:
        if ig in l.lower():
            return True
    return False


def clean_command():
    global need_reprint_buffer
    global process_id
    L.info("clean_command")
    os.system(clean_cmd)
    buffer[:] = []
    buffer_compiled[:] = []
    buffer_filtered[:] = []
    need_reprint_buffer = True
    process_id = ""
    filter_buffer()


def help_command():
    L.info("help_command")
    global show_help
    show_help = True


def clean_up(screen, from_line):
    wh, ww = screen.dimensions
    for j in xrange(from_line, ww - 1):
        screen.paint(("{0:%d}" % (ww)).format(" "), 0, j)


def print_help(screen):
    clean_up(screen, 1)
    help = help_string.split("\n")
    posy = 0
    for l in help:
        screen.paint(l, 0, posy)
        posy += 1


def print_buffer(screen):
    global need_reprint_buffer
    global last_filtered_value

    if not need_reprint_buffer:
        return

    if user_filter == "" and not process_lookup_enabled:
        last_filtered_value = ""
        bf = buffer_compiled
    else:
        if user_filter != last_filtered_value and not process_lookup_enabled:
            filter_buffer()
        bf = buffer_filtered

    global user_command
    wh, ww = screen.dimensions
    max_count = wh - 2
    start_from = view_line if view_line else len(bf)
    start = max(start_from - indent - max_count, 0)
    printy = 1
    pbf = bf[start:start + max_count]

    for line in pbf:
        value = ("[%d]{0:%d}" % (line[0], ww)).format(line[2])
        try:
            screen.paint(unicode(value, "utf-8"), 0, printy, colour=line_tags[line[1]])
        except UnicodeDecodeError:
            print "error ascii at line ", line
            exit(1)

        printy += 1

    clean_up(screen, printy)
    need_reprint_buffer = False


def handle_command(command):
    L.info("handle_command")
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
    elif command.startswith(":pc"):
        value = command[3:].strip()
        return process_lookup_command(value)
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
        check_ignores()
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
    return
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


def set_filter(words):
    global user_filter
    global need_reprint_buffer
    user_filter = words
    filter_buffer()
    need_reprint_buffer = True


def handle_user_input(c):
    if not c:
        return
    L.info("handle_user_input")

    global user_command
    global last_user_command
    global view_line
    global indent
    global show_help
    global need_reprint_buffer

    ask = "Press ESC again to exit"

    if c == Screen.KEY_ESCAPE:
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
            set_filter("")
        need_reprint_buffer = True
    elif c == Screen.KEY_BACK:
        user_command = user_command[0:len(user_command) - 1]
        if len(user_command) == 0 and len(user_filter) != 0:
            set_filter("")
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

    if c != Screen.KEY_ESCAPE and last_user_command == ask:
        last_user_command = ""

    if user_command.startswith("/"):
        set_filter(user_command[1:])


def print_info(screen):
    if show_info:
        wh, ww = screen.dimensions

        count = len(buffer)
        if user_filter != "":
            count = len(buffer_filtered)
        value = "[%d:%d]     " % (count, len(buffer))
        if view_line:
            value += "indent: %d     " % indent
        if len(user_filter):
            value += "filter: %s   " % user_filter

        if process_lookup_enabled:
            if process_id != "":
                value += "pid: " + process_id
            else:
                value += "pid: None"

        value = ("{0:%d}" % (ww,)).format(value)
        screen.paint(value, 0, 0, colour=Screen.COLOUR_YELLOW)


def print_user_command(screen):
    wh, ww = screen.dimensions
    value = ("{0:%d}" % (ww / 2)).format(user_command)
    value2 = ("{:>%d}" % (ww / 2)).format(last_user_command)
    screen.paint(value2, ww / 2, wh - 1, colour=Screen.COLOUR_YELLOW)
    screen.paint(value, 0, wh - 1, colour=Screen.COLOUR_WHITE)


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
        q.put(interrupt_command)


queue = Queue()
readThread = Thread(target=read_output, args=(queue,))


def update(screen):
    global user_command

    while True:
        try:
            while 1:
                line = queue.get_nowait()  # or q.get(timeout=.1)
                if interrupt_command == line:
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

read_conf_command()

if _args.cs:
    clean_command()

readThread.daemon = True
readThread.start()

while True:
    try:
        need_reprint_buffer = True
        Screen.wrapper(update)
    except ResizeScreenError:
        continue
    except KeyboardInterrupt:
        break
        pass

cmds = exit_commands.split(";")
for c in cmds:
    handle_command(":%s" % c)

# save_command("highlights.txt", highlights)
# save_command("filtered.txt", buffer_filtered)
# save_command("compiled.txt", buffer_compiled)

print "Done!"
