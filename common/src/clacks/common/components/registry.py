# -*- coding: utf-8 -*-
import os
import StringIO
import logging
from inspect import isclass
from lxml import etree
#pylint: disable=E0611
from pkg_resources import resource_filename, resource_listdir, iter_entry_points, resource_isdir
from clacks.common.handler import IInterfaceHandler
from clacks.common import Environment


class PluginRegistry(object):
    """
    Plugin registry class. The registry holds plugin instances and
    provides overall functionality like "serve" and "shutdown".

    =============== ============
    Parameter       Description
    =============== ============
    component       What setuptools entrypoint to use when looking for :class:`clacks.common.components.plugin.Plugin`.
    =============== ============
    """
    modules = {}
    handlers = {}
    evreg = {}

    def __init__(self, component="agent.module"):
        env = Environment.getInstance()
        self.env = env
        self.log = logging.getLogger(__name__)
        self.log.debug("inizializing plugin registry")

        # Load common event resources
        base_dir = resource_filename('clacks.common', 'data/events') + os.sep
        if os.sep == "\\":
            base_dir = "file:///" + "/".join(base_dir.split("\\"))

        files = [ev for ev in resource_listdir('clacks.common', 'data/events')
                if ev[-4:] == '.xsd']
        for f in files:
            event = os.path.splitext(f)[0]
            self.log.debug("adding common event '%s'" % event)
            PluginRegistry.evreg[event] = os.path.join(base_dir, f)

        # Get module from setuptools
        for entry in iter_entry_points(component):
            module = entry.load()
            self.log.info("module %s included" % module.__name__)
            PluginRegistry.modules[module.__name__] = module

            # Save interface handlers
            # pylint: disable=E1101
            if IInterfaceHandler.implementedBy(module):
                self.log.debug("registering handler module %s" % module.__name__)
                PluginRegistry.handlers[module.__name__] = module

        # Register module events
        for module, clazz  in PluginRegistry.modules.iteritems():

            # Check for event resources
            if resource_isdir(clazz.__module__, 'data/events'):
                base_dir = resource_filename(clazz.__module__, 'data/events')
                if os.sep == "\\":
                    base_dir = "file:///" + "/".join(base_dir.split("\\"))

                for filename in resource_listdir(clazz.__module__, 'data/events'):
                    if filename[-4:] != '.xsd':
                        continue
                    event = os.path.splitext(filename)[0]
                    if not event in PluginRegistry.evreg:
                        PluginRegistry.evreg[event] = os.path.join(base_dir, filename)
                        self.log.debug("adding module event '%s'" % event)

        # Initialize component handlers
        for handler, clazz  in PluginRegistry.handlers.iteritems():
            PluginRegistry.handlers[handler] = clazz()

        # Initialize modules
        for module, clazz  in PluginRegistry.modules.iteritems():
            if module in PluginRegistry.handlers:
                PluginRegistry.modules[module] = PluginRegistry.handlers[module]
            else:
                PluginRegistry.modules[module] = clazz()

        # Let handlers serve
        for handler, clazz in sorted(PluginRegistry.handlers.iteritems(),
                key=lambda k: k[1]._priority_):

            if hasattr(clazz, 'serve'):
                clazz.serve()

        #NOTE: For component handler: list implemented interfaces
        #print(list(zope.interface.implementedBy(module)))

    @staticmethod
    def shutdown():
        """
        Call handlers stop() methods in order to grant a clean shutdown.
        """
        for clazz  in PluginRegistry.handlers.values():
            if hasattr(clazz, 'stop'):
                clazz.stop()
                del clazz

    @staticmethod
    def getInstance(name):
        """
        Return an instance of a registered class.

        =============== ============
        Parameter       Description
        =============== ============
        name            name of the class to get instance of
        =============== ============

        >>> from clacks.common.components import PluginRegistry
        >>> cr = PluginRegistry.getInstance("CommandRegistry")

        """
        if not name in PluginRegistry.modules:
            raise ValueError("no module '%s' available" % name)

        if isclass(PluginRegistry.modules[name]):
            return None

        return PluginRegistry.modules[name]

    @staticmethod
    def getEventSchema():
        stylesheet = resource_filename('clacks.common', 'data/events/events.xsl')
        eventsxml = "<events>"

        for file_path in PluginRegistry.evreg.values():

            # Build a tree of all event paths
            eventsxml += '<path name="%s">%s</path>' % (os.path.splitext(os.path.basename(file_path))[0], file_path)

        eventsxml += '</events>'

        # Parse the string with all event paths
        eventsxml = StringIO.StringIO(eventsxml)
        xml_doc = etree.parse(eventsxml)

        # Parse XSLT stylesheet and create a transform object
        xslt_doc = etree.parse(stylesheet)
        transform = etree.XSLT(xslt_doc)

        # Transform the tree of all event paths into the final XSD
        res = transform(xml_doc)
        return str(res)
