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

from clacks.phone.resolver import PhoneNumberResolver
from clacks.common.components.cache import cache
from clacks.common.components import PluginRegistry
from clacks.agent.objects import ObjectProxy


class ClacksNumberResolver(PhoneNumberResolver):
    """
    Configuration keys for section **resolver-clacks**

    +------------------+------------+-------------------------------------------------------------+
    + Key              | Format     +  Description                                                |
    +==================+============+=============================================================+
    + priority         | Integer    + Priority for this resolver.                                 |
    +------------------+------------+-------------------------------------------------------------+

    """
    priority = 4

    def __init__(self):
        super(ClacksNumberResolver, self).__init__()

        try:
            self.priority = float(self.env.config.get("resolver-clacks.priority",
                default=str(self.priority)))
        except:
            # leave default priority
            pass

    @cache(ttl=3600)
    def resolve(self, number):
        number = self.replaceNumber(number)

        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'_type': 'User', 'telephoneNumber': str(number)},
            {'dn': 1})

        if res.count() != 1:
            res = index.search({'_type': 'User', 'uid': str(number)},
                {'dn': 1})

        if res.count() == 1:
            obj = ObjectProxy(res[0]['dn'])
            result = {
                    'company_id': '',
                    'company_name': 'Intern',
                    'company_phone': '',
                    'company_detail_url': '',
                    'contact_id': obj.uid,
                    'contact_name': obj.cn,
                    'contact_phone': obj.telephoneNumber[0],
                    'contact_detail_url': '',
                    'avatar': obj.jpegPhoto.get() if obj.jpegPhoto else None,
                    'ldap_uid': obj.uid,
                    'resource': 'ldap',
            }

            return result

        return None
