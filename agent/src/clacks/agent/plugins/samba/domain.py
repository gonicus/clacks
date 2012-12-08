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

from datetime import date, datetime
from time import mktime
from clacks.common.utils import N_
from zope.interface import implements
from clacks.common.components import Plugin
from clacks.common.handler import IInterfaceHandler
from clacks.common.components import PluginRegistry
from clacks.common.components import Command
from clacks.agent.objects.comparator import ElementComparator


class SambaGuiMethods(Plugin):
    implements(IInterfaceHandler)
    _target_ = 'gosa'
    _priority_ = 80

    @Command(__help__=N_("Returns the current samba domain policy for a given user"))
    def getSambaDomainInformation(self, target_object):

        # Use proxy if available
        _self = target_object

        sambaMinPwdLength = "unset"
        sambaPwdHistoryLength = "unset"
        sambaLogonToChgPwd = "unset"
        sambaMaxPwdAge = "unset"
        sambaMinPwdAge = "unset"
        sambaLockoutDuration = "unset"
        sambaLockoutThreshold = "unset"
        sambaForceLogoff = "unset"
        sambaRefuseMachinePwdChange = "unset"
        sambaPwdLastSet = "unset"
        sambaLogonTime = "unset"
        sambaLogoffTime = "unset"
        sambaKickoffTime = "unset"
        sambaPwdCanChange = "unset"
        sambaPwdMustChange = "unset"
        sambaBadPasswordCount = "unset"
        sambaBadPasswordTime = "unset"

        # Domain attributes
        domain_attributes = ["sambaMinPwdLength","sambaPwdHistoryLength","sambaMaxPwdAge",
                "sambaMinPwdAge","sambaLockoutDuration","sambaRefuseMachinePwdChange",
                "sambaLogonToChgPwd","sambaLockoutThreshold","sambaForceLogoff"]

        # User attributes
        user_attributes = ["sambaBadPasswordTime","sambaPwdLastSet","sambaLogonTime","sambaLogoffTime",
                "sambaKickoffTime","sambaPwdCanChange","sambaPwdMustChange","sambaBadPasswordCount", "sambaSID"]

        index = PluginRegistry.getInstance("ObjectIndex")
        res = index.search({'_type': 'SambaDomain', 'sambaDomainName': _self.sambaDomainName}, dict(zip(domain_attributes, [1 for n in domain_attributes])))
        if not res.count():
            return("invalid domain selected")

        attrs = {}
        for item in domain_attributes:
            if item in res[0]:
                attrs[item] = res[0][item][0]
            else:
                attrs[item] = "unset"

        for item in user_attributes:
            if getattr(_self, item):
                attrs[item] = getattr(_self, item)
            else:
                attrs[item] = "unset"

        if attrs['sambaPwdMustChange'] and attrs['sambaPwdMustChange'] != "unset":
            attrs['sambaPwdMustChange'] = date.fromtimestamp(int(attrs['sambaPwdMustChange'])).strftime("%d.%m.%Y")
        if attrs['sambaKickoffTime'] and attrs['sambaKickoffTime'] != "unset":
            attrs['sambaKickoffTime'] = date.fromtimestamp(int(attrs['sambaKickoffTime'])).strftime("%d.%m.%Y")

        # sambaMinPwdLength: Password length has a default of 5
        if attrs['sambaMinPwdLength'] == "unset" or int(attrs['sambaMinPwdLength']) == 5:
            attrs['sambaMinPwdLength'] = "5 <i>(" + N_("default") + ")</i>"

        # sambaPwdHistoryLength: Length of Password History Entries (default: 0 => off)
        if attrs['sambaPwdHistoryLength'] == "unset" or int(attrs['sambaPwdHistoryLength']) == 0:
            attrs['sambaPwdHistoryLength'] = N_("Off") + " <i>(" + N_("default") + ")</i>"

        # sambaLogonToChgPwd: Force Users to logon for password change (default: 0 => off, 2 => on)
        if attrs['sambaLogonToChgPwd'] == "unset" or int(attrs['sambaLogonToChgPwd']) == 0:
            attrs['sambaLogonToChgPwd'] = N_("Off") + " <i>(" + N_("default") + ")</i>"
        else:
            attrs['sambaLogonToChgPwd'] = N_("On")

        # sambaMaxPwdAge: Maximum password age, in seconds (default: -1 => never expire passwords)'
        if attrs['sambaMaxPwdAge'] == "unset" or int(attrs['sambaMaxPwdAge']) <= 0:
            attrs['sambaMaxPwdAge'] = N_("disabled") + " <i>(" + N_("default") + ")</i>"
        else:
            attrs['sambaMaxPwdAge'] += " " + N_("seconds")

        # sambaMinPwdAge: Minimum password age, in seconds (default: 0 => allow immediate password change
        if attrs['sambaMinPwdAge'] == "unset" or int(attrs['sambaMinPwdAge']) <= 0:
            attrs['sambaMinPwdAge'] = N_("disabled") + " <i>(" + N_("default") + ")</i>"
        else:
            attrs['sambaMinPwdAge'] += " " + N_("seconds")

        # sambaLockoutDuration: Lockout duration in minutes (default: 30, -1 => forever)
        if attrs['sambaLockoutDuration'] == "unset" or int(attrs['sambaLockoutDuration']) == 30:
            attrs['sambaLockoutDuration'] = "30 " + N_("minutes") + " <i>(" + N_("default") + ")</i>"
        elif attrs['sambaLockoutDuration'] == -1:
            attrs['sambaLockoutDuration'] = N_("forever")
        else:
            attrs['sambaLockoutDuration'] += " " + N_("minutes")

        # sambaLockoutThreshold: Lockout users after bad logon attempts (default: 0 => off
        if attrs['sambaLockoutThreshold'] == "unset" or int(attrs['sambaLockoutThreshold']) == 0:
            attrs['sambaLockoutThreshold'] = N_("disabled") + " <i>(" + N_("default") + ")</i>"

        # sambaForceLogoff: Disconnect Users outside logon hours (default: -1 => off, 0 => on
        if attrs['sambaForceLogoff'] == "unset" or int(attrs['sambaForceLogoff']) == -1:
            attrs['sambaForceLogoff'] = N_("off") + " <i>(" + N_("default") + ")</i>"
        else:
            attrs['sambaForceLogoff'] = N_("on")

        # sambaRefuseMachinePwdChange: Allow Machine Password changes (default: 0 => off
        if attrs['sambaRefuseMachinePwdChange'] == "unset" or int(attrs['sambaRefuseMachinePwdChange']) == 0:
            attrs['sambaRefuseMachinePwdChange'] = N_("off") + " <i>(" + N_("default") + ")</i>"
        else:
            attrs['sambaRefuseMachinePwdChange'] = N_("on")

        # sambaBadPasswordTime: Time of the last bad password attempt
        if attrs['sambaBadPasswordTime'] == "unset" or not attrs['sambaBadPasswordTime']:
            attrs['sambaBadPasswordTime'] = "<i>(" + N_("unset") + ")</i>"
        else:
            attrs['sambaRefuseMachinePwdChange'] = date.fromtimestamp(int(attrs['sambaBadPasswordTime'])).strftime("%d.%m.%Y")

        # sambaBadPasswordCount: Bad password attempt count
        if attrs['sambaBadPasswordCount'] == "unset" or not attrs['sambaBadPasswordCount']:
            attrs['sambaBadPasswordCount'] = "<i>(" + N_("unset") + ")</i>"
        else:
            attrs['sambaBadPasswordCount'] = date.fromtimestamp(int(attrs['sambaBadPasswordCount'])).strftime("%d.%m.%Y")

        # sambaPwdLastSet: Timestamp of the last password update
        if attrs['sambaPwdLastSet'] == "unset" or not attrs['sambaPwdLastSet']:
            attrs['sambaPwdLastSet'] = "<i>(" + N_("unset") + ")</i>"
        else:
            attrs['sambaPwdLastSet'] = date.fromtimestamp(int(attrs['sambaPwdLastSet'])).strftime("%d.%m.%Y")

        # sambaLogonTime: Timestamp of last logon
        if attrs['sambaLogonTime'] == "unset" or not attrs['sambaLogonTime']:
            attrs['sambaLogonTime'] = "<i>(" + N_("unset") + ")</i>"
        else:
            attrs['sambaLogonTime'] = date.fromtimestamp(int(attrs['sambaLogonTime'])).strftime("%d.%m.%Y")

        # sambaLogoffTime: Timestamp of last logoff
        if attrs['sambaLogoffTime'] == "unset" or not attrs['sambaLogoffTime']:
            attrs['sambaLogoffTime'] = "<i>(" + N_("unset") + ")</i>"
        else:
            attrs['sambaLogoffTime'] = date.fromtimestamp(int(attrs['sambaLogoffTime'])).strftime("%d.%m.%Y")

        # sambaKickoffTime: Timestamp of when the user will be logged off automatically
        if attrs['sambaKickoffTime'] == "unset" or not attrs['sambaKickoffTime']:
            attrs['sambaKickoffTime'] = "<i>(" + N_("unset") + ")</i>"

        # sambaPwdMustChange: Timestamp of when the password will expire
        if attrs['sambaPwdMustChange'] == "unset" or not attrs['sambaPwdMustChange']:
            attrs['sambaPwdMustChange'] = "<i>(" + N_("unset") + ")</i>"

        # sambaPwdCanChange: Timestamp of when the user is allowed to update the password
        time_now = mktime(datetime.now().timetuple())
        if attrs['sambaPwdCanChange'] == "unset" or not attrs['sambaPwdCanChange']:
            attrs['sambaPwdCanChange'] = "<i>(" + N_("unset") + ")</i>"
        elif attrs['sambaPwdCanChange'] != "unset" and time_now > int(attrs['sambaPwdCanChange']):
            attrs['sambaPwdCanChange'] = N_("immediately")
        else:
            days = int((int(attrs['sambaPwdCanChange']) - time_now) / (60*60*24))
            hours = int(((int(attrs['sambaPwdCanChange']) - time_now) / (60*60)) % 24)
            minutes = int(((int(attrs['sambaPwdCanChange']) - time_now) / (60)) % 60)
            attrs['sambaPwdCanChange'] = " " + days    + " " + N_("days")
            attrs['sambaPwdCanChange']+= " " + hours   + " " + N_("hours")
            attrs['sambaPwdCanChange']+= " " + minutes + " " + N_("minutes")


        res = "\n<div style='height:200px; overflow: auto;'>" + \
            "\n<table style='width:100%;'>" + \
            "\n<tr><td><b>" + N_("Domain attributes") + "</b></td></tr>" + \
            "\n<tr><td>" + N_("Min password length") + ":           </td><td>" + attrs['sambaMinPwdLength'] + "</td></tr>" + \
            "\n<tr><td>" + N_("Min password length") + ":           </td><td>" + attrs['sambaMinPwdLength'] + "</td></tr>" + \
            "\n<tr><td>" + N_("Password history") + ":              </td><td>" + attrs['sambaPwdHistoryLength'] + "</td></tr>" + \
            "\n<tr><td>" + N_("Force password change") + ":         </td><td>" + attrs['sambaLogonToChgPwd'] + "</td></tr>" + \
            "\n<tr><td>" + N_("Maximum password age") + ":          </td><td>" + attrs['sambaMaxPwdAge'] + "</td></tr>" + \
            "\n<tr><td>" + N_("Minimum password age") + ":          </td><td>" + attrs['sambaMinPwdAge'] + "</td></tr>" + \
            "\n<tr><td>" + N_("Lockout duration") + ":              </td><td>" + attrs['sambaLockoutDuration'] + "</td></tr>" + \
            "\n<tr><td>" + N_("Bad lockout attempt") + ":           </td><td>" + attrs['sambaLockoutThreshold'] + "</td></tr>" + \
            "\n<tr><td>" + N_("Disconnect time") + ":               </td><td>" + attrs['sambaForceLogoff'] + "</td></tr>" + \
            "\n<tr><td>" + N_("Refuse machine password change") + ":</td><td>" + attrs['sambaRefuseMachinePwdChange'] + "</td></tr>" + \
            "\n<tr><td>&nbsp;</td></tr>" + \
            "\n<tr><td><b>" + N_("User attributes") + "</b></td></tr>" + \
            "\n<tr><td>" + N_("SID") + ":                           </td><td>" + attrs['sambaSID'] + "</td></tr>" + \
            "\n<tr><td>" + N_("Last failed login") + ":             </td><td>" + attrs['sambaBadPasswordTime'] + "</td></tr>" + \
            "\n<tr><td>" + N_("Log on attempts") + ":                </td><td>"+ attrs['sambaBadPasswordCount'] + "</td></tr>" + \
            "\n<tr><td>" + N_("Last password update") + ":          </td><td>" + attrs['sambaPwdLastSet'] + "</td></tr>" + \
            "\n<tr><td>" + N_("Last log on") + ":                    </td><td>"+ attrs['sambaLogonTime'] + "</td></tr>" + \
            "\n<tr><td>" + N_("Last log off") + ":                   </td><td>"+ attrs['sambaLogoffTime'] + "</td></tr>" + \
            "\n<tr><td>" + N_("Automatic log off") + ":              </td><td>"+ attrs['sambaKickoffTime'] + "</td></tr>";

        return res


class IsValidSambaDomainName(ElementComparator):
    """
    Validates a given sambaDomainName.
    """

    def __init__(self, obj):
        super(IsValidSambaDomainName, self).__init__()

    def process(self, all_props, key, value):
        domain = value[0]
        errors = []
        index = PluginRegistry.getInstance("ObjectIndex")

        res = index.search({'_type': 'SambaDomain', 'sambaDomainName': domain},
            {'_uuid': 1})

        if res.count():
            return True, errors

        errors.append(dict(index=0, detail=N_("Unknown domain '%(domain)s'"), domain=value[0]))

        return False, errors
