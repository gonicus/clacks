import StringIO
from lxml import etree, objectify
import os

# Schema files to combine
xsds = [
        "events/NodeLeave.xsd",
        "events/NodeCapabilities.xsd",
        "events/NodeAnnounce.xsd",
        "events/NodeStatus.xsd",
        "events/Inventory.xsd"
        ]

# Combine style sheet to use
stylesheet = "events.xsl"

##
## This code is copied from the original gosa-ng source, with a few modification to work
## with the given test scenario.
##
eventsxml = "<events>"
for file_path in xsds:
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

# ----

# Initialize parser
schema_root = etree.XML(str(res))
schema = etree.XMLSchema(schema_root)
parser = objectify.makeparser(schema=schema)


##
## Try to validate the test-event files
##
try:
    d = objectify.fromstring(open('tests/valid.xml').read(), parser)
    print "OK: Schema file tests/valid.xml is valid! (As expected)"

    print objectify.dump(d)

except Exception as e:
    print "FAILED: Schema file tests/valid.xml is INvalid! (Unexpected!!)"
    print e

#try:
#    d = objectify.fromstring(open('tests/invalid.xml').read(), parser)
#    print "FAILED: Schema file tests/valid.xml is valid! (Unexpected!!)"
#except Exception as e:
#    print "OK: Schema file tests/valid.xml is INvalid! (As expected)"
#    print e
