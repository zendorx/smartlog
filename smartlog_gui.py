#!/usr/bin/env python
# -*- coding: utf-8 -*-

from smcore import *
from Tkinter import *

if __name__ == "__main__":
    root = Tk()



    panelFrame = Frame(root, height=60, bg='gray')
    textFrame = Frame(root, height=1500, width=1000)

    panelFrame.pack(side='top', fill='x')
    textFrame.pack(side='bottom', fill='both', expand=1)

    textbox = Text(textFrame, wrap='word', bg="black", fg="white")
    textbox.place(x=0, y=0, width=100, height=100)
    textbox.pack(side='left', fill='both', expand=1)
    textbox.tag_config(default.tag_error(), foreground="red")
    textbox.tag_config(default.tag_warning(), foreground="yellow")
    textbox.tag_config(default.tag_debug(), foreground="magenta")
    textbox.tag_config(default.tag_lookup(), foreground="green")
    textbox.tag_config(default.tag_normal(), foreground="white")

    sv = StringVar()
    textFilter = Entry(panelFrame, bg="black", fg="green", insertbackground="white", textvariable=sv).place(x=300, y=13, width=200, height = 25)
    scrollbar = Scrollbar(textFrame)
    scrollbar['command'] = textbox.yview
    scrollbar.pack(side='right', fill='y')
    textbox['yscrollcommand'] = scrollbar.set

    app = SmartlogApp()


    def command_text_changed(ev):
        app.set_filter(ev.get())

        textbox.configure(state=NORMAL)
        textbox.delete(1.0, END)
        for compiled_line in app.get_filtered_buffer():
            textbox.insert(END, "%s\n" % (compiled_line.get(),), compiled_line.get_tag())
        textbox.configure(state=DISABLED)
        textbox.see(END)

    def on_new_lines(compiled_lines):
        textbox.configure(state=NORMAL)
        for line in compiled_lines:
            textbox.insert(END, "%s\n" % (line.get(),), line.get_tag())

        textbox.configure(state=DISABLED)
        if scrollbar.get()[1] == 1.0:
            textbox.see(END)

    sv.trace("w", lambda name, index, mode, sv=sv: command_text_changed(sv))

    app.set_new_lines_callback(on_new_lines)
    app.start_read()

    while 1:
        try:
            app.update()
            root.update_idletasks()
            root.update()
        except TclError as e:
            break
            pass

