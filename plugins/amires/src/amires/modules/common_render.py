# -*- coding: utf-8 -*-
import cgi
import pkg_resources
import gettext
from amires.render import BaseRenderer
from clacks.common import Environment

# Set locale domain
t = gettext.translation('messages', pkg_resources.resource_filename("amires",
"locale"),
        fallback=False)
_ = t.ugettext


class CommonRenderer(BaseRenderer):

    priority = 1

    def __init__(self):
        pass

    def getHTML(self, info, event):
        super(CommonRenderer, self).getHTML(info)

        # build html for company name
        comp = u""
        if info['company_name']:
            if 'company_detail_url' in info and info['company_detail_url']:
                comp += "<a href='%s'>%s</a>" %(
                    cgi.escape(info['company_detail_url']),
                    cgi.escape(info['company_name']))
            else:
                comp += cgi.escape(info['company_name'])

        # build html for contact name
        cont = u""
        if info['contact_name']:
            if 'contact_detail_url' in info and info['contact_detail_url']:
                cont += "<a href='%s'>%s</a>" %(
                    cgi.escape(info['contact_detail_url']),
                    cgi.escape(info['contact_name']))
            else:
                cont += cgi.escape(info['contact_name'])

        # build actual html section
        html = u"<b>%s:</b>\n" % cgi.escape(_("Attendee"))
        if cont:
            html += cont
            if comp:
                html += " (" + comp + ")"
        elif comp:
            html += comp

        if 'Duration' in event:
            duration = int(float(event['Duration']))
            html += "\n\n<b>%s:</b> " % cgi.escape(_("Duration"))
            html += "%d\'%02d\"\n" % (duration / 60, duration % 60)

        return html
