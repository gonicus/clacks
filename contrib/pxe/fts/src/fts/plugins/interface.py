# -*- coding: utf-8 -*-


class BootPlugin(object):

    def __init__(self):
        """
        Plugins for FTS need to be inherited from BootPlugin in order to
        provide the correct interface. Additionally, you have to announce
        the plugin in your setup.py's [fts.plugin] entry point section,
        so that it gets loaded on startup.
        """
        pass

    def getBootParams(self, address):
        """
        This method tries to find a propper boot configuration for the given
        address. If the address is no candidate for the current plugin, it
        should return '''None'''.

        ========= ============================================================
        Parameter Description
        ========= ============================================================
        address   Case insensitive MAC address, separator is "-"
        ========= ============================================================

        ``Return``: String or None
        """
        raise NotImplemented("getBootParams(address) is not implemented")

    def getInfo(self):
        """
        Return a short description for the boot plugin.

        ``Return``: String
        """
        raise NotImplemented("getInfo() is not implemented")
