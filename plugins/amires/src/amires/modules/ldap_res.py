# This file is part of the clacks framework.
#
#  http://clacks-project.org
#
# Copyright:
#  (C) 2010-2012 GONICUS GmbH, Germany, http://www.gonicus.de
#
# License:
#  GPL-2: http://www.gnu.org/licenses/gpl-2.0.html
#
# See the LICENSE file in the project's top-level directory for details.

import ldap
from clacks.agent.ldap_utils import LDAPHandler
from amires.resolver import PhoneNumberResolver
from clacks.common.components.cache import cache


class LDAPNumberResolver(PhoneNumberResolver):

    priority = 4

    def __init__(self):
        super(LDAPNumberResolver, self).__init__()

        try:
            self.priority = float(self.env.config.get("resolver-ldap.priority",
                default=str(self.priority)))
        except:
            # leave default priority
            pass

    @cache(ttl=3600)
    def resolve(self, number):
        number = self.replaceNumber(number)

        filtr = ldap.filter.filter_format("(&(uid=*)(telephoneNumber=%s))", [str(number)])
        attrs = ['cn', 'uid', 'telephoneNumber', 'jpegPhoto']

        # search ldap
        lh = LDAPHandler.get_instance()
        with lh.get_handle() as conn:
            res = conn.search_s(lh.get_base(), ldap.SCOPE_SUBTREE, filtr, attrs)
            if len(res) == 1:
                result = {
                        'company_id': '',
                        'company_name': 'Intern',
                        'company_phone': '',
                        'company_detail_url': '',
                        'contact_id': res[0][1]['uid'][0],
                        'contact_name': unicode(res[0][1]['cn'][0], 'UTF-8'),
                        'contact_phone': res[0][1]['telephoneNumber'][0],
                        'contact_detail_url': '',
                        'avatar': res[0][1]['jpegPhoto'][0] if 'jpegPhoto' in res[0][1] else None,
                        'ldap_uid': res[0][1]['uid'][0],
                        'resource': 'ldap',
                }
                return result
            else:
                return None
