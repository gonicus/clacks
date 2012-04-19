# -*- coding: utf-8 -*-
import MySQLdb
import pkg_resources
import gettext
import math
from datetime import datetime
from amires.render import BaseRenderer
from clacks.common import Environment

# Set locale domain
t = gettext.translation('messages', pkg_resources.resource_filename("amires", "locale"), fallback=False)
_ = t.ugettext


class DoingReportRenderer(BaseRenderer):

    priority = 20

    def __init__(self):
        self.env = env = Environment.getInstance()
        host = env.config.get("fetcher-goforge.host",
            default="localhost")
        user = env.config.get("fetcher-goforge.user",
            default="root")
        passwd = env.config.get("fetcher-goforge.pass",
            default="")
        db = env.config.get("fetcher-goforge.base",
            default="goforge")

        # connect to GOforge db
        self.forge_db = MySQLdb.connect(host=host,
            user=user, passwd=passwd, db=db, charset="latin1")

        self.whitelisted_users = self.env.config.get("doingreport.users")
        if self.whitelisted_users:
            self.whitelisted_users = [s.strip() for s in self.whitelisted_users.split(",")]

        self.forge_url = self.env.config.get("fetcher-goforge.site_url",
            default="http://localhost/")

    def getHTML(self, particiantInfo, selfInfo, event):
        super(DoingReportRenderer, self).getHTML(particiantInfo, selfInfo, event)

        if event['Type'] != "CallEnded":
            return ""
        if not "Duration" in event:
            return ""
        #TODO: threshold?

        ldap_uid = selfInfo['ldap_uid'] if 'ldap_uid' in selfInfo else None
        if not ldap_uid:
            return ""

        #TODO: remove me
        if self.whitelisted_users and not ldap_uid in self.whitelisted_users:
            return ""

        company_id = particiantInfo['company_id'] if 'company_id' in particiantInfo else None
        contact_name = particiantInfo['contact_name'] if 'contact_name' in particiantInfo else None
        contact_phone = particiantInfo['contact_phone'] if 'contact_phone' in particiantInfo else None
        company_name = particiantInfo['company_name'] if 'company_name' in particiantInfo else None
        company_phone = particiantInfo['company_phone'] if 'company_phone' in particiantInfo else None

        if not (contact_name or company_name or company_phone or contact_phone):
            return ""

        cursor = self.forge_db.cursor()

        try:
            # Lookup GOforge user_id from ldap_uid
            res = cursor.execute("""
                SELECT user_id
                FROM user
                WHERE user_name = %s""",
                (ldap_uid,))

            if not res:
                return ""

            user_id = int(cursor.fetchone()[0])

            # Lookup GOforge customer ID from sugar company_id
            customer_id = None
            if company_id:
                res = cursor.execute("""
                    SELECT customer_id
                    FROM customer
                    WHERE customer_unique_ldap_attribute = %s""",
                    (company_id,))

                if res:
                    customer_id = int(cursor.fetchone()[0])

            # Assemble new entry for TB
            date = datetime.strftime(datetime.utcnow(), "%Y.%m.%d")
            minutes = int(math.ceil(float(event["Duration"]) % 60))
            details = u"Bitte ergänzen"
            comment = "Telefonat mit %s" % contact_name or contact_phone or company_name or company_phone

            if customer_id:
                cursor.execute("""
                    INSERT INTO doingreport (user_id, customer_id, date, minutes, details, comments)
                    VALUES (%s, %s, %s, %s, %s, %s)""", (user_id, customer_id,
                        date, minutes, details.encode('ascii', 'xmlcharrefreplace'),
                        comment.encode('ascii', 'xmlcharrefreplace')))
            else:
                cursor.execute("""
                    INSERT INTO doingreport (user_id, date, minutes, details, comments)
                    VALUES (%s, %s, %s, %s, %s)""", (user_id, date, minutes,
                        details.encode('ascii', 'xmlcharrefreplace'),
                        comment.encode('ascii', 'xmlcharrefreplace')))

        finally:
            cursor.close()

        return ""
