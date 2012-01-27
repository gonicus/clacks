import re
import os
import time
import pyinotify
import logging
from clacks.common import Environment


class ShellDNotifier(pyinotify.ProcessEvent):

    path = None
    callback = None
    regex = None

    def __init__(self, path, regex, callback):
        self.bp = self.path = path
        self.regex = regex
        self.callback = callback
        self.env = Environment.getInstance()
        self.log = logging.getLogger(__name__)

        # Start the files ystem surveillance thread now
        self.__start()

    def __start(self):
        wm = pyinotify.WatchManager()
        wm.add_watch(self.path, pyinotify.IN_ATTRIB | pyinotify.IN_MODIFY | pyinotify.IN_DELETE, rec=True, auto_add=True)
        notifier = pyinotify.ThreadedNotifier(wm, self)
        notifier.daemon = True
        notifier.start()

    def process_IN_ATTRIB(self, event):
        self.__handle(event.pathname)

    def process_IN_MODIFY(self, event):
        self.__handle(event.pathname)

    def process_IN_DELETE(self, event):
        self.__handle(event.pathname)

    def __handle(self, path):
        shortname = path[len(self.path) +1:]
        if re.match(self.regex, shortname):
            if os.access(path, os.X_OK):

                # Use the callback method to announce the new change event
                self.log.debug("received script change for script '%s'" % (shortname,))
                self.callback(shortname)
            else:
                self.log.debug("received script change for '%s', but its not an executable file" % (shortname,))
        else:
            self.log.debug("received script change for '%s', but its name is not valid" % (shortname,))
