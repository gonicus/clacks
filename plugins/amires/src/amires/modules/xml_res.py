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

from lxml import etree
from clacks.common.components.cache import cache
from amires.resolver import PhoneNumberResolver


class XMLNumberResolver (PhoneNumberResolver):
    """
    Configuration keys for section **resolver-xml**

    +------------------+------------+-------------------------------------------------------------+
    + Key              | Format     +  Description                                                |
    +==================+============+=============================================================+
    + priority         | Integer    + Priority of this resolver.                                  |
    +------------------+------------+-------------------------------------------------------------+
    + filename         | String     + Filename for the configuration file.                        |
    +------------------+------------+-------------------------------------------------------------+

    """
    priority = 2

    def __init__(self):
        super(XMLNumberResolver, self).__init__()

        # read config
        filename = self.env.config.get("resolver-xml.filename",
             default="./numbers.xml")

        try:
            self.priority = float(self.env.config.get("resolver-xml.priority",
                default=str(self.priority)))
        except:
            # leave default priority
            pass

        xml = etree.parse(filename).getroot()

        self.numbers = {}
        for entry in xml:
            number = entry.get("number")
            self.numbers[number] = {
                'company_id': '',
                'company_name': '',
                'company_phone': '',
                'company_detail_url': '',
                'contact_id': '',
                'contact_name': '',
                'contact_phone': number,
                'ldap_uid': '',
                'contact_detail_url': ''}
            for e in entry:
                if e.tag not in self.numbers[number]:
                    raise RuntimeError("Invalid XML element while parsing.")

                self.numbers[number][e.tag] = e.text

    @cache()
    def resolve(self, number):
        if number in self.numbers:
            self.numbers[number]['resource'] = "xml"
            return self.numbers[number]
        else:
            return None
