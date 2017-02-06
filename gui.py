
from smcore import *
from Tkinter import *

class AppGui():
    def update(self):
        try:
            self.root.update_idletasks()
            self.root.update()
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

    def command_text_changed(self, ev):
        self.app.set_filter(ev.get())

        self.textbox.configure(state=NORMAL)
        self.textbox.delete(1.0, END)
        for compiled_line in self.app.get_filtered_buffer():
            self.textbox.insert(END, "%s\n" % (compiled_line.get(),), compiled_line.get_tag())
        self.textbox.configure(state=DISABLED)
        self.textbox.see(END)

    def on_new_lines(self, compiled_lines):
        self.textbox.configure(state=NORMAL)
        for line in compiled_lines:
            self.textbox.insert(END, "%s\n" % (line.get(),), line.get_tag())

        self.textbox.configure(state=DISABLED)
        if self.scrollbar.get()[1] == 1.0:
            self.textbox.see(END)

    def __init__(self, app):
        self.app = app
        self.root = Tk()
        self.finish = False
        self.root.iconbitmap("icon.ico")
        self.root.title("Smartlog")

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

        self.status_bar = Label(self.root, text="Hello!", bd=1, relief=SUNKEN, anchor=E, bg="grey30", fg="yellow")
        self.status_bar.pack(side="bottom", fill="both")

        # TOP
        self.label_filter = Label(self.panelFrame, text="Filter", bg="grey")
        self.label_filter.grid(row=0)

        self.sv = StringVar()
        self.textFilter = Entry(self.panelFrame, bg="gray20", fg="green", insertbackground="white", textvariable=self.sv, width=45)
        self.textFilter.grid(row=0, column=1, padx=5, pady=10)

        #
        self.scrollbar = Scrollbar(self.textFrame)
        self.scrollbar['command'] = self.textbox.yview
        self.scrollbar.pack(side='right', fill='y')
        self.textbox['yscrollcommand'] = self.scrollbar.set

        self.root.bind("<Escape>", self.on_esc_pressed)
        self.sv.trace("w", lambda name, index, mode, sv=self.sv: self.command_text_changed(sv))
        app.set_new_lines_callback(self.on_new_lines)

