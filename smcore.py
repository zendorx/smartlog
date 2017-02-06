# defaults
import subprocess
from Queue import Queue, Empty
from threading import Thread
from logging import getLogger
L = getLogger(__name__)

def error(text):
    print "\nError: ", str(text), "\n\n"

def log(text):
    print str(text)

class default():
    @staticmethod
    def command(): return "netstat -a"

    @staticmethod
    def interrupt(): return "__interrupted__"

    @staticmethod
    def tag_error(): return "__error_tag__"

    @staticmethod
    def tag_warning(): return "__warning_tag__"

    @staticmethod
    def tag_debug(): return "__debug_tag__"

    @staticmethod
    def tag_lookup(): return "__lookup_tag__"

    @staticmethod
    def tag_normal(): return "__normal_tag__"

    @staticmethod
    def get_tag(tag_shortcut):
        tags = { "e" : default.tag_error(), "w" : default.tag_warning(), "d" : default.tag_debug(), "l" : default.tag_lookup(), "n" : default.tag_normal()}
        return tags[tag_shortcut]



class CompiledLine():
    def __init__(self, index, text, tag):
        self.index = index
        self.tag = tag
        self.original = text
        self.text = text.lower()

    def get_tag(self):
        return self.tag

    def get(self):
        return self.original

    def can_show(self, filter_words):
        for word in filter_words:
            if not word in self.text:
                return False
        return True



def _read_output(command, queue):
    try:
        while 1:
            p = subprocess.Popen(command, stdout=subprocess.PIPE, universal_newlines=True)
            for line in iter(p.stdout.readline, b''):
                log("queue: " + line)
                queue.put(line.strip())
    except KeyboardInterrupt:
        exit()
    except Exception:
        error("Failed to execute command: '%s' " % command)
        queue.put(default.interrupt())

queue = Queue()

class Reader():
    def __init__(self, command):
        global queue
        self.set_command(command)
        self.read_thread = Thread(target=_read_output, args=(command, queue,))
        self.read_thread.daemon = True
        self.read_thread.start()

    def set_command(self, command):
        self.command = command

    def update(self):
        lines = []
        try:
            while 1:
                line = queue.get_nowait()
                if len(line):
                    log(line)
                lines.append(line)
        except Empty:
            pass

        if len(lines):
            log("lines:" + str(lines))
        return lines

def compile_lines(lines):
    return [CompiledLine(index, x, default.get_tag("n")) for index, x in enumerate(lines)]

class SMBuffer():
    def __init__(self):
        self.lines = []
        self.compiled = []

    def add(self, compiled_lines):
        self.lines.append(compiled_lines)
        self.compiled.extend(compiled_lines)

    def get_lines(self):
        return self.lines

    def get_compiled(self):
        return self.compiled

    def save_to_file(self, name):
        pass



class SmartlogApp():
    def __init__(self):
        self.buffer = SMBuffer()
        self.filter = []
        self.command = default.command()
        self.new_line_callback = None

    def start_read(self):
        self.reader = Reader(self.command)

    def set_command_exec(self, command):
        self.command = command

    def get_filter(self):
        return self.filter

    def remove_filter(self):
        self.filter[:] = []

    def set_filter(self, words):
        self.remove_filter()
        for word in words.split(" "):
            self.filter.append(word.lower().strip())

    def set_new_lines_callback(self, callback):
        self.new_line_callback = callback

    def get_filtered_buffer(self):#return filtered CompiledLine list
        if len(self.filter):
            return [x for x in self.buffer.get_compiled() if x.can_show(self.filter)]
        else:
            return self.buffer.get_compiled()

    def update(self):
        lines = self.reader.update()

        if len(lines):
            compiled_lines = compile_lines(lines)
            self.buffer.add(compiled_lines)

            if self.new_line_callback:
                self.new_line_callback(compiled_lines)
