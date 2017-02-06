
from smcore import *
from Tkinter import *

class AppGui():

    def update_status_bar(self):
        total = len(self.app.get_lines())
        showed = self._filtered_count if self._filtered_count else total
        self.sv_status_bar.set("%d / %d" % (showed, total,))

    def update(self):
        try:
            self.root.update_idletasks()
            self.root.update()
            self.update_status_bar()
        except TclError:
            self.finish = True


    def on_esc_pressed(self, event):
        self.textFilter.delete(0, END)
        if self.app.get_filter():
            self.app.remove_filter()
        else:
            self.finish = True

    def is_finished(self):
        return self.finish

    def add_line(self, cl):
        self.textbox.insert(END, "[%d]\t%s\n" % (cl.get_index(), cl.get(),), cl.get_tag())

    def command_text_changed(self, ev):
        self.app.set_filter(ev.get())
        self._filtered_count = 0

        self.textbox.configure(state=NORMAL)
        self.textbox.delete(1.0, END)
        for line in self.app.get_filtered_buffer():
            self.add_line(line)
            self._filtered_count += 1

        self.textbox.configure(state=DISABLED)
        self.textbox.see(END)

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

    def __init__(self, app):
        self._filtered_count = 0
        self.app = app
        self.root = Tk()
        self.finish = False
        self.root.iconbitmap("icon.ico")

        self.root.update_idletasks()  # Update "requested size" from geometry manager
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
        self.status_bar = Label(self.root, text="Hello!", bd=1, relief=SUNKEN, anchor=E, bg="grey30", fg="yellow", textvariable=self.sv_status_bar)
        self.status_bar.pack(side="bottom", fill="both")

        # TOP
        self.label_filter = Label(self.panelFrame, text="Filter", bg="grey")
        self.label_filter.grid(row=0)

        self.sv_filter = StringVar()


        self.textFilter = Entry(self.panelFrame, bg="gray20", fg="green", insertbackground="white", textvariable=self.sv_filter, width=45)
        self.textFilter.grid(row=0, column=1, padx=5, pady=10)

        #
        self.scrollbar = Scrollbar(self.textFrame)
        self.scrollbar['command'] = self.textbox.yview
        self.scrollbar.pack(side='right', fill='y')
        self.textbox['yscrollcommand'] = self.scrollbar.set

        self.root.bind("<Escape>", self.on_esc_pressed)
        self.sv_filter.trace("w", lambda name, index, mode, sv=self.sv_filter: self.command_text_changed(self.sv_filter))
        app.set_new_lines_callback(self.on_new_lines)

