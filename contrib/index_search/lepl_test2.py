from search_wrapper import SearchWrapper
from pprint import pprint

query = """
SELECT User.sn, SambaDomain.*, User.Type
BASE SambaDomain SUB "dc=gonicus,dc=de"
BASE User SUB "dc=gonicus,dc=de"
WHERE (SambaDomain.sambaDomainName = User.sambaDomainName)
ORDER BY User.sn, User.givenName DESC
"""

_query = """
SELECT User.sn, User.givenName, User.DN
BASE User BASE "cn=Sebastian Denz,ou=people,ou=Technik,dc=gonicus,dc=de"
ORDER BY User.sn, User.givenName DESC
"""

sw = SearchWrapper.get_instance()
pprint(sw.execute(query))

