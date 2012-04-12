# -*- coding: utf-8 -*-
from amires.resolver import PhoneNumberResolver
from clacks.common.components.cache import cache
from clacks.common.components import PluginRegistry
from clacks.agent.objects import ObjectProxy


class ClacksNumberResolver(PhoneNumberResolver):

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
        #TODO: escaping of number
        res = index.xquery("collection('objects')/o:User[*/o:telephoneNumber = '%s']/o:DN/string()" % str(number))

        if len(res) == 1:
            obj = ObjectProxy(res[0])
            result = {
                    'company_id': '',
                    'company_name': 'Intern',
                    'company_phone': '',
                    'company_detail_url': '',
                    'contact_id': obj.uid,
                    'contact_name': obj.cn,
                    'contact_phone': obj.telephoneNumber[0],
                    'contact_detail_url': '',
                    'avatar': obj.jpegPhoto,
                    'ldap_uid': obj.uid,
                    'resource': 'ldap',
            }
            return result

        return None
