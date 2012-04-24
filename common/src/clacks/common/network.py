import gobject
import dbus
import dbus.glib
import dbus.mainloop.glib
from time import sleep
from threading import Thread
from logging import getLogger


NM_STATE_UNKNOWN = 0
NM_STATE_ASLEEP = 10
NM_STATE_DISCONNECTED = 20
NM_STATE_DISCONNECTING = 30
NM_STATE_CONNECTING = 40
NM_STATE_CONNECTED_LOCAL = 50
NM_STATE_CONNECTED_SITE = 60
NM_STATE_CONNECTED_GLOBAL = 70


class Monitor(object):

    def __init__(self, callback=None):
        self.__callback = callback
        self.log = getLogger(__name__)
        self.__running = False
        self.__thread = None

        self.log.info("Initializing network state monitor")

        # Initialize DBUS
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.__loop = gobject.MainLoop()
        self.__bus = dbus.SystemBus()
        gobject.threads_init()
        dbus.glib.init_threads()

        # Register actions to detect the network state
        self.__upower_actions()
        self.__network_actions()

        # Get current state
        try:
            proxy = self.__bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
            iface = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')
            self.__state = iface.Get("org.freedesktop.NetworkManager", "State") in [NM_STATE_CONNECTED_SITE, NM_STATE_CONNECTED_GLOBAL]

        except:
            self.log.warning("no network-manager detected: defaulting to state 'online'")
            self.__state = True

    def start(self):
        self.__running = True

        def runner():
            context = gobject.MainLoop().get_context()

            while self.__running:
                context.iteration(False)
                if not context.pending():
                    sleep(1)

        self.__thread = Thread(target=runner)
        self.__thread.start()

    def stop(self):
        self.__running = False
        self.__loop.quit()
        self.__thread.join()

    def is_online(self):
        return self.__state

    def __upower_actions(self):
        try:
            proxy = self.__bus.get_object('org.freedesktop.UPower', '/org/freedesktop/UPower')
            iface = dbus.Interface(proxy, 'org.freedesktop.UPower')
  
            iface.connect_to_signal("Sleeping", self.__upower_sleeping)
        except:
            self.log.warning("no UPower detected: will not be able to suppend network")

    def __network_actions(self):
        try:
            proxy = self.__bus.get_object('org.freedesktop.NetworkManager', '/org/freedesktop/NetworkManager')
            iface = dbus.Interface(proxy, 'org.freedesktop.NetworkManager')
  
            iface.connect_to_signal("StateChanged", self.__network_state)
        except:
            self.log.warning("no network-manager detected: will not be able to suspend or activate network")

    def __upower_sleeping(self):
        self.log.info("network down")
        self.__state = False

        if self.__callback:
            self.__callback(False)
  
    def __network_state(self, state):
        if not self.__state and state in [NM_STATE_CONNECTED_SITE, NM_STATE_CONNECTED_GLOBAL]:
            self.log.info("network up")
            self.__state = True

            if self.__callback:
                self.__callback(True)

        elif self.__state:
            self.log.info("network down")
            self.__state = False

            if self.__callback:
                self.__callback(False)
