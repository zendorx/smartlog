#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gui import *

if __name__ == "__main__":

    app = SmartlogApp()
    gui = AppGui(app)

    app.start_read()

    while not gui.is_finished():
        app.update()
        gui.update()

