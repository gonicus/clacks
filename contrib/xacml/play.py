from ez_setup import use_setuptools
use_setuptools()

import logging
logging.basicConfig(level=logging.DEBUG)

from ndg.xacml.core.attribute import Attribute
from ndg.xacml.core.attributevalue import AttributeValueClassFactory
from ndg.xacml.core.context.request import Request
from ndg.xacml.core.context.subject import Subject
from ndg.xacml.core.context.resource import Resource
from ndg.xacml.core.context.action import Action
from ndg.xacml.core.context.pdp import PDP
from ndg.xacml.core.policy import Policy
from ndg.xacml.parsers.etree.factory import ReaderFactory


# Build up PolicyDecisionPoint
PolicyReader = ReaderFactory.getReader(Policy)
policy = PolicyReader.parse("test_policy.xml")
pdp = PDP(policy)

# Build up a test request
# with no action and no target.
# It just has a subject telling us that the user
# is in the role 'adminstrators'
request = Request()

# Build up the "role" attribute
#   type:   http://www.w3.org/2001/XMLSchema#string
#   value:  administrator
attributeValueFactory = AttributeValueClassFactory()
role = attributeValueFactory("http://www.w3.org/2001/XMLSchema#string")
arole = role("administrator")

# Add the role-attribute to the request-subject
#   id:     urn:oasis:names:tc:xacml:2.0:example:attribute:role
attr = Attribute()
attr.attributeId = "urn:oasis:names:tc:xacml:2.0:example:attribute:role"
attr.dataType = role.IDENTIFIER         # = http://www.w3.org/2001/XMLSchema#string
attr.attributeValues.append(arole)

subject = Subject()
subject.attributes.append(attr)
request.subjects.append(subject)

# See what we've received as result
res =  pdp.evaluate(request)
for result in  res.results:
    print result.decision


"""

How to add actions (I did not test it yet):


somevalue = attributeValueFactory("http://www.w3.org/2001/XMLSchema#string")
avalue = somevalue("https://www.gonicus.de/webdav")
bvalue = somevalue("read")

# Add a resource attribute
resourceAttribute = Attribute()
resourceAttribute.attributeId = Identifiers.Resource.RESOURCE_ID
resourceAttribute.dataType = avalue.IDENTIFIER
resourceAttribute.attributeValues.append(avalue)
resource.attributes.append(resourceAttribute)
request.resources.append(resource)

# Create a dummy 'read' action
actionAttribute = Attribute()
actionAttribute.attributeId = Identifiers.Action.ACTION_ID
actionAttribute.dataType = bvalue.IDENTIFIER
actionAttribute.attributeValues.append(bvalue)
request.action.attributes.append(actionAttribute)



-------------------------------
Notes
-------------------------------

Attribute that can be created are using the AttributeValueClassFactory():
    factory = AttributeValueClassFactory()
    attribute = factory(<type>)

Types:
>>  urn:oasis:names:tc:xacml:1.0:data-type:x500Name
>>  urn:oasis:names:tc:xacml:2.0:data-type:dnsName
>>  http://www.w3.org/2001/XMLSchema#string
>>  http://www.w3.org/TR/2002/WD-xquery-operators-20020816#yearMonthDuration
>>  urn:oasis:names:tc:xacml:1.0:data-type:rfc822Name
>>  http://www.w3.org/2001/XMLSchema#integer
>>  http://www.w3.org/2001/XMLSchema#dateTime
>>  http://www.w3.org/2001/XMLSchema#boolean
>>  http://www.w3.org/2001/XMLSchema#anyURI
>>  http://www.w3.org/2001/XMLSchema#base64Binary
>>  http://www.w3.org/2001/XMLSchema#hexBinary
>>  http://www.w3.org/2001/XMLSchema#date
>>  http://www.w3.org/2001/XMLSchema#time
>>  urn:oasis:names:tc:xacml:2.0:data-type:ipAddress
>>  http://www.w3.org/2001/XMLSchema#double
>>  http://www.w3.org/TR/2002/WD-xquery-operators-20020816#dayTimeDuration

"""

