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

        try:
            wm = pyinotify.WatchManager()
            wm.add_watch(self.path, pyinotify.IN_ATTRIB | pyinotify.IN_MODIFY | pyinotify.IN_DELETE, rec=True, auto_add=True)
            notifier = pyinotify.ThreadedNotifier(wm, self)
            notifier.start()
        except KeyboardInterrupt:

            # On Strg+C stop our thread and re-raise the Exception so that other processes
            # can terminate too
            notifier.stop()
            raise

    def process_IN_ATTRIB(self, event):
        self.__handle(event.pathname)

    def process_IN_MODIFY(self, event):
        self.__handle(event.pathname)

    def process_IN_DELETE(self, event):
        self.__handle(event.pathname)

    def __handle(self, path):
        if re.match(self.regex, path[len(self.path) +1:]):
            if os.access(path, os.X_OK):

                # Use the callback method to announce the new change event
                self.log.debug("received script change for script '%s'" % (path[len(self.path) +1:]))
                self.callback(path)
            else:
                self.log.debug("received script change for '%s', but its not an executable file" % (path[len(self.path) +1:]))
        else:
            self.log.debug("received script change for '%s', but its name is not valid" % (path[len(self.path) +1:]))
