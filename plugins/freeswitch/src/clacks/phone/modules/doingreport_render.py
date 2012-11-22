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

import pkg_resources
import gettext
import math
from datetime import datetime
from clacks.phone.render import BaseRenderer, mr
from clacks.common import Environment
from sqlalchemy import Column, String
from sqlalchemy.sql import select, and_


# Set locale domain
t = gettext.translation('messages', pkg_resources.resource_filename("clacks.phone", "locale"), fallback=False)
_ = t.ugettext


class DoingReportRenderer(BaseRenderer):
    """
    Configuration keys for section **resolver-ldap**

    +------------------+------------+-------------------------------------------------------------+
    + Key              | Format     +  Description                                                |
    +==================+============+=============================================================+
    + users            | String     + Comma separated list of user IDs that get automatic report  |
    +                  |            + entries on phone calls.                                     |
    +------------------+------------+-------------------------------------------------------------+

    Configuration keys for section **fetcher-goforge**

    +------------------+------------+-------------------------------------------------------------+
    + Key              | Format     +  Description                                                |
    +==================+============+=============================================================+
    + site-url         | String     + URL to the goforge setup.                                   |
    +------------------+------------+-------------------------------------------------------------+

    """
    priority = 20

    def __init__(self):
        self.env = env = Environment.getInstance()

        self.whitelisted_users = self.env.config.get("doingreport.users")
        if self.whitelisted_users:
            self.whitelisted_users = [s.strip() for s in self.whitelisted_users.split(",")]

        self.forge_url = self.env.config.get("fetcher-goforge.site-url",
            default="http://localhost/")

    def getHTML(self, particiantInfo, selfInfo, event):
        super(DoingReportRenderer, self).getHTML(particiantInfo, selfInfo, event)

        if event['Type'] != "CallEnded":
            return ""
        if not "Duration" in event:
            return ""

        ldap_uid = selfInfo['ldap_uid'] if 'ldap_uid' in selfInfo else None
        if not ldap_uid:
            return ""

        # Filter out white listed users
        if self.whitelisted_users and not ldap_uid in self.whitelisted_users:
            return ""

        company_id = particiantInfo['company_id'] if 'company_id' in particiantInfo else None
        contact_name = particiantInfo['contact_name'] if 'contact_name' in particiantInfo else None
        contact_phone = particiantInfo['contact_phone'] if 'contact_phone' in particiantInfo else None
        company_name = particiantInfo['company_name'] if 'company_name' in particiantInfo else None
        company_phone = particiantInfo['company_phone'] if 'company_phone' in particiantInfo else None

        if not (contact_name or company_name or company_phone or contact_phone):
            return ""

        # Connect to GOforge db
        sess = self.env.getDatabaseSession("fetcher-goforge")

        # Lookup GOforge user_id from ldap_uid
        res = sess.execute(select(['user_id'], Column(String(), name='user_name').__eq__(ldap_uid), 'user')).fetchone()
        if not res:
            sess.close()
            return ""

        user_id = int(res[0])

        # Lookup GOforge customer ID from sugar company_id
        customer_id = None
        if company_id:
            res = sess.execute(select(['customer_id'], Column(String(),
                name='customer_unique_ldap_attribute').__eq__(company_id), 'customer')).fetchone()

            if res:
                customer_id = int(res[0])

        # Assemble new entry for TB
        date = datetime.strftime(datetime.utcnow(), "%Y.%m.%d")
        minutes = int(math.ceil(float(event["Duration"]) / 60))
        details = "Please amend"
        comment = "Phone call with %s" % contact_name or contact_phone or company_name or company_phone

        if customer_id:
            sess.execute("""
                INSERT INTO doingreport (user_id, customer_id, date, minutes, details, comments, flag)
                VALUES (:user_id, :customer_id, :date, :minutes, :details, :comments, '?')""",
                dict(
                    user_id=user_id,
                    customer_id=customer_id,
                    date=date,
                    minutes=minutes,
                    details=mr(details).encode('ascii', 'xmlcharrefreplace'),
                    comment=mr(comment).encode('ascii', 'xmlcharrefreplace')))
        else:
            sess.execute("""
                INSERT INTO doingreport (user_id, date, minutes, details, comments, flag)
                VALUES (:user_id, :date, :minutes, :details, :comments, '?')""",
                dict(
                    user_id=user_id,
                    date=date,
                    minutes=minutes,
                    details=mr(details).encode('ascii', 'xmlcharrefreplace'),
                    comments=mr(comment).encode('ascii', 'xmlcharrefreplace')))

        # Eventually we need to create an entry in doing_account in order
        # to make the TB editable.
        res = sess.execute(select(['id'], and_(
            Column(String(), name='date').__eq__(date),
            Column(String(), name='user_id').__eq__(user_id)),
            'doing_account')).fetchone()
        if not res:
            sess.execute("""
                INSERT INTO doing_account (date, user_id, account_user, account_billing)
                VALUES(:date, :user_id, 'no', 'no');
            """, dict(date=date, user_id=user_id))

        sess.close()
        return ""
