#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse

from gui import *

# INFO-------------------------
version = "0.5"
app_name = "SmartLog"
source_info = "https://github.com/zendorx/smart-logcat"
contacts_info = "zendorx@gmail.com"

# CONSTS-----------------------
# const_wait = "- waiting for device -"
# const_ignore = "ignore:"


# VARIABLES--------------------
default_file_name = "{t} {uid}.log"
conf_file = "default.cfg"
interrupt_command = "__interrupt_command__"

parser = argparse.ArgumentParser(prog=app_name,  # todo: move to description
                                 usage="""1)Install android SDK"
                                          2)Add '{$SDK}\platform-tools\\adb.exe' to the PATH or setup -adb <path>
                                          3)Run program
                                          """,
                                 description="Program prints stream output and provides bunch of useful features like filter, highlight.")
parser.add_argument("-cd", default="",
                    help="specifies directory where log files will be saved")

parser.add_argument("--command_execute", default="adb logcat", action='store_const', const=True,
                    help="executes clean command on app close.")

parser.add_argument("--exit_clean", default=False, action='store_const', const=True,
                    help="executes clean command on app close.")
parser.add_argument("--start_clean", default=False, action='store_const', const=True,
                    help="executes clean command on startup.")
parser.add_argument("--command_clean", default="adb logcat -c", help="specifies clean command.")

parser.add_argument("--pid_lookup", default="", help="specifies string for looking process id.")
parser.add_argument("--pid_mask", default="\((.*?)\)", help="specifies regex to searching pid in a text line.")

parser.add_argument("--file", default="", help="specifies log file to read.")
# parser.add_argument("-ec", default=exit_commands,
#                     help="commands that will executed on exit splited by ';' e.g:  'w;q' will write file and open explorer. To see more commands type :h")
#
# parser.add_argument("-cf", default=conf_file,
#                     help="specifies config file name. By default is '%s'" % (conf_file,))
#
# parser.add_argument("-cd", default=current_dir,
#                     help="specifies directory where log files will be saved")
#
# parser.add_argument("-cs", default=False,
#                     action='store_const',
#                     const=True,
#                     help="execute clean command on startup. By default %s" % clean_cmd)
#
# parser.add_argument("-pc", default=process_lookup,
#                     help="specifies process lookup string")
#
# parser.add_argument("--init", default=False,
#                     action='store_const',
#                     const=True,
#                     help="creates default config file in app folder")
#
# parser.add_argument('--version', "-v",
#                     action='version',
#                     version="%s %s" % (app_name, version))
#
# parser.add_argument('-execute', default=exec_cmd,
#                     help="specifies execute command that will output log stream. By default is %s" % exec_cmd)
#
# parser.add_argument('-clean', default=clean_cmd,
#                     help="specifies clean command e.g. 'adb logcat -c'.")

_args = parser.parse_args()

# IF DEBUG
# _args.command_execute = "netstat -a"
# _args.command_clean = None



file_name = default_file_name


def fix_current_dir(value):
    cd = value
    if cd == ".":
        cd = ""
    if cd != "" and not (cd.endswith("\\") or cd.endswith("/")):
        cd += "/"
    return cd


current_dir = fix_current_dir(_args.cd)

# ---------------------------------------------------------------------------------------------------------------------------------------------



# ---------------------------------------------------------------------------------------------------------------------------------------------
app = SmartlogApp()
gui = AppGui(app)

gui.set_clean_command(_args.command_clean)

if _args.start_clean:
    app.clear()

gui.set_current_file_name(file_name)
gui.set_current_folder(current_dir)
gui.update_title("Smartlog - '" + _args.command_execute + "'")

if _args.pid_lookup:
    gui.set_pid_mask(_args.pid_mask)
    gui.set_pid_lookup(_args.pid_lookup)

app.set_command_exec(_args.command_execute)

if _args.file:
    app.read_from_file(_args.file)
else:
    app.start_reading()

while not gui.is_finished():
    app.update()
    gui.update()

if not _args.file:
    app.stop_reading()

if _args.exit_clean:
    app.clear(_args.command_clean)

print "Done!"
