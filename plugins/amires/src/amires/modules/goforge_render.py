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

import cgi
import pkg_resources
import gettext
from amires.render import BaseRenderer, mr
from clacks.common import Environment
from sqlalchemy import Table, Column, String, Integer, MetaData
from sqlalchemy.sql import select, and_


# Set locale domain
t = gettext.translation('messages', pkg_resources.resource_filename("amires", "locale"), fallback=False)
_ = t.ugettext


class GOForgeRenderer(BaseRenderer):
    """
    Configuration keys for section **fetcher-goforge**

    +------------------+------------+-------------------------------------------------------------+
    + Key              | Format     +  Description                                                |
    +==================+============+=============================================================+
    + site-url         | String     + URL to the goforge site.                                    |
    +------------------+------------+-------------------------------------------------------------+

    """
    priority = 10

    def __init__(self):
        self.env = env = Environment.getInstance()

        self.forge_url = self.env.config.get("fetcher-goforge.site_url",
            default="http://localhost/")

    def getHTML(self, particiantInfo, selfInfo, event):
        super(GOForgeRenderer, self).getHTML(particiantInfo, selfInfo, event)

        if not 'company_id' in particiantInfo:
            return ""

        company_id = particiantInfo['company_id']
        if not company_id:
            return ""

        # prepare result
        result = []
        html = ""

        # Connect to GOforge db
        sess = self.env.getDatabaseSession("fetcher-goforge")

        # obtain GOforge internal customer id
        res = sess.execute(select(['customer_id'],
            Column(String(), name='customer_unique_ldap_attribute').__eq__(company_id),
            'customer'))

        if res.rowcount == 1:
            row = res.fetchone()

            # fetch tickets from database
            m = MetaData()
            bug = Table('bug', m,
                    Column('bug_id', Integer),
                    Column('summary', String),
                    Column('group_id', String),
                    Column('status_id', Integer),
                    Column('assigned_to', Integer),
                    Column('customer_id', Integer))
            user = Table('user', m,
                    Column('user_name', String),
                    Column('user_id', Integer))
            rows = sess.execute(select([bug.c.bug_id, bug.c.summary, bug.c.group_id, user.c.user_name],
                and_(bug.c.status_id == 1, bug.c.assigned_to == user.c.user_id,
                    bug.c.customer_id == row[0]),
                [bug, user]).limit(29)).fetchall()

            # put results into dictionary
            for row in rows:
                result.append({'id': row[0],
                    'summary': row[1],
                    'group_id': row[2],
                    'assigned': row[3]})

            if len(result) == 0:
                sess.close()
                return ""

            html = u"<b>%s</b>" % _("GOForge tickets")

            for row in result:
                html += u"\n<a href='%s'>%s</a> %s" %(
                    self.forge_url + "/bugs/?func=detailbug" \
                        + "&bug_id=" + str(row['id']) \
                        + "&group_id=" + str(row['group_id']),
                    row['id'],
                    cgi.escape(mr(row['summary'])))

        sess.close()
        return html
