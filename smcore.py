# defaults
import subprocess
from Queue import Queue, Empty
from threading import Thread, Event
import threading
from logging import getLogger
L = getLogger(__name__)

def check_class(var, clazz):
    if not isinstance(var, clazz):
        err = "wrong type " + str(type(var)) + ", looking for " + str(clazz)
        raise Exception(err)

def error(text):
    print "\nError: ", str(text), "\n\n"

def log(text):
    return
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


def read_output(command, queue):
    try:
        while 1:
            p = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
            # print "subprocess id : %d" % (p.pid, )
            for line in iter(p.stdout.readline, b''):
                log("queue: " + line)
                queue.put(line.strip().decode('866').encode("utf-8"))
                if (threading.current_thread().is_stopped()):
                    raise KeyboardInterrupt("")
    except KeyboardInterrupt:
        print "Finished"
        exit()
    except Exception:
        error("Failed to execute command: '%s' " % command)
        queue.put(default.interrupt())


class StoppableThread(Thread):
    def __init__(self, command, queue):
        super(StoppableThread, self).__init__(target=read_output, args=(command, queue,))
        self._stop = Event()
        self.command = command

    def stop(self):
        self._stop.set()

    def is_stopped(self):
        return self._stop.isSet()



class CompiledLine():
    def __init__(self, index, text, tag):
        self.index = index
        self.tag = tag
        self.original = text
        self.text = text.lower()

    def get_original(self):
        return self.original

    def get_index(self):
        return self.index

    def get_tag(self):
        return self.tag

    def get(self):
        return self.original

    def can_show(self, filter_words):
        for word in filter_words:
            if not word in self.text:
                return False
        return True

class Reader():
    def __init__(self, command):
        self.queue = Queue()
        self.set_command(command)
        self.read_thread = StoppableThread(command, self.queue)
        self.read_thread.daemon = True
        self.read_thread.start()

    def stop(self):
        self.read_thread.stop()

    def set_command(self, command):
        self.command = command

    def update(self):
        lines = []
        try:
            while 1:
                line = self.queue.get_nowait()
                if len(line):
                    log(line)
                lines.append(line)
        except Empty:
            pass

        if len(lines):
            log("lines:" + str(lines))
        return lines



def compile_lines(lines, total):
    return [CompiledLine(total + index, x, default.get_tag("n")) for index, x in enumerate(lines)]



class SMBuffer():
    def __init__(self):
        self.compiled = []

    def add(self, compiled_lines):
        for i in compiled_lines:
            check_class(i, CompiledLine)

        self.compiled.extend(compiled_lines)

    def clear(self):
        self.compiled[:] = []

    def get_lines(self):
        return self.compiled

    def save_to_file(self, name):
        pass



class SmartlogApp():
    def __init__(self):
        self.buffer = SMBuffer()
        self.filter = []
        self.command = default.command()
        self.new_line_callback = None

    def stop_reading(self):
        self.reader.stop()

    def start_reading(self):
        self.reader = Reader(self.command)

    def set_command_exec(self, command):
        self.command = command

    def get_lines(self):
        return self.buffer.get_lines()

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

    def do_filter(self, lines):
        return [x for x in lines if x.can_show(self.filter)]

    def get_filtered_buffer(self):#return filtered CompiledLine list
        if self.filter:
            return self.do_filter(self.buffer.get_lines())
        else:
            return self.buffer.get_lines()

    def update(self):
        lines = self.reader.update()

        if len(lines):
            compiled_lines = compile_lines(lines, len(self.buffer.get_lines()))
            self.buffer.add(compiled_lines)

            if self.new_line_callback:
                if self.filter:
                    self.new_line_callback(self.do_filter(compiled_lines))
                else:
                    self.new_line_callback(compiled_lines)
