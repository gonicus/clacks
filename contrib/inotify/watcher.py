#!/usr/bin/env python
import re
import time
import pyinotify


class DirWatcher(pyinotify.ProcessEvent):

    def __init__(self):
        self.bp = "/etc/clacks/shell.d"

    def process_IN_CREATE(self, event):
        print "Create:", event.pathname[len(self.bp + 1):]

    def process_IN_MODIFY(self, event):
        print "Modify:", event.pathname[len(self.bp + 1):]

    def process_IN_DELETE(self, event):
        print "Delete:", event.pathname[len(self.bp + 1):]


wm = pyinotify.WatchManager()
wm.add_watch("/etc/clacks/shell.d", pyinotify.IN_CREATE | pyinotify.IN_MODIFY | pyinotify.IN_DELETE, rec=True, auto_add=True)

notifier = pyinotify.ThreadedNotifier(wm, DirWatcher())
notifier.start()

try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    notifier.stop()
