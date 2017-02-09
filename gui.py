import getpass
import time
from Tkinter import *
import re


from smcore import *


class AppGui():
    def update_status_bar(self):
        text = ""


        if self.last_saved_file:
            text += "Saved: " + self.last_saved_file + "               "

        if self.pid_lookup_enabled:
            text += "pid: %s" % (self.app.get_current_pid()) + "              "


        total = len(self.app.get_lines())

        showed = self._filtered_count if self._filtered_count else total
        text += "%d / %d" % (showed, total,)

        if self.ready_to_finish:
            text = "Press ESC to exit"

        self.sv_status_bar.set(text)

    def update(self):
        try:
            self.root.update_idletasks()
            self.root.update()
            self.update_status_bar()

            if self.scrollbar.get()[1] != 1.0:
                self.ready_to_finish = False

        except TclError:
            self.finish = True

    def on_esc_pressed(self, event):
        self.textFilter.delete(0, END)
        if self.app.get_filter():
            self.app.remove_filter()
        elif self.scrollbar.get()[1] != 1.0:
            self.textbox.see(END)
        elif self.ready_to_finish:
            self.finish = True
        else:
            self.ready_to_finish = True

    def is_finished(self):
        return self.finish

    def add_line(self, cl):
        self.textbox.insert(END, "[%d]\t%s\n" % (cl.get_index(), cl.get(),), cl.get_tag())

    def redraw_lines(self):
        self._filtered_count = 0
        self.textbox.configure(state=NORMAL)
        self.textbox.delete(1.0, END)
        for line in self.app.get_filtered_buffer():
            self.add_line(line)
            self._filtered_count += 1

        self.textbox.configure(state=DISABLED)
        self.textbox.see(END)

    def command_text_changed(self, ev):
        self.app.set_filter(ev.get())
        self.redraw_lines()
        self.ready_to_finish = False

    def on_lines_changed(self):
        self.redraw_lines()

    def on_new_lines(self, compiled_lines):
        self.textbox.configure(state=NORMAL)
        for line in compiled_lines:
            self.add_line(line)
            self._filtered_count += 1

        self.textbox.configure(state=DISABLED)
        if self.scrollbar.get()[1] == 1.0:
            self.textbox.see(END)

    def update_title(self, title):
        self.root.title(title)

    def set_current_folder(self, folder_name):
        self.current_folder = folder_name

    def open_current_folder(self):
        os.system("start .")  # todo Get current dir

    def set_current_file_name(self, fname):
        self.current_file_name = fname

    def save_lines(self, fname, lines):
        with open(fname, 'w') as f:
            for line in lines:
                f.write("%s\n" % str(line.get_original()))

    def gen_fname(self):
        name = self.current_file_name
        uid = getpass.getuser()
        t = time.strftime("%m.%d (%H-%M)")
        name = name.replace("{uid}", uid)
        name = name.replace("{t}", t)
        return self.current_folder + name

    def save_current_file(self):
        self.save(self.gen_fname())

    def save(self, fname):
        self.save_lines(fname, self.app.get_lines())

    def save_filtered(self):
        self.save_lines(self.gen_fname(), self.app.get_filtered_buffer())

    def set_clean_command(self, command):
        self.clean_command = command

    def do_clean(self):
        self.app.clear()
        self.redraw_lines()

    def set_pid_lookup(self, string):
        self.pid_lookup = string
        self.set_pid_lookup_enabled(True)
        self.app.set_pid_lookup_string(string)
        self.app.set_pid_filter_enabled(True)


    def set_pid_lookup_enabled(self, value):
        if not self.pid_lookup and value:
            error("Cannot set pid lookup, pid lookup string is empty")
            return

        self.pid_lookup_enabled = value

    def set_pid_mask(self, string):
        self.app.set_pid_mask(re.compile(string))

    def __init__(self, app):
        self._filtered_count = 0
        self.app = app
        self.root = Tk()
        self.finish = False
        self.set_current_folder("")
        self.last_saved_file = ""
        self.root.iconbitmap("icon.ico")
        self.set_current_folder("{t} {uid}.log")
        self.clean_command = "adb logcat -c"
        self.ready_to_finish = False
        self.pid_lookup = ""
        self.pid = None
        self.pid_lookup_enabled = False

        self.root.update_idletasks()
        w = 800
        h = 900
        x = (self.root.winfo_screenwidth() - w) / 2
        y = (self.root.winfo_screenheight() - h) / 2
        self.root.geometry("%dx%d+%d+%d" % (w, h, x, y))

        self.panelFrame = Frame(self.root, height=60, width=1000, bg='gray')
        self.textFrame = Frame(self.root, height=800, width=1000)

        self.panelFrame.pack(side='top', fill='x')
        self.textFrame.pack(side='top', fill='both', expand=1)

        self.textbox = Text(self.textFrame, wrap='word', bg="black", fg="white")
        self.textbox.pack(side='left', fill='both', expand=1)

        self.textbox.tag_config(default.tag_error(), foreground="red")
        self.textbox.tag_config(default.tag_warning(), foreground="yellow")
        self.textbox.tag_config(default.tag_debug(), foreground="magenta")
        self.textbox.tag_config(default.tag_lookup(), foreground="green")
        self.textbox.tag_config(default.tag_normal(), foreground="white")

        self.sv_status_bar = StringVar()
        self.status_bar = Label(self.root, text="Hello!", bd=1, relief=SUNKEN, anchor=E, bg="grey30", fg="yellow",
                                textvariable=self.sv_status_bar)
        self.status_bar.pack(side="bottom", fill="both")

        self.label_filter = Label(self.panelFrame, text="Filter", bg="grey")
        self.label_filter.grid(row=0)

        self.sv_filter = StringVar()

        self.textFilter = Entry(self.panelFrame, bg="gray20", fg="green", insertbackground="white",
                                textvariable=self.sv_filter, width=45)
        self.textFilter.grid(row=0, column=1, padx=5, pady=10)

        self.scrollbar = Scrollbar(self.textFrame)
        self.scrollbar['command'] = self.textbox.yview
        self.scrollbar.pack(side='right', fill='y')
        self.textbox['yscrollcommand'] = self.scrollbar.set

        self.root.bind("<Escape>", self.on_esc_pressed)
        self.sv_filter.trace("w",
                             lambda name, index, mode, sv=self.sv_filter: self.command_text_changed(self.sv_filter))

        app.set_new_lines_callback(self.on_new_lines)
        app.set_lines_changed_callback(self.on_lines_changed)
