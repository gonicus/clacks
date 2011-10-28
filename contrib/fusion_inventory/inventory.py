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
        if os.path.exists('/tmp/fusion_tmp'):
            shutil.rmtree('/tmp/fusion_tmp')
        os.mkdir('/tmp/fusion_tmp')

        if False:
            # Execute the fusion-invetory agent
            process = subprocess.Popen(["fusioninventory-agent","--local=/tmp/fusion_tmp"], \
                      shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            process.communicate()
        else:
            # !! A workaround to avoid executing the report agent over and over again.
            shutil.copyfile('examples/cajus', '/tmp/fusion_tmp/dyn-153-2011-10-26-15-01-12.ocs')

        # Open resulting xml file
        flist = os.listdir('/tmp/fusion_tmp')
        result = None
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
            print checksum_result
            m = hashlib.md5()
            m.update(etree.tostring(checksum_result))
            print m.hexdigest()

        # Remove temporary files
        shutil.rmtree('/tmp/fusion_tmp')
        return result

# Client part
c = client(uuid='Blafasel')
xml = c.tranform_xml()
#print xml

