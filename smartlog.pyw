#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse

from gui import *

# INFO-------------------------
version = "0.4"
app_name = "SmartLog"
source_info = "https://github.com/zendorx/smart-logcat"
contacts_info = "zendorx@gmail.com"

# CONSTS-----------------------
# const_wait = "- waiting for device -"
# const_ignore = "ignore:"


# VARIABLES--------------------
default_file_name = "{t} {uid}.log"
conf_file = "default.cfg"
exit_commands = ""
current_dir = ""

last_saved_fname = ""
adb_path = "adb.exe"
interrupt_command = "__interrupt_command__"
exec_cmd = "adb logcat"
clean_cmd = "adb logcat -c"

# DEBUG
exec_cmd = "netstat -a"
# ----

process_id = ""
process_lookup = ""
process_lookup_enabled = False
parser = argparse.ArgumentParser(prog=app_name,  # todo: move to description
                                 usage="""1)Install android SDK"
                                          2)Add '{$SDK}\platform-tools\\adb.exe' to the PATH or setup -adb <path>
                                          3)Run program
                                          """,
                                 description="Program prints stream output and provides bunch of useful features like filter, highlight. Type :h in program for more help.")

parser.add_argument("-ec", default=exit_commands,
                    help="commands that will executed on exit splited by ';' e.g:  'w;q' will write file and open explorer. To see more commands type :h")

parser.add_argument("-cf", default=conf_file,
                    help="specifies config file name. By default is '%s'" % (conf_file,))

parser.add_argument("-cd", default=current_dir,
                    help="specifies directory where log files will be saved")

parser.add_argument("-cs", default=False,
                    action='store_const',
                    const=True,
                    help="execute clean command on startup. By default %s" % clean_cmd)

parser.add_argument("-pc", default=process_lookup,
                    help="specifies process lookup string")

parser.add_argument("--init", default=False,
                    action='store_const',
                    const=True,
                    help="creates default config file in app folder")

parser.add_argument('--version', "-v",
                    action='version',
                    version="%s %s" % (app_name, version))

parser.add_argument('-execute', default=exec_cmd,
                    help="specifies execute command that will output log stream. By default is %s" % exec_cmd)

parser.add_argument('-clean', default=clean_cmd,
                    help="specifies clean command e.g. 'adb logcat -c'.")

_args = parser.parse_args()

exit_commands = _args.ec
conf_file = _args.cf
exec_cmd = _args.execute
clean_cmd = _args.clean
process_lookup = _args.pc
file_name = default_file_name


def fix_current_dir(value):
    cd = value
    if cd == ".":
        cd = ""
    if cd != "" and not (cd.endswith("\\") or cd.endswith("/")):
        cd += "/"
    return cd


current_dir = fix_current_dir(_args.cd)

if len(process_lookup) > 0:
    process_lookup_enabled = True
    print "PC: '%s'" % process_lookup

# ---------------------------------------------------------------------------------------------------------------------------------------------
app = SmartlogApp()
gui = AppGui(app)

gui.set_clean_command(clean_cmd)
gui.set_current_file_name(file_name)
gui.set_current_folder(current_dir)
gui.update_title("Smartlog - '" + exec_cmd + "'")

app.set_command_exec(exec_cmd)
app.start_reading()

while not gui.is_finished():
    app.update()
    gui.update()

app.stop_reading()

print "Done!"
