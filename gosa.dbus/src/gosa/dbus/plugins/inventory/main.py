# -*- coding: utf-8 -*-
import os
import shutil
import StringIO
import hashlib
import subprocess
import dbus.service
from pkg_resources import resource_filename
from lxml import etree, objectify
from gosa.common import Environment
from gosa.common.components import Plugin
from gosa.dbus import get_system_bus


class InventoryException(Exception):
    pass

class DBusInventoryHandler(dbus.service.Object, Plugin):
    """ This handler collect client inventory data """

    def __init__(self):
        conn = get_system_bus()
        dbus.service.Object.__init__(self, conn, '/com/gonicus/gosa/inventory')
        self.env = Environment.getInstance()

    @dbus.service.method('com.gonicus.gosa', in_signature='', out_signature='ss')
    def inventory(self):
        """
        Start inventory client and transform the results into a GOsa usable way.

        We should support other invetory clients, later.
        """

        # Added other report types here
        result = ""
        if True:

            # Fusion Inventory Client
            result = self.load_from_fusion_agent()

        # Remove time base or frequently changing values (like processes) from the
        # result to generate a useable checksum.
        # We use a XSL file which reads the result and skips some tags.
        try:
            xml_doc = etree.parse(StringIO.StringIO(result))
            checksum_doc = etree.parse(resource_filename("gosa.dbus",'plugins/inventory/xmlToChecksumXml.xsl'))
            check_trans = etree.XSLT(checksum_doc)
            checksum_result = check_trans(xml_doc)
        except Exception as e:
            raise InventoryException("No report files could be found in '%s'" % (path,))

        # Once we've got a 'clean' result, create the checksum.
        m = hashlib.md5()
        m.update(etree.tostring(checksum_result))
        checksum = m.hexdigest()
        return (checksum, result)

    def load_from_fusion_agent(self):

        # Execute the fusion-invetory agent
        #
        # Unfortunately we cannot specify a target file for the generated
        # xml-report directly, we can only name a path where the results should go to.
        # So we've to detect the generated file by ourselves later.

        # Create the target directory for the result.
        path = '/tmp/fusion_tmp'
        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)

        # Execute the inventory agent.
        process = subprocess.Popen(["fusioninventory-agent","--local="+path], \
                shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate()

        # Try to read the generated xml result.
        flist = os.listdir(path)
        result = None
        checksum = None
        if flist:

            # Open the first found result file and transform it into a GOsa usable
            # event-style xml.
            try:
                xml_doc = etree.parse(os.path.join('/tmp/fusion_tmp',flist[0]))
                xslt_doc = etree.parse(resource_filename("gosa.dbus", "plugins/inventory/fusionToGosa.xsl"))
                transform = etree.XSLT(xslt_doc)
                result = transform(xml_doc)
            except Exception as e:
                raise InventoryException("Failed to read and transform fusion-invetory-agent results (%s)!" % (
                    os.path.join('/tmp/fusion_tmp',flist[0])))

        else:
            raise InventoryException("No report files could be found in '%s'" % (path,))

        # Remove temporary created files created by the inventory agent.
        shutil.rmtree('/tmp/fusion_tmp')
        return etree.tostring(result)
