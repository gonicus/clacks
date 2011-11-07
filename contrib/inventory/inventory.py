from lxml import etree, objectify
from pprint import pprint
import subprocess
from subprocess import PIPE
import re
import os
import shutil
import json
import StringIO
import hashlib


class client(object):

    uuid = None

    def __init__(self, uuid=None):
        self.uuid = uuid

    def tranform_xml(self):

        # Clean up old reports
        path = '/tmp/fusion_tmp'
        if os.path.exists(path):
            shutil.rmtree(path)
        os.mkdir(path)

        # Execute the fusion-invetory agent
        process = subprocess.Popen(["fusioninventory-agent","--local="+path], \
                  shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate()

        #shutil.copyfile('examples/lars2', '/tmp/fusion_tmp/dyn-153-2011-10-26-15-01-12.ocs')

        # Open resulting xml file
        flist = os.listdir(path)
        result = None
        checksum = None
        if flist:
            xml_doc = etree.parse(os.path.join('/tmp/fusion_tmp',flist[0]))
            xslt_doc = etree.parse('fusionToGosa.xsl')
            transform = etree.XSLT(xslt_doc)
            result = transform(xml_doc)

            # Remove time base or frequently changing values (like processes) from the xml file
            # to be able to generate a useable checksum.
            xml_doc = etree.parse(StringIO.StringIO(result))
            checksum_doc = etree.parse('xmlToChecksumXml.xsl')
            check_trans = etree.XSLT(checksum_doc)
            checksum_result = check_trans(xml_doc)
            m = hashlib.md5()
            m.update(etree.tostring(checksum_result))
            checksum = m.hexdigest()

        # Remove temporary files
        shutil.rmtree('/tmp/fusion_tmp')
        return checksum, result

# Client part
c = client(uuid='Blafasel')
checksum, xml = c.tranform_xml()
print checksum

