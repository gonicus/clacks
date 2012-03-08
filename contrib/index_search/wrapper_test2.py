from search_wrapper2 import SearchWrapper
from pprint import pprint
import time

query1 = """
SELECT User.sn, User.Type, Country.*
BASE User ONE "ou=Technik,dc=gonicus,dc=de"
BASE Country ONE "ou=Technik,dc=gonicus,dc=de"
WHERE User.ParentDN = Country.ParentDN
ORDER BY User.sn, User.givenName DESC
LIMIT 10, 20
"""

query1 = """
SELECT Country.*
BASE Country ONE "ou=Technik,dc=gonicus,dc=de"
"""

query1 = """
SELECT Country.*
BASE Country SUB "ou=Technik,dc=gonicus,dc=de"
LIMIT 5
"""

sw = SearchWrapper.get_instance()
print(len(sw.execute(query1)))

