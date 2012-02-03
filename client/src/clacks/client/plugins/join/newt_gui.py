# -*- coding: utf-8 -*-
import time
import gettext
from clacks.common.components.zeroconf_client import ZeroconfClient
from clacks.client import __version__ as VERSION
from clacks.client.plugins.join.methods import join_method
from pkg_resources import resource_filename

try:
    from snack import *
    available = True
except ImportError:
    available = False

# Include locales
t = gettext.translation('messages', resource_filename("clacks.client", "locale"), fallback=True)
_ = t.ugettext


class NewtGUI(join_method):
    priority = 40

    def __init__(self, parent=None):
        super(NewtGUI, self).__init__()

    def start_gui(self):
        self.screen = SnackScreen()
        self.screen.pushHelpLine(" ")

    def end_gui(self):
        self.screen.finish()

    @staticmethod
    def available():
        global available
        return available

    def PopupWindow(self, title, text, width=50, sleep=None):
        t = TextboxReflowed(width, text)

        g = GridForm(self.screen, title, 1, 1)
        g.add(t, 0, 0, padding = (0, 0, 0, 0))
        g.setTimer(1)
        result = g.run()

        # Just show us some seconds
        if sleep:
            time.sleep(sleep)
            self.screen.popWindow()

        # Else someone else needs to call "popWindow"...


    def JoinWindow(self, title, text, allowCancel=0, width=50,
            entryWidth=37, buttons=['Join'], help=None):
        bb = ButtonBar(self.screen, buttons);
        t = TextboxReflowed(width, text)

        sg = Grid(2, 2)

        entryList = []
        e = Entry(entryWidth)
        sg.setField(Label("User name"), 0, 0, padding = (0, 0, 1, 0), anchorLeft = 1)
        sg.setField(e, 1, 0, anchorLeft = 1)
        entryList.append(e)
        e = Entry(entryWidth, password=1)
        sg.setField(Label("Password"), 0, 1, padding = (0, 0, 1, 0), anchorLeft = 1)
        sg.setField(e, 1, 1, anchorLeft = 1)
        entryList.append(e)

        g = GridForm(self.screen, title, 1, 3)

        g.add(t, 0, 0, padding = (0, 0, 0, 1))
        g.add(sg, 0, 1, padding = (0, 0, 0, 1))
        g.add(bb, 0, 2, growx = 1)

        result = g.runOnce()

        entryValues = []
        for entry in entryList:
            entryValues.append(entry.value())

        return (bb.buttonPressed(result), tuple(entryValues))

    def discover(self):
        aw = PopupWindow(screen, _("Clacks Infrastructure") + "v%s" % VERSION, _("Searching service provider..."))
        self.url = ZeroconfClient.discover(['_amqps._tcp', '_amqp._tcp'], domain=self.domain)[0]
        self.screen.popWindow()
        return self.url

    def join_dialog(self):
        key = None

        while not key:
            username, password = JoinWindow(screen, _("Clacks Infrastructure") + "v%s" % VERSION, _("Please enter the credentials of an administrative user to join this client."))
            if not username or not password:
                self.show_error("Please enter a user name and a password!")
                continue

            key = self.join(username, password)

    def show_error(self, error):
        aw = PopupWindow(screen, _("Error") % VERSION, error, sleep=3)
