# -*- coding: utf-8 -*-
import re
from amires.resolver import PhoneNumberResolver
from clacks.common.components.cache import cache
from sqlalchemy import Column, String
from sqlalchemy.sql import select, or_


class SugarNumberResolver(PhoneNumberResolver):

    priority = 5

    def __init__(self):
        super(SugarNumberResolver, self).__init__()

        self.priority = float(self.env.config.get("resolver-sugar.priority",
            default=str(self.priority)))
        self.sugar_url = self.env.config.get("resolver-sugar.site_url",
            default="http://localhost/sugarcrm")

    @cache(ttl=3600)
    def resolve(self, number):
        number = self.replaceNumber(number)

        # split optional country code from rest of number
        res = re.match(r"^(\+([0-9]{2}))?([0-9]*)$", number)
        if res is None:
            return None

        country = res.group(2)
        rest = res.group(3)
        found = False

        # build regular expression for DB search
        sep = "[-[:blank:]/()]*"
        regex = "^"

        if country is not None:
            regex += r"((\+" + country + ")|(0))" + sep
            regex += r"(0)?" + sep

        for c in rest:
            regex += c + sep

        regex += "$"

        # query database
        result = {
            'company_id': '',
            'company_name': '',
            'company_phone': '',
            'company_detail_url': '',
            'contact_id': '',
            'contact_name': '',
            'contact_phone': '',
            'contact_detail_url': '',
            'ldap_uid': '',
            'resource': 'sugar'}

        # query for accounts
        sess = self.env.getDatabaseSession("resolver-sugar")
        dat = sess.execute(select(['id', 'name', 'phone_office'], Column(String(), name='phone_office').op('regexp')(regex), 'accounts')).fetchone()

        if dat:

            # fill result data with found data
            if dat[0] is not None:
                result['company_id'] = dat[0]
                result['company_detail_url'] = self.sugar_url \
                    + '/index.php?module=Accounts&action=DetailView' \
                    + '&record=' + dat[0]
            if dat[1] is not None:
                result['company_name'] = dat[1]
            if dat[2] is not None:
                result['company_phone'] = dat[2]

            found = True
        else:
            # query for contacts
            dat = sess.execute(select(['id', 'first_name', 'last_name', 'phone_work'],
                    or_(Column(String(), name='phone_work').op('regexp')(regex),
                        Column(String(), name='phone_home').op('regexp')(regex),
                        Column(String(), name='phone_mobile').op('regexp')(regex),
                        Column(String(), name='phone_other').op('regexp')(regex)),
                    'contacts')).fetchone()

            if dat:

                # fill result data with found data
                result['contact_id'] = dat[0]
                if dat[1] is not None:
                    result['contact_name'] = dat[1]
                if dat[2] is not None:
                    if not result['contact_name'] == '':
                        result['contact_name'] += ' '
                    result['contact_name'] += dat[2]
                if dat[3] is not None:
                    result['contact_phone'] = dat[3]
                result['contact_detail_url'] = self.sugar_url \
                    + 'index.php?module=Contacts&action=DetailView' \
                    + '&record=' + dat[0]

                found = True

                dat = sess.execute(select(['account_id'],
                    Column(String(), name='contact_id').__eq__(dat[0]),
                    'accounts_contacts')).fetchone()

                if dat:
                    dat = sess.execute(select(['id', 'name', 'phone_office'],
                        Column(String(), name='id').__eq__(dat[0]),
                        'accounts')).fetchone()

                    if dat:
                        if dat[0] is not None:
                            result['company_id'] = dat[0]
                            result['company_detail_url'] = self.sugar_url \
                                + 'index.php?module=Accounts&action=DetailView'\
                                + '&record=' + dat[0]
                        if dat[1] is not None:
                            result['company_name'] = dat[1]
                        if dat[2] is not None:
                            result['company_phone'] = dat[2]

        # Close session
        sess.close()

        # return what was found
        if found == False:
            return None

        result['resource'] = 'sugar'
        return result
