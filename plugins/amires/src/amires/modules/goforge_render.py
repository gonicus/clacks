# -*- coding: utf-8 -*-
import cgi
import pkg_resources
import gettext
from amires.render import BaseRenderer
from clacks.common import Environment
from sqlalchemy import Column, String
from sqlalchemy.sql import select, and_


# Set locale domain
t = gettext.translation('messages', pkg_resources.resource_filename("amires", "locale"), fallback=False)
_ = t.ugettext


class GOForgeRenderer(BaseRenderer):

    priority = 10

    def __init__(self):
        self.env = env = Environment.getInstance()

        # Connect to GOforge db
        self.__sess = self.env.getDatabaseSession("fetcher-goforge")

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

        # obtain GOforge internal customer id
        res = self.__sess.execute(select(['customer_id'],
            Column(String(), name='customer_unique_ldap_attribute').__eq__(company_id),
            'customer'))

        if res.rowcount == 1:
            row = res.fetchone()

            # fetch tickets from database
            rows = self.__sess.execute(select(['bug.id', 'bug.summary', 'bug.group_id', 'user.user_name'],
                and_(Column(String(), name='bug.status_id').__eq__(1),
                    Column(String(), name='bug.assigned_to').__eq__(Column(String(), name='user.user_id')),
                    Column(String(), name='bug.customer_id').__eq__(row[0])),
                ['bug', 'user']).limit(29)).fetchall()

            # put results into dictionary
            for row in rows:
                result.append({'id': row[0],
                    'summary': row[1],
                    'group_id': row[2],
                    'assigned': row[3]})

            if len(result) == 0:
                return ""

            html = u"<b>%s</b>" % _("GOForge tickets")
            more = ""
            try:
                more = row['summary'].encode('raw_unicode_escape').decode('utf-8')
            except:
                import traceback
                print "="*80
                print "nicht enkodierbar:"
                print row
                print "-"*80
                traceback.print_exc()
                print "="*80

            for row in result:
                html += u"\n<a href='%s'>%s</a> %s" %(
                    self.forge_url + "/bugs/?func=detailbug" \
                        + "&bug_id=" + str(row['id']) \
                        + "&group_id=" + str(row['group_id']),
                    row['id'],
                    cgi.escape(more))

        return html
